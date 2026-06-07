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
    parser.add_argument("target_dir", type=Path, help="Directory where the review pack will be created.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing files.")
    parser.add_argument("--target", default="", help="Short description of the reviewed artifact.")
    parser.add_argument(
        "--from-paper-review",
        type=Path,
        help="Seed open issues from a paper-review directory or final_issues.json file.",
    )
    return parser.parse_args()


def _severity_from_impact(value: object) -> str:
    if isinstance(value, int):
        if value >= 4:
            return "major"
        if value <= 2:
            return "minor"
    return "moderate"


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


def _seed_from_paper_review(path: Path) -> tuple[list[dict], list[str]]:
    issues_path = _paper_review_issue_path(path)
    if not issues_path.exists():
        raise SystemExit(f"paper-review issues file not found: {issues_path}")

    issues = json.loads(issues_path.read_text(encoding="utf-8"))
    if not isinstance(issues, list):
        raise SystemExit(f"paper-review issues file must contain a JSON array: {issues_path}")

    review_dir = issues_path.parent
    seeded: list[dict] = []
    for idx, issue in enumerate(issues, start=1):
        if not isinstance(issue, dict):
            continue
        impact = issue.get("impact_rating")
        confidence = issue.get("confidence_rating")
        severity = issue.get("severity") or _severity_from_impact(impact)
        seeded.append(
            {
                "id": f"PR{idx}",
                "severity": severity,
                "impact_rating": impact,
                "confidence_rating": confidence,
                "title": issue.get("title", f"Paper-review issue {idx}"),
                "status": "open",
                "evidence": issue.get("explanation", ""),
                "required_action": "Revise the artifact, add evidence, narrow the claim, or explicitly accept the risk.",
                "source_quote": issue.get("quote", ""),
                "source_section": issue.get("source_section", ""),
                "related_sections": issue.get("related_sections", []),
                "origin": str(issues_path),
            }
        )

    return seeded, _existing_support_artifacts(review_dir)


def main() -> None:
    args = parse_args()
    args.target_dir.mkdir(parents=True, exist_ok=True)

    targets = [args.target_dir / "REVIEW_STATE.json"]
    targets.extend(args.target_dir / name for name in FILE_TEMPLATES)
    existing = [path.name for path in targets if path.exists()]
    if existing and not args.force:
        raise SystemExit(
            "Refusing to overwrite existing files without --force: " + ", ".join(sorted(existing))
        )

    state = copy.deepcopy(STATE_TEMPLATE)
    state["target"] = args.target
    if args.from_paper_review:
        state["open_issues"], state["source_artifacts"] = _seed_from_paper_review(
            args.from_paper_review
        )
        state["summary"] = f"Seeded {len(state['open_issues'])} issues from paper-review artifacts."

    state_path = args.target_dir / "REVIEW_STATE.json"
    state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    print(f"created {state_path}")

    for name, content in FILE_TEMPLATES.items():
        path = args.target_dir / name
        path.write_text(content, encoding="utf-8")
        print(f"created {path}")


if __name__ == "__main__":
    main()
