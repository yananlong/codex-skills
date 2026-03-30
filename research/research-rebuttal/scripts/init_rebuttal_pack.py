#!/usr/bin/env python3
"""Create deterministic scaffolds for rebuttal planning and drafting."""

from __future__ import annotations

import argparse
from pathlib import Path


FILE_TEMPLATES = {
    "review-analysis.md": """# Review Analysis

## Header

- Paper:
- Venue:
- Operating mode: standalone / orchestrated
- Artifact structure:
- Deadline:

## Score Matrix

| Reviewer | Score | Confidence | Stance | Core concern | AC-facing note |
| --- | --- | --- | --- | --- | --- |
| R1 | | | Champion / Persuadable / Entrenched | | |

## Shared Concerns

| Concern | Reviewers | Severity | Planned handling |
| --- | --- | --- | --- |
| | | Major-Blocking / Major-Addressable / Minor / Misunderstanding | |

## Decision View

- Main accept case:
- Main reject risk:
- Highest-leverage rebuttal targets:
""",
    "issue-board.md": """# Issue Board

| Issue ID | Reviewer | Severity | Category | Strategy | Stance | Status | Shared with | Evidence source | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| R1-1 | R1 | Major-Blocking / Major-Addressable / Minor / Misunderstanding | | | Champion / Persuadable / Entrenched | open | | | |
""",
    "task-list.md": """# Task List

| Task ID | Issue IDs | Objective | Owner | Evidence source | Output artifact | Draft blocker | Affects | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T1 | | | | | | yes / no | manuscript / rebuttal / both | todo |
""",
    "rebuttal-working.md": """# Rebuttal Working Draft

## Header

- Venue:
- Format:
- Limit:
- Operating mode: standalone / orchestrated

## Global Summary

- 

## Reviewer Responses

### [Reviewer ID]

- Concern:
- Direct answer:
- Evidence:
- Implication:
- [INTERNAL] Source check:

## Open Risks

- 

## Final Checks

- Provenance gate:
- Commitment gate:
- Coverage gate:
- Length check:
""",
    "rebuttal-paste-ready.md": """# Paste-Ready Rebuttal

Remove headings or formatting not accepted by the venue before submission.
""",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target_dir", type=Path, help="Directory where the pack will be created.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing files.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.target_dir.mkdir(parents=True, exist_ok=True)

    existing = [name for name in FILE_TEMPLATES if (args.target_dir / name).exists()]
    if existing and not args.force:
        raise SystemExit(
            "Refusing to overwrite existing files without --force: " + ", ".join(sorted(existing))
        )

    for name, content in FILE_TEMPLATES.items():
        path = args.target_dir / name
        path.write_text(content, encoding="utf-8")
        print(f"created {path}")


if __name__ == "__main__":
    main()
