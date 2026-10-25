#!/usr/bin/env python3
"""Create deterministic scaffolds for iterative research review."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path


STATE_TEMPLATE = {
    "version": "1.0",
    "target": "",
    "round": 1,
    "status": "open",
    "summary": "",
    "source_artifacts": [],
    "open_issues": [],
    "resolved_issues": [],
    "accepted_risks": [],
}

FILE_TEMPLATES = {
    "AUTO_REVIEW.md": """# Research Review Report

## Header

- Artifact:
- Version:
- Review round:
- Review date:
- Prior round artifacts:
- Source artifacts:
- Reviewer constraints:

## Executive Summary

- Bottom line:
- Major issues:
- Highest-leverage fixes:

## Claim Ledger Summary

| ID | Location | Claim | Type | Status | Evidence / fix |
| --- | --- | --- | --- | --- | --- |

## Major Issues

- ID:
- Source artifact:
- Impact / confidence:
- Location:
- Problem:
- Why it matters:
- Evidence:
- Suggested fix:

## Moderate Issues

-

## Minor Issues

- 

## Open Questions

- 
""",
    "NARRATIVE_REPORT.md": """# Narrative Review Summary

## Current Status

- Target:
- Review round:
- Overall judgment:

## Most Important Problems

- 

## What Changed Since the Last Round

- 

## What Must Happen Next

- 
""",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "target_dir",
        type=Path,
        nargs="?",
        help="Directory where the review pack will be created. Optional with --from-state, "
        "which defaults to a sibling round-<N+1>/ folder.",
    )
    parser.add_argument("--force", action="store_true", help="Overwrite existing files.")
    parser.add_argument("--target", default="", help="Short description of the reviewed artifact.")
    parser.add_argument(
        "--from-paper-review",
        type=Path,
        help="Seed open issues from a paper-review directory or final_issues.json file.",
    )
    parser.add_argument(
        "--from-state",
        type=Path,
        help="Continue from a prior REVIEW_STATE.json (or the round folder holding it): carry "
        "open, resolved, and accepted-risk entries unchanged and set round = prior + 1.",
    )
    parser.add_argument(
        "--round",
        type=int,
        dest="round_number",
        help="Explicit round number for the new state (overrides prior + 1).",
    )
    args = parser.parse_args()
    if args.target_dir is None and args.from_state is None:
        parser.error("target_dir is required unless --from-state is given")
    if args.round_number is not None and args.round_number < 1:
        parser.error("--round must be a positive integer")
    return args


REQUIRED_SEED_FIELDS = ("title", "source_quote", "evidence", "severity")

FIELD_ALIASES = {
    "title": ("title",),
    "source_quote": ("quote", "source_quote"),
    "evidence": ("explanation", "evidence"),
    "source_section": ("source_section", "section", "location"),
    "impact_rating": ("impact_rating", "impact"),
    "confidence_rating": ("confidence_rating", "confidence"),
}

SEVERITY_VALUES = {"major", "moderate", "minor"}


def _first_present(issue: dict, field: str):
    for key in FIELD_ALIASES[field]:
        value = issue.get(key)
        if value not in (None, "", []):
            return value
    return None


def _rating(value: object) -> int | None:
    """Return a 1-5 integer rating, or None for prose or out-of-range values."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int) and 1 <= value <= 5:
        return value
    return None


def _severity_from_impact(value: object) -> str | None:
    if isinstance(value, int) and not isinstance(value, bool):
        if value >= 4:
            return "major"
        if value <= 2:
            return "minor"
        return "moderate"
    return None


def _resolve_relative_artifact(path: Path, review_dir: Path) -> Path:
    if path.is_absolute():
        return path
    return (review_dir.parent.parent / path).resolve()


def _paper_review_issue_path(path: Path) -> Path:
    path = path.expanduser().resolve()
    if path.is_dir():
        return path / "final_issues.json"
    return path


def _existing_support_artifacts(review_dir: Path) -> list[str]:
    names = ["summary.md", "final_issues.json", "review_summary.json", "overall_assessment.txt"]
    artifacts = [str((review_dir / name).resolve()) for name in names if (review_dir / name).exists()]

    metadata_path = review_dir / "metadata.json"
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        metadata = None

    if isinstance(metadata, dict):
        artifacts.append(str(metadata_path.resolve()))
        round_summaries = metadata.get("round_summaries")
        if isinstance(round_summaries, dict):
            for value in round_summaries.values():
                if isinstance(value, str):
                    path = _resolve_relative_artifact(Path(value), review_dir)
                    if path.exists():
                        artifacts.append(str(path))

    for path in sorted(review_dir.glob("round-*/review_summary.json")):
        resolved = str(path.resolve())
        if resolved not in artifacts:
            artifacts.append(resolved)

    return artifacts


def _seed_from_paper_review(path: Path, taken_ids: set[str] | None = None) -> tuple[list[dict], list[str]]:
    issues_path = _paper_review_issue_path(path)
    if not issues_path.exists():
        raise SystemExit(f"paper-review issues file not found: {issues_path}")

    issues = json.loads(issues_path.read_text(encoding="utf-8"))
    if not isinstance(issues, list):
        raise SystemExit(f"paper-review issues file must contain a JSON array: {issues_path}")

    review_dir = issues_path.parent
    taken = set(taken_ids or ())
    incoming_ids = {
        str(issue["id"]) for issue in issues if isinstance(issue, dict) and issue.get("id") not in (None, "")
    }
    next_minted = 1
    seeded: list[dict] = []
    empty: dict[str, list[str]] = {}
    for idx, issue in enumerate(issues, start=1):
        if not isinstance(issue, dict):
            continue
        issue_id = issue.get("id")
        if issue_id in (None, ""):
            while f"PR{next_minted}" in taken or f"PR{next_minted}" in incoming_ids:
                next_minted += 1
            issue_id = f"PR{next_minted}"
            next_minted += 1
        issue_id = str(issue_id)
        if issue_id in taken:
            print(f"skipped {issue_id}: already tracked in the carried review state")
            continue
        taken.add(issue_id)

        impact = _rating(_first_present(issue, "impact_rating"))
        confidence = _rating(_first_present(issue, "confidence_rating"))
        severity = issue.get("severity")
        if severity not in SEVERITY_VALUES:
            severity = _severity_from_impact(impact)
        entry = {
            "id": issue_id,
            "severity": severity,
            "impact_rating": impact,
            "confidence_rating": confidence,
            "title": _first_present(issue, "title") or "",
            "status": "open",
            "evidence": _first_present(issue, "evidence") or "",
            "required_action": issue.get("required_action")
            or "Revise the artifact, add evidence, narrow the claim, or explicitly accept the risk.",
            "source_quote": _first_present(issue, "source_quote") or "",
            "source_section": _first_present(issue, "source_section") or "",
            "related_sections": issue.get("related_sections", []),
            "origin": str(issues_path),
        }
        for field in REQUIRED_SEED_FIELDS:
            if entry[field] in (None, ""):
                empty.setdefault(field, []).append(issue_id)
        seeded.append(entry)

    if empty:
        lines = [f"required issue fields resolved empty in {issues_path}:"]
        for field, ids in empty.items():
            aliases = {
                "severity": "severity (major/moderate/minor) or a 1-5 impact_rating/impact",
            }.get(field, " or ".join(FIELD_ALIASES.get(field, (field,))))
            lines.append(f"  {field} (from {aliases}): {', '.join(ids)}")
        lines.append("Fix the source issues or normalize the field names before seeding; nothing was written.")
        raise SystemExit("\n".join(lines))

    return seeded, _existing_support_artifacts(review_dir)


def _load_prior_state(path: Path) -> tuple[Path, dict]:
    path = path.expanduser().resolve()
    if path.is_dir():
        path = path / "REVIEW_STATE.json"
    if not path.exists():
        raise SystemExit(f"prior review state not found: {path}")
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"prior review state is not valid JSON: {path}: {exc}")
    if not isinstance(state, dict):
        raise SystemExit(f"prior review state must be a JSON object: {path}")
    return path, state


def _prior_round(state: dict, state_path: Path) -> int:
    value = state.get("round")
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    digits = "".join(ch for ch in state_path.parent.name if ch.isdigit())
    if digits:
        return int(digits)
    raise SystemExit(f"cannot determine the prior round number from {state_path}; pass --round")


def _next_round_dir(state_path: Path, round_number: int) -> Path:
    state_dir = state_path.parent
    base = state_dir.parent if state_dir.name.startswith("round-") else state_dir
    return base / f"round-{round_number}"


def main() -> None:
    args = parse_args()

    state = copy.deepcopy(STATE_TEMPLATE)
    prior_path: Path | None = None
    if args.from_state:
        prior_path, prior = _load_prior_state(args.from_state)
        round_number = args.round_number or _prior_round(prior, prior_path) + 1
        for key in ("open_issues", "resolved_issues", "accepted_risks"):
            value = prior.get(key, [])
            if not isinstance(value, list):
                raise SystemExit(f"prior review state field {key} must be a list: {prior_path}")
            state[key] = copy.deepcopy(value)
        state["version"] = prior.get("version", state["version"])
        state["target"] = args.target or prior.get("target", "")
        prior_sources = prior.get("source_artifacts", [])
        state["source_artifacts"] = [str(prior_path)] + [
            item for item in (prior_sources if isinstance(prior_sources, list) else []) if item != str(prior_path)
        ]
        target_dir = args.target_dir or _next_round_dir(prior_path, round_number)
    else:
        round_number = args.round_number or 1
        state["target"] = args.target
        target_dir = args.target_dir
    state["round"] = round_number

    seeded: list[dict] = []
    if args.from_paper_review:
        taken = {
            str(issue.get("id"))
            for key in ("open_issues", "resolved_issues", "accepted_risks")
            for issue in state[key]
            if isinstance(issue, dict) and issue.get("id") not in (None, "")
        }
        seeded, review_artifacts = _seed_from_paper_review(args.from_paper_review, taken)
        state["open_issues"].extend(seeded)
        for item in review_artifacts:
            if item not in state["source_artifacts"]:
                state["source_artifacts"].append(item)

    if prior_path is not None:
        state["summary"] = (
            f"Round {round_number} continues from {prior_path}: carried "
            f"{len(state['open_issues']) - len(seeded)} open, {len(state['resolved_issues'])} resolved, "
            f"and {len(state['accepted_risks'])} accepted-risk entries unchanged"
            + (f"; seeded {len(seeded)} new issues from paper-review artifacts." if seeded else ".")
        )
    elif args.from_paper_review:
        state["summary"] = f"Seeded {len(seeded)} issues from paper-review artifacts."

    targets = [target_dir / "REVIEW_STATE.json"]
    targets.extend(target_dir / name for name in FILE_TEMPLATES)
    existing = [path.name for path in targets if path.exists()]
    if existing and not args.force:
        raise SystemExit(
            "Refusing to overwrite existing files without --force: " + ", ".join(sorted(existing))
        )
    target_dir.mkdir(parents=True, exist_ok=True)

    state_path = target_dir / "REVIEW_STATE.json"
    state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    print(f"created {state_path}")

    for name, content in FILE_TEMPLATES.items():
        path = target_dir / name
        content = content.replace("- Review round:\n", f"- Review round: {round_number}\n")
        if prior_path is not None:
            content = content.replace("- Prior round artifacts:\n", f"- Prior round artifacts: {prior_path}\n")
        path.write_text(content, encoding="utf-8")
        print(f"created {path}")


if __name__ == "__main__":
    main()
