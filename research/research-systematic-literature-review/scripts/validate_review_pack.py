#!/usr/bin/env python3
"""Validate a recall-audited literature review pack."""
from __future__ import annotations

import argparse
import json
import re
from datetime import date
from pathlib import Path
from typing import Any

PROFILES = {
    "comprehensive-systematic",
    "bounded-systematic",
    "critical-evidence-map",
    "rapid-scan",
    "novelty-prior-art",
}
SYSTEMATIC = {"comprehensive-systematic", "bounded-systematic"}
VERDICTS = {
    "insufficient",
    "adequate-for-bounded-claims",
    "adequate-for-comprehensive-claim",
}
CHANNEL_STATUSES = {"required", "performed", "unavailable", "not-applicable"}
REQUIRED_CHANNELS = {
    "backward-citation",
    "forward-citation",
    "venue-census",
    "author-lab-expansion",
    "benchmark-dataset-tracing",
    "prior-review-harvesting",
    "grey-literature",
    "zotero-cross-check",
}
COUNTS = [
    "records_identified",
    "duplicates_removed",
    "records_screened",
    "records_excluded",
    "reports_sought_for_retrieval",
    "reports_not_retrieved",
    "reports_assessed_for_eligibility",
    "reports_excluded",
    "studies_included",
]
PLACEHOLDERS = {"", "todo", "tbd", "unknown", "none", "null", "n/a", "na", "-"}
URL_RE = re.compile(r"^https?://", re.I)

REQUIRED_HEADINGS = {
    "protocol": [
        "# Protocol:",
        "## Metadata",
        "## Inputs",
        "## Assumptions applied",
        "## Inclusion criteria",
        "## Exclusion criteria",
        "## Discovery assurance",
        "## PRISMA scope",
    ],
    "search_log": [
        "# Search Log:",
        "## Search metadata",
        "## Source queries",
        "## Seed recovery ledger",
        "## Search-channel decisions",
        "## Deduplication ledger",
        "## Version resolution ledger",
        "## Search repairs and late omissions",
    ],
    "recall_audit": [
        "# Recall Audit:",
        "## Declared review profile",
        "## Visible seed recovery",
        "## Withheld challenge evaluation",
        "## Search-channel assurance",
        "## Search-strategy review",
        "## Coverage gaps and source constraints",
        "## Corpus freeze",
        "## Late major omissions",
        "## Stopping rationale",
        "## Bounded assurance verdict",
    ],
    "screening_log": [
        "# Screening Log:",
        "## PRISMA Counts",
        "## Decision ledger",
    ],
    "evidence": ["# Evidence Table:", "## Extraction matrix"],
    "report": [
        "## Protocol",
        "## Discovery Assurance",
        "## Search Strategy",
        "## Screening Decisions",
        "## Evidence Table",
        "## Synthesis",
        "## Adversarial Stress Test",
        "## Limitations",
        "## Confidence Assessment",
        "## PRISMA flow accounting",
    ],
}


def substantive(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    normalized = value.strip().lower()
    return normalized not in PLACEHOLDERS and "todo" not in normalized


def read_text(path: Path, label: str, errors: list[str]) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        errors.append(f"missing {label} file: {path}")
        return ""


def read_json(path: Path, label: str, errors: list[str]) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(f"missing {label} file: {path}")
    except json.JSONDecodeError as exc:
        errors.append(f"invalid {label} JSON: {exc}")
    return None


def table_value(text: str, field: str) -> str | None:
    match = re.search(rf"(?mi)^\|\s*{re.escape(field)}\s*\|\s*(.*?)\s*\|\s*$", text)
    return match.group(1).strip() if match else None


def section(text: str, heading: str) -> str:
    match = re.search(rf"(?m)^{re.escape(heading)}\s*$", text)
    if not match:
        return ""
    tail = text[match.end():]
    next_heading = re.search(r"(?m)^##\s+", tail)
    return tail[:next_heading.start()] if next_heading else tail


def parse_table(text: str, heading: str, errors: list[str], label: str) -> tuple[list[str], list[dict[str, str]]]:
    body = section(text, heading)
    lines = [line.strip() for line in body.splitlines() if line.strip().startswith("|")]
    if len(lines) < 2:
        errors.append(f"{label}: no table found under {heading}")
        return [], []
    header = [cell.strip() for cell in lines[0].strip("|").split("|")]
    rows: list[dict[str, str]] = []
    for line in lines[1:]:
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if all(set(cell) <= {"-", ":"} for cell in cells):
            continue
        if len(cells) < len(header):
            cells += [""] * (len(header) - len(cells))
        rows.append(dict(zip(header, cells[:len(header)])))
    return header, rows


def require_columns(header: list[str], required: set[str], label: str, errors: list[str]) -> None:
    missing = sorted(required - set(header))
    if missing:
        errors.append(f"{label}: missing required columns: {', '.join(missing)}")


def parse_non_negative(value: str, label: str, errors: list[str]) -> int | None:
    cleaned = value.replace(",", "").strip()
    if not re.fullmatch(r"\d+", cleaned):
        errors.append(f"{label} must be a non-negative integer")
        return None
    return int(cleaned)


def parse_prisma(text: str, errors: list[str]) -> dict[str, int]:
    header, rows = parse_table(text, "## PRISMA Counts", errors, "screening log")
    require_columns(header, {"Metric", "Count"}, "screening log PRISMA table", errors)
    result: dict[str, int] = {}
    for row in rows:
        key = row.get("Metric", "")
        if key not in COUNTS:
            continue
        if key in result:
            errors.append(f"screening log: duplicate PRISMA metric {key}")
            continue
        parsed = parse_non_negative(row.get("Count", ""), f"screening log {key}", errors)
        if parsed is not None:
            result[key] = parsed
    missing = [key for key in COUNTS if key not in result]
    if missing:
        errors.append("screening log missing PRISMA metrics: " + ", ".join(missing))
        return result
    checks = [
        (result["duplicates_removed"] <= result["records_identified"], "duplicates_removed cannot exceed records_identified"),
        (result["records_screened"] == result["records_identified"] - result["duplicates_removed"], "records_screened mismatch"),
        (result["reports_sought_for_retrieval"] <= result["records_screened"], "reports_sought_for_retrieval cannot exceed records_screened"),
        (result["records_excluded"] == result["records_screened"] - result["reports_sought_for_retrieval"], "records_excluded mismatch"),
        (result["reports_not_retrieved"] <= result["reports_sought_for_retrieval"], "reports_not_retrieved cannot exceed reports_sought_for_retrieval"),
        (result["reports_assessed_for_eligibility"] == result["reports_sought_for_retrieval"] - result["reports_not_retrieved"], "reports assessed mismatch"),
        (result["studies_included"] <= result["reports_assessed_for_eligibility"], "studies_included cannot exceed reports assessed"),
        (result["reports_excluded"] == result["reports_assessed_for_eligibility"] - result["studies_included"], "reports_excluded mismatch"),
    ]
    errors.extend(f"screening log: {message}" for ok, message in checks if not ok)
    return result


def validate_manifest(manifest: Any, profile: str | None, errors: list[str]) -> tuple[str | None, set[str], set[str]]:
    if not isinstance(manifest, dict):
        errors.append("corpus manifest must be a JSON object")
        return None, set(), set()
    required = {
        "schema_version", "topic", "review_profile", "freeze_date", "corpus_version",
        "records", "seed_ids", "challenge_ids", "post_freeze_amendments",
        "search_strategy_review", "assurance_verdict",
    }
    missing = sorted(required - set(manifest))
    if missing:
        errors.append("corpus manifest missing fields: " + ", ".join(missing))
    if manifest.get("schema_version") != "1.0":
        errors.append("corpus manifest schema_version must be 1.0")
    if not substantive(manifest.get("topic")):
        errors.append("corpus manifest topic must be substantive")
    if manifest.get("review_profile") != profile:
        errors.append("corpus manifest review_profile does not match protocol")
    if not isinstance(manifest.get("corpus_version"), int) or manifest.get("corpus_version", 0) < 1:
        errors.append("corpus manifest corpus_version must be a positive integer")

    verdict = manifest.get("assurance_verdict")
    if verdict not in VERDICTS:
        errors.append(f"invalid assurance_verdict: {verdict}")
        verdict = None
    if verdict == "adequate-for-comprehensive-claim" and profile != "comprehensive-systematic":
        errors.append("adequate-for-comprehensive-claim requires comprehensive-systematic profile")

    records = manifest.get("records")
    record_ids: set[str] = set()
    if not isinstance(records, list):
        errors.append("corpus manifest records must be a list")
        records = []
    for index, record in enumerate(records, 1):
        label = f"corpus manifest records[{index}]"
        if not isinstance(record, dict):
            errors.append(f"{label} must be an object")
            continue
        record_id = record.get("record_id")
        if not substantive(record_id):
            errors.append(f"{label}.record_id must be substantive")
        elif record_id in record_ids:
            errors.append(f"duplicate corpus record_id: {record_id}")
        else:
            record_ids.add(record_id)
        for field in ("canonical_citation", "publication_status"):
            if not substantive(record.get(field)):
                errors.append(f"{label}.{field} must be substantive")
        url = record.get("publication_url")
        if not isinstance(url, str) or not URL_RE.match(url.strip()):
            errors.append(f"{label}.publication_url must be an http(s) URL")

    seed_ids = manifest.get("seed_ids")
    challenge_ids = manifest.get("challenge_ids")
    for name, value in (("seed_ids", seed_ids), ("challenge_ids", challenge_ids), ("post_freeze_amendments", manifest.get("post_freeze_amendments"))):
        if not isinstance(value, list):
            errors.append(f"corpus manifest {name} must be a list")
    seed_set = {str(value) for value in seed_ids or []}
    challenge_set = {str(value) for value in challenge_ids or []}

    amendments = manifest.get("post_freeze_amendments")
    if isinstance(amendments, list):
        for index, amendment in enumerate(amendments, 1):
            if not isinstance(amendment, dict):
                errors.append(f"post_freeze_amendments[{index}] must be an object")
                continue
            for field in ("record_id", "reason", "effect_on_conclusions"):
                if not substantive(amendment.get(field)):
                    errors.append(f"post_freeze_amendments[{index}].{field} must be substantive")

    review = manifest.get("search_strategy_review")
    if not isinstance(review, dict):
        errors.append("corpus manifest search_strategy_review must be an object")
    else:
        if not isinstance(review.get("performed"), bool):
            errors.append("search_strategy_review.performed must be boolean")
        if not substantive(review.get("independence")):
            errors.append("search_strategy_review.independence must be substantive")
        if verdict and verdict != "insufficient" and not substantive(review.get("notes")):
            errors.append("adequate verdict requires search_strategy_review.notes explaining review or non-review")
        if verdict == "adequate-for-comprehensive-claim" and review.get("performed") is not True:
            errors.append("comprehensive assurance requires a performed search-strategy review")

    if verdict and verdict != "insufficient":
        freeze = manifest.get("freeze_date")
        try:
            date.fromisoformat(freeze)
        except (TypeError, ValueError):
            errors.append("adequate verdict requires an ISO freeze_date")
        if not records:
            errors.append("adequate verdict requires a non-empty candidate corpus")

    return verdict, seed_set, challenge_set


def validate_search(text: str, profile: str | None, verdict: str | None, manifest_seeds: set[str], errors: list[str]) -> None:
    query_header, query_rows = parse_table(text, "## Source queries", errors, "search log")
    require_columns(
        query_header,
        {"run_id", "channel", "source", "coverage_target", "query_or_seed", "records_returned", "unique_candidates", "included_yield"},
        "search log source queries",
        errors,
    )
    substantive_queries = []
    for index, row in enumerate(query_rows, 1):
        if not substantive(row.get("run_id")):
            continue
        for field in ("channel", "source", "coverage_target", "query_or_seed"):
            if not substantive(row.get(field)):
                errors.append(f"source query row {index}.{field} must be substantive")
        for field in ("records_returned", "unique_candidates", "included_yield"):
            parse_non_negative(row.get(field, ""), f"source query row {index}.{field}", errors)
        substantive_queries.append(row)
    if not substantive_queries:
        errors.append("search log must contain at least one substantive source query")

    seed_header, seed_rows = parse_table(text, "## Seed recovery ledger", errors, "search log")
    require_columns(
        seed_header,
        {"seed_id", "canonical_citation", "recovered_by_run", "recovered", "miss_reason", "repair_run"},
        "seed recovery ledger",
        errors,
    )
    seeds: dict[str, str] = {}
    for index, row in enumerate(seed_rows, 1):
        seed_id = row.get("seed_id", "")
        if not substantive(seed_id):
            continue
        if seed_id in seeds:
            errors.append(f"duplicate seed_id: {seed_id}")
            continue
        seeds[seed_id] = row.get("recovered", "").strip().lower()
        if not substantive(row.get("canonical_citation")):
            errors.append(f"seed row {index}.canonical_citation must be substantive")
        recovered = seeds[seed_id]
        if recovered not in {"yes", "no"}:
            errors.append(f"seed row {index}.recovered must be yes or no")
        elif recovered == "yes" and not substantive(row.get("recovered_by_run")):
            errors.append(f"seed row {index} recovered=yes requires recovered_by_run")
        elif recovered == "no":
            if not substantive(row.get("miss_reason")):
                errors.append(f"seed row {index} recovered=no requires miss_reason")
            if not substantive(row.get("repair_run")):
                errors.append(f"seed row {index} recovered=no requires repair_run")

    if profile in SYSTEMATIC and not seeds:
        errors.append("systematic profile requires at least one substantive seed")
    if profile in SYSTEMATIC and verdict and verdict != "insufficient":
        if manifest_seeds != set(seeds):
            errors.append("corpus manifest seed_ids must match the seed recovery ledger")
        missed = sorted(seed_id for seed_id, recovered in seeds.items() if recovered != "yes")
        if missed:
            errors.append("adequate systematic verdict requires all visible seeds recovered after repair: " + ", ".join(missed))

    channel_header, channel_rows = parse_table(text, "## Search-channel decisions", errors, "search log")
    require_columns(
        channel_header,
        {"channel", "status", "rationale", "rounds", "unique_candidates", "included_yield", "last_round_yield"},
        "search-channel decisions",
        errors,
    )
    channels: dict[str, dict[str, str]] = {}
    for index, row in enumerate(channel_rows, 1):
        name = row.get("channel", "")
        if not substantive(name):
            continue
        if name in channels:
            errors.append(f"duplicate search-channel decision: {name}")
            continue
        channels[name] = row
        status = row.get("status", "").strip().lower()
        if status not in CHANNEL_STATUSES:
            errors.append(f"search-channel row {index}.status must be one of {sorted(CHANNEL_STATUSES)}")
        if not substantive(row.get("rationale")):
            errors.append(f"search-channel row {index}.rationale must be substantive")
        for field in ("rounds", "unique_candidates", "included_yield", "last_round_yield"):
            parse_non_negative(row.get(field, ""), f"search-channel row {index}.{field}", errors)
        if status == "performed" and row.get("rounds", "0").strip() == "0":
            errors.append(f"search-channel row {index} performed status requires rounds > 0")

    if profile in SYSTEMATIC:
        missing_channels = sorted(REQUIRED_CHANNELS - set(channels))
        if missing_channels:
            errors.append("systematic profile missing channel decisions: " + ", ".join(missing_channels))
    if profile in SYSTEMATIC and verdict and verdict != "insufficient":
        unfinished = sorted(name for name, row in channels.items() if row.get("status", "").strip().lower() == "required")
        if unfinished:
            errors.append("adequate verdict cannot leave required search channels unfinished: " + ", ".join(unfinished))
    if verdict == "adequate-for-comprehensive-claim":
        for name in ("backward-citation", "forward-citation"):
            if channels.get(name, {}).get("status", "").strip().lower() != "performed":
                errors.append(f"comprehensive assurance requires performed {name} searching")


def validate_recall(text: str, profile: str | None, verdict: str | None, challenge_ids: set[str], errors: list[str]) -> None:
    declared = re.search(r"(?mi)^-\s*Profile:\s*(\S+)\s*$", section(text, "## Declared review profile"))
    if not declared or declared.group(1) != profile:
        errors.append("recall audit profile does not match protocol")
    verdict_match = re.search(r"(?mi)^-\s*Verdict:\s*(\S+)\s*$", section(text, "## Bounded assurance verdict"))
    if not verdict_match or verdict_match.group(1) != verdict:
        errors.append("recall audit verdict does not match corpus manifest")

    if verdict and verdict != "insufficient":
        for heading in (
            "## Visible seed recovery",
            "## Withheld challenge evaluation",
            "## Search-channel assurance",
            "## Search-strategy review",
            "## Coverage gaps and source constraints",
            "## Corpus freeze",
            "## Late major omissions",
            "## Stopping rationale",
            "## Bounded assurance verdict",
        ):
            body = section(text, heading)
            if not substantive(body) or "todo" in body.lower():
                errors.append(f"adequate verdict requires a completed recall-audit section: {heading}")
    if verdict == "adequate-for-comprehensive-claim" and not challenge_ids:
        challenge = section(text, "## Withheld challenge evaluation").lower()
        if "unavailable" not in challenge or "because" not in challenge:
            errors.append("comprehensive assurance requires challenge_ids or a substantive unavailability rationale")


def validate_evidence(text: str, studies_included: int | None, errors: list[str]) -> None:
    header, rows = parse_table(text, "## Extraction matrix", errors, "evidence table")
    require_columns(
        header,
        {"study_id", "canonical_citation", "publication_url", "year", "venue", "doi", "publication_status", "work_type"},
        "evidence extraction matrix",
        errors,
    )
    data_rows = [row for row in rows if substantive(row.get("study_id"))]
    ids: set[str] = set()
    for index, row in enumerate(data_rows, 1):
        study_id = row.get("study_id", "")
        if study_id in ids:
            errors.append(f"duplicate evidence study_id: {study_id}")
        ids.add(study_id)
        if not substantive(row.get("canonical_citation")):
            errors.append(f"evidence row {index}.canonical_citation must be substantive")
        if not URL_RE.match(row.get("publication_url", "").strip()):
            errors.append(f"evidence row {index}.publication_url must be an http(s) URL")
        if not substantive(row.get("publication_status")):
            errors.append(f"evidence row {index}.publication_status must be substantive")
    if studies_included is not None and len(data_rows) != studies_included:
        errors.append(
            f"evidence rows ({len(data_rows)}) must equal studies_included ({studies_included})"
        )


def validate_screening(text: str, errors: list[str]) -> None:
    header, rows = parse_table(text, "## Decision ledger", errors, "screening log")
    require_columns(
        header,
        {"study_id", "record_type", "canonical_citation", "publication_url", "stage", "decision"},
        "screening decision ledger",
        errors,
    )
    for index, row in enumerate(rows, 1):
        if not substantive(row.get("study_id")):
            continue
        decision = row.get("decision", "").strip().lower()
        if decision not in {"include", "exclude"}:
            errors.append(f"screening row {index}.decision must be include or exclude")
        if decision == "include":
            if not substantive(row.get("canonical_citation")):
                errors.append(f"screening row {index}.canonical_citation must be substantive for included records")
            if not URL_RE.match(row.get("publication_url", "").strip()):
                errors.append(f"screening row {index}.publication_url must be an http(s) URL for included records")


def validate_report(text: str, verdict: str | None, errors: list[str]) -> None:
    if not re.search(r"(?m)^# (Systematic Literature Review|Literature Evidence Review):", text):
        errors.append("report: missing recognized title")
    report_verdict = re.search(r"(?mi)^-\s*Assurance verdict:\s*(\S+)\s*$", section(text, "## Discovery Assurance"))
    if not report_verdict or report_verdict.group(1) != verdict:
        errors.append("report assurance verdict does not match corpus manifest")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for arg in (
        "protocol", "search_log", "recall_audit", "corpus_manifest",
        "screening_log", "evidence", "report",
    ):
        parser.add_argument("--" + arg.replace("_", "-"), required=True)
    args = parser.parse_args()
    paths = {key: Path(value).expanduser().resolve() for key, value in vars(args).items()}
    errors: list[str] = []
    texts = {
        key: read_text(path, key.replace("_", "-"), errors)
        for key, path in paths.items()
        if key != "corpus_manifest"
    }
    manifest = read_json(paths["corpus_manifest"], "corpus manifest", errors)

    for name, headings in REQUIRED_HEADINGS.items():
        content = texts.get(name, "")
        for heading in headings:
            if heading not in content:
                errors.append(f"{name}: missing heading {heading}")

    profile = table_value(texts.get("protocol", ""), "Review profile")
    if profile not in PROFILES:
        errors.append(f"invalid or missing Review profile: {profile}")
    domain = table_value(texts.get("protocol", ""), "Domain")
    if not substantive(domain):
        errors.append("protocol Domain must be substantive")
    if profile in SYSTEMATIC:
        for field in ("intended_decision", "domain_adapter"):
            if not substantive(table_value(texts.get("protocol", ""), field)):
                errors.append(f"systematic protocol {field} must be substantive")

    verdict, manifest_seeds, challenge_ids = validate_manifest(manifest, profile, errors)
    counts = parse_prisma(texts.get("screening_log", ""), errors)
    validate_search(texts.get("search_log", ""), profile, verdict, manifest_seeds, errors)
    validate_recall(texts.get("recall_audit", ""), profile, verdict, challenge_ids, errors)
    validate_screening(texts.get("screening_log", ""), errors)
    validate_evidence(texts.get("evidence", ""), counts.get("studies_included"), errors)
    validate_report(texts.get("report", ""), verdict, errors)

    if verdict and verdict != "insufficient" and counts.get("studies_included", 0) < 1:
        errors.append("adequate verdict requires at least one included study or work")

    if errors:
        print("Validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print(
        f"Validation passed: review artifacts satisfy the declared {profile} process profile "
        f"with verdict {verdict}. This validates recorded structure, consistency, and declared "
        "recall controls; it does not prove actual completeness, source independence, or scientific validity."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
