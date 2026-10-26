#!/usr/bin/env python3
r"""List every citation key in a draft that no bibliography or inventory resolves.

A first draft may cite only keys that exist: in a .bib file, in the bib inventory the
literature-review skill writes (bib-inventory.json, keys marked resolved), or in an explicit key
list. Everything else is reported, so an invented or misspelled key never reaches the reviser.
Keys are read from LaTeX \cite variants (cite, citep, citet, citealp, citeauthor, citeyear,
parencite, textcite, autocite, footcite, nocite, with optional [..] arguments and multiple keys)
and from Pandoc-style [@key] or @key citations in Markdown.

Usage:
    check_draft_citations.py <draft> [--bib refs.bib ...] [--bib-inventory bib-inventory.json]
                             [--keys keys.txt] [--format text|json]

Exit status 1 when any key is unresolved, 2 when a source cannot be read.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

LATEX_CITE_RE = re.compile(
    r"\\(?:[Cc]ite(?:p|t|alp|alt|author|year|yearpar|num)?\*?|[Pp]arencite|[Tt]extcite|[Aa]utocite|[Ff]ootcite|nocite|[Ss]martcite)"
    r"(?:\[[^\]]*\]){0,2}\{([^}]*)\}"
)
MD_CITE_RE = re.compile(r"(?<![\w@])@([A-Za-z][\w:.\-/+]*[\w])")
BIB_ENTRY_RE = re.compile(r"@(?!comment|preamble|string)\w+\s*\{\s*([^,\s]+)\s*,", re.IGNORECASE)
CITATION_MARKER_RE = re.compile(r"\[CITATION NEEDED[^\]]*\]")


def draft_keys(text: str) -> list[tuple[int, str]]:
    found: list[tuple[int, str]] = []
    for line_no, raw in enumerate(text.splitlines(), start=1):
        line = CITATION_MARKER_RE.sub(" ", raw)
        line = re.sub(r"(?<!\\)%.*", "", line) if "\\" in line else line
        for match in LATEX_CITE_RE.finditer(line):
            for key in match.group(1).split(","):
                key = key.strip()
                if key:
                    found.append((line_no, key))
        if "\\cite" not in line:
            for match in MD_CITE_RE.finditer(re.sub(r"`[^`]*`", " ", line)):
                found.append((line_no, match.group(1).rstrip(".")))
    return found


def keys_from_bib(path: Path) -> set[str]:
    return set(BIB_ENTRY_RE.findall(path.read_text(encoding="utf-8", errors="replace")))


def keys_from_inventory(path: Path) -> set[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    keys: set[str] = set()
    records = data.get("entries") or data.get("keys") or data.get("records") or data if isinstance(data, dict) else data
    if isinstance(records, dict):
        for key, value in records.items():
            status = value.get("status") if isinstance(value, dict) else value
            if status in (None, "resolved", True):
                keys.add(str(key))
        return keys
    if isinstance(records, list):
        for record in records:
            if isinstance(record, str):
                keys.add(record)
            elif isinstance(record, dict):
                key = record.get("key") or record.get("cite_key") or record.get("id")
                status = record.get("status", "resolved")
                if key and status in ("resolved", True, None):
                    keys.add(str(key))
    return keys


def keys_from_list(path: Path) -> set[str]:
    return {line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip() and not line.startswith("#")}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("draft", type=Path)
    parser.add_argument("--bib", type=Path, action="append", default=[])
    parser.add_argument("--bib-inventory", type=Path, action="append", default=[])
    parser.add_argument("--keys", type=Path, action="append", default=[], help="a text file with one allowed key per line")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args(argv)

    try:
        text = args.draft.read_text(encoding="utf-8")
        known: set[str] = set()
        for path in args.bib:
            known |= keys_from_bib(path)
        for path in args.bib_inventory:
            known |= keys_from_inventory(path)
        for path in args.keys:
            known |= keys_from_list(path)
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    cited = draft_keys(text)
    unresolved = [{"line": line, "key": key} for line, key in cited if key not in known]
    markers = sum(1 for _ in CITATION_MARKER_RE.finditer(text))
    report = {
        "draft": str(args.draft),
        "cited": len(cited),
        "distinct": len({k for _, k in cited}),
        "known_keys": len(known),
        "unresolved": unresolved,
        "citation_markers": markers,
    }
    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(f"citations: {report['distinct']} distinct keys cited, {len(unresolved)} unresolved, {markers} [CITATION NEEDED] markers, {len(known)} known keys")
        for item in unresolved:
            print(f"  unresolved line {item['line']}: {item['key']}")
    return 1 if unresolved else 0


if __name__ == "__main__":
    sys.exit(main())
