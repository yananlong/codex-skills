#!/usr/bin/env python3
"""Validate the canonical paper-level research commitment artifact."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "1.0"
STATUSES = {"exploring", "committed", "executing", "interpreting", "closed"}
CONTRIBUTION_CLASSES = {
    "theory", "method", "protocol", "benchmark", "dataset",
    "empirical-finding", "position", "mixed",
}
SUCCESSOR_POLICIES = {"park", "reject", "separate-project"}
DRIFT_CLASSES = {"D0", "D1", "D2", "D3", "D4"}
PIVOT_DECISIONS = {"authorize-D3", "close-and-create-D4"}
PAPER_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,191}$")
REQUIRED_FIELDS = {
    "schema_version", "paper_id", "identity_version", "status", "main_question",
    "central_object_or_phenomenon", "contribution_class", "minimum_publishable_claim",
    "primary_evidence_obligation", "intended_audience", "permitted_refinements",
    "pivot_triggers", "kill_conditions", "successor_idea_policy",
    "next_mandatory_evidence_artifact", "reconsideration_gate", "selection_history",
    "predecessor_failures", "last_change_class", "last_change_rationale",
}
IDENTITY_FIELDS = (
    "main_question", "central_object_or_phenomenon", "minimum_publishable_claim",
    "primary_evidence_obligation", "intended_audience",
)
ACTIVE_FIELDS = IDENTITY_FIELDS + ("next_mandatory_evidence_artifact", "reconsideration_gate")


def _substantive(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_commitment(data: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["commitment must be a JSON object"]

    missing = sorted(REQUIRED_FIELDS - set(data))
    extra = sorted(set(data) - REQUIRED_FIELDS)
    if missing:
        errors.append("missing fields: " + ", ".join(missing))
    if extra:
        errors.append("unsupported fields: " + ", ".join(extra))

    if data.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION}")
    paper_id = data.get("paper_id")
    if not isinstance(paper_id, str) or not PAPER_ID_RE.fullmatch(paper_id):
        errors.append("paper_id must be a non-empty stable identifier using letters, numbers, dot, underscore, colon, or hyphen")
    if not isinstance(data.get("identity_version"), int) or data.get("identity_version", 0) < 1:
        errors.append("identity_version must be a positive integer")
    if data.get("status") not in STATUSES:
        errors.append(f"status must be one of {sorted(STATUSES)}")
    if data.get("contribution_class") not in CONTRIBUTION_CLASSES:
        errors.append(f"contribution_class must be one of {sorted(CONTRIBUTION_CLASSES)}")
    if data.get("successor_idea_policy") not in SUCCESSOR_POLICIES:
        errors.append(f"successor_idea_policy must be one of {sorted(SUCCESSOR_POLICIES)}")
    if data.get("last_change_class") not in DRIFT_CLASSES:
        errors.append(f"last_change_class must be one of {sorted(DRIFT_CLASSES)}")
    if not _substantive(data.get("last_change_rationale")):
        errors.append("last_change_rationale must be a substantive string")

    for field in (
        "permitted_refinements", "pivot_triggers", "kill_conditions",
        "selection_history", "predecessor_failures",
    ):
        if not isinstance(data.get(field), list):
            errors.append(f"{field} must be a list")

    for field in ("permitted_refinements", "pivot_triggers", "kill_conditions"):
        values = data.get(field)
        if isinstance(values, list):
            for index, value in enumerate(values, 1):
                if not _substantive(value):
                    errors.append(f"{field}[{index}] must be a substantive string")

    history = data.get("selection_history")
    if isinstance(history, list):
        for index, item in enumerate(history, 1):
            if not isinstance(item, dict):
                errors.append(f"selection_history[{index}] must be an object")
                continue
            if not _substantive(item.get("decision")):
                errors.append(f"selection_history[{index}].decision must be a substantive string")
            if not _substantive(item.get("rationale")):
                errors.append(f"selection_history[{index}].rationale must be a substantive string")

    status = data.get("status")
    if status in {"committed", "executing", "interpreting"}:
        for field in ACTIVE_FIELDS:
            if not _substantive(data.get(field)):
                errors.append(f"{field} must be non-empty for status {status}")
        if not data.get("pivot_triggers"):
            errors.append("pivot_triggers must be non-empty after commitment")
        if not data.get("kill_conditions"):
            errors.append("kill_conditions must be non-empty after commitment")
    elif status == "closed":
        for field in IDENTITY_FIELDS:
            if not _substantive(data.get(field)):
                errors.append(f"{field} must remain non-empty for a closed lineage")

    if status != "exploring" and data.get("last_change_class") in {"D3", "D4"}:
        decisions = {
            item.get("decision")
            for item in history or []
            if isinstance(item, dict)
        }
        if not decisions.intersection(PIVOT_DECISIONS):
            errors.append("D3/D4 state requires an explicit authorized pivot decision in selection_history")

    return errors


def load_commitment(path: Path) -> tuple[Any, list[str]]:
    try:
        return json.loads(path.read_text(encoding="utf-8")), []
    except FileNotFoundError:
        return None, [f"missing file: {path}"]
    except json.JSONDecodeError as exc:
        return None, [f"invalid JSON: {exc}"]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("commitment", type=Path)
    args = parser.parse_args()
    path = args.commitment.expanduser().resolve()
    data, errors = load_commitment(path)
    if not errors:
        errors.extend(validate_commitment(data))
    if errors:
        print("Validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print(
        f"Validation passed: paper {data['paper_id']} identity v{data['identity_version']} "
        f"is a valid {data['status']} commitment contract. This establishes structural "
        "consistency only, not scientific validity, authenticated approval, or independent review."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
