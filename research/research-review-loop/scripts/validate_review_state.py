#!/usr/bin/env python3
"""Validate a review-loop REVIEW_STATE.json against the canonical review-issue schema.

The default mode reads any known state layout through review_schema.py. Aliased field names,
issues kept in extra *_issues lists, closed entries that only reference an earlier issue, and
missing top-level fields are warnings. Errors are what blocks routing: an open issue with no title
or no severity, a duplicate issue id, an unknown status, or a file that is not a review state.

--strict checks a state written in the canonical schema (references/review-state-schema.md): every
top-level field present, canonical field names only, issues only in open_issues, resolved_issues,
and accepted_risks, and every warning above becomes an error. init_review_loop.py writes states
that pass --strict.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from review_schema import (
    ISSUE_FIELDS,
    ISSUE_STATUSES,
    STATE_ISSUE_LISTS,
    STATE_STATUSES,
    issues_from_state,
)

TOP_LEVEL = ("version", "target", "round", "status", "summary", "source_artifacts",
             "open_issues", "resolved_issues", "accepted_risks")


def validate_state(state: object, *, strict: bool = False) -> tuple[list[str], list[str], str]:
    """Return (errors, warnings, layout)."""
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(state, dict):
        return ["REVIEW_STATE.json must hold a JSON object"], warnings, "unknown"
    soft = errors if strict else warnings

    missing = [key for key in TOP_LEVEL if key not in state]
    if missing:
        soft.append("missing top-level fields: " + ", ".join(missing))
    round_value = state.get("round")
    if "round" in state and (isinstance(round_value, bool) or not isinstance(round_value, int) or round_value < 1):
        soft.append("round must be a positive integer")
    if "status" in state and state.get("status") not in STATE_STATUSES:
        soft.append(f"status must be one of {list(STATE_STATUSES)}")
    for key in STATE_ISSUE_LISTS:
        if key in state and not isinstance(state[key], list):
            errors.append(f"{key} must be a list")

    layout, issues = issues_from_state(state)
    if layout == "review_state_without_issues":
        soft.append("no issue lists: the state records no open, resolved, or accepted issues")
    elif layout == "review_loop_state_extended":
        extra_lists = sorted({issue.get("extra", {}).get("source_list") for issue in issues} - {None})
        soft.append("issues kept outside open_issues/resolved_issues/accepted_risks: " + ", ".join(extra_lists))

    if strict:
        for key in STATE_ISSUE_LISTS:
            for index, raw in enumerate(state.get(key) or [], 1):
                if isinstance(raw, dict):
                    unknown = sorted(set(raw) - set(ISSUE_FIELDS) - {"extra"})
                    if unknown:
                        errors.append(
                            f"{key}[{index}]: fields outside the canonical issue schema: {', '.join(unknown)}; "
                            "move them under extra"
                        )

    seen: dict[tuple[str, str], str] = {}
    for index, issue in enumerate(issues, 1):
        label = f"issue {issue.get('id') or f'#{index}'}"
        for problem in issue["_problems"]:
            if problem.startswith("status "):
                soft.append(f"{label}: {problem}")
            elif issue.get("status") == "open":
                errors.append(f"{label}: {problem}")
            else:
                soft.append(f"{label}: {problem}")
        for note in issue["_notes"]:
            # The canonical schema allows a closed entry that only references an earlier issue.
            warnings.append(f"{label}: {note}")
        if issue.get("status") not in ISSUE_STATUSES:
            errors.append(f"{label}: status must be one of {list(ISSUE_STATUSES)}")
        aliases = {field: key for field, key in issue["_aliases"].items() if not key.startswith("same id")}
        if aliases:
            soft.append(f"{label}: legacy field names " + ", ".join(f"{key} -> {field}" for field, key in sorted(aliases.items())))
        issue_id = issue.get("id")
        if issue_id in (None, ""):
            soft.append(f"{label}: no id; ids must stay stable across rounds")
            continue
        key = str(issue_id)
        list_name = issue.get("_list") or "issues"
        if (key, list_name) in seen:
            errors.append(f"duplicate issue id {key} in {list_name}")
        seen[(key, list_name)] = list_name
    return errors, warnings, layout


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("state", type=Path, help="REVIEW_STATE.json, or the round folder that holds it")
    parser.add_argument("--strict", action="store_true", help="Require the canonical schema exactly.")
    args = parser.parse_args()
    path = args.state.expanduser()
    if path.is_dir():
        path = path / "REVIEW_STATE.json"
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"Validation failed:\n- missing file: {path}")
        return 1
    except json.JSONDecodeError as exc:
        print(f"Validation failed:\n- {path} is not valid JSON: {exc}")
        return 1
    errors, warnings, layout = validate_state(state, strict=args.strict)
    print(f"Layout: {layout}")
    if errors:
        print("Validation failed:")
        for error in errors:
            print(f"- {error}")
    else:
        mode = "canonical schema" if args.strict else "canonical schema after normalisation"
        print(f"Validation passed: {path} matches the {mode}.")
    if warnings:
        print("Warnings:")
        for warning in warnings:
            print(f"- {warning}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
