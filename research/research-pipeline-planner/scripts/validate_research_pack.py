#!/usr/bin/env python3
"""Validate legacy or harness-backed orchestrated research-suite layouts."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import harness_runtime
from harness_common import SCHEMA_VERSION, canonical_json, path_digest, resolve_inside_root, sha256_bytes
from validate_research_commitment import load_commitment, validate_commitment

BASE_FILES = {
    "research-brief.md": "# Research Brief",
    "task-board.md": "# Task Board",
    "decision-log.md": "# Decision Log",
    "artifact-index.md": "# Artifact Index",
}
COMMITMENT_FILE = "research-commitment.json"
STAGE_DIRS = [
    "zotero", "literature-review", "ideation", "novelty-review", "experiment-plan",
    "results-audit", "paper-review", "paper-plan", "review-loop", "rebuttal",
]
HARNESS_FILES = ["HARNESS_STATE.json", "work-items.json", "harness-events.jsonl"]
HARNESS_DIRS = ["episodes", "checkpoints"]
INDEX_ROWS = [
    "./research-brief.md", "./task-board.md", "./decision-log.md", "./zotero/",
    "./literature-review/", "./ideation/", "./novelty-review/", "./experiment-plan/",
    "./results-audit/", "./paper-review/", "./paper-plan/", "./review-loop/", "./rebuttal/",
]
COMMITMENT_INDEX_ROW = "./research-commitment.json"
HARNESS_INDEX_ROWS = [
    "./harness-events.jsonl", "./HARNESS_STATE.json", "./work-items.json",
    "./episodes/", "./checkpoints/",
]
WORK_STATES = {"queued", "ready", "running", "awaiting_verification", "completed", "blocked"}
GATE_RESULTS = {"pass", "fail", "inconclusive", "not_applicable"}
SCIENTIFIC_DISPOSITIONS = {
    "supports_claim", "weakens_claim", "falsifies_claim", "inconclusive", "diagnostic_only",
}
LINEAGE_RELATIONS = {
    "baseline", "replication", "ablation", "parameter_variation", "negative_control",
    "sensitivity", "alternative_hypothesis", "technical_retry",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target_dir", type=Path)
    parser.add_argument("--profile", choices=("auto", "legacy", "harness"), default="auto")
    return parser.parse_args()


def read_json(path: Path, errors: list[str]):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(f"missing file: {path}")
    except json.JSONDecodeError as exc:
        errors.append(f"invalid JSON in {path}: {exc}")
    return None


def validate_commitment_file(root: Path, required: bool, errors: list[str]) -> None:
    path = root / COMMITMENT_FILE
    if not path.exists():
        if required:
            errors.append(f"missing commitment file: {path}")
        return
    data, load_errors = load_commitment(path)
    errors.extend(f"commitment: {error}" for error in load_errors)
    if not load_errors:
        errors.extend(f"commitment: {error}" for error in validate_commitment(data))
    index = root / "artifact-index.md"
    if index.is_file() and COMMITMENT_INDEX_ROW not in index.read_text(encoding="utf-8"):
        errors.append(f"{index}: missing canonical path '{COMMITMENT_INDEX_ROW}'")


def validate_base(root: Path, errors: list[str], *, require_commitment: bool) -> None:
    for name, heading in BASE_FILES.items():
        path = root / name
        if not path.is_file():
            errors.append(f"missing file: {path}")
        elif heading not in path.read_text(encoding="utf-8"):
            errors.append(f"{path}: missing heading '{heading}'")
    for name in STAGE_DIRS:
        if not (root / name).is_dir():
            errors.append(f"missing directory: {root / name}")
    index = root / "artifact-index.md"
    if index.is_file():
        content = index.read_text(encoding="utf-8")
        for row in INDEX_ROWS:
            if row not in content:
                errors.append(f"{index}: missing canonical path '{row}'")
    validate_commitment_file(root, require_commitment, errors)


def validate_work_items(data, errors: list[str]) -> None:
    if not isinstance(data, dict) or data.get("schema_version") != SCHEMA_VERSION:
        errors.append("work-items.json must be a schema_version 1.0 object")
        return
    items = data.get("items")
    if not isinstance(items, list):
        errors.append("work-items.json.items must be a list")
        return
    ids: set[str] = set()
    active = 0
    for index, item in enumerate(items, 1):
        label = f"work-items.json.items[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{label} must be an object")
            continue
        wid = item.get("work_item_id")
        if not isinstance(wid, str) or not wid:
            errors.append(f"{label}.work_item_id must be a non-empty string")
        elif wid in ids:
            errors.append(f"duplicate work_item_id: {wid}")
        else:
            ids.add(wid)
        if item.get("state") not in WORK_STATES:
            errors.append(f"{label}.state must be one of {sorted(WORK_STATES)}")
        if item.get("state") in {"running", "awaiting_verification"}:
            active += 1
        for field in ("stage", "owner_skill", "objective", "evidence_class", "enforcement_scope"):
            if not isinstance(item.get(field), str) or not item[field].strip():
                errors.append(f"{label}.{field} must be a non-empty string")
        for field in (
            "context_manifest", "expected_artifacts", "acceptance_checks", "dependencies",
            "write_scope", "predecessor_failures", "episodes", "verifications",
        ):
            if not isinstance(item.get(field), list):
                errors.append(f"{label}.{field} must be a list")
        activation = item.get("activation_conditions", [])
        if not isinstance(activation, list):
            errors.append(f"{label}.activation_conditions must be a list when present")
        if item.get("experiment_binding") is not None and not isinstance(item.get("experiment_binding"), dict):
            errors.append(f"{label}.experiment_binding must be an object when present")
        if not isinstance(item.get("attempt"), int) or item["attempt"] < 0:
            errors.append(f"{label}.attempt must be a non-negative integer")
        if not isinstance(item.get("attempt_budget"), int) or item["attempt_budget"] < 1:
            errors.append(f"{label}.attempt_budget must be a positive integer")
        if not isinstance(item.get("tool_call_budget"), int) or item["tool_call_budget"] < 0:
            errors.append(f"{label}.tool_call_budget must be a non-negative integer")
    if active > 1:
        errors.append("single-writer policy allows at most one active work item")
    for index, item in enumerate(items, 1):
        for dependency in item.get("dependencies", []):
            if dependency not in ids:
                errors.append(f"work-items.json.items[{index}] references unknown dependency: {dependency}")
    graph = {
        item.get("work_item_id"): item.get("dependencies", [])
        for item in items
        if isinstance(item, dict) and isinstance(item.get("work_item_id"), str)
    }
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> None:
        if node in visiting:
            errors.append(f"work-item dependency cycle includes {node}")
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


def _validate_bound_file(
    root: Path,
    binding: dict[str, Any],
    path_field: str,
    digest_field: str,
    label: str,
    errors: list[str],
) -> Any:
    relative = binding.get(path_field)
    expected = binding.get(digest_field)
    if not isinstance(relative, str) or not relative or not isinstance(expected, str) or not expected:
        errors.append(f"experiment binding lacks {path_field} or {digest_field}")
        return None
    try:
        path = resolve_inside_root(root, relative, label)
    except SystemExit as exc:
        errors.append(str(exc))
        return None
    if not path.is_file():
        errors.append(f"bound {label} file is missing: {relative}")
        return None
    if path_digest(path) != expected:
        errors.append(f"bound {label} digest mismatch: {relative}")
    return read_json(path, errors)


def validate_experiment_integrity(root: Path, work_items: dict, errors: list[str]) -> None:
    items = [item for item in work_items.get("items", []) if isinstance(item, dict)]
    by_id = {item.get("work_item_id"): item for item in items if isinstance(item.get("work_item_id"), str)}
    run_index: dict[str, tuple[dict[str, Any], dict[str, Any]]] = {}

    for item in items:
        wid = item.get("work_item_id", "<unknown>")
        binding = item.get("experiment_binding")
        activation = item.get("activation_conditions", [])
        if activation and binding is None:
            errors.append(f"{wid}: activation conditions require an experiment binding")
        if isinstance(activation, list):
            for index, condition in enumerate(activation, 1):
                label = f"{wid}.activation_conditions[{index}]"
                if not isinstance(condition, dict):
                    errors.append(f"{label} must be an object")
                    continue
                predecessor = condition.get("predecessor_work_item_id")
                gate_id = condition.get("gate_id")
                allowed = condition.get("allowed_results")
                if predecessor not in by_id:
                    errors.append(f"{label} references unknown predecessor {predecessor}")
                if predecessor not in item.get("dependencies", []):
                    errors.append(f"{label} predecessor must also be a dependency")
                if not isinstance(gate_id, str) or not gate_id:
                    errors.append(f"{label}.gate_id must be substantive")
                if not isinstance(allowed, list) or not allowed:
                    errors.append(f"{label}.allowed_results must be a non-empty list")
                elif set(allowed) - GATE_RESULTS:
                    errors.append(f"{label}.allowed_results contains unsupported values")

        if binding is None:
            for record in item.get("episodes", []):
                if isinstance(record, dict) and record.get("experiment_run") is not None:
                    errors.append(f"{wid}: unbound work item contains experiment_run metadata")
            continue
        if not isinstance(binding, dict):
            continue
        for field in ("block_id", "decision_gate_id", "paper_id"):
            if not isinstance(binding.get(field), str) or not binding[field]:
                errors.append(f"{wid}.experiment_binding.{field} must be substantive")
        if not isinstance(binding.get("identity_version"), int) or binding.get("identity_version", 0) < 1:
            errors.append(f"{wid}.experiment_binding.identity_version must be positive")
        claim_map = _validate_bound_file(root, binding, "claim_map_path", "claim_map_digest", "claim-map", errors)
        run_blocks = _validate_bound_file(root, binding, "run_blocks_path", "run_blocks_digest", "run-blocks", errors)
        commitment = _validate_bound_file(root, binding, "commitment_path", "commitment_digest", "commitment", errors)
        if isinstance(commitment, dict) and (
            commitment.get("paper_id") != binding.get("paper_id")
            or commitment.get("identity_version") != binding.get("identity_version")
        ):
            errors.append(f"{wid}: bound commitment identity mismatch")
        if isinstance(claim_map, list):
            claim_ids = {
                entry.get("claim_id")
                for entry in claim_map
                if isinstance(entry, dict) and isinstance(entry.get("claim_id"), str)
            }
            if set(binding.get("claim_ids", [])) - claim_ids:
                errors.append(f"{wid}: binding references unknown claim IDs")
        if isinstance(run_blocks, list):
            matches = [
                block for block in run_blocks
                if isinstance(block, dict) and block.get("block_id") == binding.get("block_id")
            ]
            if len(matches) != 1:
                errors.append(f"{wid}: bound block does not resolve exactly once")
            elif matches[0].get("decision_gate_id") != binding.get("decision_gate_id"):
                errors.append(f"{wid}: bound block gate does not match the binding")

        if item.get("state") in {"running", "awaiting_verification", "completed"}:
            snapshot = item.get("execution_snapshot")
            if not isinstance(snapshot, dict):
                errors.append(f"{wid}: started experiment item lacks execution_snapshot")
            else:
                for field in ("declared_inputs", "declared_evaluator_artifacts"):
                    values = snapshot.get(field)
                    if not isinstance(values, dict):
                        errors.append(f"{wid}.execution_snapshot.{field} must be an object")
                        continue
                    for relative, expected in values.items():
                        try:
                            path = resolve_inside_root(root, relative, field)
                        except SystemExit as exc:
                            errors.append(str(exc))
                            continue
                        if not path.exists() or path_digest(path) != expected:
                            errors.append(f"{wid}: declared snapshot digest mismatch: {relative}")

        for record in item.get("episodes", []):
            if not isinstance(record, dict):
                continue
            run = record.get("experiment_run")
            if not isinstance(run, dict):
                errors.append(f"{wid}: experiment-bound episode lacks experiment_run")
                continue
            run_id = run.get("run_id")
            if not isinstance(run_id, str) or not run_id:
                errors.append(f"{wid}: experiment run ID must be substantive")
                continue
            if run_id in run_index:
                errors.append(f"duplicate experiment run ID: {run_id}")
            else:
                run_index[run_id] = (item, record)
            if run.get("block_id") != binding.get("block_id"):
                errors.append(f"{wid}: experiment run block does not match binding")
            if run.get("gate_id") != binding.get("decision_gate_id"):
                errors.append(f"{wid}: experiment run gate does not match binding")
            if run.get("gate_result") not in GATE_RESULTS:
                errors.append(f"{wid}: invalid experiment gate result")
            if run.get("scientific_disposition") not in SCIENTIFIC_DISPOSITIONS:
                errors.append(f"{wid}: invalid scientific disposition")
            if run.get("relation") not in LINEAGE_RELATIONS:
                errors.append(f"{wid}: invalid experiment lineage relation")
            if run.get("relation") not in binding.get("allowed_lineage_relations", []):
                errors.append(f"{wid}: experiment lineage relation is not allowed by the binding")

        if item.get("state") == "completed" and item.get("episodes"):
            latest = item["episodes"][-1]
            run = latest.get("experiment_run") if isinstance(latest, dict) else None
            verification = item.get("verifications", [])[-1] if item.get("verifications") else None
            if isinstance(run, dict) and isinstance(verification, dict):
                if verification.get("gate_results", {}).get(run.get("gate_id")) != run.get("gate_result"):
                    errors.append(f"{wid}: verified gate result does not match the submitted run")
                if verification.get("scientific_disposition") != run.get("scientific_disposition"):
                    errors.append(f"{wid}: verified scientific disposition does not match the submitted run")

    for run_id, (item, record) in run_index.items():
        run = record["experiment_run"]
        parent_id = run.get("parent_run_id")
        if parent_id is None:
            continue
        if parent_id not in run_index:
            errors.append(f"experiment run {run_id} references unknown parent {parent_id}")
            continue
        parent_item, parent_record = run_index[parent_id]
        binding = item.get("experiment_binding", {})
        parent_binding = parent_item.get("experiment_binding", {})
        if (
            binding.get("paper_id") != parent_binding.get("paper_id")
            or binding.get("identity_version") != parent_binding.get("identity_version")
        ):
            errors.append(f"experiment run {run_id} has a parent from another paper identity")
        if run.get("relation") == "technical_retry" and run.get("block_id") != parent_record["experiment_run"].get("block_id"):
            errors.append(f"technical retry {run_id} has a parent from another block")


def validate_evidence(root: Path, work_items: dict, errors: list[str]) -> None:
    referenced_episodes: set[str] = set()
    for item in work_items.get("items", []):
        for record in item.get("episodes", []):
            if not isinstance(record, dict):
                errors.append(f"{item.get('work_item_id')}: legacy episode record lacks digest metadata")
                continue
            relative = record.get("episode_path")
            digest = record.get("episode_digest")
            if not isinstance(relative, str) or not isinstance(digest, str):
                errors.append(f"{item.get('work_item_id')}: episode record is incomplete")
                continue
            referenced_episodes.add(relative)
            try:
                path = resolve_inside_root(root, relative, "episode path")
            except SystemExit as exc:
                errors.append(str(exc))
                continue
            if not path.is_file():
                errors.append(f"missing submitted episode: {relative}")
            elif path_digest(path) != digest:
                errors.append(f"submitted episode digest mismatch: {relative}")
            for artifact, expected in record.get("artifact_digests", {}).items():
                try:
                    artifact_path = resolve_inside_root(root, artifact, "artifact")
                except SystemExit as exc:
                    errors.append(str(exc))
                    continue
                if not artifact_path.exists() or path_digest(artifact_path) != expected:
                    errors.append(f"submitted artifact digest mismatch: {artifact}")
    episodes_dir = root / "episodes"
    if episodes_dir.is_dir():
        for path in episodes_dir.rglob("*.json"):
            relative = path.relative_to(root).as_posix()
            if relative not in referenced_episodes:
                errors.append(f"orphan episode package: {relative}")

    referenced_checkpoints: set[str] = set()
    try:
        events, _, _ = harness_runtime.reconstruct(root)
    except SystemExit as exc:
        errors.append(f"harness event replay failed: {exc}")
        return
    for event in events:
        if event.get("event_type") != "checkpoint_saved":
            continue
        details = event.get("details", {})
        relative = details.get("checkpoint_path")
        expected = details.get("checkpoint_digest")
        if not isinstance(relative, str) or not isinstance(expected, str):
            errors.append("checkpoint_saved event lacks digest metadata")
            continue
        referenced_checkpoints.add(relative)
        try:
            path = resolve_inside_root(root, relative, "checkpoint path")
        except SystemExit as exc:
            errors.append(str(exc))
            continue
        if not path.is_file() or path_digest(path) != expected:
            errors.append(f"checkpoint digest mismatch: {relative}")
            continue
        data = read_json(path, errors)
        if isinstance(data, dict):
            stored = data.get("snapshot_digest")
            body = dict(data)
            body.pop("snapshot_digest", None)
            actual = sha256_bytes(canonical_json(body).encode("utf-8"))
            if stored != actual:
                errors.append(f"checkpoint snapshot_digest mismatch: {relative}")
    checkpoints_dir = root / "checkpoints"
    if checkpoints_dir.is_dir():
        for path in checkpoints_dir.rglob("*.json"):
            relative = path.relative_to(root).as_posix()
            if relative not in referenced_checkpoints:
                errors.append(f"orphan checkpoint package: {relative}")


def validate_harness(root: Path, errors: list[str]) -> None:
    for name in HARNESS_FILES:
        if not (root / name).is_file():
            errors.append(f"missing harness file: {root / name}")
    for name in HARNESS_DIRS:
        if not (root / name).is_dir():
            errors.append(f"missing harness directory: {root / name}")
    index = root / "artifact-index.md"
    if index.is_file():
        content = index.read_text(encoding="utf-8")
        for row in HARNESS_INDEX_ROWS:
            if row not in content:
                errors.append(f"{index}: missing harness path '{row}'")
    if errors:
        return
    state = read_json(root / "HARNESS_STATE.json", errors)
    work_items = read_json(root / "work-items.json", errors)
    if not isinstance(state, dict) or not isinstance(work_items, dict):
        return
    validate_work_items(work_items, errors)
    try:
        replayed_state, replayed_items = harness_runtime.replay(root, write=False)
    except SystemExit as exc:
        errors.append(f"harness event replay failed: {exc}")
        return
    if state != replayed_state:
        errors.append("HARNESS_STATE.json does not match replayed event state; run harness_runtime.py replay")
    if work_items != replayed_items:
        errors.append("work-items.json does not match replayed event state; run harness_runtime.py replay")
    active = [
        item["work_item_id"]
        for item in work_items.get("items", [])
        if item.get("state") in {"running", "awaiting_verification"}
    ]
    if state.get("active_work_item_id") is None and active:
        errors.append("HARNESS_STATE.json omits an active work item")
    elif state.get("active_work_item_id") is not None and active != [state.get("active_work_item_id")]:
        errors.append("HARNESS_STATE.json active_work_item_id disagrees with work-items.json")
    validate_experiment_integrity(root, work_items, errors)
    validate_evidence(root, work_items, errors)


def main() -> int:
    args = parse_args()
    root = args.target_dir.expanduser().resolve()
    errors: list[str] = []
    profile = args.profile
    if profile == "auto":
        profile = "harness" if any((root / name).exists() for name in HARNESS_FILES) else "legacy"
    validate_base(root, errors, require_commitment=profile == "harness")
    if profile == "harness":
        validate_harness(root, errors)
    if errors:
        print("Validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    if profile == "harness":
        print(
            "Validation passed: commitment structure, harness layout, event chain, projections, "
            "dependency graph, experiment bindings, accepted gate results, lineage references, "
            "and digest-anchored evidence are internally consistent. This is repository validation "
            "only; declared snapshots are not proof of filesystem isolation, external immutability, "
            "scientific validity, or independent verification."
        )
    else:
        print(
            "Validation passed: legacy research-suite layout is structurally consistent. "
            "A commitment file was validated when present, but this profile does not provide "
            "durable execution, replay, or verifier-backed transitions."
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
