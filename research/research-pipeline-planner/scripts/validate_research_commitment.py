#!/usr/bin/env python3
"""Validate the canonical paper-level research commitment artifact."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

STATUSES = {"exploring", "committed", "executing", "interpreting", "closed"}
CLASSES = {"theory", "method", "protocol", "benchmark", "dataset", "empirical-finding", "position", "mixed"}
POLICIES = {"park", "reject", "separate-project"}
DRIFT = {"D0", "D1", "D2", "D3", "D4"}
REQUIRED = {
    "schema_version", "paper_id", "identity_version", "status", "main_question",
    "central_object_or_phenomenon", "contribution_class", "minimum_publishable_claim",
    "primary_evidence_obligation", "intended_audience", "permitted_refinements",
    "pivot_triggers", "kill_conditions", "successor_idea_policy",
    "next_mandatory_evidence_artifact", "reconsideration_gate", "selection_history",
    "predecessor_failures", "last_change_class", "last_change_rationale",
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("commitment", type=Path)
    args = parser.parse_args()
    errors: list[str] = []
    try:
        data = json.loads(args.commitment.expanduser().resolve().read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"Validation failed:\n- missing file: {args.commitment}")
        return 1
    except json.JSONDecodeError as exc:
        print(f"Validation failed:\n- invalid JSON: {exc}")
        return 1
    missing = sorted(REQUIRED - set(data))
    if missing:
        errors.append("missing fields: " + ", ".join(missing))
    if data.get("schema_version") != "1.0":
        errors.append("schema_version must be 1.0")
    if not isinstance(data.get("paper_id"), str) or not data.get("paper_id", "").strip():
        errors.append("paper_id must be a non-empty string")
    if not isinstance(data.get("identity_version"), int) or data.get("identity_version", 0) < 1:
        errors.append("identity_version must be a positive integer")
    if data.get("status") not in STATUSES:
        errors.append("invalid status")
    if data.get("contribution_class") not in CLASSES:
        errors.append("invalid contribution_class")
    if data.get("successor_idea_policy") not in POLICIES:
        errors.append("invalid successor_idea_policy")
    if data.get("last_change_class") not in DRIFT:
        errors.append("invalid last_change_class")
    for field in ("permitted_refinements", "pivot_triggers", "kill_conditions", "selection_history", "predecessor_failures"):
        if not isinstance(data.get(field), list):
            errors.append(f"{field} must be a list")
    if data.get("status") in {"committed", "executing", "interpreting"}:
        for field in ("main_question", "central_object_or_phenomenon", "minimum_publishable_claim", "primary_evidence_obligation", "intended_audience", "next_mandatory_evidence_artifact", "reconsideration_gate"):
            if not isinstance(data.get(field), str) or not data.get(field, "").strip():
                errors.append(f"{field} must be non-empty for status {data.get('status')}")
        if not data.get("pivot_triggers"):
            errors.append("pivot_triggers must be non-empty after commitment")
        if not data.get("kill_conditions"):
            errors.append("kill_conditions must be non-empty after commitment")
        if data.get("last_change_class") in {"D3", "D4"}:
            history = data.get("selection_history", [])
            if not any(isinstance(item, dict) and item.get("decision") in {"authorize-D3", "close-and-create-D4"} for item in history):
                errors.append("D3/D4 state requires an explicit authorized pivot decision in selection_history")
    if errors:
        print("Validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"Validation passed: paper {data['paper_id']} identity v{data['identity_version']} is a valid {data['status']} commitment contract. This does not establish scientific validity or independent approval.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
