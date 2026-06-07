#!/usr/bin/env python3
"""Validate deep-review handoff bundles and compatible imported layouts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


REQUIRED_FILES = {
    "summary.md",
    "final_issues.json",
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
}

REQUIRED_RATING_KEYS = {
    "impact_rating",
    "confidence_rating",
}

SEVERITY_VALUES = {"major", "moderate", "minor"}


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


def _load_json_optional(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def _round_number(value: object) -> int:
    text = str(value)
    digits = "".join(ch for ch in text if ch.isdigit())
    return int(digits) if digits else -1


def _round_summary_candidates(review_dir: Path) -> list[Path]:
    candidates: list[Path] = []
    metadata = _load_json_optional(review_dir / "metadata.json")
    if isinstance(metadata, dict):
        round_summaries = metadata.get("round_summaries")
        if isinstance(round_summaries, dict):
            sorted_items = sorted(
                round_summaries.items(), key=lambda item: _round_number(item[0]), reverse=True
            )
            for _, value in sorted_items:
                if isinstance(value, str):
                    path = Path(value)
                    if not path.is_absolute():
                        path = review_dir.parent.parent / path
                    candidates.append(path)

    sorted_round_paths = sorted(
        review_dir.glob("round-*/review_summary.json"),
        key=lambda path: _round_number(path.parent.name),
        reverse=True,
    )
    for path in sorted_round_paths:
        candidates.append(path)
    return candidates


def _resolve_review_summary(review_dir: Path) -> tuple[Path | None, dict | None]:
    root_summary = review_dir / "review_summary.json"
    if root_summary.exists():
        summary = _load_json_optional(root_summary)
        return root_summary, summary if isinstance(summary, dict) else None

    for path in _round_summary_candidates(review_dir):
        if path.exists():
            summary = _load_json_optional(path)
            if isinstance(summary, dict):
                return path, summary
    return None, None


def _infer_provenance(review_dir: Path, final_issues) -> list[str]:
    provenance: list[str] = []
    metadata = _load_json_optional(review_dir / "metadata.json")
    if isinstance(metadata, dict):
        review_mode = metadata.get("review_mode")
        if isinstance(review_mode, str):
            provenance.append(f"metadata.review_mode={review_mode}")
        if isinstance(metadata.get("review_loop"), dict) or isinstance(
            metadata.get("round_summaries"), dict
        ):
            provenance.append("review_loop_metadata")

    if (review_dir / "review_summary.json").exists():
        provenance.append("codex_native_review_summary")
    if any(review_dir.glob("round-*/REVIEW_STATE.json")):
        provenance.append("round_snapshot_layout")

    if isinstance(final_issues, list):
        has_impact = any(
            isinstance(issue, dict)
            and {"impact_rating", "confidence_rating"}.issubset(issue)
            for issue in final_issues
        )
        has_severity = any(isinstance(issue, dict) and "severity" in issue for issue in final_issues)
        if has_impact:
            provenance.append("codex_rating_schema")
        if has_severity:
            provenance.append("openaireview_severity_schema")

    return provenance or ["unknown"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review-dir", required=True, help="Path to the paper-review workspace")
    parser.add_argument(
        "--strict-native",
        action="store_true",
        help="Require the Codex-native root review_summary.json and 1-5 issue ratings.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    review_dir = Path(args.review_dir).expanduser().resolve()
    errors: list[str] = []

    required_files = set(REQUIRED_FILES)
    if args.strict_native:
        required_files.add("review_summary.json")

    for name in sorted(required_files):
        if not (review_dir / name).exists():
            errors.append(f"missing required file: {review_dir / name}")

    sections_index = review_dir / "sections" / "index.json"
    if not sections_index.exists():
        errors.append(f"missing required file: {sections_index}")

    final_issues = _load_json(review_dir / "final_issues.json", "final_issues.json", errors)
    summary_path, review_summary = _resolve_review_summary(review_dir)
    if review_summary is None:
        errors.append(
            "missing required summary: provide review_summary.json at the review root "
            "or a resolvable round-N/review_summary.json recorded in metadata.json"
        )

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
            missing_ratings = sorted(REQUIRED_RATING_KEYS - set(issue))
            if missing_ratings:
                severity = issue.get("severity")
                if args.strict_native or severity not in SEVERITY_VALUES:
                    errors.append(
                        f"final_issues.json[{idx}] missing required rating keys: "
                        f"{', '.join(missing_ratings)}"
                    )
            else:
                _check_rating(
                    issue.get("impact_rating"), f"final_issues.json[{idx}].impact_rating", errors
                )
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
    if summary_path is not None:
        print(f"Summary artifact: {summary_path}")
    print("Inferred provenance: " + ", ".join(_infer_provenance(review_dir, final_issues)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
