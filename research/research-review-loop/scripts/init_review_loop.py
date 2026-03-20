#!/usr/bin/env python3
"""Create deterministic scaffolds for iterative research review."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


STATE_TEMPLATE = {
    "version": "1.0",
    "target": "",
    "round": 1,
    "status": "open",
    "summary": "",
    "open_issues": [],
    "resolved_issues": [],
    "accepted_risks": [],
}

FILE_TEMPLATES = {
    "AUTO_REVIEW.md": """# Research Review Report

## Header

- Artifact:
- Version:
- Review round:
- Review date:
- Reviewer constraints:

## Executive Summary

- Bottom line:
- Major issues:
- Highest-leverage fixes:

## Claim Ledger Summary

| ID | Location | Claim | Type | Status | Evidence / fix |
| --- | --- | --- | --- | --- | --- |

## Major Issues

- Location:
- Problem:
- Why it matters:
- Evidence:
- Suggested fix:

## Minor Issues

- 

## Open Questions

- 
""",
    "NARRATIVE_REPORT.md": """# Narrative Review Summary

## Current Status

- Target:
- Review round:
- Overall judgment:

## Most Important Problems

- 

## What Changed Since the Last Round

- 

## What Must Happen Next

- 
""",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target_dir", type=Path, help="Directory where the review pack will be created.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing files.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.target_dir.mkdir(parents=True, exist_ok=True)

    targets = [args.target_dir / "REVIEW_STATE.json"]
    targets.extend(args.target_dir / name for name in FILE_TEMPLATES)
    existing = [path.name for path in targets if path.exists()]
    if existing and not args.force:
        raise SystemExit(
            "Refusing to overwrite existing files without --force: " + ", ".join(sorted(existing))
        )

    state_path = args.target_dir / "REVIEW_STATE.json"
    state_path.write_text(json.dumps(STATE_TEMPLATE, indent=2) + "\n", encoding="utf-8")
    print(f"created {state_path}")

    for name, content in FILE_TEMPLATES.items():
        path = args.target_dir / name
        path.write_text(content, encoding="utf-8")
        print(f"created {path}")


if __name__ == "__main__":
    main()
