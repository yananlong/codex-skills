#!/usr/bin/env python3
"""Validate tracked research ideation packs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


REQUIRED_MARKDOWN_HEADINGS = {
    "landscape-map.md": [
        "# Landscape Map",
        "## Scope",
        "## Existing Context Used",
        "## Subareas and Active Approaches",
        "## Closest Work",
        "## Gap Inventory",
        "## Search and Source Limits",
    ],
    "idea-bank.md": [
        "# Idea Bank",
        "## Generation Setup",
        "## Candidate Ideas",
    ],
    "selected-idea.md": [
        "# Selected Idea",
        "## Recommendation",
        "## Idea Summary",
        "## Differentiation",
        "## Minimum Validation",
        "## Risks and Blocking Questions",
        "## Handoff Notes",
    ],
    "rejected-ideas.md": [
        "# Rejected Ideas",
        "## Rejection Categories",
    ],
}

SCORE_FIELDS = {
    "clarity",
    "novelty_signal",
    "feasibility",
    "testability",
    "significance",
}
IDEA_STATUSES = {"selected", "shortlisted", "rejected", "needs_research"}
RISKS = {"low", "medium", "high"}
EFFORTS = {"hours", "days", "weeks", "months"}
CONTRIBUTION_TYPES = {
    "method",
    "empirical",
    "theory",
    "diagnostic",
    "dataset",
    "benchmark",
    "tooling",
    "mixed",
}
DECISIONS = {"proceed_to_novelty_review", "revise_scope", "generate_more", "stop"}
NEXT_SKILLS = {
    None,
    "research-novelty-review",
    "research-systematic-literature-review",
    "research-experiment-plan",
    "research-pipeline-planner",
}


def read_text(path: Path, label: str, errors: list[str]) -> str:
    if not path.exists():
        errors.append(f"missing {label}: {path}")
        return ""
    return path.read_text(encoding="utf-8")


def load_json(path: Path, label: str, errors: list[str]):
    if not path.exists():
        errors.append(f"missing {label}: {path}")
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"{label} is not valid JSON: {exc}")
        return None


def validate_markdown(root: Path, errors: list[str]) -> None:
    for name, headings in REQUIRED_MARKDOWN_HEADINGS.items():
        content = read_text(root / name, name, errors)
        for heading in headings:
            if content and heading not in content:
                errors.append(f"{name}: missing heading '{heading}'")


def validate_scores(data, allow_empty: bool, errors: list[str]) -> set[str]:
    if not isinstance(data, dict):
        errors.append("idea-scores.json must be an object")
        return set()
    ideas = data.get("ideas")
    if not isinstance(ideas, list):
        errors.append("idea-scores.json.ideas must be a list")
        return set()
    if not allow_empty and not ideas:
        errors.append("idea-scores.json.ideas must contain at least one idea")
        return set()

    ids: set[str] = set()
    for idx, idea in enumerate(ideas, start=1):
        label = f"idea-scores.json.ideas[{idx}]"
        if not isinstance(idea, dict):
            errors.append(f"{label} must be an object")
            continue
        idea_id = idea.get("idea_id")
        if not isinstance(idea_id, str) or not idea_id.strip():
            errors.append(f"{label}.idea_id must be a non-empty string")
        elif idea_id in ids:
            errors.append(f"duplicate idea_id: {idea_id}")
        else:
            ids.add(idea_id)

        for field in ("title", "summary", "hypothesis", "minimum_validation", "differentiation", "rationale"):
            if not isinstance(idea.get(field), str) or not idea.get(field, "").strip():
                errors.append(f"{label}.{field} must be a non-empty string")

        if idea.get("contribution_type") not in CONTRIBUTION_TYPES:
            errors.append(f"{label}.contribution_type must be one of {sorted(CONTRIBUTION_TYPES)}")
        if idea.get("risk") not in RISKS:
            errors.append(f"{label}.risk must be one of {sorted(RISKS)}")
        if idea.get("estimated_effort") not in EFFORTS:
            errors.append(f"{label}.estimated_effort must be one of {sorted(EFFORTS)}")
        if idea.get("status") not in IDEA_STATUSES:
            errors.append(f"{label}.status must be one of {sorted(IDEA_STATUSES)}")

        scores = idea.get("scores")
        if not isinstance(scores, dict):
            errors.append(f"{label}.scores must be an object")
        else:
            missing = SCORE_FIELDS - set(scores)
            if missing:
                errors.append(f"{label}.scores missing fields: {', '.join(sorted(missing))}")
            for score_name in SCORE_FIELDS:
                value = scores.get(score_name)
                if not isinstance(value, int) or value < 1 or value > 5:
                    errors.append(f"{label}.scores.{score_name} must be an integer from 1 to 5")

        for list_field in ("closest_work", "blocking_questions"):
            if not isinstance(idea.get(list_field), list):
                errors.append(f"{label}.{list_field} must be a list")
    return ids


def validate_decision(data, idea_ids: set[str], allow_empty: bool, errors: list[str]) -> None:
    if not isinstance(data, dict):
        errors.append("ideation-decision.json must be an object")
        return
    decision = data.get("decision")
    if decision not in DECISIONS:
        errors.append(f"ideation-decision.json.decision must be one of {sorted(DECISIONS)}")
    selected = data.get("selected_idea_ids")
    if not isinstance(selected, list):
        errors.append("ideation-decision.json.selected_idea_ids must be a list")
        selected = []
    unknown = [idea_id for idea_id in selected if idea_id not in idea_ids]
    if unknown and not allow_empty:
        errors.append("ideation-decision.json.selected_idea_ids reference unknown ideas: " + ", ".join(unknown))
    if decision == "proceed_to_novelty_review" and not selected:
        errors.append("proceed_to_novelty_review requires at least one selected idea")
    if data.get("next_skill") not in NEXT_SKILLS:
        errors.append(f"ideation-decision.json.next_skill must be one of {sorted(str(x) for x in NEXT_SKILLS)}")
    if not isinstance(data.get("rationale"), str):
        errors.append("ideation-decision.json.rationale must be a string")
    for list_field in ("required_handoffs", "limits"):
        if not isinstance(data.get(list_field), list):
            errors.append(f"ideation-decision.json.{list_field} must be a list")
    if decision == "stop" and not data.get("limits"):
        errors.append("stop decisions must include at least one limit")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pack_dir", type=Path, help="Directory containing ideation artifacts.")
    parser.add_argument("--allow-empty", action="store_true", help="Allow an initialized pack with no scored ideas.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.pack_dir.expanduser().resolve()
    errors: list[str] = []

    validate_markdown(root, errors)
    scores = load_json(root / "idea-scores.json", "idea-scores.json", errors)
    decision = load_json(root / "ideation-decision.json", "ideation-decision.json", errors)
    idea_ids = validate_scores(scores, args.allow_empty, errors) if scores is not None else set()
    if decision is not None:
        validate_decision(decision, idea_ids, args.allow_empty, errors)

    if errors:
        print("Validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Validation passed: ideation pack is structurally consistent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
