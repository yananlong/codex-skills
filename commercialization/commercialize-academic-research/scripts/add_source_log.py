#!/usr/bin/env python3
"""Add a source-log file to an existing commercialization case pack."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def template(case_name: str) -> str:
    return f"""# {case_name}.source-log

## Evidence posture

- Mode: user-facts-only / light desk research / source-grounded diligence / sibling-skill evidence
- Live research used: yes / no
- Sibling skill artifacts consumed:
- Retrieval date:
- Known limits:

## Search and source log

| Date | Query or source | Source type | Claim supported | Key observation | Reliability | Follow-up needed |
| --- | --- | --- | --- | --- | --- | --- |
|  |  | official / regulator / customer / procurement / peer-reviewed / patent / industry / user-provided |  |  | low / medium / high |  |

## Source-backed facts

| Fact | Source | Confidence | Decision relevance |
| --- | --- | --- | --- |
|  |  |  |  |

## Assumptions where evidence is missing

| Assumption | Why acceptable for now | What would verify or falsify it |
| --- | --- | --- |
|  |  |  |
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a source-log file for a case pack.")
    parser.add_argument("case_dir", help="Path to the existing case directory")
    parser.add_argument("--overwrite", action="store_true", help="Replace an existing source-log file")
    args = parser.parse_args()

    case_dir = Path(args.case_dir).resolve()
    if not case_dir.is_dir():
        print(f"[ERROR] Case directory not found: {case_dir}")
        return 1

    target = case_dir / f"{case_dir.name}.source-log.md"
    if target.exists() and not args.overwrite:
        print(f"[OK] Source log already exists: {target}")
        return 0

    try:
        target.write_text(template(case_dir.name), encoding="utf-8")
    except OSError as exc:
        print(f"[ERROR] Failed to write source log: {exc}")
        return 1

    print(f"[OK] Created source log: {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
