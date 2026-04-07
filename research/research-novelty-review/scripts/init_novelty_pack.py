#!/usr/bin/env python3
"""Create deterministic scaffolds for novelty review."""

from __future__ import annotations

import argparse
from pathlib import Path


FILE_TEMPLATES = {
    "novelty-report.md": """# Novelty Report

## Contribution Under Review

- One-sentence claim:
- Operating mode: standalone / orchestrated
- Upstream artifacts used:

## Claim Decomposition

| Dimension | Claimed novelty | Searchable formulation |
| --- | --- | --- |
| framing | | |
| method | | |
| protocol | | |
| artifact | | |
| finding | | |

## Strongest Overlaps

| Work | Threat rating (1-5) | Why it matters |
| --- | --- | --- |
| | | |

## Novelty-Killing Objections

- Objection:
- Why it could kill the claim:

## Decision

- Novelty decision rating (1-5):
- Decision confidence rating (1-5):
- Narrowest defensible positioning:
- What would change the decision:
""",
    "prior-art-matrix.md": """# Prior Art Matrix

| Work | Venue / year | Closest overlap | Threat rating (1-5) | What still looks new | What could kill the claim |
| --- | --- | --- | --- | --- | --- |
| | | | 1-5 | | |
""",
    "search-log.md": """# Search Log

| Query | Source | Filters | Purpose | Closest hits | Notes |
| --- | --- | --- | --- | --- | --- |
| | | | falsify framing / method / protocol / artifact / result | | |
""",
    "novelty-decision.json": """{
  "novelty_decision_rating": 3,
  "decision_confidence_rating": 3,
  "narrowest_defensible_positioning": "",
  "what_would_change_the_decision": "",
  "top_kill_shot_objections": []
}
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
