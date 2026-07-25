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
        if all(
            find_item(work_items, dependency).get("state") == "completed"
            for dependency in candidate.get("dependencies", [])
        ):
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
        item["state"] = (
            "ready"
            if all(
                find_item(work_items, dependency).get("state") == "completed"
                for dependency in item.get("dependencies", [])
            )
            else "queued"
        )
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


def validate_work_item(args: argparse.Namespace) -> dict[str, Any]:
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
    return {
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
        "dependencies": args.depends_on or [],
        "attempt_budget": args.attempt_budget,
        "tool_call_budget": args.tool_call_budget,
        "write_scope": args.write_scope,
        "permission_policy": args.permission_policy,
        "predecessor_failures": args.predecessor_failure or [],
        "evidence_class": args.evidence_class,
        "enforcement_scope": "repository_validation_only",
    }


def validate_episode(root: Path, item: dict[str, Any], episode_path: Path) -> dict[str, Any]:
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
                raise SystemExit(
                    f"episode.failures[{index}].{field} must be a substantive string"
                )
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
        missing_expected = [a for a in item["expected_artifacts"] if a not in artifacts]
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
    episode["_relative_path"] = relative
    episode["_digest"] = path_digest(episode_path)
    episode["_artifact_digests"] = artifact_digests
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


def command_add(args: argparse.Namespace) -> None:
    root = args.root.resolve()
    _, _, items = reconstruct(root)
    if any(item["work_item_id"] == args.work_item_id for item in items["items"]):
        raise SystemExit(f"work item already exists: {args.work_item_id}")
    item = validate_work_item(args)
    for dependency in item["dependencies"]:
        find_item(items, dependency)
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
    commit_event(root, "work_item_started", args.actor, args.work_item_id, {"idempotency_key": key})
    print(f"started {args.work_item_id} with {key}")


def command_submit(args: argparse.Namespace) -> None:
    root = args.root.resolve()
    events, _, items = reconstruct(root)
    item = find_item(items, args.work_item_id)
    if args.actor != item["owner_skill"]:
        raise SystemExit("only the declared owner skill may submit the episode")
    episode = validate_episode(root, item, args.episode.resolve())
    key = args.idempotency_key or f"{args.work_item_id}:submit:{episode['_digest']}"
    matches = [
        event for event in events
        if event.get("event_type") == "episode_submitted"
        and event.get("details", {}).get("idempotency_key") == key
    ]
    if matches:
        match = matches[0]
        details = match.get("details", {})
        if details.get("episode_digest") != episode["_digest"] or match.get("work_item_id") != args.work_item_id:
            raise SystemExit("idempotency key was previously used for a different episode submission")
        print(f"already submitted {args.work_item_id}")
        return
    commit_event(
        root, "episode_submitted", args.actor, args.work_item_id,
        {
            "episode_path": episode["_relative_path"],
            "episode_id": episode["episode_id"],
            "episode_digest": episode["_digest"],
            "artifact_digests": episode["_artifact_digests"],
            "outcome": episode["outcome"],
            "transition_request": episode["transition_request"],
            "idempotency_key": key,
        },
    )
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
    if args.decision == "approve":
        if submitted["outcome"] != "completed" or submitted["transition_request"] != "approve":
            raise SystemExit("only a completed episode requesting approval may be approved")
    event_type = {
        "approve": "verification_approved",
        "revise": "verification_revise",
        "block": "work_item_blocked",
    }[args.decision]
    commit_event(
        root, event_type, args.actor, args.work_item_id,
        {"decision": args.decision, "evidence": args.evidence, "self_review": args.self_review},
    )
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
            {"checkpoint_id": checkpoint_id, "checkpoint_path": checkpoint_path.relative_to(root).as_posix(),
             "checkpoint_digest": path_digest(checkpoint_path), "reason": args.reason},
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
    add.add_argument("--attempt-budget", type=int, default=2)
    add.add_argument("--tool-call-budget", type=int, default=20)
    add.add_argument("--write-scope", action="append", default=[])
    add.add_argument("--permission-policy", default="least_privilege")
    add.add_argument("--predecessor-failure", action="append", default=[])
    add.add_argument("--evidence-class", choices=sorted(EVIDENCE_CLASSES), default="exploratory")
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
    return parser


def main() -> int:
    args = build_parser().parse_args()
    with runtime_lock(args.root.resolve()):
        args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
