#!/usr/bin/env python3
"""Create a deterministic research planning pack."""

from __future__ import annotations

import argparse
from pathlib import Path


FILE_TEMPLATES = {
    "research-brief.md": """# Research Brief

## Core Question

- Project:
- Main question:
- Falsifiable thesis:
- Intended audience:
- Stakes:

## Success Criteria

- Primary success condition:
- Secondary success conditions:
- Clear failure condition:

## Constraints

- Time budget:
- Compute budget:
- Data/tool constraints:
- Non-goals:

## Required Artifacts

- Canonical brief:
- Experiment plan:
- Review artifact:
- Draft/manuscript artifact:

## Open Questions

- Question:
- Why it matters:
- What would resolve it:
""",
    "task-board.md": """# Task Board

| Stage | Task | Status | Dependency | Output | Exit criterion |
| --- | --- | --- | --- | --- | --- |
| framing | | todo | | | |
| evidence | | todo | | | |
| planning | | todo | | | |
| execution | | todo | | | |
| review | | todo | | | |
""",
    "decision-log.md": """# Decision Log

## Entry

- Date:
- Decision:
- Context:
- Alternatives considered:
- Rationale:
- Expected consequence:
- Follow-up trigger:
""",
    "artifact-index.md": """# Artifact Index

| Artifact | Path | Status | Role |
| --- | --- | --- | --- |
| research brief | ./research-brief.md | canonical | project framing |
| task board | ./task-board.md | canonical | staged execution |
| decision log | ./decision-log.md | canonical | major decisions |
| review artifact | | pending | adversarial review |
| manuscript artifact | | pending | paper or memo |
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
        (args.target_dir / name).write_text(content, encoding="utf-8")
        print(f"created {args.target_dir / name}")


if __name__ == "__main__":
    main()
