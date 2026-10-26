"""Shared decision vocabulary and claim-trajectory record for the research suite.

The canonical copy lives in research-pipeline-planner/scripts/. Byte-identical copies ship with
research-experiment-plan, research-results-auditor, and research-novelty-review so each skill
validates on its own; scripts/tests/test_shared_modules.py fails when a copy drifts. Edit the
canonical copy and copy it over. references/suite-contract.md in the planner documents the vocabulary.
"""
from __future__ import annotations

import re
from typing import Any

# The five decision kinds. Each answers a different question; none substitutes for another.
TECHNICAL_OUTCOMES = ("completed", "partial", "failed")  # did the work run as specified?
GATE_RESULTS = ("pass", "fail", "inconclusive", "not_applicable")  # what did the gate's evidence say?
VERIFIER_DECISIONS = ("approve", "revise", "block")  # does the verifier accept the submitted work?
ROUTE_ACTIONS = ("continue", "narrow", "pivot-request", "kill", "park-successor")  # where does the project go?
EVIDENCE_CLASS_ACTIONS = ("promote", "hold", "downgrade")  # what class does the evidence now carry?

# Repairs for a claim that is not yet proven, or for a gate's Revise branch. Ordered so that
# narrowing comes last: a repair that keeps the claim is considered before one that shrinks it.
REPAIR_ACTIONS = (
    "add_evidence",
    "sharpen_comparator",
    "lower_assurance",
    "reframe",
    "narrow",
    "pivot",
    "stop",
)
LEGACY_REPAIR_ALIASES = {"drop": "stop", "defer": "add_evidence"}

# How a claim changed between two versions of it.
CHANGE_CLASSES = ("precision", "qualification", "scope_narrowing", "reframing", "identity_drift")
CONTENT_CHANGING = {"scope_narrowing", "reframing", "identity_drift"}
FLOOR_STATUSES = ("unchecked", "met", "not_met")
NARROWING_REVIEW_THRESHOLD = 2

_ACTION_CELL = re.compile(r"^\s*`?([a-z_\-]+)`?\s*[:–—-]\s*(.+)$", re.S)
_PLACEHOLDERS = {"", "todo", "tbd", "n/a", "na", "none", "-", "unknown"}


def substantive(value: Any) -> bool:
    return isinstance(value, str) and value.strip().lower() not in _PLACEHOLDERS and "todo" not in value.lower()


def parse_action_text(text: Any, actions: tuple[str, ...] = REPAIR_ACTIONS) -> tuple[str | None, str]:
    """Split "`add_evidence`: run a second seed" into ("add_evidence", "run a second seed").

    Returns (None, text) when the text does not start with a known action.
    """
    if not isinstance(text, str):
        return None, ""
    match = _ACTION_CELL.match(text)
    if match and match.group(1) in actions:
        return match.group(1), match.group(2).strip()
    stripped = text.strip().strip("`")
    if stripped in actions:
        return stripped, ""
    return None, text.strip()


def check_repair(value: Any, label: str, errors: list[str], warnings: list[str]) -> str | None:
    """Validate a repair: {"action": ..., "note": ...}, a bare action, or "action: note" text.

    Legacy free text and the old drop/defer values still validate, with a warning naming the
    replacement. Returns the action, or None.
    """
    if isinstance(value, dict):
        action = value.get("action")
        if action not in REPAIR_ACTIONS:
            errors.append(f"{label}.action must be one of {list(REPAIR_ACTIONS)}")
            return None
        if "note" in value and not isinstance(value["note"], str):
            errors.append(f"{label}.note must be a string")
        return action
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{label} must name a repair action: one of {list(REPAIR_ACTIONS)}, optionally with a note")
        return None
    action, _ = parse_action_text(value)
    if action:
        return action
    legacy = LEGACY_REPAIR_ALIASES.get(value.strip())
    if legacy:
        warnings.append(f"{label}: legacy value '{value.strip()}'; write {{\"action\": \"{legacy}\", \"note\": \"...\"}}")
        return legacy
    warnings.append(
        f"{label}: free text without a repair action; start it with one of {list(REPAIR_ACTIONS)} "
        "followed by a colon, or use {\"action\": ..., \"note\": ...}"
    )
    return None


def check_trajectory(record: Any, label: str, errors: list[str]) -> str | None:
    """Validate one claim-trajectory record and return its change class.

    Required: claim_id and change_class. A change that loses content (scope_narrowing,
    reframing, identity_drift) must say what was lost, which claim-preserving alternatives were
    considered, and what evidence would restore the stronger claim. identity_drift must name the
    pivot request that carries it.
    """
    if not isinstance(record, dict):
        errors.append(f"{label} must be an object")
        return None
    if not substantive(record.get("claim_id")):
        errors.append(f"{label}.claim_id must name the claim that changed")
    change_class = record.get("change_class")
    if change_class not in CHANGE_CLASSES:
        errors.append(f"{label}.change_class must be one of {list(CHANGE_CLASSES)}")
        return None
    if change_class in CONTENT_CHANGING:
        if not substantive(record.get("content_lost")):
            errors.append(f"{label}.content_lost must say what scientific content the change gives up")
        alternatives = record.get("alternatives_considered")
        if not isinstance(alternatives, list) or not any(substantive(item) for item in alternatives):
            errors.append(
                f"{label}.alternatives_considered must list the claim-preserving repairs tried or rejected "
                f"(for example {', '.join(REPAIR_ACTIONS[:4])})"
            )
        if not substantive(record.get("restoring_evidence")):
            errors.append(f"{label}.restoring_evidence must say what evidence would restore the stronger claim")
    else:
        for field in ("content_lost", "restoring_evidence"):
            if field in record and not isinstance(record[field], str):
                errors.append(f"{label}.{field} must be a string")
        if "alternatives_considered" in record and not isinstance(record["alternatives_considered"], list):
            errors.append(f"{label}.alternatives_considered must be a list")
    if change_class == "identity_drift" and not substantive(record.get("pivot_request")):
        errors.append(f"{label}: identity_drift must name the pivot_request that carries it (D3 or D4)")
    return change_class


def check_contribution_floor(floor: Any, label: str, errors: list[str]) -> None:
    """The least contribution worth publishing, stated so that it can fail."""
    if not isinstance(floor, dict):
        errors.append(f"{label} must be an object")
        return
    if not substantive(floor.get("statement")):
        errors.append(f"{label}.statement must state the least contribution that still justifies the paper")
    if not substantive(floor.get("non_vacuity_outcome")):
        errors.append(
            f"{label}.non_vacuity_outcome must name an observable result that would show the floor is not met"
        )
    invariants = floor.get("invariants", [])
    if not isinstance(invariants, list) or any(not substantive(item) for item in invariants):
        errors.append(f"{label}.invariants must be a list of substantive strings (properties any narrowed claim keeps)")
    if floor.get("status", "unchecked") not in FLOOR_STATUSES:
        errors.append(f"{label}.status must be one of {list(FLOOR_STATUSES)}")


def narrowings_needing_review(history: Any) -> dict[str, int]:
    """Claims narrowed at least twice with no project-level review after the latest narrowing.

    A project review is a selection_history entry {"decision": "project-review", "claim_id": ...}.
    """
    counts: dict[str, int] = {}
    reviewed_after: dict[str, bool] = {}
    for entry in history if isinstance(history, list) else []:
        if not isinstance(entry, dict):
            continue
        trajectory = entry.get("trajectory")
        if isinstance(trajectory, dict) and trajectory.get("change_class") == "scope_narrowing":
            claim = str(trajectory.get("claim_id"))
            counts[claim] = counts.get(claim, 0) + 1
            reviewed_after[claim] = False
        elif entry.get("decision") == "project-review" and entry.get("claim_id") is not None:
            reviewed_after[str(entry["claim_id"])] = True
    return {
        claim: count
        for claim, count in counts.items()
        if count >= NARROWING_REVIEW_THRESHOLD and not reviewed_after.get(claim)
    }
