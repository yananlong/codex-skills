#!/usr/bin/env python3
"""Validate an iteration-loop ledger (results.tsv) and optionally its notebook.

Checks the header, the column count, the commit hash format, numeric metric and cost, the status
enum, that crash rows record zeros, that the first row is the baseline, and that every `keep` row
improves on the best kept metric so far in the declared direction. With --notebook, every ledger
row must have a matching `## <commit> <status>` entry.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

EXPECTED_HEADER = ["commit", "metric", "cost", "status", "description"]
STATUSES = {"keep", "discard", "crash"}
COMMIT_RE = re.compile(r"^[0-9a-f]{7,40}$")


def parse_ledger(text: str) -> tuple[list[dict], list[str]]:
    errors: list[str] = []
    lines = text.splitlines()
    if not lines:
        return [], ["ledger is empty; expected a header row"]
    header = lines[0].split("\t")
    if header != EXPECTED_HEADER:
        return [], [f"header must be {chr(9).join(EXPECTED_HEADER)!r}, got {lines[0]!r}"]
    rows: list[dict] = []
    for number, line in enumerate(lines[1:], start=2):
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) != len(EXPECTED_HEADER):
            errors.append(f"line {number}: expected {len(EXPECTED_HEADER)} tab-separated columns, got {len(parts)}")
            continue
        row = dict(zip(EXPECTED_HEADER, parts))
        row["line"] = number
        if not COMMIT_RE.match(row["commit"]):
            errors.append(f"line {number}: commit {row['commit']!r} is not a hex hash of 7 to 40 characters")
        for field in ("metric", "cost"):
            try:
                row[field] = float(row[field])
            except ValueError:
                errors.append(f"line {number}: {field} {row[field]!r} is not a number")
                row[field] = None
        if row["status"] not in STATUSES:
            errors.append(f"line {number}: status {row['status']!r} must be one of {sorted(STATUSES)}")
        if not row["description"].strip():
            errors.append(f"line {number}: description is empty")
        rows.append(row)
    return rows, errors


def validate_rows(rows: list[dict], direction: str) -> list[str]:
    errors: list[str] = []
    if not rows:
        return errors
    if rows[0]["status"] != "keep":
        errors.append(f"line {rows[0]['line']}: the first row is the baseline and must have status keep")
    better = (lambda new, best: new < best) if direction == "lower" else (lambda new, best: new > best)
    best = None
    for row in rows:
        if row["metric"] is None or row["cost"] is None:
            continue
        if row["status"] == "crash":
            if row["metric"] != 0 or row["cost"] != 0:
                errors.append(f"line {row['line']}: crash rows must record metric 0 and cost 0")
            continue
        if row["status"] == "keep":
            if best is not None and not better(row["metric"], best):
                errors.append(
                    f"line {row['line']}: keep row metric {row['metric']} does not improve on best kept {best} ({direction} is better)"
                )
            if best is None or better(row["metric"], best):
                best = row["metric"]
        elif row["status"] == "discard" and best is not None and better(row["metric"], best):
            errors.append(
                f"line {row['line']}: discard row metric {row['metric']} improves on best kept {best}; status should be keep or the row needs a reason in description"
            )
    return errors


def validate_notebook(rows: list[dict], notebook: str) -> list[str]:
    headings = {}
    for match in re.finditer(r"^## ([0-9a-f]{7,40}) (keep|discard|crash)\s*$", notebook, flags=re.M):
        headings[match.group(1)] = match.group(2)
    errors = []
    for row in rows:
        status = headings.get(row["commit"])
        if status is None:
            errors.append(f"line {row['line']}: no notebook entry '## {row['commit']} <status>'")
        elif status != row["status"]:
            errors.append(f"line {row['line']}: notebook entry says {status}, ledger says {row['status']}")
    return errors


def summarize(rows: list[dict], direction: str) -> str:
    kept = [r for r in rows if r["status"] == "keep" and r["metric"] is not None]
    crashes = sum(1 for r in rows if r["status"] == "crash")
    if not kept:
        return f"{len(rows)} runs, no kept rows, {crashes} crashes"
    best = min(kept, key=lambda r: r["metric"]) if direction == "lower" else max(kept, key=lambda r: r["metric"])
    return (
        f"{len(rows)} runs, {len(kept)} kept, {crashes} crashes; best {best['metric']} at {best['commit']} "
        f"({best['description']}); baseline {kept[0]['metric']}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ledger", type=Path, help="Path to results.tsv")
    parser.add_argument("--direction", choices=("lower", "higher"), default="lower", help="Which metric direction is better")
    parser.add_argument("--notebook", type=Path, help="experiments.md to cross-check against the ledger")
    args = parser.parse_args()

    try:
        text = args.ledger.read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"[ERROR] ledger not found: {args.ledger}", file=sys.stderr)
        return 1
    rows, errors = parse_ledger(text)
    if rows:
        errors.extend(validate_rows(rows, args.direction))
    elif not errors:
        errors.append("ledger has no runs; the first row must be the baseline")
    if args.notebook and rows:
        try:
            errors.extend(validate_notebook(rows, args.notebook.read_text(encoding="utf-8")))
        except FileNotFoundError:
            errors.append(f"notebook not found: {args.notebook}")
    if errors:
        for error in errors:
            print(f"[ERROR] {error}", file=sys.stderr)
        return 1
    print(f"[OK] ledger valid: {summarize(rows, args.direction)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
