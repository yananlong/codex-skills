#!/usr/bin/env python3
"""Durable single-writer runtime for orchestrated research-suite work items."""
from __future__ import annotations

import argparse
import copy
import json
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Any

try:
    import fcntl
except ImportError:  # pragma: no cover
    fcntl = None

from harness_common import (
    EVIDENCE_CLASSES,
    SCHEMA_VERSION,
    atomic_write_json,
    canonical_json,
    event_hash,
    find_item,
    initial_state,
    initial_work_items,
    load_json,
    path_digest,
    path_is_in_scope,
    read_events,
    resolve_inside_root,
    sha256_bytes,
    utc_now,
    validate_checkpoint_id,
    validate_identifier,
    verify_chain,
)

STATE_CHANGING_WHILE_PAUSED = {
    "work_item_added",
    "work_item_started",
    "episode_submitted",
    "verification_approved",
    "verification_revise",
    "work_item_failed_retryable",
    "work_item_blocked",
    "checkpoint_saved",
}
GATE_RESULTS = {"pass", "fail", "inconclusive", "not_applicable"}
SCIENTIFIC_DISPOSITIONS = {
    "supports_claim",
    "weakens_claim",
    "falsifies_claim",
    "inconclusive",
    "diagnostic_only",
}
LINEAGE_RELATIONS = {
    "baseline",
    "replication",
    "ablation",
    "parameter_variation",
    "negative_control",
    "sensitivity",
    "alternative_hypothesis",
    "technical_retry",
}
PARENT_REQUIRED_RELATIONS = {
    "technical_retry",
    "ablation",
    "parameter_variation",
    "sensitivity",
}
CLAIM_EFFECTS = {"strengthen", "weaken", "kill", "unchanged", "inconclusive"}
EXECUTION_MODES = {"command", "notebook", "manual", "external_job"}


def _meaningful(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _relative_arg_path(root: Path, value: Path | str, label: str) -> str:
    raw = Path(value).expanduser()
    candidate = raw.resolve() if raw.is_absolute() else (root / raw).resolve()
    try:
        return candidate.relative_to(root.resolve()).as_posix()
    except ValueError as exc:
        raise SystemExit(f"{label} must be stored inside the suite root") from exc


def _load_required_json(root: Path, relative: str, label: str) -> Any:
    path = resolve_inside_root(root, relative, label)
    if not path.is_file():
        raise SystemExit(f"{label} file not found: {relative}")
    return load_json(path, None)


def _find_block(run_blocks: Any, block_id: str) -> dict[str, Any]:
    if not isinstance(run_blocks, list):
        raise SystemExit("run-blocks artifact must be a JSON array")
    matches = [entry for entry in run_blocks if isinstance(entry, dict) and entry.get("block_id") == block_id]
    if len(matches) != 1:
        raise SystemExit(f"experiment block must resolve exactly once: {block_id}")
    return matches[0]


def _claim_ids(claim_map: Any) -> set[str]:
    if not isinstance(claim_map, list):
        raise SystemExit("claim-map artifact must be a JSON array")
    ids = {
        entry.get("claim_id")
        for entry in claim_map
        if isinstance(entry, dict) and _meaningful(entry.get("claim_id"))
    }
    if not ids:
        raise SystemExit("claim-map artifact has no valid claim IDs")
    return {str(value) for value in ids}


def _normalize_path_entries(entries: Any, field: str) -> list[dict[str, str]]:
    if not isinstance(entries, list):
        raise SystemExit(f"execution.{field} must be a list")
    normalized: list[dict[str, str]] = []
    seen: set[str] = set()
    for index, entry in enumerate(entries, start=1):
        if isinstance(entry, str):
            path = entry
            item = {"path": entry}
        elif isinstance(entry, dict):
            path = entry.get("path")
            item = copy.deepcopy(entry)
        else:
            raise SystemExit(f"execution.{field}[{index}] must be a string or object")
        if not _meaningful(path):
            raise SystemExit(f"execution.{field}[{index}].path must be substantive")
        if path in seen:
            raise SystemExit(f"execution.{field} contains duplicate path: {path}")
        seen.add(path)
        item["path"] = str(path)
        if field in {"declared_inputs", "declared_evaluator_artifacts"}:
            snapshot = item.get("snapshot", "digest-at-start")
            if snapshot != "digest-at-start":
                raise SystemExit(f"execution.{field}[{index}].snapshot must be digest-at-start")
            item["snapshot"] = snapshot
        normalized.append(item)
    return normalized


def _validate_execution_declaration(
    root: Path,
    block: dict[str, Any],
    expected_artifacts: list[str],
    write_scope: list[str],
) -> dict[str, Any]:
    gate_id = block.get("decision_gate_id")
    if not _meaningful(gate_id):
        raise SystemExit("bound experiment block requires decision_gate_id")
    execution = block.get("execution")
    if not isinstance(execution, dict):
        raise SystemExit("bound experiment block requires an execution object")
    mode = execution.get("mode")
    if mode not in EXECUTION_MODES:
        raise SystemExit(f"execution.mode must be one of {sorted(EXECUTION_MODES)}")
    entrypoint = execution.get("entrypoint")
    if mode in {"command", "notebook", "external_job"}:
        if not isinstance(entrypoint, dict):
            raise SystemExit(f"execution.entrypoint is required for mode {mode}")
        argv = entrypoint.get("argv")
        if not isinstance(argv, list) or not argv or not all(_meaningful(value) for value in argv):
            raise SystemExit("execution.entrypoint.argv must be a non-empty list of strings")
        cwd = entrypoint.get("cwd", ".")
        if not _meaningful(cwd):
            raise SystemExit("execution.entrypoint.cwd must be substantive")
        resolve_inside_root(root, cwd, "execution entrypoint cwd")
    elif entrypoint is not None and entrypoint != {}:
        raise SystemExit("manual execution must omit entrypoint or use an empty object")

    declared_inputs = _normalize_path_entries(execution.get("declared_inputs", []), "declared_inputs")
    evaluators = _normalize_path_entries(
        execution.get("declared_evaluator_artifacts", []),
        "declared_evaluator_artifacts",
    )
    outputs = _normalize_path_entries(execution.get("required_outputs", []), "required_outputs")
    if not outputs:
        raise SystemExit("bound experiment block requires at least one execution.required_outputs entry")

    input_paths = {entry["path"] for entry in declared_inputs}
    evaluator_paths = {entry["path"] for entry in evaluators}
    output_paths = {entry["path"] for entry in outputs}
    overlap = (input_paths | evaluator_paths) & output_paths
    if overlap:
        raise SystemExit("declared inputs/evaluators cannot also be required outputs: " + ", ".join(sorted(overlap)))
    for path in sorted(input_paths | evaluator_paths):
        resolve_inside_root(root, path, "declared snapshot path")
        if path_is_in_scope(root, path, write_scope):
            raise SystemExit(f"declared input/evaluator is inside write scope: {path}")
    for path in sorted(output_paths):
        resolve_inside_root(root, path, "required output path")
        if path not in expected_artifacts:
            raise SystemExit(f"required output is not a frozen expected artifact: {path}")
        if not path_is_in_scope(root, path, write_scope):
            raise SystemExit(f"required output is outside declared write scope: {path}")

    expected_output = block.get("expected_output_artifact")
    if _meaningful(expected_output) and expected_output not in output_paths:
        raise SystemExit("block.expected_output_artifact must appear in execution.required_outputs")

    policy = block.get("lineage_policy")
    if not isinstance(policy, dict):
        raise SystemExit("bound experiment block requires lineage_policy")
    allowed = policy.get("allowed_relations")
    if not isinstance(allowed, list) or not allowed:
        raise SystemExit("lineage_policy.allowed_relations must be a non-empty list")
    unknown = sorted({str(value) for value in allowed} - LINEAGE_RELATIONS)
    if unknown:
        raise SystemExit("lineage_policy contains unsupported relations: " + ", ".join(unknown))
    if "baseline" not in allowed:
        raise SystemExit("lineage_policy.allowed_relations must include baseline")

    normalized = copy.deepcopy(execution)
    normalized["declared_inputs"] = declared_inputs
    normalized["declared_evaluator_artifacts"] = evaluators
    normalized["required_outputs"] = outputs
    return normalized


def _parse_activation_condition(raw: str) -> dict[str, Any]:
    try:
        if raw.lstrip().startswith("{"):
            condition = json.loads(raw)
        else:
            predecessor, gate_id, allowed = raw.split(":", 2)
            condition = {
                "predecessor_work_item_id": predecessor,
                "gate_id": gate_id,
                "allowed_results": [value for value in allowed.split(",") if value],
            }
    except (ValueError, json.JSONDecodeError) as exc:
        raise SystemExit(
            "activation condition must be JSON or PREDECESSOR:GATE:pass[,inconclusive]"
        ) from exc
    if not isinstance(condition, dict):
        raise SystemExit("activation condition must be an object")
    predecessor = condition.get("predecessor_work_item_id")
    gate_id = condition.get("gate_id")
    allowed = condition.get("allowed_results")
    if not _meaningful(predecessor) or not _meaningful(gate_id):
        raise SystemExit("activation condition requires predecessor_work_item_id and gate_id")
    if not isinstance(allowed, list) or not allowed:
        raise SystemExit("activation condition allowed_results must be a non-empty list")
    normalized = {str(value) for value in allowed}
    unknown = normalized - GATE_RESULTS
    if unknown:
        raise SystemExit("activation condition has unsupported gate results: " + ", ".join(sorted(unknown)))
    return {
        "predecessor_work_item_id": str(predecessor),
        "gate_id": str(gate_id),
        "allowed_results": sorted(normalized),
    }


def _activation_conditions_satisfied(work_items: dict[str, Any], item: dict[str, Any]) -> bool:
    for condition in item.get("activation_conditions", []):
        predecessor = find_item(work_items, condition.get("predecessor_work_item_id"))
        if predecessor.get("state") != "completed":
            return False
        verifications = predecessor.get("verifications", [])
        if not verifications:
            return False
        gate_results = verifications[-1].get("gate_results", {})
        if gate_results.get(condition.get("gate_id")) not in condition.get("allowed_results", []):
            return False
    return True


def _item_ready(work_items: dict[str, Any], item: dict[str, Any]) -> bool:
    return all(
        find_item(work_items, dependency).get("state") == "completed"
        for dependency in item.get("dependencies", [])
    ) and _activation_conditions_satisfied(work_items, item)


def derive_status(state: dict[str, Any], work_items: dict[str, Any]) -> None:
    items = work_items.get("items", [])
    active = [item for item in items if item.get("state") in {"running", "awaiting_verification"}]
    if len(active) > 1:
        raise SystemExit("more than one work item is active")
    state["active_work_item_id"] = active[0]["work_item_id"] if active else None
    if state.get("paused"):
        state["status"] = "interrupted"
    elif items and all(item.get("state") == "completed" for item in items):
        state["status"] = "completed"
    elif any(item.get("state") == "blocked" for item in items):
        state["status"] = "blocked"
    elif active:
        state["status"] = "running"
    else:
        state["status"] = "initialized"


def refresh_dependencies(work_items: dict[str, Any]) -> None:
    for candidate in work_items.get("items", []):
        if candidate.get("state") != "queued":
            continue
        if _item_ready(work_items, candidate):
            candidate["state"] = "ready"


def apply_event(state: dict[str, Any], work_items: dict[str, Any], event: dict[str, Any]) -> None:
    event_type = event.get("event_type")
    details = event.get("details") or {}
    work_item_id = event.get("work_item_id")
    if state.get("paused") and event_type in STATE_CHANGING_WHILE_PAUSED:
        raise SystemExit("run is paused; resume before changing harness state")

    if event_type == "work_item_added":
        if any(item.get("work_item_id") == work_item_id for item in work_items["items"]):
            raise SystemExit(f"duplicate work item in event log: {work_item_id}")
        item = copy.deepcopy(details.get("work_item"))
        if not isinstance(item, dict):
            raise SystemExit("work_item_added event lacks a work item")
        for dependency in item.get("dependencies", []):
            find_item(work_items, dependency)
        for condition in item.get("activation_conditions", []):
            predecessor = condition.get("predecessor_work_item_id")
            find_item(work_items, predecessor)
            if predecessor not in item.get("dependencies", []):
                raise SystemExit("activation-condition predecessor must also be a dependency")
        item["state"] = "ready" if _item_ready(work_items, item) else "queued"
        item["attempt"] = 0
        item["episodes"] = []
        item["verifications"] = []
        work_items["items"].append(item)

    elif event_type == "work_item_started":
        item = find_item(work_items, work_item_id)
        if item.get("state") != "ready":
            raise SystemExit(f"cannot start {work_item_id} from {item.get('state')}")
        if state.get("active_work_item_id") not in {None, work_item_id}:
            raise SystemExit("another work item is already active")
        if event.get("actor") != item.get("owner_skill"):
            raise SystemExit("only the declared owner skill may start the work item")
        key = details.get("idempotency_key")
        if not isinstance(key, str) or not key:
            raise SystemExit("start event requires an idempotency key")
        item["state"] = "running"
        item["attempt"] += 1
        item["idempotency_key"] = key
        if "execution_snapshot" in details:
            item["execution_snapshot"] = copy.deepcopy(details["execution_snapshot"])

    elif event_type == "episode_submitted":
        item = find_item(work_items, work_item_id)
        if item.get("state") != "running":
            raise SystemExit(f"cannot submit {work_item_id} from {item.get('state')}")
        if event.get("actor") != item.get("owner_skill"):
            raise SystemExit("only the declared owner skill may submit the episode")
        record = {
            "episode_path": details.get("episode_path"),
            "episode_id": details.get("episode_id"),
            "episode_digest": details.get("episode_digest"),
            "artifact_digests": copy.deepcopy(details.get("artifact_digests", {})),
            "outcome": details.get("outcome"),
            "transition_request": details.get("transition_request"),
            "idempotency_key": details.get("idempotency_key"),
        }
        if details.get("experiment_run") is not None:
            record["experiment_run"] = copy.deepcopy(details["experiment_run"])
        if details.get("verified_execution_snapshot") is not None:
            record["verified_execution_snapshot"] = copy.deepcopy(details["verified_execution_snapshot"])
        if details.get("verified_binding_digests") is not None:
            record["verified_binding_digests"] = copy.deepcopy(details["verified_binding_digests"])
        if not all(isinstance(record.get(field), str) and record[field] for field in (
            "episode_path", "episode_id", "episode_digest", "outcome",
            "transition_request", "idempotency_key"
        )):
            raise SystemExit("episode submission event is incomplete")
        item["episodes"].append(record)
        item["state"] = "awaiting_verification"

    elif event_type == "verification_approved":
        item = find_item(work_items, work_item_id)
        if item.get("state") != "awaiting_verification":
            raise SystemExit(f"cannot approve {work_item_id} from {item.get('state')}")
        latest = item.get("episodes", [])[-1]
        if latest.get("outcome") != "completed" or latest.get("transition_request") != "approve":
            raise SystemExit("only a completed episode requesting approval may be approved")
        item["state"] = "completed"
        item["verifications"].append(copy.deepcopy(details))
        refresh_dependencies(work_items)

    elif event_type == "verification_revise":
        item = find_item(work_items, work_item_id)
        if item.get("state") != "awaiting_verification":
            raise SystemExit(f"cannot revise {work_item_id} from {item.get('state')}")
        item["verifications"].append(copy.deepcopy(details))
        item["state"] = "blocked" if item["attempt"] >= item["attempt_budget"] else "ready"

    elif event_type == "work_item_failed_retryable":
        item = find_item(work_items, work_item_id)
        if item.get("state") != "running":
            raise SystemExit(f"cannot fail {work_item_id} from {item.get('state')}")
        item["state"] = "blocked" if item["attempt"] >= item["attempt_budget"] else "ready"

    elif event_type == "work_item_blocked":
        item = find_item(work_items, work_item_id)
        if item.get("state") not in {"ready", "running", "awaiting_verification", "queued"}:
            raise SystemExit(f"cannot block {work_item_id} from {item.get('state')}")
        item["state"] = "blocked"

    elif event_type == "checkpoint_saved":
        checkpoint_id = details.get("checkpoint_id")
        if not isinstance(checkpoint_id, str) or not checkpoint_id:
            raise SystemExit("checkpoint_saved event lacks checkpoint_id")
        state["last_checkpoint_id"] = checkpoint_id

    elif event_type == "run_paused":
        if state.get("paused"):
            raise SystemExit("run is already paused")
        state["paused"] = True

    elif event_type == "run_resumed":
        if not state.get("paused"):
            raise SystemExit("run is not paused")
        state["paused"] = False

    elif event_type == "observation_recorded":
        pass
    else:
        raise SystemExit(f"unsupported event type: {event_type}")

    derive_status(state, work_items)
    state["last_event_id"] = event["event_id"]
    state["last_event_hash"] = event["event_hash"]
    state["updated_at"] = event["timestamp"]


def reconstruct(root: Path) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    events = read_events(root / "harness-events.jsonl")
    verify_chain(events)
    state = initial_state()
    work_items = initial_work_items()
    for event in events:
        apply_event(state, work_items, event)
    return events, state, work_items


def replay(root: Path, write: bool = True) -> tuple[dict[str, Any], dict[str, Any]]:
    _, state, work_items = reconstruct(root)
    if write:
        atomic_write_json(root / "HARNESS_STATE.json", state)
        atomic_write_json(root / "work-items.json", work_items)
    return state, work_items


def build_event(
    events: list[dict[str, Any]], event_type: str, actor: str,
    work_item_id: str | None, details: dict[str, Any]
) -> dict[str, Any]:
    event = {
        "schema_version": SCHEMA_VERSION,
        "event_id": f"EV-{len(events) + 1:06d}",
        "timestamp": utc_now(),
        "event_type": event_type,
        "actor": actor,
        "work_item_id": work_item_id,
        "previous_event_hash": events[-1]["event_hash"] if events else None,
        "details": details,
    }
    event["event_hash"] = event_hash(event)
    return event


def commit_event(
    root: Path, event_type: str, actor: str,
    work_item_id: str | None, details: dict[str, Any]
) -> dict[str, Any]:
    root.mkdir(parents=True, exist_ok=True)
    events, state, work_items = reconstruct(root)
    event = build_event(events, event_type, actor, work_item_id, details)
    next_state = copy.deepcopy(state)
    next_items = copy.deepcopy(work_items)
    apply_event(next_state, next_items, event)
    with (root / "harness-events.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=True) + "\n")
        handle.flush()
        if os.environ.get("HARNESS_DISABLE_FSYNC") != "1":
            os.fsync(handle.fileno())
    atomic_write_json(root / "HARNESS_STATE.json", next_state)
    atomic_write_json(root / "work-items.json", next_items)
    return event


def _build_experiment_binding(
    root: Path,
    args: argparse.Namespace,
    expected_artifacts: list[str],
    write_scope: list[str],
) -> dict[str, Any] | None:
    supplied = (
        args.experiment_run_blocks,
        args.experiment_claim_map,
        args.experiment_block_id,
        args.commitment,
    )
    if not any(value is not None for value in supplied):
        return None
    if not all(value is not None for value in supplied):
        raise SystemExit(
            "experiment binding requires --experiment-run-blocks, --experiment-claim-map, "
            "--experiment-block-id, and --commitment"
        )
    run_blocks_path = _relative_arg_path(root, args.experiment_run_blocks, "run-blocks")
    claim_map_path = _relative_arg_path(root, args.experiment_claim_map, "claim-map")
    commitment_path = _relative_arg_path(root, args.commitment, "commitment")
    run_blocks = _load_required_json(root, run_blocks_path, "run-blocks")
    claim_map = _load_required_json(root, claim_map_path, "claim-map")
    commitment = _load_required_json(root, commitment_path, "commitment")
    if not isinstance(commitment, dict):
        raise SystemExit("commitment must be a JSON object")
    paper_id = commitment.get("paper_id")
    identity_version = commitment.get("identity_version")
    if not _meaningful(paper_id) or not isinstance(identity_version, int) or identity_version < 1:
        raise SystemExit("commitment lacks a valid paper_id or identity_version")
    block = _find_block(run_blocks, args.experiment_block_id)
    known_claims = _claim_ids(claim_map)
    block_claims = block.get("claim_ids")
    if not isinstance(block_claims, list) or not block_claims:
        raise SystemExit("bound experiment block requires claim_ids")
    unknown_claims = sorted({str(value) for value in block_claims} - known_claims)
    if unknown_claims:
        raise SystemExit("bound block references unknown claims: " + ", ".join(unknown_claims))
    execution = _validate_execution_declaration(root, block, expected_artifacts, write_scope)
    return {
        "claim_map_path": claim_map_path,
        "claim_map_digest": path_digest(resolve_inside_root(root, claim_map_path, "claim-map")),
        "run_blocks_path": run_blocks_path,
        "run_blocks_digest": path_digest(resolve_inside_root(root, run_blocks_path, "run-blocks")),
        "block_id": args.experiment_block_id,
        "decision_gate_id": block["decision_gate_id"],
        "commitment_path": commitment_path,
        "commitment_digest": path_digest(resolve_inside_root(root, commitment_path, "commitment")),
        "paper_id": paper_id,
        "identity_version": identity_version,
        "execution": execution,
        "claim_ids": [str(value) for value in block_claims],
        "allowed_lineage_relations": sorted(set(block["lineage_policy"]["allowed_relations"])),
    }


def validate_work_item(
    root: Path,
    work_items: dict[str, Any],
    args: argparse.Namespace,
) -> dict[str, Any]:
    validate_identifier(args.work_item_id, "work item id")
    if not args.acceptance_check:
        raise SystemExit("at least one --acceptance-check is required")
    if not args.expected_artifact:
        raise SystemExit("at least one --expected-artifact is required")
    if not args.write_scope:
        raise SystemExit("at least one --write-scope is required")
    if args.attempt_budget < 1:
        raise SystemExit("--attempt-budget must be positive")
    if args.tool_call_budget < 0:
        raise SystemExit("--tool-call-budget must be non-negative")
    dependencies = args.depends_on or []
    for dependency in dependencies:
        find_item(work_items, dependency)
    activation_conditions = [_parse_activation_condition(raw) for raw in (args.activation_condition or [])]
    for condition in activation_conditions:
        predecessor = condition["predecessor_work_item_id"]
        find_item(work_items, predecessor)
        if predecessor not in dependencies:
            raise SystemExit("activation-condition predecessor must also be supplied with --depends-on")
    binding = _build_experiment_binding(root, args, args.expected_artifact, args.write_scope)
    if activation_conditions and binding is None:
        raise SystemExit("activation conditions are supported only for experiment-bound work items")
    item = {
        "work_item_id": args.work_item_id,
        "stage": args.stage,
        "owner_skill": args.owner_skill,
        "objective": args.objective,
        "context_manifest": args.context or [],
        "expected_artifacts": args.expected_artifact,
        "acceptance_checks": [
            {"check_id": f"AC{index}", "criterion": value}
            for index, value in enumerate(args.acceptance_check, start=1)
        ],
        "dependencies": dependencies,
        "activation_conditions": activation_conditions,
        "attempt_budget": args.attempt_budget,
        "tool_call_budget": args.tool_call_budget,
        "write_scope": args.write_scope,
        "permission_policy": args.permission_policy,
        "predecessor_failures": args.predecessor_failure or [],
        "evidence_class": args.evidence_class,
        "enforcement_scope": "repository_validation_only",
    }
    if binding is not None:
        item["experiment_binding"] = binding
    return item


def _verify_binding_digests(root: Path, item: dict[str, Any]) -> dict[str, Any] | None:
    binding = item.get("experiment_binding")
    if binding is None:
        return None
    if not isinstance(binding, dict):
        raise SystemExit("experiment_binding must be an object")
    for path_field, digest_field, label in (
        ("claim_map_path", "claim_map_digest", "claim-map"),
        ("run_blocks_path", "run_blocks_digest", "run-blocks"),
        ("commitment_path", "commitment_digest", "commitment"),
    ):
        path = resolve_inside_root(root, binding.get(path_field), label)
        if not path.is_file():
            raise SystemExit(f"bound {label} artifact no longer exists")
        if path_digest(path) != binding.get(digest_field):
            raise SystemExit(f"bound {label} digest changed after work-item creation")
    commitment = _load_required_json(root, binding["commitment_path"], "commitment")
    if (
        not isinstance(commitment, dict)
        or commitment.get("paper_id") != binding.get("paper_id")
        or commitment.get("identity_version") != binding.get("identity_version")
    ):
        raise SystemExit("bound commitment identity no longer matches the work item")
    run_blocks = _load_required_json(root, binding["run_blocks_path"], "run-blocks")
    block = _find_block(run_blocks, binding.get("block_id"))
    if block.get("decision_gate_id") != binding.get("decision_gate_id"):
        raise SystemExit("bound experiment gate changed after work-item creation")
    return block


def _binding_digest_record(item: dict[str, Any]) -> dict[str, str]:
    binding = item.get("experiment_binding")
    if not isinstance(binding, dict):
        return {}
    return {
        "claim_map_digest": binding["claim_map_digest"],
        "run_blocks_digest": binding["run_blocks_digest"],
        "commitment_digest": binding["commitment_digest"],
    }


def _execution_snapshot(root: Path, item: dict[str, Any]) -> dict[str, dict[str, str]] | None:
    block = _verify_binding_digests(root, item)
    if block is None:
        return None
    execution = item["experiment_binding"].get("execution", {})
    snapshot: dict[str, dict[str, str]] = {
        "declared_inputs": {},
        "declared_evaluator_artifacts": {},
    }
    for field in snapshot:
        for entry in execution.get(field, []):
            path = resolve_inside_root(root, entry.get("path"), field)
            if not path.exists():
                raise SystemExit(f"declared snapshot artifact does not exist: {entry.get('path')}")
            snapshot[field][entry["path"]] = path_digest(path)
    return snapshot


def _verify_execution_snapshot(root: Path, item: dict[str, Any]) -> None:
    if item.get("experiment_binding") is None:
        return
    _verify_binding_digests(root, item)
    snapshot = item.get("execution_snapshot")
    if not isinstance(snapshot, dict):
        raise SystemExit("experiment work item lacks a start-time execution snapshot")
    for field in ("declared_inputs", "declared_evaluator_artifacts"):
        values = snapshot.get(field)
        if not isinstance(values, dict):
            raise SystemExit(f"execution snapshot lacks {field}")
        for relative, expected in values.items():
            path = resolve_inside_root(root, relative, field)
            if not path.exists() or path_digest(path) != expected:
                raise SystemExit(f"declared snapshot changed after start: {relative}")


def _existing_runs(work_items: dict[str, Any]) -> dict[str, tuple[dict[str, Any], dict[str, Any]]]:
    runs: dict[str, tuple[dict[str, Any], dict[str, Any]]] = {}
    for item in work_items.get("items", []):
        for record in item.get("episodes", []):
            if not isinstance(record, dict) or not isinstance(record.get("experiment_run"), dict):
                continue
            run_id = record["experiment_run"].get("run_id")
            if _meaningful(run_id):
                if run_id in runs:
                    raise SystemExit(f"duplicate experiment run ID in event history: {run_id}")
                runs[str(run_id)] = (item, record)
    return runs


def _validate_experiment_run(
    item: dict[str, Any],
    episode: dict[str, Any],
    work_items: dict[str, Any],
) -> dict[str, Any] | None:
    binding = item.get("experiment_binding")
    run = episode.get("experiment_run")
    if binding is None:
        if run is not None:
            raise SystemExit("experiment_run is allowed only for experiment-bound work items")
        return None
    if not isinstance(run, dict):
        raise SystemExit("experiment-bound episode requires experiment_run")
    required = {
        "run_id", "block_id", "relation", "parent_run_id", "gate_id", "gate_result",
        "scientific_disposition", "claim_effects", "interpretation",
    }
    missing = sorted(required - set(run))
    if missing:
        raise SystemExit("experiment_run missing fields: " + ", ".join(missing))
    run_id = run.get("run_id")
    if not _meaningful(run_id):
        raise SystemExit("experiment_run.run_id must be substantive")
    validate_identifier(str(run_id), "experiment run id")
    if str(run_id) in _existing_runs(work_items):
        raise SystemExit(f"duplicate experiment run ID: {run_id}")
    if run.get("block_id") != binding.get("block_id"):
        raise SystemExit("experiment_run.block_id does not match the frozen binding")
    relation = run.get("relation")
    if relation not in LINEAGE_RELATIONS:
        raise SystemExit(f"experiment_run.relation must be one of {sorted(LINEAGE_RELATIONS)}")
    if relation not in binding.get("allowed_lineage_relations", []):
        raise SystemExit(f"experiment lineage relation is not allowed by the block: {relation}")
    if relation == "pivot":  # defensive; pivot is intentionally absent from LINEAGE_RELATIONS
        raise SystemExit("D3/D4 pivots cannot be encoded as experiment lineage")
    if run.get("gate_id") != binding.get("decision_gate_id"):
        raise SystemExit("experiment_run.gate_id does not match the frozen block gate")
    if run.get("gate_result") not in GATE_RESULTS:
        raise SystemExit(f"experiment_run.gate_result must be one of {sorted(GATE_RESULTS)}")
    if run.get("scientific_disposition") not in SCIENTIFIC_DISPOSITIONS:
        raise SystemExit(
            "experiment_run.scientific_disposition must be one of "
            + str(sorted(SCIENTIFIC_DISPOSITIONS))
        )
    if not _meaningful(run.get("interpretation")):
        raise SystemExit("experiment_run.interpretation must be substantive")

    parent_run_id = run.get("parent_run_id")
    existing = _existing_runs(work_items)
    if relation == "baseline" and parent_run_id is not None:
        raise SystemExit("baseline experiment run cannot have a parent_run_id")
    if relation in PARENT_REQUIRED_RELATIONS and not _meaningful(parent_run_id):
        raise SystemExit(f"{relation} experiment run requires parent_run_id")
    if relation != "baseline" and not _meaningful(parent_run_id):
        if not _meaningful(run.get("parent_rationale")):
            raise SystemExit(
                "non-baseline experiment run without a parent requires parent_rationale"
            )
    if _meaningful(parent_run_id):
        if parent_run_id == run_id:
            raise SystemExit("experiment run cannot be its own parent")
        if parent_run_id not in existing:
            raise SystemExit(f"unknown parent experiment run: {parent_run_id}")
        parent_item, parent_record = existing[str(parent_run_id)]
        parent_binding = parent_item.get("experiment_binding", {})
        if (
            parent_binding.get("paper_id") != binding.get("paper_id")
            or parent_binding.get("identity_version") != binding.get("identity_version")
        ):
            raise SystemExit("parent experiment run belongs to a different paper identity")
        if relation == "technical_retry" and parent_record["experiment_run"].get("block_id") != run.get("block_id"):
            raise SystemExit("technical_retry parent must use the same block_id")

    effects = run.get("claim_effects")
    if not isinstance(effects, list):
        raise SystemExit("experiment_run.claim_effects must be a list")
    seen_claims: set[str] = set()
    normalized_effects: list[dict[str, str]] = []
    for index, effect in enumerate(effects, start=1):
        if not isinstance(effect, dict):
            raise SystemExit(f"experiment_run.claim_effects[{index}] must be an object")
        claim_id = effect.get("claim_id")
        value = effect.get("effect")
        scope = effect.get("scope")
        if claim_id not in binding.get("claim_ids", []):
            raise SystemExit(f"experiment run references claim outside the block: {claim_id}")
        if claim_id in seen_claims:
            raise SystemExit(f"duplicate experiment claim effect: {claim_id}")
        seen_claims.add(str(claim_id))
        if value not in CLAIM_EFFECTS:
            raise SystemExit(f"experiment claim effect must be one of {sorted(CLAIM_EFFECTS)}")
        if not _meaningful(scope):
            raise SystemExit("experiment claim effect requires a substantive scope")
        normalized_effects.append({"claim_id": str(claim_id), "effect": str(value), "scope": str(scope)})
    disposition = run["scientific_disposition"]
    if disposition == "supports_claim" and not any(effect["effect"] == "strengthen" for effect in normalized_effects):
        raise SystemExit("supports_claim requires at least one strengthen claim effect")
    if disposition == "weakens_claim" and not any(effect["effect"] == "weaken" for effect in normalized_effects):
        raise SystemExit("weakens_claim requires at least one weaken claim effect")
    if disposition == "falsifies_claim" and not any(effect["effect"] == "kill" for effect in normalized_effects):
        raise SystemExit("falsifies_claim requires at least one kill claim effect")

    required_outputs = {
        entry["path"]
        for entry in binding.get("execution", {}).get("required_outputs", [])
        if isinstance(entry, dict) and _meaningful(entry.get("path"))
    }
    missing_outputs = sorted(required_outputs - set(episode.get("artifacts", [])))
    if missing_outputs:
        raise SystemExit("experiment episode missing required outputs: " + ", ".join(missing_outputs))
    normalized = copy.deepcopy(run)
    normalized["run_id"] = str(run_id)
    normalized["claim_effects"] = normalized_effects
    return normalized


def validate_episode(
    root: Path,
    work_items: dict[str, Any],
    item: dict[str, Any],
    episode_path: Path,
) -> dict[str, Any]:
    episode_path = episode_path.resolve()
    try:
        relative = episode_path.relative_to(root.resolve()).as_posix()
    except ValueError as exc:
        raise SystemExit("episode must be stored inside the suite root") from exc
    relative_path = Path(relative)
    if relative_path.parent != Path("episodes"):
        raise SystemExit("episode must be a direct child of episodes/")
    episode = load_json(episode_path, None)
    if not isinstance(episode, dict):
        raise SystemExit("episode must be a JSON object")
    required = {
        "schema_version", "episode_id", "work_item_id", "attempt", "owner_skill",
        "objective", "artifacts", "verification", "failures", "outcome",
        "transition_request", "summary",
    }
    missing = sorted(required - set(episode))
    if missing:
        raise SystemExit("episode missing fields: " + ", ".join(missing))
    validate_identifier(str(episode["episode_id"]), "episode id")
    if episode_path.stem != episode["episode_id"]:
        raise SystemExit("episode filename must match episode_id")
    if episode["schema_version"] != SCHEMA_VERSION:
        raise SystemExit("episode schema_version mismatch")
    if episode["work_item_id"] != item["work_item_id"]:
        raise SystemExit("episode work_item_id mismatch")
    if episode["attempt"] != item["attempt"]:
        raise SystemExit("episode attempt mismatch")
    if episode["owner_skill"] != item["owner_skill"]:
        raise SystemExit("episode owner_skill mismatch")
    if episode["objective"] != item["objective"]:
        raise SystemExit("episode objective differs from frozen work item")
    if episode["outcome"] not in {"completed", "partial", "failed"}:
        raise SystemExit("invalid episode outcome")
    if episode["transition_request"] not in {"approve", "revise", "block"}:
        raise SystemExit("invalid transition_request")
    if (episode["outcome"] == "completed") != (episode["transition_request"] == "approve"):
        raise SystemExit("completed outcome and approve transition_request must occur together")
    failures = episode.get("failures")
    if not isinstance(failures, list):
        raise SystemExit("episode.failures must be a list")
    if episode["outcome"] == "failed" and not failures:
        raise SystemExit("failed episode must record at least one failure")
    for index, failure in enumerate(failures, start=1):
        if not isinstance(failure, dict):
            raise SystemExit(f"episode.failures[{index}] must be an object")
        for field in ("category", "reason"):
            value = failure.get(field)
            if not isinstance(value, str) or not value.strip():
                raise SystemExit(f"episode.failures[{index}].{field} must be a substantive string")
    tool_calls = episode.get("tool_calls", [])
    if not isinstance(tool_calls, list):
        raise SystemExit("episode.tool_calls must be a list when present")
    observed = episode.get("observed_usage", {})
    if not isinstance(observed, dict):
        raise SystemExit("episode.observed_usage must be an object when present")
    observed_calls = observed.get("max_tool_calls", len(tool_calls))
    if not isinstance(observed_calls, int) or observed_calls < len(tool_calls):
        raise SystemExit("episode observed tool-call usage is invalid")
    if observed_calls > item["tool_call_budget"]:
        raise SystemExit("episode exceeds the work item tool-call budget")

    artifacts = episode.get("artifacts")
    if not isinstance(artifacts, list):
        raise SystemExit("episode.artifacts must be a list")
    if episode["outcome"] == "completed" and not artifacts:
        raise SystemExit("completed episode must list artifacts")
    if episode["outcome"] == "completed":
        missing_expected = [artifact for artifact in item["expected_artifacts"] if artifact not in artifacts]
        if missing_expected:
            raise SystemExit("completed episode missing expected artifacts: " + ", ".join(missing_expected))
    artifact_digests: dict[str, str] = {}
    for artifact in artifacts:
        if not isinstance(artifact, str):
            raise SystemExit("episode artifact paths must be strings")
        candidate = resolve_inside_root(root, artifact, "artifact")
        if not candidate.exists():
            raise SystemExit(f"episode artifact does not exist: {artifact}")
        if not path_is_in_scope(root, artifact, item["write_scope"]):
            raise SystemExit(f"episode artifact is outside declared write scope: {artifact}")
        artifact_digests[artifact] = path_digest(candidate)

    results = {
        entry.get("check_id"): entry
        for entry in episode.get("verification", [])
        if isinstance(entry, dict)
    }
    if episode["outcome"] == "completed":
        for check in item["acceptance_checks"]:
            result = results.get(check["check_id"])
            if not result or result.get("result") != "pass" or not str(result.get("evidence", "")).strip():
                raise SystemExit(f"acceptance check not passed with evidence: {check['check_id']}")
    experiment_run = _validate_experiment_run(item, episode, work_items)
    episode["_relative_path"] = relative
    episode["_digest"] = path_digest(episode_path)
    episode["_artifact_digests"] = artifact_digests
    episode["_experiment_run"] = experiment_run
    return episode


def latest_episode(item: dict[str, Any]) -> dict[str, Any]:
    episodes = item.get("episodes", [])
    if not episodes:
        raise SystemExit("work item has no submitted episode")
    latest = episodes[-1]
    if not isinstance(latest, dict):
        raise SystemExit("legacy episode record lacks integrity metadata")
    return latest


def verify_submitted_integrity(root: Path, item: dict[str, Any]) -> dict[str, Any]:
    submitted = latest_episode(item)
    episode_path = resolve_inside_root(root, submitted["episode_path"], "episode path")
    if not episode_path.exists():
        raise SystemExit("submitted episode no longer exists")
    if path_digest(episode_path) != submitted["episode_digest"]:
        raise SystemExit("submitted episode digest changed after submission")
    for artifact, digest in submitted.get("artifact_digests", {}).items():
        path = resolve_inside_root(root, artifact, "artifact")
        if not path.exists() or path_digest(path) != digest:
            raise SystemExit(f"submitted artifact digest changed after submission: {artifact}")
    return submitted


def _parse_gate_results(values: list[str] | None) -> dict[str, str]:
    results: dict[str, str] = {}
    for raw in values or []:
        if "=" not in raw:
            raise SystemExit("--gate-result must use GATE=pass|fail|inconclusive|not_applicable")
        gate_id, result = raw.split("=", 1)
        if not _meaningful(gate_id) or result not in GATE_RESULTS:
            raise SystemExit("invalid --gate-result value")
        if gate_id in results:
            raise SystemExit(f"duplicate --gate-result for {gate_id}")
        results[gate_id] = result
    return results


def command_add(args: argparse.Namespace) -> None:
    root = args.root.resolve()
    _, _, items = reconstruct(root)
    if any(item["work_item_id"] == args.work_item_id for item in items["items"]):
        raise SystemExit(f"work item already exists: {args.work_item_id}")
    item = validate_work_item(root, items, args)
    commit_event(root, "work_item_added", args.actor, args.work_item_id, {"work_item": item})
    print(f"added {args.work_item_id}")


def command_start(args: argparse.Namespace) -> None:
    root = args.root.resolve()
    events, _, items = reconstruct(root)
    item = find_item(items, args.work_item_id)
    key = args.idempotency_key or f"{args.work_item_id}:attempt:{item['attempt'] + 1}"
    matches = [
        event for event in events
        if event.get("event_type") == "work_item_started"
        and event.get("details", {}).get("idempotency_key") == key
    ]
    if matches:
        match = matches[0]
        if match.get("work_item_id") != args.work_item_id or match.get("actor") != args.actor:
            raise SystemExit("idempotency key was previously used for a different start request")
        print(f"already started {args.work_item_id} with {key}")
        return
    details: dict[str, Any] = {"idempotency_key": key}
    snapshot = _execution_snapshot(root, item)
    if snapshot is not None:
        details["execution_snapshot"] = snapshot
    commit_event(root, "work_item_started", args.actor, args.work_item_id, details)
    print(f"started {args.work_item_id} with {key}")


def command_submit(args: argparse.Namespace) -> None:
    root = args.root.resolve()
    events, _, items = reconstruct(root)
    item = find_item(items, args.work_item_id)
    if args.actor != item["owner_skill"]:
        raise SystemExit("only the declared owner skill may submit the episode")
    episode_path = args.episode.resolve()
    if not episode_path.is_file():
        raise SystemExit(f"episode file not found: {episode_path}")
    requested_digest = path_digest(episode_path)
    key = args.idempotency_key or f"{args.work_item_id}:submit:{requested_digest}"
    matches = [
        event for event in events
        if event.get("event_type") == "episode_submitted"
        and event.get("details", {}).get("idempotency_key") == key
    ]
    if matches:
        match = matches[0]
        details = match.get("details", {})
        if (
            details.get("episode_digest") != requested_digest
            or match.get("work_item_id") != args.work_item_id
            or match.get("actor") != args.actor
        ):
            raise SystemExit("idempotency key was previously used for a different episode submission")
        print(f"already submitted {args.work_item_id}")
        return
    _verify_execution_snapshot(root, item)
    episode = validate_episode(root, items, item, episode_path)
    details = {
        "episode_path": episode["_relative_path"],
        "episode_id": episode["episode_id"],
        "episode_digest": episode["_digest"],
        "artifact_digests": episode["_artifact_digests"],
        "outcome": episode["outcome"],
        "transition_request": episode["transition_request"],
        "idempotency_key": key,
    }
    if episode["_experiment_run"] is not None:
        details["experiment_run"] = episode["_experiment_run"]
        details["verified_execution_snapshot"] = copy.deepcopy(item["execution_snapshot"])
        details["verified_binding_digests"] = _binding_digest_record(item)
    commit_event(root, "episode_submitted", args.actor, args.work_item_id, details)
    print(f"submitted {args.work_item_id}")


def command_verify(args: argparse.Namespace) -> None:
    root = args.root.resolve()
    _, _, items = reconstruct(root)
    item = find_item(items, args.work_item_id)
    if args.actor == item["owner_skill"] and not args.self_review:
        raise SystemExit("worker-role verification must be explicitly marked --self-review")
    if item["state"] != "awaiting_verification":
        raise SystemExit("work item is not awaiting verification")
    submitted = verify_submitted_integrity(root, item)
    gate_results = _parse_gate_results(args.gate_result)
    disposition = args.scientific_disposition
    experiment_run = submitted.get("experiment_run")
    if item.get("experiment_binding") is not None:
        if not isinstance(experiment_run, dict):
            raise SystemExit("submitted experiment episode lacks experiment_run")
        if args.decision == "approve":
            expected_gate = experiment_run["gate_id"]
            expected_results = {expected_gate: experiment_run["gate_result"]}
            if gate_results != expected_results:
                raise SystemExit(
                    "experiment approval requires a matching --gate-result for the submitted run"
                )
            if disposition != experiment_run["scientific_disposition"]:
                raise SystemExit(
                    "experiment approval requires --scientific-disposition to match the submitted run"
                )
    elif gate_results or disposition is not None:
        raise SystemExit("gate results and scientific disposition require an experiment-bound work item")
    if args.decision == "approve":
        if submitted["outcome"] != "completed" or submitted["transition_request"] != "approve":
            raise SystemExit("only a completed episode requesting approval may be approved")
    event_type = {
        "approve": "verification_approved",
        "revise": "verification_revise",
        "block": "work_item_blocked",
    }[args.decision]
    details: dict[str, Any] = {
        "decision": args.decision,
        "evidence": args.evidence,
        "self_review": args.self_review,
        "episode_id": submitted["episode_id"],
    }
    if gate_results:
        details["gate_results"] = gate_results
    if disposition is not None:
        details["scientific_disposition"] = disposition
    commit_event(root, event_type, args.actor, args.work_item_id, details)
    print(f"verification {args.decision}: {args.work_item_id}")


def command_fail(args: argparse.Namespace) -> None:
    root = args.root.resolve()
    event_type = "work_item_failed_retryable" if args.retryable else "work_item_blocked"
    commit_event(root, event_type, args.actor, args.work_item_id, {"reason": args.reason})
    print(f"recorded failure for {args.work_item_id}")


def command_record(args: argparse.Namespace) -> None:
    root = args.root.resolve()
    event = commit_event(
        root, "observation_recorded", args.actor, args.work_item_id,
        {"category": args.category, "note": args.note},
    )
    print(event["event_id"])


def command_checkpoint(args: argparse.Namespace) -> None:
    root = args.root.resolve()
    _, state, items = reconstruct(root)
    checkpoints = root / "checkpoints"
    checkpoints.mkdir(parents=True, exist_ok=True)
    checkpoint_id = args.checkpoint_id or f"CP-{len(list(checkpoints.glob('*.json'))) + 1:06d}"
    validate_checkpoint_id(checkpoint_id)
    checkpoint_path = checkpoints / f"{checkpoint_id}.json"
    if checkpoint_path.exists():
        raise SystemExit(f"checkpoint already exists: {checkpoint_id}")
    payload = {
        "schema_version": SCHEMA_VERSION,
        "checkpoint_id": checkpoint_id,
        "created_at": utc_now(),
        "reason": args.reason,
        "state": state,
        "work_items": items,
    }
    payload["snapshot_digest"] = sha256_bytes(canonical_json(payload).encode("utf-8"))
    atomic_write_json(checkpoint_path, payload)
    try:
        commit_event(
            root, "checkpoint_saved", args.actor, state.get("active_work_item_id"),
            {
                "checkpoint_id": checkpoint_id,
                "checkpoint_path": checkpoint_path.relative_to(root).as_posix(),
                "checkpoint_digest": path_digest(checkpoint_path),
                "reason": args.reason,
            },
        )
    except BaseException:
        checkpoint_path.unlink(missing_ok=True)
        raise
    print(checkpoint_id)


def command_pause_resume(args: argparse.Namespace, event_type: str) -> None:
    event = commit_event(args.root.resolve(), event_type, args.actor, None, {"reason": args.reason})
    print(event["event_type"])


def command_status(args: argparse.Namespace) -> None:
    state, items = replay(args.root.resolve(), write=True)
    print(json.dumps({"state": state, "work_items": items}, indent=2, sort_keys=True))


def command_replay(args: argparse.Namespace) -> None:
    replay(args.root.resolve(), write=True)
    print("replayed")


def command_experiment_lineage(args: argparse.Namespace) -> None:
    _, _, items = reconstruct(args.root.resolve())
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, str]] = []
    verification_by_episode: dict[str, dict[str, Any]] = {}
    for item in items.get("items", []):
        for verification in item.get("verifications", []):
            if isinstance(verification, dict) and _meaningful(verification.get("episode_id")):
                verification_by_episode[verification["episode_id"]] = verification
    for item in items.get("items", []):
        for record in item.get("episodes", []):
            run = record.get("experiment_run") if isinstance(record, dict) else None
            if not isinstance(run, dict):
                continue
            if args.block_id and run.get("block_id") != args.block_id:
                continue
            verification = verification_by_episode.get(record.get("episode_id"), {})
            node = {
                "run_id": run.get("run_id"),
                "work_item_id": item.get("work_item_id"),
                "episode_id": record.get("episode_id"),
                "block_id": run.get("block_id"),
                "relation": run.get("relation"),
                "parent_run_id": run.get("parent_run_id"),
                "submitted_gate_result": run.get("gate_result"),
                "verified_gate_results": verification.get("gate_results", {}),
                "scientific_disposition": run.get("scientific_disposition"),
                "verification_decision": verification.get("decision"),
            }
            nodes.append(node)
            if _meaningful(run.get("parent_run_id")):
                edges.append({"parent_run_id": run["parent_run_id"], "child_run_id": run["run_id"]})
    nodes.sort(key=lambda node: str(node.get("run_id")))
    edges.sort(key=lambda edge: (edge["parent_run_id"], edge["child_run_id"]))
    print(json.dumps({"nodes": nodes, "edges": edges}, indent=2, sort_keys=True))


@contextmanager
def runtime_lock(root: Path):
    root.mkdir(parents=True, exist_ok=True)
    with (root / ".harness.lock").open("a+", encoding="utf-8") as handle:
        if fcntl is not None:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            if fcntl is not None:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True, help="Research-suite root")
    sub = parser.add_subparsers(dest="command", required=True)
    add = sub.add_parser("add")
    add.add_argument("--work-item-id", required=True)
    add.add_argument("--stage", required=True)
    add.add_argument("--owner-skill", required=True)
    add.add_argument("--objective", required=True)
    add.add_argument("--acceptance-check", action="append", default=[])
    add.add_argument("--context", action="append", default=[])
    add.add_argument("--expected-artifact", action="append", default=[])
    add.add_argument("--depends-on", action="append", default=[])
    add.add_argument("--activation-condition", action="append", default=[])
    add.add_argument("--attempt-budget", type=int, default=2)
    add.add_argument("--tool-call-budget", type=int, default=20)
    add.add_argument("--write-scope", action="append", default=[])
    add.add_argument("--permission-policy", default="least_privilege")
    add.add_argument("--predecessor-failure", action="append", default=[])
    add.add_argument("--evidence-class", choices=sorted(EVIDENCE_CLASSES), default="exploratory")
    add.add_argument("--experiment-run-blocks", type=Path)
    add.add_argument("--experiment-claim-map", type=Path)
    add.add_argument("--experiment-block-id")
    add.add_argument("--commitment", type=Path)
    add.add_argument("--actor", default="research-pipeline-planner")
    add.set_defaults(func=command_add)
    start = sub.add_parser("start")
    start.add_argument("work_item_id")
    start.add_argument("--actor", required=True)
    start.add_argument("--idempotency-key")
    start.set_defaults(func=command_start)
    submit = sub.add_parser("submit")
    submit.add_argument("work_item_id")
    submit.add_argument("--episode", type=Path, required=True)
    submit.add_argument("--actor", required=True)
    submit.add_argument("--idempotency-key")
    submit.set_defaults(func=command_submit)
    verify = sub.add_parser("verify")
    verify.add_argument("work_item_id")
    verify.add_argument("--decision", choices=["approve", "revise", "block"], required=True)
    verify.add_argument("--evidence", required=True)
    verify.add_argument("--gate-result", action="append", default=[])
    verify.add_argument("--scientific-disposition", choices=sorted(SCIENTIFIC_DISPOSITIONS))
    verify.add_argument("--actor", required=True)
    verify.add_argument("--self-review", action="store_true")
    verify.set_defaults(func=command_verify)
    fail = sub.add_parser("fail")
    fail.add_argument("work_item_id")
    fail.add_argument("--reason", required=True)
    fail.add_argument("--retryable", action="store_true")
    fail.add_argument("--actor", required=True)
    fail.set_defaults(func=command_fail)
    record = sub.add_parser("record")
    record.add_argument("--work-item-id")
    record.add_argument("--category", required=True)
    record.add_argument("--note", required=True)
    record.add_argument("--actor", required=True)
    record.set_defaults(func=command_record)
    checkpoint = sub.add_parser("checkpoint")
    checkpoint.add_argument("--checkpoint-id")
    checkpoint.add_argument("--reason", required=True)
    checkpoint.add_argument("--actor", required=True)
    checkpoint.set_defaults(func=command_checkpoint)
    pause = sub.add_parser("pause")
    pause.add_argument("--reason", required=True)
    pause.add_argument("--actor", required=True)
    pause.set_defaults(func=lambda args: command_pause_resume(args, "run_paused"))
    resume = sub.add_parser("resume")
    resume.add_argument("--reason", required=True)
    resume.add_argument("--actor", required=True)
    resume.set_defaults(func=lambda args: command_pause_resume(args, "run_resumed"))
    replay_command = sub.add_parser("replay")
    replay_command.set_defaults(func=command_replay)
    status = sub.add_parser("status")
    status.set_defaults(func=command_status)
    lineage = sub.add_parser("experiment-lineage")
    lineage.add_argument("--block-id")
    lineage.set_defaults(func=command_experiment_lineage)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    with runtime_lock(args.root.resolve()):
        args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
