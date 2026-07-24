#!/usr/bin/env python3
"""Validate legacy or harness-backed orchestrated research-suite layouts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import harness_runtime


LEGACY_REQUIRED_FILES = {
    "research-brief.md": "# Research Brief",
    "task-board.md": "# Task Board",
    "decision-log.md": "# Decision Log",
    "artifact-index.md": "# Artifact Index",
}

REQUIRED_DIRS = [
    "zotero",
    "literature-review",
    "ideation",
    "novelty-review",
    "experiment-plan",
    "results-audit",
    "paper-review",
    "paper-plan",
    "review-loop",
    "rebuttal",
]

LEGACY_INDEX_ROWS = [
    "./research-brief.md",
    "./task-board.md",
    "./decision-log.md",
    "./zotero/",
    "./literature-review/",
    "./ideation/",
    "./novelty-review/",
    "./experiment-plan/",
    "./results-audit/",
    "./paper-review/",
    "./paper-plan/",
    "./review-loop/",
    "./rebuttal/",
]

HARNESS_FILES = ["HARNESS_STATE.json", "work-items.json", "harness-events.jsonl"]
HARNESS_DIRS = ["episodes", "checkpoints"]
HARNESS_INDEX_ROWS = [
    "./harness-events.jsonl",
    "./HARNESS_STATE.json",
    "./work-items.json",
    "./episodes/",
    "./checkpoints/",
]

WORK_STATES = {
    "queued",
    "ready",
    "running",
    "awaiting_verification",
    "completed",
    "blocked",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target_dir", type=Path, help="Research suite root directory.")
    parser.add_argument(
        "--profile",
        choices=("auto", "legacy", "harness"),
        default="auto",
        help="Validation profile. Auto selects harness when harness artifacts are present.",
    )
    return parser.parse_args()


def load_json(path: Path, errors: list[str]):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(f"missing file: {path}")
    except json.JSONDecodeError as exc:
        errors.append(f"invalid JSON in {path}: {exc}")
    return None


def validate_base(root: Path, errors: list[str]) -> None:
    for name, heading in LEGACY_REQUIRED_FILES.items():
        path = root / name
        if not path.exists():
            errors.append(f"missing file: {path}")
            continue
        content = path.read_text(encoding="utf-8")
        if heading not in content:
            errors.append(f"{path}: missing heading '{heading}'")

    for name in REQUIRED_DIRS:
        path = root / name
        if not path.is_dir():
            errors.append(f"missing directory: {path}")

    index_path = root / "artifact-index.md"
    if index_path.exists():
        index_content = index_path.read_text(encoding="utf-8")
        for row in LEGACY_INDEX_ROWS:
            if row not in index_content:
                errors.append(f"{index_path}: missing canonical path '{row}'")


def validate_work_items(data, errors: list[str]) -> None:
    if not isinstance(data, dict) or data.get("schema_version") != "1.0":
        errors.append("work-items.json must be a schema_version 1.0 object")
        return
    items = data.get("items")
    if not isinstance(items, list):
        errors.append("work-items.json.items must be a list")
        return
    ids: set[str] = set()
    active = 0
    for index, item in enumerate(items, start=1):
        label = f"work-items.json.items[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{label} must be an object")
            continue
        work_item_id = item.get("work_item_id")
        if not isinstance(work_item_id, str) or not work_item_id.strip():
            errors.append(f"{label}.work_item_id must be a non-empty string")
        elif work_item_id in ids:
            errors.append(f"duplicate work_item_id: {work_item_id}")
        else:
            ids.add(work_item_id)
        if item.get("state") not in WORK_STATES:
            errors.append(f"{label}.state must be one of {sorted(WORK_STATES)}")
        if item.get("state") in {"running", "awaiting_verification"}:
            active += 1
        for field in ("stage", "owner_skill", "objective", "evidence_class"):
            if not isinstance(item.get(field), str) or not item[field].strip():
                errors.append(f"{label}.{field} must be a non-empty string")
        for field in (
            "context_manifest",
            "expected_artifacts",
            "acceptance_checks",
            "dependencies",
            "write_scope",
            "predecessor_failures",
            "episodes",
            "verifications",
        ):
            if not isinstance(item.get(field), list):
                errors.append(f"{label}.{field} must be a list")
        if not isinstance(item.get("attempt"), int) or item["attempt"] < 0:
            errors.append(f"{label}.attempt must be a non-negative integer")
        if not isinstance(item.get("attempt_budget"), int) or item["attempt_budget"] < 1:
            errors.append(f"{label}.attempt_budget must be a positive integer")
    if active > 1:
        errors.append("default single-writer policy allows at most one active work item")


def validate_harness(root: Path, errors: list[str]) -> None:
    for name in HARNESS_FILES:
        if not (root / name).exists():
            errors.append(f"missing harness file: {root / name}")
    for name in HARNESS_DIRS:
        if not (root / name).is_dir():
            errors.append(f"missing harness directory: {root / name}")

    index_path = root / "artifact-index.md"
    if index_path.exists():
        index_content = index_path.read_text(encoding="utf-8")
        for row in HARNESS_INDEX_ROWS:
            if row not in index_content:
                errors.append(f"{index_path}: missing harness path '{row}'")

    if errors:
        return

    state = load_json(root / "HARNESS_STATE.json", errors)
    work_items = load_json(root / "work-items.json", errors)
    if state is None or work_items is None:
        return
    validate_work_items(work_items, errors)

    try:
        replayed_state, replayed_items = harness_runtime.replay(root, write=False)
    except SystemExit as exc:
        errors.append(f"harness event replay failed: {exc}")
        return

    if state != replayed_state:
        errors.append(
            "HARNESS_STATE.json does not match replayed event state; run harness_runtime.py replay"
        )
    if work_items != replayed_items:
        errors.append(
            "work-items.json does not match replayed event state; run harness_runtime.py replay"
        )

    active_id = state.get("active_work_item_id")
    active_items = [
        item["work_item_id"]
        for item in work_items.get("items", [])
        if item.get("state") in {"running", "awaiting_verification"}
    ]
    if active_id is None and active_items:
        errors.append("HARNESS_STATE.json omits an active work item")
    if active_id is not None and active_items != [active_id]:
        errors.append("HARNESS_STATE.json active_work_item_id disagrees with work-items.json")


def main() -> int:
    args = parse_args()
    root = args.target_dir.expanduser().resolve()
    errors: list[str] = []

    profile = args.profile
    harness_present = any((root / name).exists() for name in HARNESS_FILES)
    if profile == "auto":
        profile = "harness" if harness_present else "legacy"

    validate_base(root, errors)
    if profile == "harness":
        validate_harness(root, errors)

    if errors:
        print("Validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    if profile == "harness":
        print(
            "Validation passed: harness layout, event chain, replayed projections, and "
            "single-writer state are structurally consistent. This does not establish "
            "scientific validity or independent verification."
        )
    else:
        print(
            "Validation passed: legacy research-suite layout is structurally consistent. "
            "This profile does not provide durable execution, replay, or verifier-backed transitions."
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
