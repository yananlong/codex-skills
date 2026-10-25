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


FAMILIES = ("openaireview_claude", "codex_native", "review_loop_hybrid")


def _round_number(value: object) -> int:
    text = str(value)
    digits = "".join(ch for ch in text if ch.isdigit())
    return int(digits) if digits else -1


def _resolve_metadata_path(review_dir: Path, value: str) -> Path:
    path = Path(value).expanduser()
    if path.is_absolute():
        return path
    bases = (review_dir, review_dir.parent, review_dir.parent.parent)
    for base in bases:
        if (base / path).exists():
            return base / path
    return review_dir / path


def _round_dirs(review_dir: Path) -> list[Path]:
    """Round folders inside the review dir and next to it (sibling layout)."""
    found: list[Path] = []
    for base in (review_dir, review_dir.parent):
        for path in sorted(base.glob("round-*")):
            if path.is_dir() and path.resolve() != review_dir and path not in found:
                found.append(path)
    return found


def _round_summary_candidates(review_dir: Path) -> list[tuple[int, str, Path]]:
    """Return (round number, source, path) for every round summary, newest first."""
    candidates: list[tuple[int, str, Path]] = []
    seen: set[Path] = set()

    def add(round_no: int, source: str, path: Path) -> None:
        key = path.resolve()
        if key not in seen:
            seen.add(key)
            candidates.append((round_no, source, path))

    metadata = _load_json_optional(review_dir / "metadata.json")
    if isinstance(metadata, dict):
        round_summaries = metadata.get("round_summaries")
        if isinstance(round_summaries, dict):
            for key, value in round_summaries.items():
                if isinstance(value, str):
                    add(_round_number(key), "metadata.round_summaries", _resolve_metadata_path(review_dir, value))

    for round_dir in _round_dirs(review_dir):
        source = "round dir" if round_dir.parent.resolve() == review_dir else "sibling round dir"
        path = round_dir / "review_summary.json"
        if path.exists():
            add(_round_number(round_dir.name), source, path)

    # Stable sort: newest round first, metadata entries before globbed ones on ties.
    candidates.sort(key=lambda item: item[0], reverse=True)
    return candidates


def _summary_errors(summary, label: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(summary, dict):
        return [f"{label} is missing, unreadable, or not a JSON object"]
    missing = sorted(REQUIRED_SUMMARY_KEYS - set(summary))
    if missing:
        return [f"{label} missing required keys: {', '.join(missing)}"]
    for key in ("overall_paper_rating", "decision_relevance_rating", "rating_confidence"):
        _check_rating(summary.get(key), f"{label}.{key}", errors)
    if not isinstance(summary.get("top_blockers"), list):
        errors.append(f"{label}.top_blockers must be a list")
    return errors


def _resolve_round_summary(review_dir: Path) -> tuple[Path | None, list[str], list[str]]:
    """Pick the newest round summary that exists; it must validate.

    Returns (path, skipped, errors). A candidate whose file is missing (a stale metadata
    entry) is skipped and the next newest is tried. A candidate that exists but is malformed is
    an error, never a reason to validate the bundle against an older round's summary.
    """
    skipped: list[str] = []
    for round_no, source, path in _round_summary_candidates(review_dir):
        if not path.exists():
            skipped.append(f"{path} ({source}): file not found")
            continue
        problems = _summary_errors(_load_json_optional(path), path.name)
        if problems:
            return None, skipped, [f"newest round summary {path} ({source}) is invalid: {'; '.join(problems)}"]
        return path, skipped, []
    return None, skipped, []


def _issue_schema(final_issues) -> tuple[bool, bool]:
    if not isinstance(final_issues, list):
        return False, False
    has_ratings = any(
        isinstance(issue, dict) and set(REQUIRED_RATING_KEYS).issubset(issue) for issue in final_issues
    )
    has_severity = any(isinstance(issue, dict) and "severity" in issue for issue in final_issues)
    return has_ratings, has_severity


def _loop_evidence(review_dir: Path) -> list[str]:
    evidence: list[str] = []
    metadata = _load_json_optional(review_dir / "metadata.json")
    if isinstance(metadata, dict):
        if isinstance(metadata.get("review_loop"), dict):
            evidence.append("metadata.review_loop")
        if isinstance(metadata.get("round_summaries"), dict):
            evidence.append("metadata.round_summaries")
    for round_dir in _round_dirs(review_dir):
        if (round_dir / "REVIEW_STATE.json").exists() or (round_dir / "review_summary.json").exists():
            where = "round dir" if round_dir.parent.resolve() == review_dir else "sibling round dir"
            evidence.append(f"{where} {round_dir.name}")
    return evidence


def infer_family(review_dir: Path, final_issues) -> tuple[str, list[str]]:
    """Infer the provenance family using the rules in SKILL.md."""
    evidence: list[str] = []
    metadata = _load_json_optional(review_dir / "metadata.json")
    if isinstance(metadata, dict) and isinstance(metadata.get("review_mode"), str):
        evidence.append(f"metadata.review_mode={metadata['review_mode']}")
    has_ratings, has_severity = _issue_schema(final_issues)
    if has_ratings:
        evidence.append("1-5 issue ratings")
    if has_severity:
        evidence.append("severity-tiered issues")
    loop = _loop_evidence(review_dir)
    evidence.extend(loop)

    if (review_dir / "review_summary.json").exists():
        evidence.append("root review_summary.json")
        return "codex_native", evidence
    if loop:
        return "review_loop_hybrid", evidence
    if has_severity:
        return "openaireview_claude", evidence
    if has_ratings:
        return "codex_native", evidence
    return "unknown", evidence


def _check_issues(final_issues, family: str, errors: list[str]) -> None:
    if not isinstance(final_issues, list):
        if final_issues is not None:
            errors.append("final_issues.json must be a JSON array")
        return
    for idx, issue in enumerate(final_issues, start=1):
        label = f"final_issues.json[{idx}]"
        if not isinstance(issue, dict):
            errors.append(f"{label} must be an object")
            continue
        missing = sorted(REQUIRED_ISSUE_KEYS - set(issue))
        if missing:
            errors.append(f"{label} missing required keys: {', '.join(missing)}")
            continue
        has_ratings = REQUIRED_RATING_KEYS.issubset(issue)
        severity = issue.get("severity")
        if "severity" in issue and severity not in SEVERITY_VALUES:
            errors.append(f"{label}.severity must be one of {', '.join(sorted(SEVERITY_VALUES))}")
        if has_ratings:
            _check_rating(issue.get("impact_rating"), f"{label}.impact_rating", errors)
            _check_rating(issue.get("confidence_rating"), f"{label}.confidence_rating", errors)
        missing_ratings = ", ".join(sorted(REQUIRED_RATING_KEYS - set(issue)))
        if family == "codex_native" and not has_ratings:
            errors.append(f"{label} missing required rating keys: {missing_ratings}")
        elif family == "openaireview_claude" and "severity" not in issue:
            errors.append(f"{label} missing required key for openaireview_claude: severity")
        elif family in ("review_loop_hybrid", "unknown") and not has_ratings and "severity" not in issue:
            errors.append(f"{label} needs either severity or rating keys: {missing_ratings}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review-dir", required=True, help="Path to the paper-review workspace")
    parser.add_argument(
        "--family",
        choices=FAMILIES,
        help="Assert a provenance family and validate against its required file set "
        "instead of the inferred one.",
    )
    parser.add_argument(
        "--strict-native",
        action="store_true",
        help="Same as --family codex_native: require root review_summary.json and 1-5 issue ratings.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    review_dir = Path(args.review_dir).expanduser().resolve()
    errors: list[str] = []
    notes: list[str] = []

    final_issues = _load_json(review_dir / "final_issues.json", "final_issues.json", errors)
    inferred, evidence = infer_family(review_dir, final_issues)
    asserted = args.family
    if args.strict_native:
        if asserted and asserted != "codex_native":
            errors.append("--strict-native conflicts with --family " + asserted)
        asserted = "codex_native"
    family = asserted or inferred

    print(f"Inferred family: {inferred}")
    print("Evidence: " + (", ".join(evidence) if evidence else "none"))
    if asserted:
        print(f"Asserted family: {asserted}")

    for name in sorted(REQUIRED_FILES - {"final_issues.json"}):
        if not (review_dir / name).exists():
            errors.append(f"missing required file: {review_dir / name}")
    sections_index = review_dir / "sections" / "index.json"
    if not sections_index.exists():
        errors.append(f"missing required file: {sections_index}")

    _check_issues(final_issues, family, errors)

    summary_path: Path | None = None
    root_summary = review_dir / "review_summary.json"
    if family == "openaireview_claude":
        if root_summary.exists():
            errors.append(
                "openaireview_claude bundles carry no root review_summary.json; "
                f"found {root_summary} (validate as codex_native instead)"
            )
    elif family == "codex_native":
        if not root_summary.exists():
            errors.append(f"missing required file for codex_native: {root_summary}")
        else:
            summary_path = root_summary
            errors.extend(_summary_errors(_load_json_optional(root_summary), "review_summary.json"))
    elif family == "review_loop_hybrid":
        summary_path, skipped, summary_errors = _resolve_round_summary(review_dir)
        notes.extend(f"skipped round summary {item}" for item in skipped)
        errors.extend(summary_errors)
        if summary_path is None and not summary_errors:
            errors.append(
                "review_loop_hybrid needs a resolvable valid round summary: none of "
                "metadata.round_summaries, <review_dir>/round-*/review_summary.json, or "
                "<review_dir>/../round-*/review_summary.json validated"
            )
    else:
        errors.append(
            "could not infer a provenance family: final_issues.json has neither severity nor "
            "1-5 ratings and there is no review_summary.json or round folder; pass --family"
        )

    for note in notes:
        print(f"Note: {note}")

    if errors:
        print("Validation failed:")
        for err in errors:
            print(f"- {err}")
        if family == "review_loop_hybrid" and not asserted:
            print(
                "Hint: to validate only the first-pass bundle, rerun with "
                "--family openaireview_claude (severity issues) or --family codex_native."
            )
        return 1

    print(f"Validation passed: {family} review bundle is structurally consistent.")
    if summary_path is not None:
        print(f"Summary artifact: {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
