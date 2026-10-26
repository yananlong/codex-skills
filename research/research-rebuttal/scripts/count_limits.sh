#!/usr/bin/env bash
# count_limits.sh — Verify rebuttal length against venue limits.
#
# Counts the raw text exactly as it will be pasted into the platform field
# (markup included). OpenReview-style limits apply to the raw field, so the
# raw count is the only count that can confirm a response fits.
#
# Usage:
#   count_limits.sh <file> [--chars|--words|--pages] [--limit N] [--venue VENUE]
#                   [--per-section|--whole] [--strip-markup]
#
# Examples:
#   count_limits.sh rebuttal.md --chars --limit 5000
#   count_limits.sh responses.md --per-section --limit 5000
#   count_limits.sh rebuttal.tex --words --strip-markup
#   count_limits.sh responses.md --venue icml-2025
#
# --venue reads the unit and limit from the shared venue table (references/venues.json, via
# scripts/venue_table.py) and prints any staleness or verification flag for that row. An explicit
# --chars/--words/--pages or --limit overrides the table.
#
# Exit codes: 0 within limit (or no limit), 1 usage or input error,
# 2 a counted unit exceeds the limit, 3 the limit cannot be verified (--pages).

set -euo pipefail

usage() {
    echo "Usage: $0 <file> [--chars|--words|--pages] [--limit N] [--venue VENUE] [--per-section|--whole] [--strip-markup]"
    echo ""
    echo "Options:"
    echo "  --chars         Count raw characters, markup included (default)"
    echo "  --words         Count raw words"
    echo "  --pages         PDF page limits cannot be verified from text; prints guidance only"
    echo "  --limit N       Fail (exit 2) if the file, or any section, exceeds N"
    echo "  --venue VENUE   Take the unit and limit from the shared venue table (explicit flags win)"
    echo "  --per-section   Count each reviewer response (level-2 heading block; level-3 when there is one response) separately"
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
MODE_SET=0
LIMIT=""
VENUE=""
SPLIT="auto"
STRIP=0

while [[ $# -gt 0 ]]; do
    case "$1" in
        --chars) MODE="chars"; MODE_SET=1; shift ;;
        --words) MODE="words"; MODE_SET=1; shift ;;
        --pages) MODE="pages"; MODE_SET=1; shift ;;
        --venue)
            if [[ $# -lt 2 ]]; then
                echo "Error: --venue requires a venue_id" >&2
                usage
            fi
            VENUE="$2"; shift 2 ;;
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

if [[ -n "$VENUE" ]]; then
    HELPER="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/venue_table.py"
    set +e
    VENUE_LIMIT="$(python3 "$HELPER" limit "$VENUE")"
    VENUE_RC=$?
    set -e
    if [[ "$VENUE_RC" -eq 3 ]]; then
        echo "Venue $VENUE: no numeric response limit recorded; counting without a limit unless --limit is given"
    elif [[ "$VENUE_RC" -ne 0 ]]; then
        echo "Error: could not read venue $VENUE from the venue table" >&2
        exit 1
    else
        read -r V_UNIT V_VALUE V_SCOPE <<< "$VENUE_LIMIT"
        echo "Venue $VENUE: $V_VALUE $V_UNIT ($V_SCOPE) from the shared venue table"
        if [[ "$MODE_SET" -eq 0 ]]; then MODE="$V_UNIT"; fi
        if [[ -z "$LIMIT" ]]; then
            LIMIT="$V_VALUE"
        elif [[ "$LIMIT" != "$V_VALUE" ]]; then
            echo "NOTE: --limit $LIMIT overrides the venue table's $V_VALUE"
        fi
        if [[ "$MODE" != "$V_UNIT" ]]; then
            echo "NOTE: counting $MODE while the venue table states its limit in $V_UNIT"
        fi
    fi
fi

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

# One response per reviewer lives under a level-2 heading. Split on level-2 headings
# when the file has more than one; otherwise the file is one response and its level-3
# subsections are parts of it, so the whole-file total is what the limit applies to.
# Each section keeps its heading line; text before the first heading becomes section 0.
H2_COUNT="$(awk '/^(```|~~~)/ { fence = !fence } !fence && /^##[ \t]/ { n++ } END { print n + 0 }' "$FILE")"
if (( H2_COUNT > 1 )); then SPLIT_RE='^##[ \t]'; else SPLIT_RE='^###[ \t]'; fi
awk -v dir="$WORK" -v split_re="$SPLIT_RE" '
    BEGIN { n = 0; out = dir "/sec_0"; title[0] = "(before first heading)"; printf "" > out }
    /^(```|~~~)/ { fence = !fence }
    !fence && $0 ~ split_re {
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
    # Auto mode splits only when the file holds several reviewer responses (level-2 headings).
    # A single response with level-3 subsections is counted whole against the limit.
    if (( H2_COUNT > 1 )); then SPLIT="yes"; else SPLIT="no"; fi
fi

TOTAL="$(count_stream < "$FILE")"
echo "File:  $FILE"
echo "Count: $TOTAL $UNIT"

FAILED=0
if [[ "$SPLIT" == "yes" ]]; then
    echo "Per-section counts (split on ${SPLIT_RE:1:3} headings, heading line included):"
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
