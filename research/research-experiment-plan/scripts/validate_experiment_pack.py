#!/usr/bin/env python3
"""Validate tracked experiment-planning packs."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

REQUIRED_PLAN_HEADINGS = [
    "# Experiment Plan", "## Context", "## Claim Map", "## Experimental Storyline",
    "## Non-Vacuity Preflight", "## Experiment Blocks", "## Run Order",
    "## Decision Gates", "## Risks and Confounds",
]
TRACKER_STATUSES = {"planned", "ready", "blocked", "running", "analyzed", "decisive", "inconclusive", "dropped"}
BLOCK_PRIORITIES = {"must-run", "nice-to-have", "defer"}
DECISION_IF_UNPROVEN = {"reframe", "drop", "defer"}
EVIDENCE_CLASSES = {"exploratory", "confirmatory", "independently_verified", "operational_high_stakes"}
EVIDENCE_RANK = {name: rank for rank, name in enumerate(("exploratory", "confirmatory", "independently_verified", "operational_high_stakes"))}
PLACEHOLDERS = {"", "n/a", "na", "none", "null", "tbd", "todo", "unknown", "-"}


def read_text(path: Path, label: str, errors: list[str]) -> str:
    if not path.is_file():
        errors.append(f"{label} file not found: {path}")
        return ""
    return path.read_text(encoding="utf-8")


def read_json(path: Path, label: str, errors: list[str]):
    if not path.is_file():
        errors.append(f"{label} file not found: {path}")
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"{label} is not valid JSON: {exc}")
        return None


def meaningful(value: Any) -> bool:
    return isinstance(value, str) and value.strip().lower() not in PLACEHOLDERS


def require_string(entry: dict, field: str, label: str, errors: list[str]) -> None:
    if not meaningful(entry.get(field)):
        errors.append(f"{label}.{field} must be a substantive non-placeholder string")


def require_list(entry: dict, field: str, label: str, errors: list[str], *, nonempty: bool = False) -> list:
    value = entry.get(field)
    if not isinstance(value, list):
        errors.append(f"{label}.{field} must be a list")
        return []
    if nonempty and not value:
        errors.append(f"{label}.{field} must be a non-empty list")
    return value


def table_rows(markdown: str, heading: str) -> list[list[str]]:
    start = markdown.find(heading)
    if start < 0:
        return []
    tail = markdown[start + len(heading):]
    next_heading = tail.find("\n#")
    section = tail if next_heading < 0 else tail[:next_heading]
    rows: list[list[str]] = []
    for line in section.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if not cells or all(set(cell) <= {"-", ":"} for cell in cells):
            continue
        if cells[0].lower() in {"run id", "gate id", "order", "claim id", "block"}:
            continue
        rows.append(cells)
    return rows


def validate_claims(data, errors: list[str], confirmatory: bool) -> tuple[dict[str, dict], dict[str, set[str]]]:
    claims: dict[str, dict] = {}
    links: dict[str, set[str]] = {}
    if not isinstance(data, list) or not data:
        errors.append("claim-map.json must be a non-empty JSON array")
        return claims, links
    for index, entry in enumerate(data, 1):
        label = f"claim-map.json[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{label} must be an object")
            continue
        claim_id = entry.get("claim_id")
        if not meaningful(claim_id):
            errors.append(f"{label}.claim_id must be a non-empty string")
            continue
        if claim_id in claims:
            errors.append(f"duplicate claim_id: {claim_id}")
            continue
        claims[claim_id] = entry
        if entry.get("decision_if_unproven") not in DECISION_IF_UNPROVEN:
            errors.append(f"{label}.decision_if_unproven must be one of {sorted(DECISION_IF_UNPROVEN)}")
        links[claim_id] = {str(value) for value in require_list(entry, "linked_blocks", label, errors, nonempty=True)}
        if confirmatory:
            evidence = entry.get("evidence_class")
            if evidence not in EVIDENCE_CLASSES:
                errors.append(f"{label}.evidence_class must be one of {sorted(EVIDENCE_CLASSES)}")
                continue
            for field in ("claim", "why_it_matters", "minimum_convincing_evidence", "anti_claim", "falsifier"):
                require_string(entry, field, label, errors)
            require_list(entry, "selection_history", label, errors, nonempty=True)
            require_list(entry, "predecessor_failures", label, errors)
            if evidence != "exploratory":
                for field in ("decision_rule", "loss_contract", "falsification_test"):
                    require_string(entry, field, label, errors)
    if confirmatory and not any(
        c.get("evidence_class") in EVIDENCE_CLASSES - {"exploratory"}
        for c in claims.values()
    ):
        errors.append("confirmatory assurance profile requires at least one valid non-exploratory claim")
    return claims, links


def validate_blocks(data, claims: dict[str, dict], errors: list[str], confirmatory: bool) -> tuple[dict[str, dict], dict[str, set[str]]]:
    blocks: dict[str, dict] = {}
    links: dict[str, set[str]] = {}
    if not isinstance(data, list) or not data:
        errors.append("run-blocks.json must be a non-empty JSON array")
        return blocks, links
    for index, entry in enumerate(data, 1):
        label = f"run-blocks.json[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{label} must be an object")
            continue
        block_id = entry.get("block_id")
        if not meaningful(block_id):
            errors.append(f"{label}.block_id must be a non-empty string")
            continue
        if block_id in blocks:
            errors.append(f"duplicate block_id: {block_id}")
            continue
        blocks[block_id] = entry
        if entry.get("priority") not in BLOCK_PRIORITIES:
            errors.append(f"{label}.priority must be one of {sorted(BLOCK_PRIORITIES)}")
        claim_ids = require_list(entry, "claim_ids", label, errors, nonempty=True)
        links[block_id] = {str(value) for value in claim_ids}
        unknown = [cid for cid in claim_ids if cid not in claims]
        if unknown:
            errors.append(f"{label}.claim_ids reference unknown claims: {', '.join(map(str, unknown))}")
        if not isinstance(entry.get("seeds"), int) or entry["seeds"] < 1:
            errors.append(f"{label}.seeds must be a positive integer")
        dependencies = require_list(entry, "dependencies", label, errors)
        if block_id in dependencies:
            errors.append(f"{label}.dependencies cannot include itself")
        if confirmatory:
            evidence = entry.get("evidence_class")
            if evidence not in EVIDENCE_CLASSES:
                errors.append(f"{label}.evidence_class must be one of {sorted(EVIDENCE_CLASSES)}")
                continue
            for field in (
                "why_this_block_exists", "dataset_split_task", "setup_details",
                "success_criterion", "minimum_effect_size", "failure_interpretation",
                "expected_output_artifact", "compute_budget",
            ):
                require_string(entry, field, label, errors)
            for field in ("systems_compared", "metrics"):
                require_list(entry, field, label, errors, nonempty=True)
            for field in ("fixed_factors", "variable_factors", "anti_claims_ruled_out", "predecessor_failures"):
                require_list(entry, field, label, errors)
            if evidence != "exploratory":
                for field in ("selection_rule", "non_vacuity_check", "complete_outcome_accounting", "hidden_information_controls"):
                    require_string(entry, field, label, errors)
                require_list(entry, "independence_requirements", label, errors)
            if evidence in {"independently_verified", "operational_high_stakes"}:
                require_list(entry, "independence_requirements", label, errors, nonempty=True)
                require_string(entry, "independence_evidence", label, errors)
            if evidence == "operational_high_stakes":
                require_string(entry, "operational_threat_model", label, errors)
                require_string(entry, "operational_harms", label, errors)
    block_ids = set(blocks)
    for index, entry in enumerate(data if isinstance(data, list) else [], 1):
        if not isinstance(entry, dict):
            continue
        unknown = [d for d in entry.get("dependencies", []) if d not in block_ids]
        if unknown:
            errors.append(f"run-blocks.json[{index}].dependencies reference unknown blocks: {', '.join(map(str, unknown))}")
    graph = {bid: list(block.get("dependencies", [])) for bid, block in blocks.items()}
    visiting: set[str] = set()
    visited: set[str] = set()
    def visit(node: str):
        if node in visiting:
            errors.append(f"run-block dependency cycle includes {node}")
            return
        if node in visited:
            return
        visiting.add(node)
        for dep in graph.get(node, []):
            if dep in graph:
                visit(dep)
        visiting.remove(node)
        visited.add(node)
    for node in graph:
        visit(node)
    return blocks, links


def validate_links(claims: dict[str, dict], claim_links: dict[str, set[str]], blocks: dict[str, dict], block_links: dict[str, set[str]], errors: list[str], confirmatory: bool) -> None:
    for claim_id, linked_blocks in claim_links.items():
        for block_id in linked_blocks:
            if block_id not in blocks:
                errors.append(f"claim {claim_id} links unknown block {block_id}")
            elif claim_id not in block_links.get(block_id, set()):
                errors.append(f"claim/block links are not reciprocal: {claim_id} -> {block_id}")
        claim_evidence = claims[claim_id].get("evidence_class")
        if confirmatory and claim_evidence != "exploratory":
            rank = EVIDENCE_RANK.get(claim_evidence)
            if rank is None:
                continue
            adequate = [
                bid for bid in linked_blocks
                if bid in blocks
                and EVIDENCE_RANK.get(blocks[bid].get("evidence_class"), -1) >= rank
            ]
            if not adequate:
                errors.append(
                    f"claim {claim_id} has no linked block at or above evidence class {claim_evidence}"
                )
    for block_id, linked_claims in block_links.items():
        for claim_id in linked_claims:
            if claim_id in claims and block_id not in claim_links.get(claim_id, set()):
                errors.append(f"claim/block links are not reciprocal: {block_id} -> {claim_id}")


def validate_gates(markdown: str, block_ids: set[str], errors: list[str], confirmatory: bool) -> set[str]:
    rows = table_rows(markdown, "# Decision Gates")
    if not rows:
        errors.append("decision-gates.md has no gate rows")
        return set()
    gate_ids: set[str] = set()
    for index, row in enumerate(rows, 1):
        if len(row) < 7:
            errors.append(f"decision-gates.md row {index} is too short")
            continue
        gate, opens_after = row[0], row[1]
        if not meaningful(gate):
            errors.append(f"decision-gates.md row {index} has no gate id")
        elif gate in gate_ids:
            errors.append(f"duplicate gate id: {gate}")
        else:
            gate_ids.add(gate)
        if opens_after not in block_ids:
            errors.append(f"decision-gates.md row {index} references unknown block '{opens_after}'")
        if confirmatory:
            for cell_name, cell in zip(("decision question", "proceed if", "revise if", "stop if", "owner"), row[2:7]):
                if not meaningful(cell):
                    errors.append(f"decision-gates.md row {index} {cell_name} must be substantive")
    return gate_ids


def validate_tracker(markdown: str, block_ids: set[str], gate_ids: set[str], errors: list[str]) -> None:
    rows = table_rows(markdown, "# Experiment Tracker")
    if not rows:
        errors.append("experiment-tracker.md has no tracker rows")
        return
    for index, row in enumerate(rows, 1):
        if len(row) < 10:
            errors.append(f"experiment-tracker.md row {index} is too short")
            continue
        if row[1] not in block_ids:
            errors.append(f"experiment-tracker.md row {index} references unknown block '{row[1]}'")
        if row[2] not in gate_ids:
            errors.append(f"experiment-tracker.md row {index} references unknown gate '{row[2]}'")
        if row[4] not in BLOCK_PRIORITIES:
            errors.append(f"experiment-tracker.md row {index} has invalid priority '{row[4]}'")
        if row[5] not in TRACKER_STATUSES:
            errors.append(f"experiment-tracker.md row {index} has invalid status '{row[5]}'")


def validate_run_order(plan: str, block_ids: set[str], gate_ids: set[str], errors: list[str]) -> None:
    rows = table_rows(plan, "## Run Order")
    if not rows:
        errors.append("experiment-plan.md has no run-order rows")
        return
    for index, row in enumerate(rows, 1):
        if len(row) < 7:
            errors.append(f"experiment-plan.md run-order row {index} is too short")
            continue
        if row[1] not in block_ids:
            errors.append(f"experiment-plan.md run-order row {index} references unknown block '{row[1]}'")
        if row[4] not in gate_ids:
            errors.append(f"experiment-plan.md run-order row {index} references unknown gate '{row[4]}'")


def validate_bridge(markdown: str, blocks: dict[str, dict], errors: list[str], confirmatory: bool) -> None:
    if "# Execution Bridge" not in markdown:
        errors.append("bridge: missing '# Execution Bridge' heading")
        return
    headings = list(re.finditer(r"(?m)^###\s+([^\r\n]+?)\s*$", markdown))
    sections: dict[str, str] = {}
    for index, match in enumerate(headings):
        title = match.group(1).strip()
        end = headings[index + 1].start() if index + 1 < len(headings) else len(markdown)
        if title in sections:
            errors.append(f"execution-bridge.md has duplicate section heading for {title}")
            continue
        sections[title] = markdown[match.end():end]
    for block_id in blocks:
        section = sections.get(block_id)
        if section is None:
            errors.append(f"execution-bridge.md missing section for {block_id}")
            continue
        if confirmatory:
            required_labels = (
                "Claim IDs:", "Expected implementation entrypoint:", "Expected command or notebook:",
                "Output artifacts to produce:", "Auditor-facing checks:",
                "Hidden information unavailable to the evaluated system:",
                "Failure, skip, null, timeout, and retry states to retain:",
                "Idempotency and restart requirements:",
            )
            for label in required_labels:
                pos = section.find(label)
                if pos < 0:
                    errors.append(f"execution-bridge.md {block_id} missing '{label}'")
                    continue
                value = section[pos + len(label):].splitlines()[0].strip()
                if not meaningful(value):
                    errors.append(f"execution-bridge.md {block_id} '{label}' must be substantive")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("plan", "tracker", "claim-map", "run-blocks", "decision-gates", "bridge"):
        p.add_argument(f"--{name}", required=True)
    p.add_argument("--assurance-profile", choices=("structural", "confirmatory"), default="structural")
    return p


def main() -> int:
    args = build_parser().parse_args()
    errors: list[str] = []
    plan = read_text(Path(args.plan).expanduser().resolve(), "plan", errors)
    tracker = read_text(Path(args.tracker).expanduser().resolve(), "tracker", errors)
    gates = read_text(Path(args.decision_gates).expanduser().resolve(), "decision-gates", errors)
    bridge = read_text(Path(args.bridge).expanduser().resolve(), "bridge", errors)
    claim_map = read_json(Path(args.claim_map).expanduser().resolve(), "claim-map", errors)
    run_blocks = read_json(Path(args.run_blocks).expanduser().resolve(), "run-blocks", errors)
    if errors:
        print("Validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    for heading in REQUIRED_PLAN_HEADINGS:
        if heading not in plan:
            errors.append(f"plan: missing required heading '{heading}'")
    if "# Experiment Tracker" not in tracker:
        errors.append("tracker: missing '# Experiment Tracker' heading")
    confirmatory = args.assurance_profile == "confirmatory"
    claims, claim_links = validate_claims(claim_map, errors, confirmatory)
    blocks, block_links = validate_blocks(run_blocks, claims, errors, confirmatory)
    validate_links(claims, claim_links, blocks, block_links, errors, confirmatory)
    gate_ids = validate_gates(gates, set(blocks), errors, confirmatory)
    validate_tracker(tracker, set(blocks), gate_ids, errors)
    validate_run_order(plan, set(blocks), gate_ids, errors)
    validate_bridge(bridge, blocks, errors, confirmatory)
    if errors:
        print("Validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    if confirmatory:
        print("Validation passed: claim/block links, evidence-class ordering, dependencies, gates, tracker references, and class-specific assurance fields are structurally present and internally consistent. This does not establish that the controls actually held; semantic and independent audit remain required where claimed.")
    else:
        print("Validation passed: experiment pack is structurally consistent. This does not certify semantic validity, independence, non-vacuity, or evidential sufficiency.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
