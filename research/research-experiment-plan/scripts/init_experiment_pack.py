#!/usr/bin/env python3
"""Create deterministic scaffolds for experiment planning."""

from __future__ import annotations

import argparse
from pathlib import Path


FILE_TEMPLATES = {
    "experiment-plan.md": """# Experiment Plan

## Context

- Problem:
- Evaluation goal:
- Operating mode: standalone / orchestrated
- Upstream artifacts used:

## Claim Map

| Claim | Type | Why it matters | Minimum convincing evidence | Anti-claim to rule out |
| --- | --- | --- | --- | --- |
| | primary / supporting | | | |

## Experiment Blocks

### Block 1

- Claim tested:
- Why this block exists:
- Dataset / split / task:
- Systems compared:
- Metrics:
- Success criterion:
- Failure interpretation:
- Priority: must-run / nice-to-have / defer

## Run Order

| Order | Block | Purpose | Dependency | Stop / go gate | Est. cost |
| --- | --- | --- | --- | --- | --- |
| 1 | | | | | |

## Risks and Confounds

- Risk:
- Mitigation:
""",
    "experiment-tracker.md": """# Experiment Tracker

| Run ID | Block | Purpose | Priority | Status | Output artifact | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| R001 | | | must-run | todo | | |
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
