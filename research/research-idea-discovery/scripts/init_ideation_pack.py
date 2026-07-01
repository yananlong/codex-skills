#!/usr/bin/env python3
"""Create a deterministic tracked ideation pack."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


FILE_TEMPLATES = {
    "landscape-map.md": """# Landscape Map

## Scope

- Direction:
- Domain:
- Target audience or venue:
- Constraints:
- Non-goals:

## Existing Context Used

| Source | Path or URL | What it contributed | Limits |
| --- | --- | --- | --- |
| | | | |

## Subareas and Active Approaches

| Subarea | Representative work or artifact | Current assumption | Open gap |
| --- | --- | --- | --- |
| | | | |

## Closest Work

| Work | Year | Relationship to target direction | Why it matters |
| --- | --- | --- | --- |
| | | | |

## Gap Inventory

| Gap ID | Gap | Evidence source | Why it may support a publishable idea | Risk |
| --- | --- | --- | --- | --- |
| GAP-001 | | | | |

## Search and Source Limits

- Search access:
- Corpus limits:
- Date/venue limits:
- Claims that remain unverified:
""",
    "idea-bank.md": """# Idea Bank

## Generation Setup

- Direction:
- Landscape map:
- Constraints:
- Lenses used:

## Candidate Ideas

### IDEA-001: Title

- Summary:
- Hypothesis:
- Mechanism or causal story:
- Minimum viable validation:
- Closest known work:
- Differentiation:
- Positive outcome would show:
- Negative outcome would show:
- Likely failure mode:
- Estimated effort:
- Initial status:
""",
    "selected-idea.md": """# Selected Idea

## Recommendation

- Decision:
- Selected idea IDs:
- Recommended next skill:

## Idea Summary

- Title:
- One-sentence claim:
- Hypothesis:
- Mechanism:
- Contribution type:

## Differentiation

- Closest work:
- What is actually different:
- What novelty review must verify:

## Minimum Validation

- Minimum viable experiment or analysis:
- Required data:
- Required code or tools:
- Success criterion:
- Failure criterion:
- Estimated effort:

## Risks and Blocking Questions

| Risk or question | Why it matters | What resolves it |
| --- | --- | --- |
| | | |

## Handoff Notes

- For research-novelty-review:
- For research-experiment-plan:
- For paper planning:
""",
    "rejected-ideas.md": """# Rejected Ideas

| Idea ID | Title | Rejection reason | Evidence or rationale | Can revisit when |
| --- | --- | --- | --- | --- |
| | | | | |

## Rejection Categories

- already_done
- too_broad
- not_testable
- too_incremental
- infeasible
- weak_significance
- unclear_mechanism
- outside_constraints
""",
}

EMPTY_SCORES = {
    "topic": "",
    "scoring_scale": "1-5",
    "ideas": [],
}

EMPTY_DECISION = {
    "decision": "generate_more",
    "selected_idea_ids": [],
    "rationale": "",
    "next_skill": None,
    "required_handoffs": [],
    "limits": ["Pack initialized before ideation was run."],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target_dir", type=Path, help="Directory where the ideation pack will be created.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing files.")
    return parser.parse_args()


def write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    args.target_dir.mkdir(parents=True, exist_ok=True)

    json_files = ["idea-scores.json", "ideation-decision.json"]
    existing = [name for name in [*FILE_TEMPLATES, *json_files] if (args.target_dir / name).exists()]
    if existing and not args.force:
        raise SystemExit(
            "Refusing to overwrite existing files without --force: " + ", ".join(sorted(existing))
        )

    for name, content in FILE_TEMPLATES.items():
        path = args.target_dir / name
        path.write_text(content, encoding="utf-8")
        print(f"created {path}")
    write_json(args.target_dir / "idea-scores.json", EMPTY_SCORES)
    print(f"created {args.target_dir / 'idea-scores.json'}")
    write_json(args.target_dir / "ideation-decision.json", EMPTY_DECISION)
    print(f"created {args.target_dir / 'ideation-decision.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
