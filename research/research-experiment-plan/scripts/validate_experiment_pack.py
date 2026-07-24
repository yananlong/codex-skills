#!/usr/bin/env python3
"""Validate tracked experiment-planning packs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


REQUIRED_PLAN_HEADINGS = [
    "# Experiment Plan",
    "## Context",
    "## Claim Map",
    "## Experimental Storyline",
    "## Experiment Blocks",
    "## Run Order",
    "## Decision Gates",
    "## Risks and Confounds",
]

TRACKER_STATUSES = {
    "planned",
    "ready",
    "blocked",
    "running",
    "analyzed",
    "decisive",
    "inconclusive",
    "dropped",
}

BLOCK_PRIORITIES = {"must-run", "nice-to-have", "defer"}
DECISION_IF_UNPROVEN = {"reframe", "drop", "defer"}
EVIDENCE_CLASSES = {
    "exploratory",
    "confirmatory",
    "independently_verified",
    "operational_high_stakes",
}
STRONG_EVIDENCE_CLASSES = EVIDENCE_CLASSES - {"exploratory"}
PLACEHOLDER_VALUES = {"", "n/a", "na", "none", "null", "tbd", "todo", "unknown"}


def _read(path: Path, label: str, errors: list[str]) -> str:
    if not path.exists():
        errors.append(f"{label} file not found: {path}")
        return ""
    return path.read_text(encoding="utf-8")


def _load_json(path: Path, label: str, errors: list[str]):
    if not path.exists():
        errors.append(f"{label} file not found: {path}")
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"{label} is not valid JSON: {exc}")
        return None


def _check_headings(content: str, label: str, required: list[str], errors: list[str]) -> None:
    for heading in required:
        if heading not in content:
            errors.append(f"{label}: missing required heading '{heading}'")


def _table_rows(markdown: str, heading: str) -> list[list[str]]:
    idx = markdown.find(heading)
    if idx < 0:
        return []
    section_text = markdown[idx:].split("\n## ", 1)[0]
    rows: list[list[str]] = []
    for line in section_text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if not cells:
            continue
        if cells[0].lower() in {"run id", "gate id", "order"}:
            continue
        if all(set(cell) <= {"-", ":"} for cell in cells):
            continue
        rows.append(cells)
    return rows


def _is_meaningful_string(value) -> bool:
    return isinstance(value, str) and value.strip().lower() not in PLACEHOLDER_VALUES


def _require_meaningful_string(entry: dict, field: str, label: str, errors: list[str]) -> None:
    if not _is_meaningful_string(entry.get(field)):
        errors.append(f"{label}.{field} must be a substantive non-placeholder string")


def _require_list(entry: dict, field: str, label: str, errors: list[str], *, nonempty: bool) -> None:
    value = entry.get(field)
    if not isinstance(value, list):
        errors.append(f"{label}.{field} must be a list")
    elif nonempty and not value:
        errors.append(f"{label}.{field} must be a non-empty list")


def _validate_claim_map(data, errors: list[str], assurance_profile: str) -> set[str]:
    if not isinstance(data, list) or not data:
        errors.append("claim-map.json must be a non-empty JSON array")
        return set()
    ids: set[str] = set()
    strong_claim_count = 0
    for idx, entry in enumerate(data, start=1):
        label = f"claim-map.json[{idx}]"
        if not isinstance(entry, dict):
            errors.append(f"{label} must be an object")
            continue
        claim_id = entry.get("claim_id")
        if not isinstance(claim_id, str) or not claim_id.strip():
            errors.append(f"{label}.claim_id must be a non-empty string")
        elif claim_id in ids:
            errors.append(f"duplicate claim_id: {claim_id}")
        else:
            ids.add(claim_id)
        if entry.get("decision_if_unproven") not in DECISION_IF_UNPROVEN:
            errors.append(
                f"{label}.decision_if_unproven must be one of {sorted(DECISION_IF_UNPROVEN)}"
            )

        if assurance_profile == "confirmatory":
            evidence_class = entry.get("evidence_class")
            if evidence_class not in EVIDENCE_CLASSES:
                errors.append(f"{label}.evidence_class must be one of {sorted(EVIDENCE_CLASSES)}")
                continue
            if evidence_class in STRONG_EVIDENCE_CLASSES:
                strong_claim_count += 1
                for field in ("decision_rule", "loss_contract", "falsification_test"):
                    _require_meaningful_string(entry, field, label, errors)
                _require_list(entry, "predecessor_failures", label, errors, nonempty=False)

    if assurance_profile == "confirmatory" and strong_claim_count == 0:
        errors.append(
            "confirmatory assurance profile requires at least one claim with evidence_class "
            "confirmatory, independently_verified, or operational_high_stakes"
        )
    return ids


def _validate_run_blocks(
    data, claim_ids: set[str], errors: list[str], assurance_profile: str
) -> set[str]:
    if not isinstance(data, list) or not data:
        errors.append("run-blocks.json must be a non-empty JSON array")
        return set()
    block_ids: set[str] = set()
    strong_block_count = 0
    for idx, entry in enumerate(data, start=1):
        label = f"run-blocks.json[{idx}]"
        if not isinstance(entry, dict):
            errors.append(f"{label} must be an object")
            continue
        block_id = entry.get("block_id")
        if not isinstance(block_id, str) or not block_id.strip():
            errors.append(f"{label}.block_id must be a non-empty string")
        elif block_id in block_ids:
            errors.append(f"duplicate block_id: {block_id}")
        else:
            block_ids.add(block_id)
        if entry.get("priority") not in BLOCK_PRIORITIES:
            errors.append(f"{label}.priority must be one of {sorted(BLOCK_PRIORITIES)}")
        linked_claim_ids = entry.get("claim_ids")
        if not isinstance(linked_claim_ids, list) or not linked_claim_ids:
            errors.append(f"{label}.claim_ids must be a non-empty list")
        else:
            missing = [cid for cid in linked_claim_ids if cid not in claim_ids]
            if missing:
                errors.append(f"{label}.claim_ids reference unknown claims: {', '.join(missing)}")
        seeds = entry.get("seeds")
        if not isinstance(seeds, int) or seeds < 1:
            errors.append(f"{label}.seeds must be a positive integer")

        if assurance_profile == "confirmatory":
            evidence_class = entry.get("evidence_class")
            if evidence_class not in EVIDENCE_CLASSES:
                errors.append(f"{label}.evidence_class must be one of {sorted(EVIDENCE_CLASSES)}")
                continue
            if evidence_class in STRONG_EVIDENCE_CLASSES:
                strong_block_count += 1
                for field in (
                    "selection_rule",
                    "non_vacuity_check",
                    "complete_outcome_accounting",
                    "hidden_information_controls",
                ):
                    _require_meaningful_string(entry, field, label, errors)
                _require_list(entry, "independence_requirements", label, errors, nonempty=True)
                _require_list(entry, "predecessor_failures", label, errors, nonempty=False)

    if assurance_profile == "confirmatory" and strong_block_count == 0:
        errors.append(
            "confirmatory assurance profile requires at least one run block with evidence_class "
            "confirmatory, independently_verified, or operational_high_stakes"
        )
    return block_ids


def _validate_tracker(tracker_md: str, errors: list[str]) -> None:
    rows = _table_rows(tracker_md, "# Experiment Tracker")
    if not rows:
        errors.append("experiment-tracker.md has no tracker rows")
        return
    for idx, row in enumerate(rows, start=1):
        if len(row) < 6:
            errors.append(f"experiment-tracker.md row {idx} is too short")
            continue
        status = row[5]
        if status not in TRACKER_STATUSES:
            errors.append(f"experiment-tracker.md row {idx} has invalid status '{status}'")


def _validate_gates(decision_gates_md: str, block_ids: set[str], errors: list[str]) -> None:
    rows = _table_rows(decision_gates_md, "# Decision Gates")
    if not rows:
        errors.append("decision-gates.md has no gate rows")
        return
    for idx, row in enumerate(rows, start=1):
        if len(row) < 6:
            errors.append(f"decision-gates.md row {idx} is too short")
            continue
        opens_after = row[1]
        if opens_after and opens_after not in block_ids:
            errors.append(
                f"decision-gates.md row {idx} references unknown block '{opens_after}'"
            )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", required=True, help="Path to experiment-plan.md")
    parser.add_argument("--tracker", required=True, help="Path to experiment-tracker.md")
    parser.add_argument("--claim-map", required=True, help="Path to claim-map.json")
    parser.add_argument("--run-blocks", required=True, help="Path to run-blocks.json")
    parser.add_argument("--decision-gates", required=True, help="Path to decision-gates.md")
    parser.add_argument("--bridge", required=True, help="Path to execution-bridge.md")
    parser.add_argument(
        "--assurance-profile",
        choices=("structural", "confirmatory"),
        default="structural",
        help=(
            "Validation depth. 'structural' preserves legacy behavior. 'confirmatory' "
            "also requires evidence-class, decision-contract, non-vacuity, outcome-accounting, "
            "hidden-information, independence, and failure-inheritance fields."
        ),
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    errors: list[str] = []

    plan_md = _read(Path(args.plan).expanduser().resolve(), "plan", errors)
    tracker_md = _read(Path(args.tracker).expanduser().resolve(), "tracker", errors)
    decision_gates_md = _read(
        Path(args.decision_gates).expanduser().resolve(), "decision-gates", errors
    )
    bridge_md = _read(Path(args.bridge).expanduser().resolve(), "bridge", errors)
    claim_map = _load_json(Path(args.claim_map).expanduser().resolve(), "claim-map", errors)
    run_blocks = _load_json(Path(args.run_blocks).expanduser().resolve(), "run-blocks", errors)

    if errors:
        print("Validation failed:")
        for err in errors:
            print(f"- {err}")
        return 1

    _check_headings(plan_md, "plan", REQUIRED_PLAN_HEADINGS, errors)
    if "# Execution Bridge" not in bridge_md:
        errors.append("bridge: missing '# Execution Bridge' heading")
    if "# Experiment Tracker" not in tracker_md:
        errors.append("tracker: missing '# Experiment Tracker' heading")

    claim_ids = _validate_claim_map(claim_map, errors, args.assurance_profile)
    block_ids = _validate_run_blocks(run_blocks, claim_ids, errors, args.assurance_profile)
    _validate_tracker(tracker_md, errors)
    _validate_gates(decision_gates_md, block_ids, errors)

    if errors:
        print("Validation failed:")
        for err in errors:
            print(f"- {err}")
        return 1

    if args.assurance_profile == "confirmatory":
        print(
            "Validation passed: confirmatory assurance fields are structurally present and "
            "internally consistent. This does not establish that the claimed controls actually "
            "hold; semantic and independent audit remain required where claimed."
        )
    else:
        print(
            "Validation passed: experiment pack is structurally consistent. This does not "
            "certify semantic validity, independence, non-vacuity, or evidential sufficiency."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
