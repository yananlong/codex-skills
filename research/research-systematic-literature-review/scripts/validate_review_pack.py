#!/usr/bin/env python3
"""Validate a recall-audited literature review pack."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

PROFILES = {"comprehensive-systematic", "bounded-systematic", "critical-evidence-map", "rapid-scan", "novelty-prior-art"}
SYSTEMATIC = {"comprehensive-systematic", "bounded-systematic"}
VERDICTS = {"insufficient", "adequate-for-bounded-claims", "adequate-for-comprehensive-claim"}
COUNTS = ["records_identified", "duplicates_removed", "records_screened", "records_excluded", "reports_sought_for_retrieval", "reports_not_retrieved", "reports_assessed_for_eligibility", "reports_excluded", "studies_included"]


def read(path: Path, errors: list[str]) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        errors.append(f"missing file: {path}")
        return ""


def table_value(text: str, field: str) -> str | None:
    match = re.search(rf"\|\s*{re.escape(field)}\s*\|\s*(.*?)\s*\|", text, re.I)
    return match.group(1).strip() if match else None


def parse_prisma(text: str, errors: list[str]) -> dict[str, int]:
    result: dict[str, int] = {}
    for key in COUNTS:
        value = table_value(text, key)
        if value is None or not re.fullmatch(r"\d+", value.replace(",", "")):
            errors.append(f"screening log missing non-negative integer {key}")
        else:
            result[key] = int(value.replace(",", ""))
    if len(result) == len(COUNTS):
        checks = [
            (result["records_screened"] == result["records_identified"] - result["duplicates_removed"], "records_screened mismatch"),
            (result["records_excluded"] == result["records_screened"] - result["reports_sought_for_retrieval"], "records_excluded mismatch"),
            (result["reports_assessed_for_eligibility"] == result["reports_sought_for_retrieval"] - result["reports_not_retrieved"], "reports assessed mismatch"),
            (result["reports_excluded"] == result["reports_assessed_for_eligibility"] - result["studies_included"], "reports_excluded mismatch"),
        ]
        errors.extend(message for ok, message in checks if not ok)
    return result


def section(text: str, heading: str) -> str:
    start = text.find(heading)
    if start < 0:
        return ""
    tail = text[start + len(heading):]
    next_heading = re.search(r"\n##\s+", tail)
    return tail[:next_heading.start()] if next_heading else tail


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for arg in ("protocol", "search_log", "recall_audit", "corpus_manifest", "screening_log", "evidence", "report"):
        parser.add_argument("--" + arg.replace("_", "-"), required=True)
    args = parser.parse_args()
    errors: list[str] = []
    paths = {key: Path(getattr(args, key)).expanduser().resolve() for key in vars(args)}
    text = {key: read(path, errors) for key, path in paths.items() if key != "corpus_manifest"}
    try:
        manifest = json.loads(paths["corpus_manifest"].read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(f"missing file: {paths['corpus_manifest']}")
        manifest = {}
    except json.JSONDecodeError as exc:
        errors.append(f"invalid corpus manifest JSON: {exc}")
        manifest = {}

    profile = table_value(text.get("protocol", ""), "Review profile")
    if profile not in PROFILES:
        errors.append(f"invalid or missing Review profile: {profile}")
    if manifest.get("review_profile") != profile:
        errors.append("corpus manifest review_profile does not match protocol")
    verdict = manifest.get("assurance_verdict")
    if verdict not in VERDICTS:
        errors.append(f"invalid assurance_verdict: {verdict}")

    required_headings = {
        "protocol": ["## Discovery assurance", "## PRISMA scope"],
        "search_log": ["## Seed recovery ledger", "## Search-channel decisions", "## Search repairs and late omissions"],
        "recall_audit": ["## Visible seed recovery", "## Search-channel assurance", "## Stopping rationale", "## Bounded assurance verdict"],
        "screening_log": ["## PRISMA Counts", "## Decision ledger"],
        "evidence": ["## Extraction matrix"],
        "report": ["## Discovery Assurance", "## Search Strategy", "## Synthesis", "## Limitations", "## PRISMA flow accounting"],
    }
    for name, headings in required_headings.items():
        for heading in headings:
            if heading not in text.get(name, ""):
                errors.append(f"{name}: missing heading {heading}")

    parse_prisma(text.get("screening_log", ""), errors)

    if profile in SYSTEMATIC:
        recall = text.get("recall_audit", "")
        search = text.get("search_log", "")
        if "seed-001" not in search and "Seeds defined:" not in recall:
            errors.append("systematic profile lacks a seed recovery record")
        if "backward-citation" not in search or "forward-citation" not in search:
            errors.append("systematic profile lacks backward/forward citation-search decisions")
        stopping = section(recall, "## Stopping rationale")
        if not stopping.strip() or "TODO" in stopping:
            errors.append("systematic profile lacks a completed stopping rationale")
        if not isinstance(manifest.get("records"), list) or not isinstance(manifest.get("seed_ids"), list):
            errors.append("corpus manifest records and seed_ids must be lists")
        if profile == "comprehensive-systematic" and verdict == "adequate-for-comprehensive-claim":
            if not manifest.get("seed_ids"):
                errors.append("comprehensive assurance requires non-empty seed_ids")
            if manifest.get("freeze_date") in (None, ""):
                errors.append("comprehensive assurance requires a freeze_date")

    if errors:
        print("Validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"Validation passed: review artifacts satisfy the declared {profile} assurance profile with verdict {verdict}. This validates recorded process and consistency, not actual completeness or independent verification.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
