#!/usr/bin/env python3
"""Create a deterministic research planning pack."""

from __future__ import annotations

import argparse
from pathlib import Path


STAGE_DIRS = [
    "literature-review",
    "novelty-review",
    "experiment-plan",
    "paper-plan",
    "review-loop",
]

FILE_TEMPLATES = {
    "research-brief.md": """# Research Brief

## Project Frame

- Project:
- Main question:
- Working thesis:
- Intended audience:
- Desired end state:

## Current State

- Operating mode: standalone / orchestrated
- Current stage:
- Existing artifacts:
- Missing artifacts:

## Success Criteria

- Primary success condition:
- Secondary success conditions:
- Clear failure condition:

## Constraints

- Time budget:
- Compute budget:
- Data/tool constraints:
- Non-goals:

## Stage Plan

| Stage | Goal | Canonical path | Owner skill | Status |
| --- | --- | --- | --- | --- |
| literature review | | ./literature-review/ | research-systematic-literature-review | optional |
| novelty review | | ./novelty-review/ | research-novelty-review | optional |
| experiment plan | | ./experiment-plan/ | research-experiment-plan | optional |
| paper plan | | ./paper-plan/ | research-paper-plan | optional |
| review loop | | ./review-loop/ | research-review-loop | optional |

## Open Questions

- Question:
- Why it matters:
- What would resolve it:
""",
    "task-board.md": """# Task Board

| Stage | Objective | Status | Dependency | Canonical output | Next action | Checkpoint |
| --- | --- | --- | --- | --- | --- | --- |
| literature review | | todo | | ./literature-review/ | | |
| novelty review | | todo | | ./novelty-review/ | | |
| experiment plan | | todo | | ./experiment-plan/ | | |
| execution / results audit | | todo | | | | |
| review loop | | todo | | ./review-loop/ | | |
| paper plan | | todo | | ./paper-plan/ | | |
""",
    "decision-log.md": """# Decision Log

## Entry

- Date:
- Stage:
- Decision:
- Status: proceed / revise / stop
- Context:
- Alternatives considered:
- Rationale:
- Expected consequence:
- Follow-up trigger:
""",
    "artifact-index.md": """# Artifact Index

| Artifact | Canonical path | Status | Notes |
| --- | --- | --- | --- |
| research brief | ./research-brief.md | canonical | planning anchor |
| task board | ./task-board.md | canonical | stage tracker |
| decision log | ./decision-log.md | canonical | checkpoint history |
| literature review | ./literature-review/ | pending | outputs from research-systematic-literature-review |
| novelty review | ./novelty-review/ | pending | outputs from research-novelty-review |
| experiment plan | ./experiment-plan/ | pending | outputs from research-experiment-plan |
| paper plan | ./paper-plan/ | pending | outputs from research-paper-plan |
| review loop | ./review-loop/ | pending | outputs from research-review-loop |
| results audit |  | optional | outputs from research-results-auditor |
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
    existing.extend(name for name in STAGE_DIRS if (args.target_dir / name).exists())
    if existing and not args.force:
        raise SystemExit(
            "Refusing to overwrite existing files without --force: " + ", ".join(sorted(existing))
        )

    for name, content in FILE_TEMPLATES.items():
        (args.target_dir / name).write_text(content, encoding="utf-8")
        print(f"created {args.target_dir / name}")

    for name in STAGE_DIRS:
        path = args.target_dir / name
        path.mkdir(parents=True, exist_ok=True)
        print(f"created {path}")


if __name__ == "__main__":
    main()
