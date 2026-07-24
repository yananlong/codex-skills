#!/usr/bin/env python3
"""Durable single-writer runtime for orchestrated research-suite work items."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import fcntl
except ImportError:  # pragma: no cover - non-POSIX fallback
    fcntl = None

SCHEMA_VERSION = "1.0"
EVIDENCE_CLASSES = {
    "exploratory",
    "confirmatory",
    "independently_verified",
    "operational_high_stakes",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def atomic_write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_json(data: dict[str, Any]) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def event_hash(event_without_hash: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json(event_without_hash).encode("utf-8")).hexdigest()


def read_events(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    events: list[dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"invalid JSON in {path} line {line_no}: {exc}") from exc
        if not isinstance(event, dict):
            raise SystemExit(f"event at {path} line {line_no} must be an object")
        events.append(event)
    return events


def verify_chain(events: list[dict[str, Any]]) -> None:
    previous = None
    for index, event in enumerate(events, start=1):
        stored = event.get("event_hash")
        body = dict(event)
        body.pop("event_hash", None)
        if body.get("previous_event_hash") != previous:
            raise SystemExit(f"event chain mismatch at event {index}")
        if stored != event_hash(body):
            raise SystemExit(f"event hash mismatch at event {index}")
        previous = stored


def append_event(
    root: Path,
    event_type: str,
    actor: str,
    work_item_id: str | None,
    details: dict[str, Any],
) -> dict[str, Any]:
    root.mkdir(parents=True, exist_ok=True)
    events_path = root / "harness-events.jsonl"
    events = read_events(events_path)
    verify_chain(events)
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
    with events_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    return event


def initial_state() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "initialized",
        "active_work_item_id": None,
        "last_event_id": None,
        "last_event_hash": None,
        "last_checkpoint_id": None,
        "updated_at": None,
    }


def initial_work_items() -> dict[str, Any]:
    return {"schema_version": SCHEMA_VERSION, "items": []}


def find_item(work_items: dict[str, Any], work_item_id: str) -> dict[str, Any]:
    for item in work_items.get("items", []):
        if item.get("work_item_id") == work_item_id:
            return item
    raise SystemExit(f"unknown work item: {work_item_id}")


def apply_event(state: dict[str, Any], work_items: dict[str, Any], event: dict[str, Any]) -> None:
    event_type = event["event_type"]
    details = event.get("details", {})
    work_item_id = event.get("work_item_id")

    if event_type == "work_item_added":
        if any(item.get("work_item_id") == work_item_id for item in work_items["items"]):
            raise SystemExit(f"duplicate work item in event log: {work_item_id}")
        item = dict(details["work_item"])
        dependencies = item.get("dependencies", [])
        item["state"] = (
            "ready"
            if not dependencies
            or all(
                find_item(work_items, dependency)["state"] == "completed"
                for dependency in dependencies
            )
            else "queued"
        )
        item["attempt"] = 0
        item["episodes"] = []
        item["verifications"] = []
        work_items["items"].append(item)
    elif event_type == "work_item_started":
        item = find_item(work_items, work_item_id)
        if item["state"] != "ready":
            raise SystemExit(f"cannot start {work_item_id} from {item['state']}")
        if state.get("active_work_item_id") not in {None, work_item_id}:
            raise SystemExit("another work item is already active")
        item["state"] = "running"
        item["attempt"] += 1
        item["idempotency_key"] = details["idempotency_key"]
        state["active_work_item_id"] = work_item_id
        state["status"] = "running"
    elif event_type == "episode_submitted":
        item = find_item(work_items, work_item_id)
        if item["state"] != "running":
            raise SystemExit(f"cannot submit {work_item_id} from {item['state']}")
        item["state"] = "awaiting_verification"
        item["episodes"].append(details["episode_path"])
        state["active_work_item_id"] = work_item_id
    elif event_type == "verification_approved":
        item = find_item(work_items, work_item_id)
        if item["state"] != "awaiting_verification":
            raise SystemExit(f"cannot approve {work_item_id} from {item['state']}")
        item["state"] = "completed"
        item["verifications"].append(details)
        state["active_work_item_id"] = None
        for candidate in work_items["items"]:
            if candidate["state"] == "queued" and all(
                find_item(work_items, dependency)["state"] == "completed"
                for dependency in candidate.get("dependencies", [])
            ):
                candidate["state"] = "ready"
        state["status"] = (
            "completed"
            if work_items["items"]
            and all(candidate["state"] == "completed" for candidate in work_items["items"])
            else "initialized"
        )
    elif event_type == "verification_revise":
        item = find_item(work_items, work_item_id)
        if item["state"] != "awaiting_verification":
            raise SystemExit(f"cannot revise {work_item_id} from {item['state']}")
        item["verifications"].append(details)
        item["state"] = "blocked" if item["attempt"] >= item["attempt_budget"] else "ready"
        state["status"] = "blocked" if item["state"] == "blocked" else "initialized"
        state["active_work_item_id"] = None
    elif event_type == "work_item_failed_retryable":
        item = find_item(work_items, work_item_id)
        if item["state"] != "running":
            raise SystemExit(f"cannot fail {work_item_id} from {item['state']}")
        item["state"] = "blocked" if item["attempt"] >= item["attempt_budget"] else "ready"
        state["status"] = "blocked" if item["state"] == "blocked" else "initialized"
        state["active_work_item_id"] = None
    elif event_type == "work_item_blocked":
        item = find_item(work_items, work_item_id)
        if item["state"] not in {"ready", "running", "awaiting_verification"}:
            raise SystemExit(f"cannot block {work_item_id} from {item['state']}")
        item["state"] = "blocked"
        state["status"] = "blocked"
        state["active_work_item_id"] = None
    elif event_type == "checkpoint_saved":
        state["last_checkpoint_id"] = details["checkpoint_id"]
    elif event_type == "run_paused":
        state["status"] = "interrupted"
    elif event_type == "run_resumed":
        state["status"] = "running" if state.get("active_work_item_id") else "initialized"
    elif event_type == "observation_recorded":
        pass
    else:
        raise SystemExit(f"unsupported event type: {event_type}")

    state["last_event_id"] = event["event_id"]
    state["last_event_hash"] = event["event_hash"]
    state["updated_at"] = event["timestamp"]


def replay(root: Path, write: bool = True) -> tuple[dict[str, Any], dict[str, Any]]:
    events = read_events(root / "harness-events.jsonl")
    verify_chain(events)
    state = initial_state()
    work_items = initial_work_items()
    for event in events:
        apply_event(state, work_items, event)
    if write:
        atomic_write_json(root / "HARNESS_STATE.json", state)
        atomic_write_json(root / "work-items.json", work_items)
    return state, work_items


def validate_work_item(args: argparse.Namespace) -> dict[str, Any]:
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
    }


def path_is_in_scope(root: Path, artifact: str, scopes: list[str]) -> bool:
    candidate = (root / artifact).resolve()
    for scope in scopes:
        scope_path = (root / scope).resolve()
        if candidate == scope_path or scope_path in candidate.parents:
            return True
    return False


def validate_episode(root: Path, item: dict[str, Any], episode_path: Path) -> dict[str, Any]:
    episode = load_json(episode_path, None)
    if not isinstance(episode, dict):
        raise SystemExit("episode must be a JSON object")
    required = {
        "schema_version",
        "episode_id",
        "work_item_id",
        "attempt",
        "owner_skill",
        "objective",
        "artifacts",
        "verification",
        "failures",
        "outcome",
        "transition_request",
        "summary",
    }
    missing = sorted(required - set(episode))
    if missing:
        raise SystemExit("episode missing fields: " + ", ".join(missing))
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

    if episode["outcome"] == "completed":
        artifacts = episode.get("artifacts")
        if not isinstance(artifacts, list) or not artifacts:
            raise SystemExit("completed episode must list artifacts")
        missing_expected = [
            artifact for artifact in item["expected_artifacts"] if artifact not in artifacts
        ]
        if missing_expected:
            raise SystemExit(
                "completed episode missing expected artifacts: " + ", ".join(missing_expected)
            )
        for artifact in artifacts:
            candidate = (root / artifact).resolve()
            try:
                candidate.relative_to(root.resolve())
            except ValueError as exc:
                raise SystemExit(f"artifact escapes suite root: {artifact}") from exc
            if not candidate.exists():
                raise SystemExit(f"episode artifact does not exist: {artifact}")
            if not path_is_in_scope(root, artifact, item["write_scope"]):
                raise SystemExit(
                    f"episode artifact is outside declared write scope: {artifact}"
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

        results = {
            entry.get("check_id"): entry
            for entry in episode.get("verification", [])
            if isinstance(entry, dict)
        }
        for check in item["acceptance_checks"]:
            result = results.get(check["check_id"])
            if (
                not result
                or result.get("result") != "pass"
                or not str(result.get("evidence", "")).strip()
            ):
                raise SystemExit(
                    f"acceptance check not passed with evidence: {check['check_id']}"
                )
    return episode


def project_after_event(root: Path, event: dict[str, Any]) -> None:
    state, _ = replay(root, write=True)
    if state["last_event_id"] != event["event_id"]:
        raise SystemExit("projection failed to include latest event")


def command_add(args: argparse.Namespace) -> None:
    root = args.root.resolve()
    _, work_items = replay(root, write=True)
    if any(item["work_item_id"] == args.work_item_id for item in work_items["items"]):
        raise SystemExit(f"work item already exists: {args.work_item_id}")
    item = validate_work_item(args)
    for dependency in item["dependencies"]:
        find_item(work_items, dependency)
    event = append_event(
        root,
        "work_item_added",
        args.actor,
        args.work_item_id,
        {"work_item": item},
    )
    project_after_event(root, event)
    print(f"added {args.work_item_id}")


def command_start(args: argparse.Namespace) -> None:
    root = args.root.resolve()
    _, work_items = replay(root, write=True)
    item = find_item(work_items, args.work_item_id)
    key = args.idempotency_key or f"{args.work_item_id}:attempt:{item['attempt'] + 1}"
    event = append_event(
        root,
        "work_item_started",
        args.actor,
        args.work_item_id,
        {"idempotency_key": key},
    )
    project_after_event(root, event)
    print(f"started {args.work_item_id} with {key}")


def command_submit(args: argparse.Namespace) -> None:
    root = args.root.resolve()
    _, work_items = replay(root, write=True)
    item = find_item(work_items, args.work_item_id)
    episode_path = args.episode.resolve()
    episode = validate_episode(root, item, episode_path)
    try:
        relative_path = str(episode_path.relative_to(root))
    except ValueError as exc:
        raise SystemExit("episode must be stored inside the suite root") from exc
    event = append_event(
        root,
        "episode_submitted",
        args.actor,
        args.work_item_id,
        {
            "episode_path": relative_path,
            "transition_request": episode["transition_request"],
        },
    )
    project_after_event(root, event)
    print(f"submitted {args.work_item_id}")


def command_verify(args: argparse.Namespace) -> None:
    root = args.root.resolve()
    _, work_items = replay(root, write=True)
    item = find_item(work_items, args.work_item_id)
    if args.actor == item["owner_skill"] and not args.self_review:
        raise SystemExit("worker-role verification must be explicitly marked --self-review")
    if item["state"] != "awaiting_verification":
        raise SystemExit("work item is not awaiting verification")
    event_type = {
        "approve": "verification_approved",
        "revise": "verification_revise",
        "block": "work_item_blocked",
    }[args.decision]
    event = append_event(
        root,
        event_type,
        args.actor,
        args.work_item_id,
        {
            "decision": args.decision,
            "evidence": args.evidence,
            "self_review": args.self_review,
        },
    )
    project_after_event(root, event)
    print(f"verification {args.decision}: {args.work_item_id}")


def command_fail(args: argparse.Namespace) -> None:
    root = args.root.resolve()
    event_type = "work_item_failed_retryable" if args.retryable else "work_item_blocked"
    event = append_event(
        root,
        event_type,
        args.actor,
        args.work_item_id,
        {"reason": args.reason},
    )
    project_after_event(root, event)
    print(f"recorded failure for {args.work_item_id}")


def command_record(args: argparse.Namespace) -> None:
    root = args.root.resolve()
    event = append_event(
        root,
        "observation_recorded",
        args.actor,
        args.work_item_id,
        {"category": args.category, "note": args.note},
    )
    project_after_event(root, event)
    print(event["event_id"])


def command_checkpoint(args: argparse.Namespace) -> None:
    root = args.root.resolve()
    state, work_items = replay(root, write=True)
    checkpoints = root / "checkpoints"
    checkpoints.mkdir(parents=True, exist_ok=True)
    checkpoint_id = args.checkpoint_id or f"CP-{len(list(checkpoints.glob('*.json'))) + 1:06d}"
    atomic_write_json(
        checkpoints / f"{checkpoint_id}.json",
        {
            "schema_version": SCHEMA_VERSION,
            "checkpoint_id": checkpoint_id,
            "created_at": utc_now(),
            "reason": args.reason,
            "state": state,
            "work_items": work_items,
        },
    )
    event = append_event(
        root,
        "checkpoint_saved",
        args.actor,
        state.get("active_work_item_id"),
        {"checkpoint_id": checkpoint_id, "reason": args.reason},
    )
    project_after_event(root, event)
    print(checkpoint_id)


def command_pause_resume(args: argparse.Namespace, event_type: str) -> None:
    root = args.root.resolve()
    event = append_event(root, event_type, args.actor, None, {"reason": args.reason})
    project_after_event(root, event)
    print(event_type)


def command_status(args: argparse.Namespace) -> None:
    state, work_items = replay(args.root.resolve(), write=True)
    print(json.dumps({"state": state, "work_items": work_items}, indent=2, sort_keys=True))


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
    add.add_argument(
        "--evidence-class", choices=sorted(EVIDENCE_CLASSES), default="exploratory"
    )
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
    submit.set_defaults(func=command_submit)

    verify = sub.add_parser("verify")
    verify.add_argument("work_item_id")
    verify.add_argument(
        "--decision", choices=["approve", "revise", "block"], required=True
    )
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
