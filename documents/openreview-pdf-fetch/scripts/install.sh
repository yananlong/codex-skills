#!/usr/bin/env bash
# Check for, or install, what the openreview-pdf-fetch scripts need. Never launches a browser.
#   install.sh [--check]    (default) install nothing; list missing items with the exact fix commands
#   install.sh --install    run those commands (sudo only when not root); DRY_RUN=1 prints them instead
# Contacts only the Ubuntu archives, registry.npmjs.org and storage.googleapis.com (Chrome for Testing).
# UNVERIFIED (never run to completion): the npm install layout ("npm install -g --prefix" is assumed from
# the reference host layout), the Node >= 22 requirement, the chrome-linux64/ folder inside the Chrome zip,
# the Ubuntu 24.04 t64 package names, and that the library list suffices on a fresh image.
# The Chrome for Testing zip is downloaded without a checksum (none is published next to it).
set -euo pipefail

AB_VERSION=0.43.0
CFT_VERSION=158.0.8127.36
CFT_URL="https://storage.googleapis.com/chrome-for-testing-public/$CFT_VERSION/linux64/chrome-linux64.zip"
AB_PREFIX="$HOME/.local/share/agent-browser/npm"
CFT_ROOT="$HOME/.local/share/chrome-for-testing"
AB_BIN="${AGENT_BROWSER:-$AB_PREFIX/bin/agent-browser}"
CHROME_BIN="$CFT_ROOT/chrome-$CFT_VERSION/chrome"
TOOLS="Xvfb:xvfb pdftotext:poppler-utils curl:curl jq:jq unzip:unzip"
LIBS="libasound2 libatk1.0-0 libatk-bridge2.0-0 libatspi2.0-0 libgbm1 libwayland-server0 libxcb-randr0
 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libxkbcommon0 libnss3 libcups2 libpango-1.0-0 libcairo2
 libdbus-1-3 libglib2.0-0 libx11-6 libxext6"

MODE=check
case "${1:---check}" in --check) ;; --install) MODE=install ;; *) echo "usage: $0 [--check|--install]" >&2; exit 2 ;; esac
run() { if [ "$MODE" = install ] && [ -z "${DRY_RUN:-}" ]; then "$@"; else printf '  $ %s\n' "$*"; fi; }
as_root() { if [ "$(id -u)" -eq 0 ]; then run "$@"; else run sudo "$@"; fi; }
fail() { echo "error: $*" >&2; [ "$MODE" = install ] && [ -z "${DRY_RUN:-}" ] && exit 1; return 0; }
installed() { dpkg-query -W -f='${Status}\n' "$1" 2>/dev/null | grep -q '^install ok installed'; }
# Ubuntu 24.04 renamed some libraries to <name>t64: prefer that name when the archive has it.
apt_name() { if apt-cache show "${1}t64" >/dev/null 2>&1; then echo "${1}t64"; else echo "$1"; fi; }

apt_missing=()
for t in $TOOLS; do
  command -v "${t%%:*}" >/dev/null 2>&1 || { echo "missing: ${t%%:*} (apt package ${t##*:})"; apt_missing+=("${t##*:}"); }
done
for l in $LIBS; do
  installed "$l" || installed "${l}t64" || { echo "missing: $l"; apt_missing+=("$l"); }
done
if [ ${#apt_missing[@]} -gt 0 ]; then
  echo "apt:"
  as_root apt-get update
  names=(); for p in "${apt_missing[@]}"; do names+=("$(apt_name "$p")"); done
  as_root env DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends "${names[@]}"
fi

[ -x "$AB_BIN" ] || AB_BIN=$(command -v agent-browser || echo "$AB_BIN")
if [ -x "$AB_BIN" ] && env -u LD_PRELOAD "$AB_BIN" --version 2>&1 | grep -qF "$AB_VERSION"; then :; else
  echo "missing: agent-browser $AB_VERSION"
  if command -v node >/dev/null && command -v npm >/dev/null && [ "$(node -p 'process.versions.node.split(".")[0]')" -ge 22 ]; then
    run npm install -g --prefix "$AB_PREFIX" --no-audit --no-fund "agent-browser@$AB_VERSION"
  else
    fail "agent-browser needs node >= 22 and npm on PATH; install them first, then rerun"
  fi
fi

if [ ! -x "$CHROME_BIN" ]; then
  echo "missing: Chrome for Testing $CFT_VERSION"
  [ -e "$CFT_ROOT/chrome-$CFT_VERSION" ] && fail "$CFT_ROOT/chrome-$CFT_VERSION exists without a chrome binary; remove it and rerun"
  run mkdir -p "$CFT_ROOT/.stage"
  run curl -fsSL --retry 3 -o "$CFT_ROOT/.stage/cft.zip" "$CFT_URL"
  run unzip -q -o "$CFT_ROOT/.stage/cft.zip" -d "$CFT_ROOT/.stage"
  run mv "$CFT_ROOT/.stage/chrome-linux64" "$CFT_ROOT/chrome-$CFT_VERSION"
  run rm -rf "$HOME/.local/share/chrome-for-testing/.stage"
  if [ "$MODE" = install ] && [ -z "${DRY_RUN:-}" ]; then [ -x "$CHROME_BIN" ] || fail "Chrome binary missing: $CHROME_BIN"; fi
fi
[ "$MODE" = check ] && echo "(check only: nothing was installed; run with --install to apply the commands above)"
echo "export AGENT_BROWSER=$AB_BIN"
echo "export CHROME=$CHROME_BIN"
