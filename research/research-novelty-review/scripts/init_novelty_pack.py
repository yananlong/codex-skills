#!/usr/bin/env python3
"""Create deterministic scaffolds for novelty review."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


NOVELTY_REPORT = """# Novelty Report

## Contribution Under Review

- One-sentence claim:
- Operating mode: standalone / orchestrated
- Upstream artifacts used:
- Literature-context artifacts used:

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

- Novelty decision rating (1-5): 3
- Impact positioning rating (1-5): 3
- Decision confidence rating (1-5): 3
- Narrowest defensible positioning:
- What would change the decision:
- Literature assurance mode: unlinked
- Literature assurance verdict:
- Unresolved high-priority novelty-critical questions:

## Paper-Review Handoff

| Finding to add | Paper location / quote | Comment type | Impact | Confidence | Evidence basis |
| --- | --- | --- | ---: | ---: | --- |
| | | claim_accuracy / missing_information / presentation / methodology | 1-5 | 1-5 | |
"""

PRIOR_ART = """# Prior Art Matrix

| Work | Venue / year | Closest overlap | Threat rating (1-5) | What still looks new | What could kill the claim |
| --- | --- | --- | --- | --- | --- |
| | | | 1-5 | | |
"""

SEARCH_LOG = """# Search Log

| Query | Source | Filters | Purpose | Closest hits | Notes |
| --- | --- | --- | --- | --- | --- |
| | | | falsify framing / method / protocol / artifact / result | | |
"""


def decision_template() -> dict:
    return {
        "schema_version": "1.1",
        "status": "draft",
        "novelty_decision_rating": 3,
        "impact_positioning_rating": 3,
        "decision_confidence_rating": 3,
        "narrowest_defensible_positioning": "",
        "what_would_change_the_decision": "",
        "top_kill_shot_objections": [],
        "literature_context_used": [],
        "paper_review_summary_used": "",
        "claims_to_qualify": [],
        "missing_prior_work": [],
        "review_findings_to_add": [],
        "literature_assurance": {
            "mode": "unlinked",
            "paths": {
                "protocol": "",
                "search_log": "",
                "recall_audit": "",
                "corpus_manifest": "",
                "screening_log": "",
                "evidence": "",
                "report": "",
            },
            "file_sha256": {
                "protocol": "",
                "search_log": "",
                "recall_audit": "",
                "corpus_manifest": "",
                "screening_log": "",
                "evidence": "",
                "report": "",
            },
            "corpus_manifest_sha256": "",
            "corpus_version": None,
            "review_profile": "",
            "assurance_verdict": "",
            "unresolved_high_priority_novelty_question_ids": [],
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target_dir", type=Path, help="Directory where the pack will be created.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing files.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.target_dir.mkdir(parents=True, exist_ok=True)
    files = {
        "novelty-report.md": NOVELTY_REPORT,
        "prior-art-matrix.md": PRIOR_ART,
        "search-log.md": SEARCH_LOG,
        "novelty-decision.json": json.dumps(decision_template(), indent=2, sort_keys=True) + "\n",
    }
    existing = [name for name in files if (args.target_dir / name).exists()]
    if existing and not args.force:
        raise SystemExit(
            "Refusing to overwrite existing files without --force: " + ", ".join(sorted(existing))
        )
    for name, content in files.items():
        path = args.target_dir / name
        path.write_text(content, encoding="utf-8")
        print(f"created {path}")


if __name__ == "__main__":
    main()
