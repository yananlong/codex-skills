#!/usr/bin/env python3
"""Run the packaged OpenAIReview viz-json helper with runtime-labelled defaults."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from _engine import DEFAULT_VENV, run_packaged_skill_script


DEFAULT_RUNTIME = "agent"


def method_key(runtime: str) -> str:
    return f"openaireview__{runtime}"


def method_label(runtime: str) -> str:
    return f"OpenAIReview ({runtime})"


def _impact_to_severity(value: object) -> str:
    if isinstance(value, int):
        if value >= 4:
            return "major"
        if value <= 2:
            return "minor"
    return "moderate"


def parse_args() -> tuple[argparse.Namespace, list[str]]:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--venv",
        type=Path,
        default=DEFAULT_VENV,
        help="Virtualenv path created by install_engine.py.",
    )
    parser.add_argument(
        "--derive-severity",
        action="store_true",
        help=(
            "Temporarily derive OpenAIReview severity tiers from 1-5 impact_rating "
            "values before running the packaged viz helper."
        ),
    )
    parser.add_argument(
        "--runtime",
        default=DEFAULT_RUNTIME,
        help="Runtime label for the viz method key (openaireview__<runtime>), method label, "
        "and model field. Default: agent.",
    )
    args, remainder = parser.parse_known_args()
    if remainder and remainder[0] == "--":
        remainder = remainder[1:]
    return args, remainder


def _parse_helper_args(remainder: list[str], runtime: str = DEFAULT_RUNTIME) -> argparse.Namespace:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("review_dir", nargs="?")
    parser.add_argument("--output-dir", default="./review_results")
    parser.add_argument("--method-key", default=method_key(runtime))
    parser.add_argument("--method-label", default=method_label(runtime))
    parser.add_argument("--slug-suffix", default="")
    parsed, _unknown = parser.parse_known_args(remainder)
    return parsed


def _with_runtime_defaults(remainder: list[str], runtime: str = DEFAULT_RUNTIME) -> list[str]:
    updated = list(remainder)
    if "--method-key" not in updated:
        updated.extend(["--method-key", method_key(runtime)])
    if "--method-label" not in updated:
        updated.extend(["--method-label", method_label(runtime)])
    return updated


def _temporarily_add_severity(review_dir: Path):
    issues_path = review_dir / "final_issues.json"
    if not issues_path.exists():
        return None

    original = issues_path.read_text(encoding="utf-8")
    issues = json.loads(original)
    if not isinstance(issues, list):
        return None

    changed = False
    for issue in issues:
        if isinstance(issue, dict) and "severity" not in issue:
            issue["severity"] = _impact_to_severity(issue.get("impact_rating"))
            changed = True

    if changed:
        issues_path.write_text(json.dumps(issues, indent=2) + "\n", encoding="utf-8")
        return original
    return None


def _restore_final_issues(review_dir: Path, original: str | None) -> None:
    if original is not None:
        (review_dir / "final_issues.json").write_text(original, encoding="utf-8")


def _mark_viz_model(helper_args: argparse.Namespace, runtime: str = DEFAULT_RUNTIME) -> None:
    if not helper_args.review_dir:
        return
    review_dir = Path(helper_args.review_dir)
    metadata_path = review_dir / "metadata.json"
    if not metadata_path.exists():
        return

    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    output_path = Path(helper_args.output_dir) / f"{metadata['slug']}{helper_args.slug_suffix}.json"
    if not output_path.exists():
        return

    data = json.loads(output_path.read_text(encoding="utf-8"))
    method = data.get("methods", {}).get(helper_args.method_key)
    if isinstance(method, dict):
        method["model"] = runtime
        output_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    args, remainder = parse_args()
    remainder = _with_runtime_defaults(remainder, args.runtime)
    helper_args = _parse_helper_args(remainder, args.runtime)
    review_dir = Path(helper_args.review_dir) if helper_args.review_dir else None
    original_final_issues = None

    try:
        if args.derive_severity and review_dir is not None:
            original_final_issues = _temporarily_add_severity(review_dir)
        result = run_packaged_skill_script(args.venv, "scripts/save_viz_json.py", remainder)
    finally:
        if review_dir is not None:
            _restore_final_issues(review_dir, original_final_issues)

    if result == 0:
        _mark_viz_model(helper_args, args.runtime)
    return result


if __name__ == "__main__":
    raise SystemExit(main())
