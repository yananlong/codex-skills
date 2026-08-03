#!/usr/bin/env python3
"""Validate novelty decisions and their exact literature-assurance binding."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "1.1"
STATUSES = {"draft", "complete"}
PATH_KEYS = (
    "protocol",
    "search_log",
    "recall_audit",
    "corpus_manifest",
    "screening_log",
    "evidence",
    "report",
)
PATH_KEY_SET = set(PATH_KEYS)
ADEQUATE_VERDICTS = {"adequate-for-bounded-claims", "adequate-for-comprehensive-claim"}
RATING_FIELDS = (
    "novelty_decision_rating",
    "impact_positioning_rating",
    "decision_confidence_rating",
)

RESEARCH_ROOT = Path(__file__).resolve().parents[2]
SLR_SCRIPTS = RESEARCH_ROOT / "research-systematic-literature-review" / "scripts"
if str(SLR_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SLR_SCRIPTS))
from review_pack_coverage import unresolved_high_priority_novelty_questions  # noqa: E402


def meaningful(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip()) and "todo" not in value.lower()


def read_text(path: Path, label: str, errors: list[str]) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        errors.append(f"missing {label}: {path}")
        return ""


def read_json(path: Path, label: str, errors: list[str]) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(f"missing {label}: {path}")
    except json.JSONDecodeError as exc:
        errors.append(f"invalid JSON in {label}: {exc}")
    return None


def string_list(value: Any, label: str, errors: list[str]) -> list[str]:
    if not isinstance(value, list):
        errors.append(f"{label} must be a list")
        return []
    items: list[str] = []
    for index, item in enumerate(value, 1):
        if not meaningful(item):
            errors.append(f"{label}[{index}] must be substantive")
        else:
            items.append(str(item))
    if len(items) != len(set(items)):
        errors.append(f"{label} contains duplicates")
    return items


def report_value(report: str, label: str) -> str | None:
    match = re.search(rf"(?mi)^-[ \t]*{re.escape(label)}:[ \t]*(.*?)[ \t]*$", report)
    return match.group(1).strip() if match else None


def resolve_path(decision_path: Path, value: Any, label: str, errors: list[str]) -> Path | None:
    if not meaningful(value):
        errors.append(f"{label} must be a substantive path")
        return None
    path = Path(str(value)).expanduser()
    if not path.is_absolute():
        path = decision_path.parent / path
    return path.resolve()


def rerun_literature_validator(paths: dict[str, Path], validator: Path, errors: list[str]) -> None:
    command = [
        sys.executable,
        str(validator),
        "--protocol",
        str(paths["protocol"]),
        "--search-log",
        str(paths["search_log"]),
        "--recall-audit",
        str(paths["recall_audit"]),
        "--corpus-manifest",
        str(paths["corpus_manifest"]),
        "--screening-log",
        str(paths["screening_log"]),
        "--evidence",
        str(paths["evidence"]),
        "--report",
        str(paths["report"]),
    ]
    completed = subprocess.run(command, text=True, capture_output=True)
    if completed.returncode != 0:
        detail = (completed.stdout + "\n" + completed.stderr).strip()
        errors.append("upstream literature-review validation failed" + (f":\n{detail}" if detail else ""))


def validate_linked_literature(
    decision_path: Path,
    assurance: Any,
    rating: int | None,
    claims_to_qualify: list[str],
    positioning: Any,
    what_changes: Any,
    validator: Path,
    errors: list[str],
) -> None:
    if not isinstance(assurance, dict):
        errors.append("linked novelty validation requires literature_assurance object")
        return
    if assurance.get("mode") != "linked":
        errors.append("linked novelty validation requires literature_assurance.mode=linked")
    raw_paths = assurance.get("paths")
    if not isinstance(raw_paths, dict):
        errors.append("literature_assurance.paths must be an object")
        return
    missing_keys = sorted(PATH_KEY_SET - set(raw_paths))
    extra_keys = sorted(set(raw_paths) - PATH_KEY_SET)
    if missing_keys:
        errors.append("literature_assurance.paths missing keys: " + ", ".join(missing_keys))
    if extra_keys:
        errors.append("literature_assurance.paths has unknown keys: " + ", ".join(extra_keys))
    resolved: dict[str, Path] = {}
    for key in PATH_KEYS:
        path = resolve_path(decision_path, raw_paths.get(key), f"literature_assurance.paths.{key}", errors)
        if path is not None:
            resolved[key] = path
    if len(resolved) != len(PATH_KEYS):
        return

    raw_digests = assurance.get("file_sha256")
    if not isinstance(raw_digests, dict):
        errors.append("literature_assurance.file_sha256 must be an object")
        raw_digests = {}
    missing_digest_keys = sorted(PATH_KEY_SET - set(raw_digests))
    extra_digest_keys = sorted(set(raw_digests) - PATH_KEY_SET)
    if missing_digest_keys:
        errors.append("literature_assurance.file_sha256 missing keys: " + ", ".join(missing_digest_keys))
    if extra_digest_keys:
        errors.append("literature_assurance.file_sha256 has unknown keys: " + ", ".join(extra_digest_keys))

    before_digests: dict[str, str] = {}
    for key in PATH_KEYS:
        try:
            digest = hashlib.sha256(resolved[key].read_bytes()).hexdigest()
        except FileNotFoundError:
            errors.append(f"missing bound literature file for digest: {resolved[key]}")
            continue
        before_digests[key] = digest
        declared = raw_digests.get(key)
        if not isinstance(declared, str) or re.fullmatch(r"[0-9a-f]{64}", declared) is None:
            errors.append(f"literature_assurance.file_sha256.{key} must be a lowercase SHA-256 hex digest")
        elif declared != digest:
            errors.append(f"literature_assurance.file_sha256.{key} does not match the bound file")

    manifest_digest = before_digests.get("corpus_manifest")
    if assurance.get("corpus_manifest_sha256") != manifest_digest:
        errors.append("literature_assurance corpus_manifest_sha256 does not match the bound manifest")
    if raw_digests.get("corpus_manifest") != assurance.get("corpus_manifest_sha256"):
        errors.append("literature_assurance corpus_manifest_sha256 disagrees with file_sha256.corpus_manifest")

    rerun_literature_validator(resolved, validator, errors)
    for key, before in before_digests.items():
        try:
            after = hashlib.sha256(resolved[key].read_bytes()).hexdigest()
        except FileNotFoundError:
            errors.append(f"bound literature file disappeared during validation: {resolved[key]}")
            continue
        if after != before:
            errors.append(f"bound literature file changed during validation: {key}")

    manifest = read_json(resolved["corpus_manifest"], "bound corpus manifest", errors)
    if not isinstance(manifest, dict):
        return
    for field in ("corpus_version", "review_profile", "assurance_verdict"):
        if assurance.get(field) != manifest.get(field):
            errors.append(f"literature_assurance.{field} does not match the bound corpus manifest")

    derived_unresolved = unresolved_high_priority_novelty_questions(manifest)
    declared_unresolved = set(
        string_list(
            assurance.get("unresolved_high_priority_novelty_question_ids"),
            "literature_assurance.unresolved_high_priority_novelty_question_ids",
            errors,
        )
    )
    if declared_unresolved != derived_unresolved:
        errors.append(
            "literature_assurance unresolved question IDs do not match the bound manifest: expected "
            + (", ".join(sorted(derived_unresolved)) or "none")
        )

    verdict = manifest.get("assurance_verdict")
    if rating in {4, 5}:
        if verdict not in ADEQUATE_VERDICTS:
            errors.append(f"novelty rating {rating} requires adequate literature assurance")
        if derived_unresolved:
            errors.append(
                f"novelty rating {rating} cannot retain unresolved high-priority novelty-critical questions: "
                + ", ".join(sorted(derived_unresolved))
            )
    if rating == 3 and (verdict not in ADEQUATE_VERDICTS or derived_unresolved):
        if not meaningful(positioning):
            errors.append("rating 3 under material literature uncertainty requires narrowest_defensible_positioning")
        if not meaningful(what_changes):
            errors.append("rating 3 under material literature uncertainty requires what_would_change_the_decision")
        if not claims_to_qualify:
            errors.append("rating 3 under material literature uncertainty requires claims_to_qualify")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--decision", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--prior-art-matrix", required=True, type=Path)
    parser.add_argument("--search-log", required=True, type=Path)
    parser.add_argument("--assurance-profile", choices=("structural", "linked"), default="structural")
    parser.add_argument("--literature-validator", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    errors: list[str] = []
    decision = read_json(args.decision, "novelty decision", errors)
    report = read_text(args.report, "novelty report", errors)
    prior_art = read_text(args.prior_art_matrix, "prior-art matrix", errors)
    search_log = read_text(args.search_log, "novelty search log", errors)
    for heading in (
        "# Novelty Report",
        "## Contribution Under Review",
        "## Claim Decomposition",
        "## Strongest Overlaps",
        "## Novelty-Killing Objections",
        "## Decision",
        "## Paper-Review Handoff",
    ):
        if heading not in report:
            errors.append(f"novelty-report.md missing heading {heading}")
    if "# Prior Art Matrix" not in prior_art:
        errors.append("prior-art-matrix.md missing title")
    if "# Search Log" not in search_log:
        errors.append("search-log.md missing title")

    if not isinstance(decision, dict):
        if decision is not None:
            errors.append("novelty-decision.json must be an object")
    else:
        if decision.get("schema_version") != SCHEMA_VERSION:
            errors.append(f"novelty-decision.schema_version must equal {SCHEMA_VERSION}")
        status = decision.get("status")
        if status not in STATUSES:
            errors.append(f"novelty-decision.status must be one of {sorted(STATUSES)}")
        ratings: dict[str, int | None] = {}
        for field in RATING_FIELDS:
            value = decision.get(field)
            if not isinstance(value, int) or isinstance(value, bool) or not 1 <= value <= 5:
                errors.append(f"novelty-decision.{field} must be an integer from 1 to 5")
                ratings[field] = None
            else:
                ratings[field] = value
        claims_to_qualify = string_list(decision.get("claims_to_qualify"), "claims_to_qualify", errors)
        for field in ("top_kill_shot_objections", "literature_context_used", "missing_prior_work"):
            string_list(decision.get(field), field, errors)
        if not isinstance(decision.get("review_findings_to_add"), list):
            errors.append("review_findings_to_add must be a list")

        if status == "complete":
            for field in ("narrowest_defensible_positioning", "what_would_change_the_decision"):
                if not meaningful(decision.get(field)):
                    errors.append(f"complete novelty decision requires {field}")
        report_fields = {
            "Novelty decision rating (1-5)": ratings.get("novelty_decision_rating"),
            "Impact positioning rating (1-5)": ratings.get("impact_positioning_rating"),
            "Decision confidence rating (1-5)": ratings.get("decision_confidence_rating"),
        }
        for label, expected in report_fields.items():
            actual = report_value(report, label)
            if actual is None:
                errors.append(f"novelty report missing {label}")
            elif expected is not None and actual != str(expected):
                errors.append(f"novelty report {label} disagrees with novelty-decision.json")

        assurance = decision.get("literature_assurance")
        if isinstance(assurance, dict):
            mode_in_report = report_value(report, "Literature assurance mode")
            if mode_in_report is None or mode_in_report != str(assurance.get("mode", "")):
                errors.append("novelty report literature assurance mode disagrees with novelty-decision.json")
            verdict_in_report = report_value(report, "Literature assurance verdict")
            expected_verdict = str(assurance.get("assurance_verdict", ""))
            if verdict_in_report is None or verdict_in_report != expected_verdict:
                errors.append("novelty report literature assurance verdict disagrees with novelty-decision.json")
            unresolved_in_report = report_value(report, "Unresolved high-priority novelty-critical questions")
            declared_unresolved = set(assurance.get("unresolved_high_priority_novelty_question_ids", [])) if isinstance(assurance.get("unresolved_high_priority_novelty_question_ids"), list) else set()
            parsed_unresolved = {part.strip() for part in (unresolved_in_report or "").replace(";", ",").split(",") if part.strip()}
            if parsed_unresolved != set(map(str, declared_unresolved)):
                errors.append("novelty report unresolved critical question IDs disagree with novelty-decision.json")
        if status == "complete":
            for label, field in (
                ("Narrowest defensible positioning", "narrowest_defensible_positioning"),
                ("What would change the decision", "what_would_change_the_decision"),
            ):
                if report_value(report, label) != str(decision.get(field, "")):
                    errors.append(f"novelty report {label} disagrees with novelty-decision.json")

        if args.assurance_profile == "linked":
            if status != "complete":
                errors.append("linked novelty validation requires status=complete")
            validator = args.literature_validator or (
                RESEARCH_ROOT / "research-systematic-literature-review" / "scripts" / "validate_review_pack.py"
            )
            validate_linked_literature(
                args.decision.resolve(),
                assurance,
                ratings.get("novelty_decision_rating"),
                claims_to_qualify,
                decision.get("narrowest_defensible_positioning"),
                decision.get("what_would_change_the_decision"),
                validator,
                errors,
            )
        elif not isinstance(assurance, dict) or assurance.get("mode") not in {"unlinked", "linked"}:
            errors.append("structural novelty validation requires literature_assurance.mode unlinked or linked")
        elif assurance.get("mode") == "linked":
            errors.append("literature_assurance.mode=linked requires --assurance-profile linked")

    if errors:
        print("Validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    if args.assurance_profile == "linked":
        print(
            "Validation passed: the exact bound literature pack was revalidated and the novelty rating, corpus "
            "identity, assurance verdict, unresolved critical questions, and report view are internally consistent. "
            "This governs novelty positioning only; it does not establish empirical validity or evidence promotion."
        )
    else:
        print(
            "Validation passed: the novelty-review pack is structurally consistent. This does not establish "
            "literature completeness, scientific novelty, empirical validity, or independent review."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
