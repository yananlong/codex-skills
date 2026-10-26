#!/usr/bin/env python3
"""Validate tracked experiment-planning packs."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from claim_trajectory import check_repair, parse_action_text

REQUIRED_PLAN_HEADINGS = [
    "# Experiment Plan", "## Context", "## Claim Map", "## Experimental Storyline",
    "## Non-Vacuity Preflight", "## Experiment Blocks", "## Run Order",
    "## Decision Gates", "## Risks and Confounds",
]
TRACKER_STATUSES = {"planned", "ready", "blocked", "running", "analyzed", "decisive", "inconclusive", "dropped"}
BLOCK_PRIORITIES = {"must-run", "nice-to-have", "defer"}
# D7: how a run relates to the plan. A tracker row without a Kind column, or with an empty cell, is planned.
RUN_KINDS = {"planned", "unplanned", "precursor", "diagnostic", "retry"}
EVIDENCE_CLASSES = {"exploratory", "confirmatory", "independently_verified", "operational_high_stakes"}
EVIDENCE_RANK = {name: rank for rank, name in enumerate(("exploratory", "confirmatory", "independently_verified", "operational_high_stakes"))}
PLACEHOLDERS = {"", "n/a", "na", "none", "null", "tbd", "todo", "unknown", "-"}
EXECUTION_MODES = {"command", "notebook", "manual", "external_job"}
LINEAGE_RELATIONS = {
    "baseline", "replication", "ablation", "parameter_variation", "negative_control",
    "sensitivity", "alternative_hypothesis", "technical_retry",
}


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


def _split_cells(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def table_rows(markdown: str, heading: str, header_first_cell: str | None = None) -> list[list[str]]:
    """Return data rows under a heading.

    When ``header_first_cell`` is given, only the first table whose header row starts with that
    canonical column is parsed, so appended history tables under the same heading are ignored.
    Without a matching header, every table row under the heading is parsed (legacy behaviour).
    """
    start = markdown.find(heading)
    if start < 0:
        return []
    tail = markdown[start + len(heading):]
    next_heading = tail.find("\n#")
    section = tail if next_heading < 0 else tail[:next_heading]
    tables: list[list[list[str]]] = []
    current: list[list[str]] = []
    for line in section.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            if current:
                tables.append(current)
                current = []
            continue
        current.append(_split_cells(stripped))
    if current:
        tables.append(current)
    if header_first_cell is not None:
        for table in tables:
            if table and table[0] and table[0][0].lower() == header_first_cell:
                tables = [table[1:]]
                break
    rows: list[list[str]] = []
    for table in tables:
        for cells in table:
            if not cells or all(set(cell) <= {"-", ":"} for cell in cells):
                continue
            if cells[0].lower() in {"run id", "gate id", "order", "claim id", "block"}:
                continue
            rows.append(cells)
    return rows


ENVELOPE_KEYS = {"claim-map.json": "claims", "run-blocks.json": "blocks"}


def unwrap_envelope(data: Any, label: str, errors: list[str]) -> Any:
    """Accept a bare array or a versioned envelope {schema_version, plan_version, claims|blocks: [...]}."""
    if not isinstance(data, dict):
        return data
    key = ENVELOPE_KEYS[label]
    entries = data.get(key)
    if not isinstance(entries, list):
        errors.append(f"{label} envelope must contain a '{key}' array")
        return None
    for field in ("schema_version", "plan_version"):
        if field in data and not isinstance(data[field], (str, int)):
            errors.append(f"{label}.{field} must be a string or integer")
    return entries


def validate_claims(
    data, errors: list[str], confirmatory: bool, warnings: list[str] | None = None
) -> tuple[dict[str, dict], dict[str, set[str]]]:
    warnings = [] if warnings is None else warnings
    claims: dict[str, dict] = {}
    links: dict[str, set[str]] = {}
    if not isinstance(data, list) or not data:
        errors.append("claim-map.json must be a non-empty JSON array or a {schema_version, plan_version, claims: [...]} envelope")
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
        check_repair(entry.get("decision_if_unproven"), f"{label}.decision_if_unproven", errors, warnings)
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
        claim.get("evidence_class") in EVIDENCE_CLASSES - {"exploratory"}
        for claim in claims.values()
    ):
        errors.append("confirmatory assurance profile requires at least one valid non-exploratory claim")
    return claims, links


def validate_path_entries(value: Any, label: str, errors: list[str]) -> list[str]:
    if not isinstance(value, list):
        errors.append(f"{label} must be a list")
        return []
    paths: list[str] = []
    for index, entry in enumerate(value, 1):
        path = entry if isinstance(entry, str) else entry.get("path") if isinstance(entry, dict) else None
        if not meaningful(path):
            errors.append(f"{label}[{index}].path must be substantive")
            continue
        if path in paths:
            errors.append(f"{label} contains duplicate path: {path}")
        paths.append(path)
        if isinstance(entry, dict) and label.endswith(("declared_inputs", "declared_evaluator_artifacts")):
            if entry.get("snapshot", "digest-at-start") != "digest-at-start":
                errors.append(f"{label}[{index}].snapshot must be digest-at-start")
    return paths


def validate_execution(entry: dict, label: str, errors: list[str], *, required: bool) -> None:
    execution = entry.get("execution")
    if execution is None:
        if required:
            errors.append(f"{label}.execution is required for must-run confirmatory blocks")
        return
    if not isinstance(execution, dict):
        errors.append(f"{label}.execution must be an object")
        return
    mode = execution.get("mode")
    if mode not in EXECUTION_MODES:
        errors.append(f"{label}.execution.mode must be one of {sorted(EXECUTION_MODES)}")
    entrypoint = execution.get("entrypoint")
    if mode in {"command", "notebook", "external_job"}:
        if not isinstance(entrypoint, dict):
            errors.append(f"{label}.execution.entrypoint is required for mode {mode}")
        else:
            argv = entrypoint.get("argv")
            if not isinstance(argv, list) or (required and not argv):
                errors.append(f"{label}.execution.entrypoint.argv must be a list" + (" and non-empty" if required else ""))
            elif any(not meaningful(value) for value in argv):
                errors.append(f"{label}.execution.entrypoint.argv entries must be substantive")
            if "cwd" in entrypoint and not meaningful(entrypoint.get("cwd")):
                errors.append(f"{label}.execution.entrypoint.cwd must be substantive")
    elif mode == "manual" and entrypoint not in {None, ""} and entrypoint != {}:
        errors.append(f"{label}.execution.entrypoint must be null or empty for manual mode")

    inputs = validate_path_entries(execution.get("declared_inputs", []), f"{label}.execution.declared_inputs", errors)
    evaluators = validate_path_entries(
        execution.get("declared_evaluator_artifacts", []),
        f"{label}.execution.declared_evaluator_artifacts",
        errors,
    )
    outputs = validate_path_entries(execution.get("required_outputs", []), f"{label}.execution.required_outputs", errors)
    if required and not outputs:
        errors.append(f"{label}.execution.required_outputs must be non-empty")
    overlap = (set(inputs) | set(evaluators)) & set(outputs)
    if overlap:
        errors.append(f"{label}.execution input/evaluator paths overlap required outputs: {', '.join(sorted(overlap))}")
    expected = entry.get("expected_output_artifact")
    if meaningful(expected) and outputs and expected not in outputs:
        errors.append(f"{label}.expected_output_artifact must appear in execution.required_outputs")


def validate_lineage_policy(entry: dict, label: str, errors: list[str], *, required: bool) -> None:
    policy = entry.get("lineage_policy")
    if policy is None:
        if required:
            errors.append(f"{label}.lineage_policy is required for must-run confirmatory blocks")
        return
    if not isinstance(policy, dict):
        errors.append(f"{label}.lineage_policy must be an object")
        return
    allowed = policy.get("allowed_relations")
    if not isinstance(allowed, list) or not allowed:
        errors.append(f"{label}.lineage_policy.allowed_relations must be a non-empty list")
        return
    unknown = sorted({str(value) for value in allowed} - LINEAGE_RELATIONS)
    if unknown:
        errors.append(f"{label}.lineage_policy contains unsupported relations: {', '.join(unknown)}")
    if "baseline" not in allowed:
        errors.append(f"{label}.lineage_policy.allowed_relations must include baseline")
    if "pivot" in allowed:
        errors.append(f"{label}.lineage_policy cannot encode D3/D4 pivot")


def validate_blocks(data, claims: dict[str, dict], errors: list[str], confirmatory: bool) -> tuple[dict[str, dict], dict[str, set[str]]]:
    blocks: dict[str, dict] = {}
    links: dict[str, set[str]] = {}
    if not isinstance(data, list) or not data:
        errors.append("run-blocks.json must be a non-empty JSON array or a {schema_version, plan_version, blocks: [...]} envelope")
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
        unknown = [claim_id for claim_id in claim_ids if claim_id not in claims]
        if unknown:
            errors.append(f"{label}.claim_ids reference unknown claims: {', '.join(map(str, unknown))}")
        if not isinstance(entry.get("seeds"), int) or entry["seeds"] < 1:
            errors.append(f"{label}.seeds must be a positive integer")
        dependencies = require_list(entry, "dependencies", label, errors)
        if block_id in dependencies:
            errors.append(f"{label}.dependencies cannot include itself")
        if "decision_gate_id" in entry and not meaningful(entry.get("decision_gate_id")):
            errors.append(f"{label}.decision_gate_id must be substantive when present")
        must_run_confirmatory = confirmatory and entry.get("priority") == "must-run"
        validate_execution(entry, label, errors, required=must_run_confirmatory)
        validate_lineage_policy(entry, label, errors, required=must_run_confirmatory)
        if must_run_confirmatory and not meaningful(entry.get("decision_gate_id")):
            errors.append(f"{label}.decision_gate_id is required for must-run confirmatory blocks")
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
        unknown = [dependency for dependency in entry.get("dependencies", []) if dependency not in block_ids]
        if unknown:
            errors.append(f"run-blocks.json[{index}].dependencies reference unknown blocks: {', '.join(map(str, unknown))}")
    graph = {block_id: list(block.get("dependencies", [])) for block_id, block in blocks.items()}
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> None:
        if node in visiting:
            errors.append(f"run-block dependency cycle includes {node}")
            return
        if node in visited:
            return
        visiting.add(node)
        for dependency in graph.get(node, []):
            if dependency in graph:
                visit(dependency)
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
                block_id for block_id in linked_blocks
                if block_id in blocks
                and EVIDENCE_RANK.get(blocks[block_id].get("evidence_class"), -1) >= rank
            ]
            if not adequate:
                errors.append(f"claim {claim_id} has no linked block at or above evidence class {claim_evidence}")
    for block_id, linked_claims in block_links.items():
        for claim_id in linked_claims:
            if claim_id in claims and block_id not in claim_links.get(claim_id, set()):
                errors.append(f"claim/block links are not reciprocal: {block_id} -> {claim_id}")


def validate_exploratory_content(claim_map: Any, run_blocks: Any, errors: list[str]) -> None:
    """Reject the untouched init scaffold: claims, falsifiers, metrics, and success criteria must be real."""
    for index, entry in enumerate(claim_map if isinstance(claim_map, list) else [], 1):
        if isinstance(entry, dict):
            for field in ("claim", "falsifier"):
                require_string(entry, field, f"claim-map.json[{index}]", errors)
    for index, entry in enumerate(run_blocks if isinstance(run_blocks, list) else [], 1):
        if not isinstance(entry, dict):
            continue
        label = f"run-blocks.json[{index}]"
        require_string(entry, "success_criterion", label, errors)
        metrics = entry.get("metrics")
        if not isinstance(metrics, list) or not metrics or any(not meaningful(value) for value in metrics):
            errors.append(f"{label}.metrics must be a non-empty list of substantive metric names")


def validate_gates(
    markdown: str, block_ids: set[str], errors: list[str], confirmatory: bool, warnings: list[str] | None = None
) -> dict[str, str]:
    warnings = [] if warnings is None else warnings
    rows = table_rows(markdown, "# Decision Gates", "gate id")
    if not rows:
        errors.append("decision-gates.md has no gate rows")
        return {}
    gate_map: dict[str, str] = {}
    for index, row in enumerate(rows, 1):
        if len(row) < 7:
            errors.append(f"decision-gates.md row {index} is too short")
            continue
        gate, opens_after = row[0], row[1]
        if not meaningful(gate):
            errors.append(f"decision-gates.md row {index} has no gate id")
        elif gate in gate_map:
            errors.append(f"duplicate gate id: {gate}")
        else:
            gate_map[gate] = opens_after
        if opens_after not in block_ids:
            errors.append(f"decision-gates.md row {index} references unknown block '{opens_after}'")
        if confirmatory:
            for cell_name, cell in zip(("decision question", "proceed if", "revise if", "stop if", "owner"), row[2:7]):
                if not meaningful(cell):
                    errors.append(f"decision-gates.md row {index} {cell_name} must be substantive")
        revise = row[4]
        if meaningful(revise) and parse_action_text(revise)[0] is None:
            warnings.append(
                f"decision-gates.md row {index} 'Revise if' does not name a repair action; start it with one of "
                "add_evidence, sharpen_comparator, lower_assurance, reframe, narrow, pivot, stop and a colon"
            )
    return gate_map


def validate_block_gate_links(blocks: dict[str, dict], gate_map: dict[str, str], errors: list[str], confirmatory: bool) -> None:
    for block_id, block in blocks.items():
        gate_id = block.get("decision_gate_id")
        if not meaningful(gate_id):
            if confirmatory and block.get("priority") == "must-run":
                errors.append(f"must-run block {block_id} lacks decision_gate_id")
            continue
        if gate_id not in gate_map:
            errors.append(f"block {block_id} references unknown decision gate {gate_id}")
        elif gate_map[gate_id] != block_id:
            errors.append(f"block {block_id} gate {gate_id} opens after {gate_map[gate_id]}, not {block_id}")


def tracker_kind_column(markdown: str) -> int | None:
    """Index of the optional Kind column in the tracker's header row, or None."""
    start = markdown.find("# Experiment Tracker")
    if start < 0:
        return None
    for line in markdown[start:].splitlines():
        stripped = line.strip()
        if stripped.startswith("|"):
            cells = _split_cells(stripped)
            if cells and cells[0].lower() == "run id":
                lowered = [cell.lower() for cell in cells]
                return lowered.index("kind") if "kind" in lowered else None
    return None


def tracker_run_kind(row: list[str], kind_column: int | None) -> str:
    if kind_column is None or kind_column >= len(row) or not row[kind_column].strip():
        return "planned"
    return row[kind_column].strip().strip("`").lower()


def validate_tracker(markdown: str, block_ids: set[str], gate_ids: set[str], errors: list[str]) -> None:
    rows = table_rows(markdown, "# Experiment Tracker", "run id")
    if not rows:
        errors.append("experiment-tracker.md has no tracker rows")
        return
    kind_column = tracker_kind_column(markdown)
    for index, row in enumerate(rows, 1):
        if len(row) < 10:
            errors.append(f"experiment-tracker.md row {index} is too short")
            continue
        kind = tracker_run_kind(row, kind_column)
        if kind not in RUN_KINDS:
            errors.append(f"experiment-tracker.md row {index} has invalid kind '{kind}'; use one of {sorted(RUN_KINDS)}")
            continue
        # Only a planned run must name a declared block, gate, and priority. Unplanned, precursor,
        # diagnostic, and retry runs may sit outside the plan; check_plan_drift.py reports them.
        planned = kind == "planned"
        if planned and row[1] not in block_ids:
            errors.append(
                f"experiment-tracker.md row {index} references unknown block '{row[1]}'; declare the block, "
                "or mark the row's Kind as unplanned, precursor, or diagnostic"
            )
        if planned and row[2] not in gate_ids:
            errors.append(f"experiment-tracker.md row {index} references unknown gate '{row[2]}'")
        if planned and row[4] not in BLOCK_PRIORITIES:
            errors.append(f"experiment-tracker.md row {index} has invalid priority '{row[4]}'")
        if row[5] not in TRACKER_STATUSES:
            errors.append(f"experiment-tracker.md row {index} has invalid status '{row[5]}'")


def validate_run_order(plan: str, block_ids: set[str], gate_ids: set[str], errors: list[str]) -> None:
    rows = table_rows(plan, "## Run Order", "order")
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
                "Claim IDs:", "Decision gate ID:", "Expected implementation entrypoint:",
                "Expected command or notebook:", "Output artifacts to produce:",
                "Auditor-facing checks:", "Intended lineage relation:",
                "Parent run ID or rationale:",
                "Hidden information unavailable to the evaluated system:",
                "Failure, skip, null, timeout, and retry states to retain:",
                "Idempotency and restart requirements:",
            )
            for required_label in required_labels:
                position = section.find(required_label)
                if position < 0:
                    errors.append(f"execution-bridge.md {block_id} missing '{required_label}'")
                    continue
                value = section[position + len(required_label):].splitlines()[0].strip()
                if not meaningful(value):
                    errors.append(f"execution-bridge.md {block_id} '{required_label}' must be substantive")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("plan", "tracker", "claim-map", "run-blocks", "decision-gates", "bridge"):
        parser.add_argument(f"--{name}", required=True)
    parser.add_argument(
        "--assurance-profile",
        choices=("structural", "exploratory", "confirmatory"),
        default="structural",
        help="structural: links only; exploratory: also rejects placeholder claims, falsifiers, metrics, "
        "success criteria, and gate cells; confirmatory: full class-specific assurance fields.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    errors: list[str] = []
    warnings: list[str] = []
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
    claim_map = unwrap_envelope(claim_map, "claim-map.json", errors)
    run_blocks = unwrap_envelope(run_blocks, "run-blocks.json", errors)
    if "# Experiment Tracker" not in tracker:
        errors.append("tracker: missing '# Experiment Tracker' heading")
    confirmatory = args.assurance_profile == "confirmatory"
    exploratory = args.assurance_profile == "exploratory"
    if exploratory:
        validate_exploratory_content(claim_map, run_blocks, errors)
    claims, claim_links = validate_claims(claim_map, errors, confirmatory, warnings)
    blocks, block_links = validate_blocks(run_blocks, claims, errors, confirmatory)
    validate_links(claims, claim_links, blocks, block_links, errors, confirmatory)
    gate_map = validate_gates(gates, set(blocks), errors, confirmatory or exploratory, warnings)
    validate_block_gate_links(blocks, gate_map, errors, confirmatory)
    validate_tracker(tracker, set(blocks), set(gate_map), errors)
    validate_run_order(plan, set(blocks), set(gate_map), errors)
    validate_bridge(bridge, blocks, errors, confirmatory)
    if errors:
        print("Validation failed:")
        for error in errors:
            print(f"- {error}")
        print_warnings(warnings)
        return 1
    if confirmatory:
        print(
            "Validation passed: claim/block links, evidence-class ordering, execution declarations, "
            "lineage policies, dependencies, decision-gate bindings, tracker references, and "
            "class-specific assurance fields are structurally present and internally consistent. "
            "This does not establish executor isolation, immutable inputs, scientific validity, or "
            "independent verification."
        )
    elif exploratory:
        print(
            "Validation passed: claims, falsifiers, metrics, success criteria, and decision-gate cells are "
            "filled in, and claim/block/gate/tracker links are consistent. This does not certify semantic "
            "validity, non-vacuity, or evidential sufficiency."
        )
    else:
        print(
            "Validation passed: experiment pack is structurally consistent. Execution declarations "
            "and lineage policies were checked when present; this does not certify semantic validity, "
            "snapshot immutability, independence, non-vacuity, or evidential sufficiency."
        )
    print_warnings(warnings)
    return 0


def print_warnings(warnings: list[str]) -> None:
    if warnings:
        print("Warnings:")
        for warning in warnings:
            print(f"- {warning}")


if __name__ == "__main__":
    raise SystemExit(main())
