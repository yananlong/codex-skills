#!/usr/bin/env python3
"""Validate legacy or harness-backed orchestrated research-suite layouts."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import harness_runtime
from harness_common import SCHEMA_VERSION, canonical_json, path_digest, resolve_inside_root, sha256_bytes

BASE_FILES = {
    "research-brief.md": "# Research Brief",
    "task-board.md": "# Task Board",
    "decision-log.md": "# Decision Log",
    "artifact-index.md": "# Artifact Index",
}
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
HARNESS_INDEX_ROWS = ["./harness-events.jsonl", "./HARNESS_STATE.json", "./work-items.json", "./episodes/", "./checkpoints/"]
WORK_STATES = {"queued", "ready", "running", "awaiting_verification", "completed", "blocked"}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("target_dir", type=Path)
    p.add_argument("--profile", choices=("auto", "legacy", "harness"), default="auto")
    return p.parse_args()


def read_json(path: Path, errors: list[str]):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(f"missing file: {path}")
    except json.JSONDecodeError as exc:
        errors.append(f"invalid JSON in {path}: {exc}")
    return None


def validate_base(root: Path, errors: list[str]) -> None:
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
        for field in ("context_manifest", "expected_artifacts", "acceptance_checks", "dependencies", "write_scope", "predecessor_failures", "episodes", "verifications"):
            if not isinstance(item.get(field), list):
                errors.append(f"{label}.{field} must be a list")
        if not isinstance(item.get("attempt"), int) or item["attempt"] < 0:
            errors.append(f"{label}.attempt must be a non-negative integer")
        if not isinstance(item.get("attempt_budget"), int) or item["attempt_budget"] < 1:
            errors.append(f"{label}.attempt_budget must be a positive integer")
    if active > 1:
        errors.append("single-writer policy allows at most one active work item")
    for index, item in enumerate(items, 1):
        for dep in item.get("dependencies", []):
            if dep not in ids:
                errors.append(f"work-items.json.items[{index}] references unknown dependency: {dep}")
    graph = {item.get("work_item_id"): item.get("dependencies", []) for item in items if isinstance(item, dict) and isinstance(item.get("work_item_id"), str)}
    visiting: set[str] = set()
    visited: set[str] = set()
    def visit(node: str):
        if node in visiting:
            errors.append(f"work-item dependency cycle includes {node}")
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
                    apath = resolve_inside_root(root, artifact, "artifact")
                except SystemExit as exc:
                    errors.append(str(exc))
                    continue
                if not apath.exists() or path_digest(apath) != expected:
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
    active = [i["work_item_id"] for i in work_items.get("items", []) if i.get("state") in {"running", "awaiting_verification"}]
    if state.get("active_work_item_id") is None and active:
        errors.append("HARNESS_STATE.json omits an active work item")
    elif state.get("active_work_item_id") is not None and active != [state.get("active_work_item_id")]:
        errors.append("HARNESS_STATE.json active_work_item_id disagrees with work-items.json")
    validate_evidence(root, work_items, errors)


def main() -> int:
    args = parse_args()
    root = args.target_dir.expanduser().resolve()
    errors: list[str] = []
    profile = args.profile
    if profile == "auto":
        profile = "harness" if any((root / name).exists() for name in HARNESS_FILES) else "legacy"
    validate_base(root, errors)
    if profile == "harness":
        validate_harness(root, errors)
    if errors:
        print("Validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    if profile == "harness":
        print("Validation passed: harness layout, event chain, projections, dependency graph, and digest-anchored evidence are internally consistent. This is repository validation only; it does not establish external immutability, executor isolation, scientific validity, or independent verification.")
    else:
        print("Validation passed: legacy research-suite layout is structurally consistent. This profile does not provide durable execution, replay, or verifier-backed transitions.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
