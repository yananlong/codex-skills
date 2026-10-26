#!/usr/bin/env python3
"""Create a deterministic, harness-ready research planning pack."""
from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path

import harness_runtime
from harness_common import read_events, sha256_file

STAGE_DIRS = [
    "zotero", "literature-review", "ideation", "novelty-review", "experiment-plan",
    "results-audit", "paper-review", "paper-plan", "review-loop", "rebuttal",
]
HARNESS_DIRS = ["episodes", "checkpoints"]
HARNESS_FILES = ["HARNESS_STATE.json", "work-items.json", "harness-events.jsonl"]
COMMITMENT_FILE = "research-commitment.json"
EVENT_LOG = "harness-events.jsonl"
# Hand-written files that are never deleted or overwritten; a fresh template is written beside them.
PRESERVED_FILES = ("research-brief.md", "decision-log.md")
CONTRIBUTION_CLASSES = (
    "theory", "method", "protocol", "benchmark", "dataset",
    "empirical-finding", "position", "mixed",
)
PAPER_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,191}$")
FILE_TEMPLATES = {
    "research-brief.md": """# Research Brief

## Project Frame
- Project:
- Main question:
- Working thesis:
- Intended audience:
- Desired end state:
- Paper ID:
- Contribution class: theory / method / protocol / benchmark / dataset / empirical-finding / position / mixed
- Commitment status: exploring / committed / executing / interpreting / closed

## Paper Identity

The canonical machine-readable authority is `./research-commitment.json`.

- Central object or phenomenon:
- Minimum publishable claim:
- Primary evidence obligation:
- Next mandatory evidence artifact:
- Reconsideration gate:
- Permitted D0-D2 refinements:
- Pivot triggers:
- Kill conditions:
- Successor idea policy: park / reject / separate-project

## Current State
- Operating mode: orchestrated
- Current stage:
- Existing artifacts:
- Missing artifacts:
- Current evidence class: exploratory
- Active identity version:
- Last identity-change class: D0 / D1 / D2 / D3 / D4

## Harness Policy
- Default concurrency: 1 active work item
- Default paper identities: 1 active identity
- Human approval boundaries:
- D3-D4 pivot approval authority:
- Network and data-access constraints:
- Secrets policy: keep credentials outside worker context and generated environments
- Default attempt budget: 2
- Default tool-call budget: 20
- Enforcement scope: repository validation only; executor-enforced controls must be documented separately

## Success Criteria
- Primary success condition:
- Secondary success conditions:
- Clear failure condition:
- Kill or split condition:

## Constraints
- Time budget:
- Compute budget:
- Data/tool constraints:
- Non-goals:

## Selection and Failure Inheritance
- Candidate directions considered:
- Why the active route was selected:
- Material predecessor failures:
- Parked successor ideas:
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
- Status: proceed / revise / narrow evidence class / pivot-request / park-successor / stop
- Identity change: D0 / D1 / D2 / D3 / D4
- Context:
- Alternatives considered:
- Rationale:
- Expected consequence:
- Follow-up trigger:
""",
    "artifact-index.md": """# Artifact Index

| Artifact | Canonical path | Authority | Status | Notes |
| --- | --- | --- | --- | --- |
| research commitment | ./research-commitment.json | canonical paper identity | exploring | paper ID, identity version, evidence obligation, and pivot controls |
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



def anchor_commitment(root: Path, reason: str) -> dict | None:
    """Record the commitment's digest in the event chain so later hand edits show as drift.

    Returns the event, or None when there is no commitment or it does not validate yet (an adopted
    project may carry a commitment that needs work; the validator then warns that it is unanchored).
    """
    path = root / COMMITMENT_FILE
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict) or harness_runtime.validate_commitment(data):
        return None
    return harness_runtime.commit_event(
        root,
        "commitment_edited",
        "init_research_pack",
        None,
        {
            "change_class": "D0",
            "reason": reason,
            "paper_id": data.get("paper_id"),
            "identity_version": data.get("identity_version"),
            "status": data.get("status"),
            "commitment_digest": harness_runtime.path_digest(path),
        },
    )

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target_dir", type=Path)
    parser.add_argument("--paper-id", help="Stable paper ID; defaults to the target directory name.")
    parser.add_argument("--contribution-class", default="mixed", choices=CONTRIBUTION_CLASSES)
    parser.add_argument(
        "--force",
        action="store_true",
        help=(
            "Delete and regenerate task-board.md, artifact-index.md, HARNESS_STATE.json, work-items.json, "
            "harness-events.jsonl, episodes/, and checkpoints/. Preserves stage outputs, the existing commitment, "
            "research-brief.md, and decision-log.md. Refuses when the event log holds more than one event "
            "unless --discard-event-history is also passed."
        ),
    )
    parser.add_argument(
        "--discard-event-history",
        action="store_true",
        help="With --force, allow deleting an event log that holds more than one event.",
    )
    parser.add_argument(
        "--adopt",
        action="store_true",
        help=(
            "Adopt an existing project: create only missing control files and directories, never delete or "
            "overwrite anything, refuse if harness-events.jsonl exists, and record one legacy_import "
            "observation listing pre-existing stage directories with file digests."
        ),
    )
    parser.add_argument(
        "--reset-stage-artifacts",
        action="store_true",
        help="With --force, also delete and recreate all canonical stage-output directories.",
    )
    parser.add_argument(
        "--reset-commitment",
        action="store_true",
        help="With --force, explicitly replace research-commitment.json.",
    )
    parser.add_argument("--legacy", action="store_true")
    return parser.parse_args()


def normalize_paper_id(value: str) -> str:
    candidate = re.sub(r"[^A-Za-z0-9._:-]+", "-", value).strip("-._:")
    if not candidate or not PAPER_ID_RE.fullmatch(candidate):
        raise SystemExit("paper ID must use letters, numbers, dot, underscore, colon, or hyphen")
    return candidate


def commitment_template(paper_id: str, contribution_class: str) -> dict:
    return {
        "schema_version": "1.0",
        "paper_id": paper_id,
        "identity_version": 1,
        "status": "exploring",
        "main_question": "",
        "central_object_or_phenomenon": "",
        "contribution_class": contribution_class,
        "minimum_publishable_claim": "",
        "primary_evidence_obligation": "",
        "intended_audience": "",
        "permitted_refinements": [],
        "pivot_triggers": [],
        "kill_conditions": [],
        "successor_idea_policy": "park",
        "next_mandatory_evidence_artifact": "",
        "reconsideration_gate": "",
        "selection_history": [],
        "predecessor_failures": [],
        "last_change_class": "D0",
        "last_change_rationale": "initialized",
    }


def reset_generated(
    root: Path,
    *,
    reset_stage_artifacts: bool = False,
    reset_commitment: bool = False,
) -> None:
    for name in list(FILE_TEMPLATES) + HARNESS_FILES:
        if name in PRESERVED_FILES:
            continue
        path = root / name
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink(missing_ok=True)
    if reset_commitment:
        (root / COMMITMENT_FILE).unlink(missing_ok=True)
    for name in HARNESS_DIRS:
        path = root / name
        if path.exists():
            shutil.rmtree(path)
    if reset_stage_artifacts:
        for name in STAGE_DIRS:
            path = root / name
            if path.exists():
                shutil.rmtree(path)
    (root / ".harness.lock").unlink(missing_ok=True)


def template_path(root: Path, name: str) -> Path:
    path = root / name
    if name in PRESERVED_FILES and path.exists():
        return path.with_name(path.stem + ".template.md")
    return path


def stage_inventory(root: Path, names: list[str]) -> list[dict[str, str]]:
    artifacts: list[dict[str, str]] = []
    for name in names:
        for path in sorted((root / name).rglob("*")):
            if path.is_file() and not path.is_symlink():
                artifacts.append({"path": path.relative_to(root).as_posix(), "sha256": sha256_file(path)})
    return artifacts


def adopt(root: Path, args: argparse.Namespace, paper_id: str) -> None:
    if args.force or args.legacy or args.reset_stage_artifacts or args.reset_commitment or args.discard_event_history:
        raise SystemExit("--adopt cannot be combined with --force, --legacy, or reset flags")
    if (root / EVENT_LOG).exists():
        raise SystemExit(f"Refusing to adopt: {root / EVENT_LOG} already exists; this is already a harness suite")
    blocking = [name for name in HARNESS_FILES + HARNESS_DIRS if (root / name).exists()]
    if blocking:
        raise SystemExit(
            "Refusing to adopt: harness projections or evidence exist without an event log: "
            + ", ".join(sorted(blocking))
        )
    existing_stages = [name for name in STAGE_DIRS if (root / name).is_dir()]
    artifacts = stage_inventory(root, existing_stages)
    commitment_path = root / COMMITMENT_FILE
    if commitment_path.exists():
        print(f"preserved {commitment_path}")
    else:
        commitment_path.write_text(
            json.dumps(commitment_template(paper_id, args.contribution_class), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(f"created {commitment_path}")
    for name, content in FILE_TEMPLATES.items():
        path = root / name
        if path.exists():
            print(f"preserved {path}")
            continue
        path.write_text(content, encoding="utf-8")
        print(f"created {path}")
    for name in STAGE_DIRS + HARNESS_DIRS:
        path = root / name
        if not path.exists():
            path.mkdir(parents=True)
            print(f"created {path}")
    event = harness_runtime.commit_event(
        root,
        "observation_recorded",
        "init_research_pack",
        None,
        {
            "category": "legacy_import",
            "note": (
                "Adopted an existing project into a harness-backed suite without deleting or overwriting files. "
                "Listed artifacts predate the event log and are not verified work-item outputs."
            ),
            "stage_directories": existing_stages,
            "artifacts": artifacts,
        },
    )
    print(f"created {root / EVENT_LOG} at {event['event_id']} (legacy_import: {len(artifacts)} artifacts)")
    anchor = anchor_commitment(root, "existing commitment anchored at adoption")
    if anchor:
        print(f"anchored {root / COMMITMENT_FILE} at {anchor['event_id']}")


def main() -> None:
    args = parse_args()
    root = args.target_dir.expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    if args.discard_event_history and not args.force:
        raise SystemExit("--discard-event-history requires --force")
    if args.adopt:
        adopt(root, args, normalize_paper_id(args.paper_id or root.name))
        return
    if args.reset_stage_artifacts and not args.force:
        raise SystemExit("--reset-stage-artifacts requires --force")
    if args.reset_commitment and not args.force:
        raise SystemExit("--reset-commitment requires --force")

    paper_id = normalize_paper_id(args.paper_id or root.name)
    generated = list(FILE_TEMPLATES) + STAGE_DIRS + [COMMITMENT_FILE]
    if not args.legacy:
        generated += HARNESS_FILES + HARNESS_DIRS
    existing = [name for name in generated if (root / name).exists()]
    if existing and not args.force:
        raise SystemExit("Refusing to overwrite existing files without --force: " + ", ".join(sorted(existing)))
    if args.force and not args.discard_event_history:
        events = read_events(root / EVENT_LOG) if (root / EVENT_LOG).is_file() else []
        # Events the initializer wrote itself (initialization, adoption, commitment anchor) are not history.
        event_count = sum(1 for event in events if event.get("actor") != "init_research_pack")
        if event_count > 0:
            raise SystemExit(
                f"Refusing --force: {root / EVENT_LOG} holds {event_count} events of canonical history. "
                "Use --adopt for a project without an event log, or pass --discard-event-history to delete it."
            )
    if args.force:
        reset_generated(
            root,
            reset_stage_artifacts=args.reset_stage_artifacts,
            reset_commitment=args.reset_commitment,
        )

    commitment_path = root / COMMITMENT_FILE
    if not commitment_path.exists():
        commitment_path.write_text(
            json.dumps(commitment_template(paper_id, args.contribution_class), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(f"created {commitment_path}")
    else:
        print(f"preserved {commitment_path}")

    for name, content in FILE_TEMPLATES.items():
        path = template_path(root, name)
        if path.name != name:
            print(f"preserved {root / name}")
        path.write_text(content, encoding="utf-8")
        print(f"created {path}")
    for name in STAGE_DIRS + ([] if args.legacy else HARNESS_DIRS):
        path = root / name
        path.mkdir(parents=True, exist_ok=True)
        print(f"created {path}")
    if not args.legacy:
        event = harness_runtime.commit_event(
            root,
            "observation_recorded",
            "init_research_pack",
            None,
            {
                "category": "harness_initialized",
                "note": "Initialized a harness-backed research suite with an exploring research commitment.",
            },
        )
        anchor = anchor_commitment(root, "initial commitment recorded at initialization")
        print(f"created {root / 'HARNESS_STATE.json'}")
        print(f"created {root / 'work-items.json'}")
        print(f"created {root / 'harness-events.jsonl'} at {event['event_id']}")
        if anchor:
            print(f"anchored {root / COMMITMENT_FILE} at {anchor['event_id']}")


if __name__ == "__main__":
    main()
