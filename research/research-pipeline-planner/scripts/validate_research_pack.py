#!/usr/bin/env python3
"""Validate the orchestrated research suite layout."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


REQUIRED_FILES = {
    "research-brief.md": "# Research Brief",
    "task-board.md": "# Task Board",
    "decision-log.md": "# Decision Log",
    "artifact-index.md": "# Artifact Index",
}

REQUIRED_DIRS = [
    "literature-review",
    "novelty-review",
    "experiment-plan",
    "paper-plan",
    "review-loop",
]

REQUIRED_INDEX_ROWS = [
    "./research-brief.md",
    "./task-board.md",
    "./decision-log.md",
    "./literature-review/",
    "./novelty-review/",
    "./experiment-plan/",
    "./paper-plan/",
    "./review-loop/",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target_dir", type=Path, help="Research suite root directory.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.target_dir.expanduser().resolve()
    errors: list[str] = []

    for name, heading in REQUIRED_FILES.items():
        path = root / name
        if not path.exists():
            errors.append(f"missing file: {path}")
            continue
        content = path.read_text(encoding="utf-8")
        if heading not in content:
            errors.append(f"{path}: missing heading '{heading}'")

    for name in REQUIRED_DIRS:
        path = root / name
        if not path.is_dir():
            errors.append(f"missing directory: {path}")

    index_path = root / "artifact-index.md"
    if index_path.exists():
        index_content = index_path.read_text(encoding="utf-8")
        for row in REQUIRED_INDEX_ROWS:
            if row not in index_content:
                errors.append(f"{index_path}: missing canonical path '{row}'")

    if errors:
        print("Validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Research suite is valid!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
