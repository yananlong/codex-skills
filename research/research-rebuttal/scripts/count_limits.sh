#!/usr/bin/env bash
# count_limits.sh — Verify rebuttal length against venue limits.
#
# Counts the raw text exactly as it will be pasted into the platform field
# (markup included). OpenReview-style limits apply to the raw field, so the
# raw count is the only count that can confirm a response fits.
#
# Usage:
#   count_limits.sh <file> [--chars|--words|--pages] [--limit N]
#                   [--per-section|--whole] [--strip-markup]
#
# Examples:
#   count_limits.sh rebuttal.md --chars --limit 5000
#   count_limits.sh responses.md --per-section --limit 5000
#   count_limits.sh rebuttal.tex --words --strip-markup
#
# Exit codes: 0 within limit (or no limit), 1 usage or input error,
# 2 a counted unit exceeds the limit, 3 the limit cannot be verified (--pages).

set -euo pipefail

usage() {
    echo "Usage: $0 <file> [--chars|--words|--pages] [--limit N] [--per-section|--whole] [--strip-markup]"
    echo ""
    echo "Options:"
    echo "  --chars         Count raw characters, markup included (default)"
    echo "  --words         Count raw words"
    echo "  --pages         PDF page limits cannot be verified from text; prints guidance only"
    echo "  --limit N       Fail (exit 2) if the file, or any section, exceeds N"
    echo "  --per-section   Count each level-2/3 Markdown heading block separately"
    echo "                  (on by default when the file has more than one such heading)"
    echo "  --whole         Count the whole file only, even if it has several headings"
    echo "  --strip-markup  Strip common LaTeX/Markdown/HTML markup first (estimate only;"
    echo "                  never use it to confirm a platform character limit)"
    exit 1
}

if [[ $# -lt 1 ]]; then
    usage
fi

FILE="$1"
shift

if [[ ! -f "$FILE" ]]; then
    echo "Error: File not found: $FILE" >&2
    exit 1
fi

MODE="chars"
LIMIT=""
SPLIT="auto"
STRIP=0

while [[ $# -gt 0 ]]; do
    case "$1" in
        --chars) MODE="chars"; shift ;;
        --words) MODE="words"; shift ;;
        --pages) MODE="pages"; shift ;;
        --per-section) SPLIT="yes"; shift ;;
        --whole) SPLIT="no"; shift ;;
        --strip-markup) STRIP=1; shift ;;
        --limit)
            if [[ $# -lt 2 || ! "$2" =~ ^[0-9]+$ ]]; then
                echo "Error: --limit requires a non-negative integer" >&2
                usage
            fi
            LIMIT="$2"; shift 2 ;;
        *) echo "Unknown option: $1" >&2; usage ;;
    esac
done

if [[ "$MODE" == "pages" ]]; then
    echo "File:  $FILE"
    echo "PDF page limits cannot be verified from text: page count depends on the venue template, fonts, figures, and floats."
    echo "Compile the response with the venue's official template (for example the rebuttal .tex kit) and check the PDF page count."
    if [[ -n "$LIMIT" ]]; then
        echo "UNVERIFIED: limit of $LIMIT pages not checked"
        exit 3
    fi
    exit 0
fi

# Count characters, not bytes: prefer a UTF-8 locale when the current one is not.
if [[ "$(locale charmap 2>/dev/null || true)" != "UTF-8" ]]; then
    for candidate in C.UTF-8 C.utf8 en_US.UTF-8 en_US.utf8; do
        if locale -a 2>/dev/null | grep -qx "$candidate"; then
            export LC_ALL="$candidate"
            break
        fi
    done
fi

# Strip common markup (estimate only).
strip_markup() {
    sed -E \
        -e 's/\\[a-zA-Z]+\{([^}]*)\}/\1/g' \
        -e 's/\\[a-zA-Z]+//g' \
        -e 's/[#*_`~]//g' \
        -e 's/<[^>]+>//g'
}

count_stream() {
    if [[ "$STRIP" -eq 1 ]]; then
        strip_markup
    else
        cat
    fi | if [[ "$MODE" == "words" ]]; then wc -w; else wc -m; fi | tr -d ' '
}

if [[ "$MODE" == "words" ]]; then
    UNIT="words"
else
    UNIT="characters"
fi
if [[ "$STRIP" -eq 1 ]]; then
    UNIT="$UNIT (estimate: markup stripped, not the platform count)"
else
    UNIT="$UNIT (raw)"
fi

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

# Split on level-2/3 Markdown headings outside fenced code blocks. Each section
# keeps its heading line; text before the first heading becomes section 0.
awk -v dir="$WORK" '
    BEGIN { n = 0; out = dir "/sec_0"; title[0] = "(before first heading)"; printf "" > out }
    /^(```|~~~)/ { fence = !fence }
    !fence && (/^##[ \t]/ || /^###[ \t]/) {
        close(out); n++; out = dir "/sec_" n
        t = $0; sub(/^#+[ \t]+/, "", t); title[n] = t
        printf "" > out
    }
    { print > out }
    END {
        close(out)
        for (i = 0; i <= n; i++) print title[i] > (dir "/titles")
        print n > (dir "/count")
    }
' "$FILE"

HEADINGS="$(cat "$WORK/count")"
if [[ "$SPLIT" == "auto" ]]; then
    if [[ "$HEADINGS" -gt 1 ]]; then SPLIT="yes"; else SPLIT="no"; fi
fi

TOTAL="$(count_stream < "$FILE")"
echo "File:  $FILE"
echo "Count: $TOTAL $UNIT"

FAILED=0
if [[ "$SPLIT" == "yes" ]]; then
    echo "Per-section counts (split on level-2/3 headings, heading line included):"
    i=0
    while IFS= read -r title; do
        sec="$WORK/sec_$i"
        if [[ $i -eq 0 ]] && ! grep -q '[^[:space:]]' "$sec"; then
            i=$((i + 1)); continue
        fi
        c="$(count_stream < "$sec")"
        status=""
        if [[ -n "$LIMIT" ]]; then
            if (( c > LIMIT )); then status="  OVER LIMIT"; FAILED=1; else status="  ok"; fi
        fi
        printf '  [%d] %s: %s%s\n' "$i" "$title" "$c" "$status"
        i=$((i + 1))
    done < "$WORK/titles"
    if [[ -n "$LIMIT" ]]; then
        if [[ "$FAILED" -eq 1 ]]; then
            echo "WARNING: At least one section exceeds the per-response limit of $LIMIT $UNIT"
            exit 2
        fi
        echo "OK: Every section is within the per-response limit of $LIMIT $UNIT"
    fi
elif [[ -n "$LIMIT" ]]; then
    if (( TOTAL > LIMIT )); then
        echo "WARNING: Exceeds limit of $LIMIT $UNIT"
        exit 2
    fi
    echo "OK: Within limit of $LIMIT $UNIT"
fi
if [[ "$STRIP" -eq 1 && -n "$LIMIT" ]]; then
    echo "NOTE: --strip-markup counts are estimates; re-run without it to confirm a platform character limit."
fi
