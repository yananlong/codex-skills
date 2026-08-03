#!/usr/bin/env python3
"""Create deterministic scaffolds for prospective research-suite evaluation."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ENDPOINTS = [
    "drift_sensitivity",
    "drift_false_positive_rate",
    "critical_paper_recall_initial",
    "critical_paper_recall_post_repair",
    "importance_weighted_recall_post_repair",
    "search_repair_gain",
    "late_omission_rate",
    "adverse_evidence_retention_rate",
    "terminal_route_rate",
    "median_days_to_terminal",
    "median_identity_transitions_to_terminal",
]


def empty_metrics() -> dict[str, None]:
    return {endpoint: None for endpoint in ENDPOINTS}


def protocol_template(study_id: str) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "study_id": study_id,
        "protocol_version": 1,
        "status": "draft",
        "frozen_at": "",
        "protocol_digest": "",
        "design_class": "descriptive",
        "assurance_class": "exploratory",
        "primary_endpoints": [
            "drift_sensitivity",
            "critical_paper_recall_post_repair",
            "adverse_evidence_retention_rate",
            "terminal_route_rate",
        ],
        "secondary_endpoints": [
            "drift_false_positive_rate",
            "critical_paper_recall_initial",
            "importance_weighted_recall_post_repair",
            "search_repair_gain",
            "late_omission_rate",
            "median_days_to_terminal",
            "median_identity_transitions_to_terminal",
        ],
        "project_eligibility": "Define genuinely new projects before exposure to suite outcomes.",
        "project_exclusion_rules": [],
        "enrollment_target": 1,
        "stopping_rule": "Freeze a pilot or confirmatory stopping rule before project outcomes.",
        "missing_data_policy": "Preserve missingness and do not promote assurance because data are absent.",
        "technical_failure_policy": "Retain technical failures and distinguish them from scientific outcomes.",
        "custody": {
            "challenge_custodian": "",
            "challenge_freeze_digest": "",
            "challenge_frozen_before_search": False,
            "evaluator_independence": {
                "self_review": True,
                "dimensions": [],
                "evidence": "",
            },
        },
        "comparison": {
            "mode": "none",
            "comparator": "",
            "allocation_frozen_before_outcome": False,
            "equal_information_access": False,
            "sample_size_rule": "",
            "uncertainty_method": "",
            "effect_thresholds": [],
        },
        "conclusion_policy": {
            "max_authority": "descriptive",
            "no_promotion_from_pilot": True,
            "downgrade_rules": [
                "Outcome-informed protocol changes cap conclusions at descriptive or exploratory authority."
            ],
        },
        "amendments": [],
    }


def observations_template(study_id: str) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "study_id": study_id,
        "protocol_version": 1,
        "protocol_digest": "",
        "challenge_set_digest": "",
        "status": "draft",
        "enrolled_project_ids": [],
        "projects": [],
    }


def summary_template(study_id: str) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "study_id": study_id,
        "protocol_digest": "",
        "status": "draft",
        "conclusion_authority": "instrumentation_only",
        "included_project_ids": [],
        "excluded_project_ids": [],
        "pending_project_ids": [],
        "metrics": empty_metrics(),
        "condition_metrics": {},
        "comparisons": [],
        "conclusion": "No prospective observations have been collected.",
        "limitations": [
            "Artifact validation does not create prospective evidence or establish research-suite effectiveness."
        ],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target_dir", type=Path)
    parser.add_argument("--study-id", default="prospective-study-001")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.target_dir.mkdir(parents=True, exist_ok=True)
    files = {
        "prospective-protocol.json": protocol_template(args.study_id),
        "prospective-observations.json": observations_template(args.study_id),
        "prospective-summary.json": summary_template(args.study_id),
    }
    existing = [name for name in files if (args.target_dir / name).exists()]
    if existing and not args.force:
        raise SystemExit("Refusing to overwrite existing files without --force: " + ", ".join(sorted(existing)))
    for name, payload in files.items():
        path = args.target_dir / name
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"created {path}")


if __name__ == "__main__":
    main()
