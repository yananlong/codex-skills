#!/usr/bin/env python3
"""Create a deterministic, harness-ready research planning pack."""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

import harness_runtime

STAGE_DIRS = [
    "zotero", "literature-review", "ideation", "novelty-review", "experiment-plan",
    "results-audit", "paper-review", "paper-plan", "review-loop", "rebuttal",
]
HARNESS_DIRS = ["episodes", "checkpoints"]
HARNESS_FILES = ["HARNESS_STATE.json", "work-items.json", "harness-events.jsonl"]
FILE_TEMPLATES = {
    "research-brief.md": """# Research Brief

## Project Frame
- Project:
- Main question:
- Working thesis:
- Intended audience:
- Desired end state:

## Current State
- Operating mode: orchestrated
- Current stage:
- Existing artifacts:
- Missing artifacts:
- Current evidence class: exploratory

## Harness Policy
- Default concurrency: 1 active work item
- Human approval boundaries:
- Network and data-access constraints:
- Secrets policy: keep credentials outside worker context and generated environments
- Default attempt budget: 2
- Default tool-call budget: 20
- Enforcement scope: repository validation only; executor-enforced controls must be documented separately

## Success Criteria
- Primary success condition:
- Secondary success conditions:
- Clear failure condition:

## Constraints
- Time budget:
- Compute budget:
- Data/tool constraints:
- Non-goals:
""",
    "task-board.md": """# Task Board

Human-readable view only. `work-items.json` and `harness-events.jsonl` are the scheduling source of truth.

| Stage | Objective | Status | Dependency | Canonical output | Next action | Checkpoint |
| --- | --- | --- | --- | --- | --- | --- |
""",
    "decision-log.md": """# Decision Log

Consequential decisions must also be represented by a machine event in `harness-events.jsonl`.

## Entry
- Date:
- Event ID:
- Work item ID:
- Stage:
- Decision:
- Status: proceed / revise / narrow evidence class / stop
- Context:
- Alternatives considered:
- Rationale:
- Expected consequence:
- Follow-up trigger:
""",
    "artifact-index.md": """# Artifact Index

| Artifact | Canonical path | Authority | Status | Notes |
| --- | --- | --- | --- | --- |
| harness event log | ./harness-events.jsonl | canonical | active | hash-chained local event history; not externally immutable |
| harness state | ./HARNESS_STATE.json | projection | active | rebuildable from event log |
| work items | ./work-items.json | projection | active | rebuildable from event log |
| episodes | ./episodes/ | canonical evidence | active | digest-anchored at submission |
| checkpoints | ./checkpoints/ | recovery aid | active | immutable-by-convention local snapshots |
| research brief | ./research-brief.md | canonical intent | canonical | planning anchor and harness policy |
| task board | ./task-board.md | human-readable view | canonical | not scheduling authority |
| decision log | ./decision-log.md | human-readable rationale | canonical | mirrors consequential events |
| zotero | ./zotero/ | stage output | pending | |
| literature review | ./literature-review/ | stage output | pending | |
| ideation | ./ideation/ | stage output | pending | |
| novelty review | ./novelty-review/ | stage output | pending | |
| experiment plan | ./experiment-plan/ | stage output | pending | |
| results audit | ./results-audit/ | stage output | pending | |
| paper review | ./paper-review/ | stage output | pending | |
| paper plan | ./paper-plan/ | stage output | pending | |
| review loop | ./review-loop/ | stage output | pending | |
| rebuttal | ./rebuttal/ | stage output | pending | |
""",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target_dir", type=Path)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--legacy", action="store_true")
    return parser.parse_args()


def reset_generated(root: Path) -> None:
    for name in list(FILE_TEMPLATES) + HARNESS_FILES:
        path = root / name
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink(missing_ok=True)
    for name in STAGE_DIRS + HARNESS_DIRS:
        path = root / name
        if path.exists():
            shutil.rmtree(path)
    (root / ".harness.lock").unlink(missing_ok=True)


def main() -> None:
    args = parse_args()
    root = args.target_dir.expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    generated = list(FILE_TEMPLATES) + STAGE_DIRS
    if not args.legacy:
        generated += HARNESS_FILES + HARNESS_DIRS
    existing = [name for name in generated if (root / name).exists()]
    if existing and not args.force:
        raise SystemExit("Refusing to overwrite existing files without --force: " + ", ".join(sorted(existing)))
    if args.force:
        reset_generated(root)
    for name, content in FILE_TEMPLATES.items():
        path = root / name
        path.write_text(content, encoding="utf-8")
        print(f"created {path}")
    for name in STAGE_DIRS + ([] if args.legacy else HARNESS_DIRS):
        path = root / name
        path.mkdir(parents=True, exist_ok=True)
        print(f"created {path}")
    if not args.legacy:
        event = harness_runtime.commit_event(
            root, "observation_recorded", "init_research_pack", None,
            {"category": "harness_initialized", "note": "Initialized a harness-backed research suite."},
        )
        print(f"created {root / 'HARNESS_STATE.json'}")
        print(f"created {root / 'work-items.json'}")
        print(f"created {root / 'harness-events.jsonl'} at {event['event_id']}")


if __name__ == "__main__":
    main()
