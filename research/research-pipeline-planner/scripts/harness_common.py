"""Shared filesystem, hashing, and schema helpers for the research harness."""
from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "1.0"
EVIDENCE_CLASSES = {
    "exploratory",
    "confirmatory",
    "independently_verified",
    "operational_high_stakes",
}
CHECKPOINT_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,191}$")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _fsync_enabled() -> bool:
    return os.environ.get("HARNESS_DISABLE_FSYNC") != "1"


def atomic_write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            if _fsync_enabled():
                os.fsync(handle.fileno())
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid JSON in {path}: {exc}") from exc


def canonical_json(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def path_digest(path: Path) -> str:
    if path.is_file():
        return sha256_file(path)
    if path.is_dir():
        digest = hashlib.sha256()
        for child in sorted(p for p in path.rglob("*") if p.is_file()):
            rel = child.relative_to(path).as_posix().encode("utf-8")
            digest.update(len(rel).to_bytes(8, "big"))
            digest.update(rel)
            digest.update(sha256_file(child).encode("ascii"))
        return digest.hexdigest()
    raise SystemExit(f"artifact is neither a regular file nor directory: {path}")


def event_hash(event_without_hash: dict[str, Any]) -> str:
    return sha256_bytes(canonical_json(event_without_hash).encode("utf-8"))


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
        if event.get("schema_version") != SCHEMA_VERSION:
            raise SystemExit(f"event schema_version mismatch at event {index}")
        expected_id = f"EV-{index:06d}"
        if event.get("event_id") != expected_id:
            raise SystemExit(f"event id mismatch at event {index}: expected {expected_id}")
        stored = event.get("event_hash")
        if not isinstance(stored, str) or not stored:
            raise SystemExit(f"missing event hash at event {index}")
        body = dict(event)
        body.pop("event_hash", None)
        if body.get("previous_event_hash") != previous:
            raise SystemExit(f"event chain mismatch at event {index}")
        if stored != event_hash(body):
            raise SystemExit(f"event hash mismatch at event {index}")
        previous = stored


def initial_state() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "initialized",
        "paused": False,
        "active_work_item_id": None,
        "last_event_id": None,
        "last_event_hash": None,
        "last_checkpoint_id": None,
        "updated_at": None,
    }


def initial_work_items() -> dict[str, Any]:
    return {"schema_version": SCHEMA_VERSION, "items": []}


def find_item(work_items: dict[str, Any], work_item_id: str | None) -> dict[str, Any]:
    if not work_item_id:
        raise SystemExit("work item id is required")
    for item in work_items.get("items", []):
        if item.get("work_item_id") == work_item_id:
            return item
    raise SystemExit(f"unknown work item: {work_item_id}")


def resolve_inside_root(root: Path, relative: str, label: str) -> Path:
    if not isinstance(relative, str) or not relative.strip():
        raise SystemExit(f"{label} must be a non-empty relative path")
    raw = Path(relative)
    if raw.is_absolute():
        raise SystemExit(f"{label} must be relative to the suite root: {relative}")
    candidate = (root / raw).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise SystemExit(f"{label} escapes suite root: {relative}") from exc
    return candidate


def path_is_in_scope(root: Path, artifact: str, scopes: list[str]) -> bool:
    candidate = resolve_inside_root(root, artifact, "artifact")
    for scope in scopes:
        scope_path = resolve_inside_root(root, scope, "write scope")
        if candidate == scope_path or scope_path in candidate.parents:
            return True
    return False


def validate_checkpoint_id(checkpoint_id: str) -> None:
    if checkpoint_id in {".", ".."} or not CHECKPOINT_ID_RE.fullmatch(checkpoint_id):
        raise SystemExit(
            "checkpoint id must contain only letters, numbers, dot, underscore, or hyphen"
        )


def validate_identifier(value: str, label: str) -> None:
    if not IDENTIFIER_RE.fullmatch(value):
        raise SystemExit(f"{label} contains unsupported characters: {value}")
