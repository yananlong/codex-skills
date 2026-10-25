#!/usr/bin/env python3
"""Trace every number in a draft back to a data source.

A first draft written from results may only carry numbers that appear in the
artifacts it was written from. This script extracts the numeric tokens from a
draft (Markdown, LaTeX, or plain text), extracts every numeric value from the
source files (JSON, CSV/TSV, Markdown tables, plain text), and reports which
draft numbers have no source. It tolerates rounding (a draft's 12.3 matches a
source's 12.34 or 0.123 when written as a percentage), and skips what is not a
measurement: years, section, table, figure, and equation numbers, citation
numbers, footnote markers, and numbers inside LaTeX citation or reference macros.

It also lists the visible gap markers (``[EVIDENCE NEEDED: ...]`` and
``[CITATION NEEDED: ...]``) so the handoff note can carry them.

Usage:
    check_draft_numbers.py <draft> --source <file> [--source <file> ...]
                           [--allow <number> ...] [--format text|json] [--allow-untraced]

Exit status 1 when any number is untraced, unless --allow-untraced is given.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

NUMBER_RE = re.compile(r"(?<![\w.])[-+]?\d{1,3}(?:,\d{3})+(?:\.\d+)?%?|(?<![\w.])[-+]?\d+(?:\.\d+)?%?(?![\w.]\d)")
MARKER_RE = re.compile(r"\[(EVIDENCE|CITATION) NEEDED:?[^\]]*\]")
SKIP_BEFORE = re.compile(
    r"(?:section|sec\.|table|tab\.|figure|fig\.|equation|eq\.|chapter|appendix|algorithm|step|line|page|p\.|pp\.|footnote|version|v)\s*$",
    re.IGNORECASE,
)
LATEX_SKIP = re.compile(r"\\(?:cite[tp]?\*?|ref|eqref|autoref|cref|Cref|label|pageref|footnote|bibitem|input|include)\s*(?:\[[^\]]*\])?\{[^}]*\}")
MD_SKIP = re.compile(r"\[\^?\d+\]|\[@[^\]]+\]|\]\([^)\n]*\)")
# Markdown code spans stay on one line; in LaTeX a backtick opens a quotation mark, so the
# span rule is skipped there or it would swallow text between two quotes.
MD_CODE_SPAN = re.compile(r"`[^`\n]*`")


LATEX_HINT = re.compile(r"\\(?:documentclass|begin|section|subsection|cite|ref|textbf|emph|label|%)")


def strip_for_scan(text: str) -> str:
    text = MARKER_RE.sub(" ", text)
    if LATEX_HINT.search(text):
        text = re.sub(r"(?<!\\)%.*", "", text)  # LaTeX comments; an escaped \% is a percent sign
        text = text.replace("\\%", "%")
    else:
        text = MD_CODE_SPAN.sub(" ", text)
    text = LATEX_SKIP.sub(" ", text)
    text = MD_SKIP.sub(" ", text)
    return text


def parse_number(token: str) -> tuple[float, int, bool] | None:
    percent = token.endswith("%")
    core = token.rstrip("%").replace(",", "")
    try:
        value = float(core)
    except ValueError:
        return None
    decimals = len(core.split(".")[1]) if "." in core else 0
    return value, decimals, percent


def is_year(token: str) -> bool:
    return re.fullmatch(r"(?:19|20)\d{2}", token) is not None


def extract_draft_numbers(text: str) -> list[tuple[int, str]]:
    found: list[tuple[int, str]] = []
    for line_no, line in enumerate(strip_for_scan(text).splitlines(), start=1):
        for match in NUMBER_RE.finditer(line):
            token = match.group(0)
            before = line[: match.start()]
            if SKIP_BEFORE.search(before):
                continue
            if is_year(token):
                continue
            if re.fullmatch(r"[-+]?\d", token):
                # Single digits are counts and list positions far more often than results.
                continue
            found.append((line_no, token))
    return found


def source_values(path: Path) -> set[float]:
    values: set[float] = set()
    suffix = path.suffix.lower()
    try:
        if suffix == ".json":
            data = json.loads(path.read_text(encoding="utf-8"))
            stack = [data]
            while stack:
                item = stack.pop()
                if isinstance(item, bool):
                    continue
                if isinstance(item, (int, float)):
                    values.add(float(item))
                elif isinstance(item, str):
                    for match in NUMBER_RE.finditer(item):
                        parsed = parse_number(match.group(0))
                        if parsed:
                            values.add(parsed[0])
                elif isinstance(item, dict):
                    stack.extend(item.values())
                elif isinstance(item, list):
                    stack.extend(item)
            return values
        if suffix in {".csv", ".tsv"}:
            with path.open(encoding="utf-8", newline="") as handle:
                reader = csv.reader(handle, delimiter="\t" if suffix == ".tsv" else ",")
                for row in reader:
                    for cell in row:
                        parsed = parse_number(cell.strip())
                        if parsed:
                            values.add(parsed[0])
                        else:
                            for match in NUMBER_RE.finditer(cell):
                                inner = parse_number(match.group(0))
                                if inner:
                                    values.add(inner[0])
            return values
        text = path.read_text(encoding="utf-8")
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ValueError(f"{path}: {exc}") from exc
    for match in NUMBER_RE.finditer(text):
        parsed = parse_number(match.group(0))
        if parsed:
            values.add(parsed[0])
    return values


def matches(draft_token: str, sources: set[float]) -> bool:
    parsed = parse_number(draft_token)
    if parsed is None:
        return False
    value, decimals, percent = parsed
    candidates = [value, value / 100.0]  # a percentage written from a source fraction
    if not percent and 0 < abs(value) < 1 and decimals > 0:
        # A fraction such as 0.82 written from a source that holds 82.3. Integers and values
        # above 1 never take this route: 64 must not match a source 6412.
        candidates.append(value * 100.0)
    base_tolerance = 0.5 * 10 ** (-decimals) + 1e-9
    for candidate in candidates:
        if candidate in sources:
            return True
        # The tolerance follows the candidate's units: a draft's 9.9% written from a source
        # fraction must match within 0.0005, not within 0.05.
        scale = candidate / value if value else 1.0
        tolerance = base_tolerance * abs(scale)
        for source in sources:
            if abs(source - candidate) <= tolerance:
                return True
    return False


def check(draft_text: str, sources: set[float], allow: set[str]) -> dict:
    traced: list[dict] = []
    untraced: list[dict] = []
    for line_no, token in extract_draft_numbers(draft_text):
        record = {"line": line_no, "token": token}
        if token in allow or matches(token, sources):
            traced.append(record)
        else:
            untraced.append(record)
    markers = [{"line": i, "marker": m.group(0)} for i, line in enumerate(draft_text.splitlines(), start=1) for m in MARKER_RE.finditer(line)]
    return {"traced": traced, "untraced": untraced, "markers": markers}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("draft", type=Path)
    parser.add_argument("--source", type=Path, action="append", default=[])
    parser.add_argument("--allow", action="append", default=[], help="a number the draft may use without a source (a fixed hyperparameter, a count stated by the author)")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--allow-untraced", action="store_true")
    args = parser.parse_args(argv)

    try:
        draft_text = args.draft.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    sources: set[float] = set()
    for source in args.source:
        try:
            sources |= source_values(source)
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2

    report = check(draft_text, sources, set(args.allow))
    report["draft"] = str(args.draft)
    report["sources"] = [str(s) for s in args.source]
    report["source_value_count"] = len(sources)

    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(
            f"numbers: {len(report['traced'])} traced, {len(report['untraced'])} untraced; "
            f"{len(report['markers'])} gap markers; {len(sources)} source values from {len(args.source)} files"
        )
        for item in report["untraced"]:
            print(f"  untraced line {item['line']}: {item['token']}")
        for item in report["markers"]:
            print(f"  marker line {item['line']}: {item['marker']}")
    if report["untraced"] and not args.allow_untraced:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
