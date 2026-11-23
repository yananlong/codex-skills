#!/usr/bin/env bash
# Start Xvfb and a headed Chrome with a local-only CDP port, or stop them.
#   launch_chrome.sh [-d DISPLAY_NUM] [-p PORT] [-c CHROME] [-s SCRATCH] start
#   launch_chrome.sh [-d DISPLAY_NUM] [-p PORT] [-s SCRATCH] stop
# Settings, each overridable by the flag or by the environment variable:
#   CHROME        Chrome for Testing binary (-c); required for start, no default
#   SCRATCH       (-s) defaults to $CLAUDE_JOB_DIR/tmp when that is set; it holds the profile and pid files
#   DISPLAY_NUM   (-d) Xvfb display number, default 77
#   CDP_PORT      (-p) local CDP port, default 9222
set -euo pipefail

DISPLAY_NUM="${DISPLAY_NUM:-77}"
PORT="${CDP_PORT:-9222}"
CHROME="${CHROME:-}"
SCRATCH="${SCRATCH:-${CLAUDE_JOB_DIR:+$CLAUDE_JOB_DIR/tmp}}"

while getopts "d:p:c:s:" opt; do
  case $opt in
    d) DISPLAY_NUM=$OPTARG ;;
    p) PORT=$OPTARG ;;
    c) CHROME=$OPTARG ;;
    s) SCRATCH=$OPTARG ;;
    *) echo "usage: $0 [-d display] [-p port] [-c chrome] [-s scratch] start|stop" >&2; exit 2 ;;
  esac
done
shift $((OPTIND - 1))
ACTION=${1:-}

[ -n "$SCRATCH" ] || { echo "error: pass -s SCRATCH or set CLAUDE_JOB_DIR (use a private scratch directory, not a shared /tmp)" >&2; exit 2; }
mkdir -p "$SCRATCH"
XVFB_PID_FILE="$SCRATCH/xvfb.pid"
CHROME_PID_FILE="$SCRATCH/chrome.pid"

stop_pid_file() {
  local f=$1
  if [ -f "$f" ]; then
    kill "$(cat "$f")" 2>/dev/null || true
    rm -f "$f"
  fi
}

case "$ACTION" in
  stop)
    stop_pid_file "$CHROME_PID_FILE"
    stop_pid_file "$XVFB_PID_FILE"
    echo "stopped. Remove $SCRATCH/udd, init.js and cookie files yourself when finished."
    exit 0
    ;;
  start) ;;
  *) echo "usage: $0 [-d display] [-p port] [-c chrome] [-s scratch] start|stop" >&2; exit 2 ;;
esac

[ -n "$CHROME" ] || { echo "error: set CHROME or pass -c (Chrome for Testing binary)" >&2; exit 2; }
[ -x "$CHROME" ] || { echo "error: Chrome not found or not executable: $CHROME" >&2; exit 1; }
command -v Xvfb >/dev/null || { echo "error: Xvfb not installed (apt package xvfb)" >&2; exit 1; }
if curl -fsS "http://127.0.0.1:$PORT/json/version" >/dev/null 2>&1; then
  echo "error: something already answers on CDP port $PORT; stop it or choose another port" >&2
  exit 1
fi

# If your shell preloads tcmalloc (LD_PRELOAD=libtcmalloc...), Chrome can crash. Unset it for both children.
env -u LD_PRELOAD Xvfb ":$DISPLAY_NUM" -screen 0 1920x1080x24 -nolisten tcp \
  >"$SCRATCH/xvfb.log" 2>&1 &
echo $! >"$XVFB_PID_FILE"
sleep 1
kill -0 "$(cat "$XVFB_PID_FILE")" 2>/dev/null \
  || { echo "error: Xvfb exited; see $SCRATCH/xvfb.log (is display :$DISPLAY_NUM in use?)" >&2; exit 1; }

env -u LD_PRELOAD DISPLAY=":$DISPLAY_NUM" TZ=America/Los_Angeles LANG=en_US.UTF-8 \
  "$CHROME" \
  --remote-debugging-port="$PORT" --remote-debugging-address=127.0.0.1 \
  --user-data-dir="$SCRATCH/udd" \
  --disable-blink-features=AutomationControlled \
  --window-size=1366,850 --lang=en-US \
  --no-first-run --no-default-browser-check \
  --use-gl=angle --use-angle=swiftshader --enable-unsafe-swiftshader --ignore-gpu-blocklist \
  >"$SCRATCH/chrome.log" 2>&1 &
echo $! >"$CHROME_PID_FILE"

for _ in $(seq 1 20); do
  if curl -fsS "http://127.0.0.1:$PORT/json/version" >/dev/null 2>&1; then
    echo "chrome up: CDP 127.0.0.1:$PORT, display :$DISPLAY_NUM, profile $SCRATCH/udd"
    exit 0
  fi
  sleep 1
done
echo "error: Chrome did not open CDP port $PORT within 20 s; see $SCRATCH/chrome.log" >&2
exit 1
