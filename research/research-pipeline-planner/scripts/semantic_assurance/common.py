from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Iterable

DRIFT_RANK = {"D0": 0, "D1": 1, "D2": 2, "D3": 3, "D4": 4}
ASSURANCE_RANK = {"none": 0, "exploratory": 1, "confirmatory": 2, "independently_verified": 3, "operational_high_stakes": 4}
ACTIVE_WORK_STATUSES = {"queued", "ready", "running", "awaiting_verification", "verification", "paused", "blocked"}
D3_FIELDS = {"contribution_class"}
IDENTITY_ANCHOR_FIELDS = {"main_question": "question", "central_object_or_phenomenon": "central_object", "primary_evidence_obligation": "evidence_obligation"}
D2_FIELDS = {"minimum_publishable_claim", "intended_audience", "permitted_refinements", "next_mandatory_evidence_artifact", "reconsideration_gate"}
IGNORED_DIFF_FIELDS = {"schema_version", "status", "identity_version", "selection_history", "last_change_class", "last_change_rationale"}
REQUIRED_PERSPECTIVES = {"direct-method-or-phenomenon", "strongest-competing-formulation", "negative-or-null-evidence", "foundational-ancestry", "recent-frontier", "methodological-validity", "benchmark-or-dataset-lineage", "reproducibility-or-implementation", "venue-and-author-lab-clusters"}
DEFAULT_CRITICAL_PERSPECTIVES = {"direct-method-or-phenomenon", "strongest-competing-formulation", "negative-or-null-evidence", "foundational-ancestry", "recent-frontier"}
REQUIRED_SEED_CLASSES = {"foundational", "closest-recent", "competing-or-critical"}
ALLOWED_EXCLUSION_CLASSES = {"corrupted-input", "executor-failure-before-measurement", "protocol-ineligible-configuration", "duplicate-logical-attempt", "invalid-hidden-truth-boundary"}
ADVERSE_OUTCOMES = {"negative", "null", "contradictory"}
SCOPE_DIMENSIONS = {"population", "environment", "intervention", "comparator", "outcomes", "time_or_version", "exclusions"}
IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,191}$")

def meaningful(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())

def load_json(path: Path, label: str, errors: list[str]) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(f"missing {label}: {path}")
    except json.JSONDecodeError as exc:
        errors.append(f"invalid JSON in {label}: {exc}")
    return None

def load_text(path: Path, label: str, errors: list[str]) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        errors.append(f"missing {label}: {path}")
        return ""

def canonical_digest(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()

def validate_id(value: Any, label: str, errors: list[str]) -> str:
    if not meaningful(value) or not IDENTIFIER_RE.fullmatch(str(value)):
        errors.append(f"{label} must be a stable identifier")
        return ""
    return str(value)

def parse_markdown_table(text: str, heading_names: Iterable[str]) -> tuple[list[str], list[dict[str, str]]]:
    lines = text.splitlines()
    heading_index: int | None = None
    names = set(heading_names)
    for index, line in enumerate(lines):
        if line.strip() in names:
            heading_index = index
            break
    if heading_index is None:
        return [], []
    table_start: int | None = None
    for index in range(heading_index + 1, len(lines)):
        stripped = lines[index].strip()
        if stripped.startswith("#"):
            break
        if stripped.startswith("|") and stripped.endswith("|"):
            table_start = index
            break
    if table_start is None or table_start + 1 >= len(lines):
        return [], []
    headers = [cell.strip() for cell in lines[table_start].strip("|").split("|")]
    rows: list[dict[str, str]] = []
    for line in lines[table_start + 2 :]:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            if rows:
                break
            continue
        if not (stripped.startswith("|") and stripped.endswith("|")):
            if rows:
                break
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if len(cells) == len(headers) and any(cells):
            rows.append(dict(zip(headers, cells)))
    return headers, rows

def split_ids(value: Any) -> set[str]:
    if not isinstance(value, str):
        return set()
    return {part.strip() for part in re.split(r"[,;]", value) if part.strip()}

def print_result(errors: list[str], success: str) -> int:
    if errors:
        print("Validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print(success)
    return 0
