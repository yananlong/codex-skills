#!/usr/bin/env python3
"""Create a deterministic, harness-ready research planning pack."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


STAGE_DIRS = [
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

HARNESS_DIRS = ["episodes", "checkpoints"]

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

## Success Criteria

- Primary success condition:
- Secondary success conditions:
- Clear failure condition:

## Constraints

- Time budget:
- Compute budget:
- Data/tool constraints:
- Non-goals:

## Stage Plan

| Stage | Goal | Canonical path | Owner skill | Status |
| --- | --- | --- | --- | --- |
| zotero | | ./zotero/ | research-zotero | optional |
| literature review | | ./literature-review/ | research-systematic-literature-review | optional |
| ideation | | ./ideation/ | research-idea-discovery | optional |
| novelty review | | ./novelty-review/ | research-novelty-review | optional |
| experiment plan | | ./experiment-plan/ | research-experiment-plan | optional |
| results audit | | ./results-audit/ | research-results-auditor | optional |
| paper review | | ./paper-review/ | research-paper-review | optional |
| paper plan | | ./paper-plan/ | research-paper-plan | optional |
| review loop | | ./review-loop/ | research-review-loop | optional |
| rebuttal | | ./rebuttal/ | research-rebuttal | optional |

## Open Questions

- Question:
- Why it matters:
- What would resolve it:
""",
    "task-board.md": """# Task Board

This is a human-readable view only. `work-items.json` and `harness-events.jsonl` are the scheduling source of truth.

| Stage | Objective | Status | Dependency | Canonical output | Next action | Checkpoint |
| --- | --- | --- | --- | --- | --- | --- |
| zotero / corpus sync | | todo | | ./zotero/ | | |
| literature review | | todo | | ./literature-review/ | | |
| ideation | | todo | | ./ideation/ | | |
| novelty review | | todo | | ./novelty-review/ | | |
| experiment plan | | todo | | ./experiment-plan/ | | |
| results audit | | todo | | ./results-audit/ | | |
| paper review | | todo | | ./paper-review/ | | |
| paper plan | | todo | | ./paper-plan/ | | |
| review loop | | todo | | ./review-loop/ | | |
| rebuttal | | todo | | ./rebuttal/ | | |
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
| harness event log | ./harness-events.jsonl | canonical | active | append-only transition and observation log |
| harness state | ./HARNESS_STATE.json | projection | active | rebuildable from event log |
| work items | ./work-items.json | projection | active | rebuildable from event log |
| episodes | ./episodes/ | canonical evidence | active | one package per worker attempt |
| checkpoints | ./checkpoints/ | recovery aid | active | resumable snapshots |
| research brief | ./research-brief.md | canonical intent | canonical | planning anchor and harness policy |
| task board | ./task-board.md | human-readable view | canonical | not scheduling authority |
| decision log | ./decision-log.md | human-readable rationale | canonical | mirrors consequential events |
| zotero | ./zotero/ | stage output | pending | outputs from research-zotero |
| literature review | ./literature-review/ | stage output | pending | outputs from research-systematic-literature-review |
| ideation | ./ideation/ | stage output | pending | outputs from research-idea-discovery |
| novelty review | ./novelty-review/ | stage output | pending | outputs from research-novelty-review |
| experiment plan | ./experiment-plan/ | stage output | pending | outputs from research-experiment-plan |
| results audit | ./results-audit/ | stage output | pending | outputs from research-results-auditor |
| paper review | ./paper-review/ | stage output | pending | outputs from research-paper-review |
| paper plan | ./paper-plan/ | stage output | pending | outputs from research-paper-plan |
| review loop | ./review-loop/ | stage output | pending | outputs from research-review-loop |
| rebuttal | ./rebuttal/ | stage output | pending | outputs from research-rebuttal |
""",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target_dir", type=Path, help="Directory where the pack will be created.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing files.")
    parser.add_argument(
        "--legacy",
        action="store_true",
        help="Create only the pre-harness layout for compatibility testing.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.target_dir.mkdir(parents=True, exist_ok=True)

    generated_files = list(FILE_TEMPLATES)
    generated_dirs = list(STAGE_DIRS)
    if not args.legacy:
        generated_files.extend(["HARNESS_STATE.json", "work-items.json", "harness-events.jsonl"])
        generated_dirs.extend(HARNESS_DIRS)

    existing = [name for name in generated_files if (args.target_dir / name).exists()]
    existing.extend(name for name in generated_dirs if (args.target_dir / name).exists())
    if existing and not args.force:
        raise SystemExit(
            "Refusing to overwrite existing files without --force: " + ", ".join(sorted(existing))
        )

    for name, content in FILE_TEMPLATES.items():
        path = args.target_dir / name
        path.write_text(content, encoding="utf-8")
        print(f"created {path}")

    for name in generated_dirs:
        path = args.target_dir / name
        path.mkdir(parents=True, exist_ok=True)
        print(f"created {path}")

    if not args.legacy:
        state = {
            "schema_version": "1.0",
            "status": "initialized",
            "active_work_item_id": None,
            "last_event_id": None,
            "last_event_hash": None,
            "last_checkpoint_id": None,
            "updated_at": utc_now(),
        }
        work_items = {"schema_version": "1.0", "items": []}
        write_json(args.target_dir / "HARNESS_STATE.json", state)
        write_json(args.target_dir / "work-items.json", work_items)
        (args.target_dir / "harness-events.jsonl").write_text("", encoding="utf-8")
        print(f"created {args.target_dir / 'HARNESS_STATE.json'}")
        print(f"created {args.target_dir / 'work-items.json'}")
        print(f"created {args.target_dir / 'harness-events.jsonl'}")


if __name__ == "__main__":
    main()
