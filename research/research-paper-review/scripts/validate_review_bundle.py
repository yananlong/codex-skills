#!/usr/bin/env python3
"""Validate deep-review handoff bundles and 1-5 rating fields."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


REQUIRED_FILES = {
    "summary.md",
    "final_issues.json",
    "review_summary.json",
    "overall_assessment.txt",
    "metadata.json",
    "full_text.md",
}

REQUIRED_SUMMARY_KEYS = {
    "overall_paper_rating",
    "decision_relevance_rating",
    "rating_confidence",
    "top_blockers",
}

REQUIRED_ISSUE_KEYS = {
    "title",
    "quote",
    "explanation",
    "comment_type",
    "impact_rating",
    "confidence_rating",
}


def _load_json(path: Path, label: str, errors: list[str]):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(f"missing required file: {path}")
    except json.JSONDecodeError as exc:
        errors.append(f"{label} is not valid JSON: {exc}")
    return None


def _check_rating(value, label: str, errors: list[str]) -> None:
    if not isinstance(value, int) or value < 1 or value > 5:
        errors.append(f"{label} must be an integer in [1, 5]")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review-dir", required=True, help="Path to the paper-review workspace")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    review_dir = Path(args.review_dir).expanduser().resolve()
    errors: list[str] = []

    for name in sorted(REQUIRED_FILES):
        if not (review_dir / name).exists():
            errors.append(f"missing required file: {review_dir / name}")

    sections_index = review_dir / "sections" / "index.json"
    if not sections_index.exists():
        errors.append(f"missing required file: {sections_index}")

    final_issues = _load_json(review_dir / "final_issues.json", "final_issues.json", errors)
    review_summary = _load_json(review_dir / "review_summary.json", "review_summary.json", errors)

    if isinstance(final_issues, list):
        for idx, issue in enumerate(final_issues, start=1):
            if not isinstance(issue, dict):
                errors.append(f"final_issues.json[{idx}] must be an object")
                continue
            missing = sorted(REQUIRED_ISSUE_KEYS - set(issue))
            if missing:
                errors.append(
                    f"final_issues.json[{idx}] missing required keys: {', '.join(missing)}"
                )
                continue
            _check_rating(issue.get("impact_rating"), f"final_issues.json[{idx}].impact_rating", errors)
            _check_rating(
                issue.get("confidence_rating"),
                f"final_issues.json[{idx}].confidence_rating",
                errors,
            )

    if isinstance(review_summary, dict):
        missing = sorted(REQUIRED_SUMMARY_KEYS - set(review_summary))
        if missing:
            errors.append(f"review_summary.json missing required keys: {', '.join(missing)}")
        else:
            _check_rating(
                review_summary.get("overall_paper_rating"),
                "review_summary.json.overall_paper_rating",
                errors,
            )
            _check_rating(
                review_summary.get("decision_relevance_rating"),
                "review_summary.json.decision_relevance_rating",
                errors,
            )
            _check_rating(
                review_summary.get("rating_confidence"),
                "review_summary.json.rating_confidence",
                errors,
            )
            if not isinstance(review_summary.get("top_blockers"), list):
                errors.append("review_summary.json.top_blockers must be a list")

    if errors:
        print("Validation failed:")
        for err in errors:
            print(f"- {err}")
        return 1

    print("Validation passed: review bundle is structurally consistent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
