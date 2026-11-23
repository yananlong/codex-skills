#!/usr/bin/env bash
# Download OpenReview PDFs with the clearanceToken cookie from the attached Chrome.
#   fetch_pdfs.sh -i IDS.tsv -o OUTDIR [-p PORT] [-s SCRATCH] [-d DELAY_SECONDS]
# AGENT_BROWSER names the agent-browser executable (default: agent-browser on PATH).
# CDP_PORT sets the default port (9222). SCRATCH defaults to $CLAUDE_JOB_DIR/tmp when that is set.
# IDS.tsv: one "record<TAB>forum_id" per line. Output files are OUTDIR/<record>.pdf.
# Stops at the first response that is not a PDF. Re-pass the check in the browser, then rerun;
# files already present are skipped. Hard cap of 20 papers per run.
set -euo pipefail

AB="${AGENT_BROWSER:-agent-browser}"
PORT="${CDP_PORT:-9222}"
DELAY=5
IDS="" OUT=""
SCRATCH="${SCRATCH:-${CLAUDE_JOB_DIR:+$CLAUDE_JOB_DIR/tmp}}"
MAX=20

while getopts "i:o:p:s:d:" opt; do
  case $opt in
    i) IDS=$OPTARG ;;
    o) OUT=$OPTARG ;;
    p) PORT=$OPTARG ;;
    s) SCRATCH=$OPTARG ;;
    d) DELAY=$OPTARG ;;
    *) echo "usage: $0 -i IDS.tsv -o OUTDIR [-p port] [-s scratch] [-d delay]" >&2; exit 2 ;;
  esac
done
[ -f "$IDS" ] || { echo "error: -i IDS.tsv required (record<TAB>forum_id per line)" >&2; exit 2; }
[ -n "$OUT" ] || { echo "error: -o OUTDIR required (a directory used only for these PDFs)" >&2; exit 2; }
[ -n "$SCRATCH" ] || { echo "error: pass -s SCRATCH or set CLAUDE_JOB_DIR (use a private scratch directory, not a shared /tmp)" >&2; exit 2; }
awk -v d="$DELAY" 'BEGIN{exit !(d+0 >= 3)}' \
  || { echo "error: delay must be at least 3 seconds" >&2; exit 2; }
n=$(grep -c . "$IDS" || true)
[ "$n" -le "$MAX" ] || { echo "error: $n entries; this skill is for small batches (max $MAX)" >&2; exit 2; }

mkdir -p "$SCRATCH" "$OUT"
HDR=$(mktemp "$SCRATCH/hdr.XXXXXX")
trap 'rm -f "$HDR"' EXIT
chmod 600 "$HDR"

# Browser user agent, taken from CDP so it matches the browser exactly.
UA=$(curl -fsS "http://127.0.0.1:$PORT/json/version" | jq -r '."User-Agent"') \
  || { echo "error: no Chrome on CDP port $PORT; run launch_chrome.sh start" >&2; exit 1; }
case "$UA" in ""|null|*HeadlessChrome*) echo "error: unusable user agent: '$UA'" >&2; exit 1 ;; esac

# Clearance cookie. Assumes `--json cookies` prints JSON containing {name, value} objects;
# check the output shape once by hand if this fails.
TOKEN=$(env -u LD_PRELOAD "$AB" --cdp "$PORT" --json cookies get 2>/dev/null \
  | jq -r '[.. | objects | select(.name? == "openreview.clearanceToken") | .value][0] // empty') || true
[ -n "$TOKEN" ] || {
  echo "error: no openreview.clearanceToken cookie in the browser. Pass the check on a forum page first (see SKILL.md, step 4)." >&2
  exit 1
}
printf 'Cookie: openreview.clearanceToken=%s\n' "$TOKEN" >"$HDR"
unset TOKEN

MANIFEST="$OUT/manifest.tsv"
[ -f "$MANIFEST" ] || printf 'record\tforum_id\thttp\tbytes\tsha256\n' >"$MANIFEST"

first=1
while IFS=$'\t' read -r rec id _; do
  [ -n "${rec:-}" ] || continue
  [[ "$rec" =~ ^[A-Za-z0-9._-]+$ ]] || { echo "error: bad record name '$rec'" >&2; exit 2; }
  [[ "${id:-}" =~ ^[A-Za-z0-9_-]+$ ]] || { echo "error: bad forum id '${id:-}' for $rec" >&2; exit 2; }
  dest="$OUT/$rec.pdf"
  [ -e "$dest" ] && { echo "skip   $rec (exists)"; continue; }
  [ "$first" = 1 ] || sleep "$DELAY"
  first=0

  part="$dest.part"
  code=$(curl -sS -m 300 -o "$part" -w '%{http_code}' \
    -H "@$HDR" -A "$UA" -e "https://openreview.net/forum?id=$id" \
    "https://openreview.net/pdf?id=$id") || code=000
  if [ "$code" = 200 ] && [ "$(head -c4 "$part")" = "%PDF" ] && tail -c 1024 "$part" | grep -a '%%EOF' >/dev/null; then
    mv "$part" "$dest"
    printf '%s\t%s\t%s\t%s\t%s\n' "$rec" "$id" "$code" "$(stat -c %s "$dest")" \
      "$(sha256sum "$dest" | cut -d' ' -f1)" >>"$MANIFEST"
    echo "ok     $rec ($(stat -c %s "$dest") bytes)"
  else
    rm -f "$part"
    echo "FAILED $rec: HTTP $code, not a complete PDF (token expired, challenge page, or truncated)." >&2
    echo "Re-pass the check on a forum page in the browser, then rerun the same command;" >&2
    echo "finished files are skipped. Stopping to avoid hammering the site." >&2
    exit 3
  fi
done <"$IDS"
echo "done. Manifest: $MANIFEST"
