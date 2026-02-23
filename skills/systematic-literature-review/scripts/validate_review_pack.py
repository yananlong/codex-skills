#!/usr/bin/env python3
"""Validate systematic literature review markdown artifacts for structure and consistency."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Dict, List

REQUIRED_METRICS = [
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

REQUIRED_HEADINGS = {
    "protocol": [
        "# Protocol:",
        "## Metadata",
        "## Inputs",
        "## Assumptions applied",
        "## Inclusion criteria",
        "## Exclusion criteria",
        "## PRISMA scope",
    ],
    "search": [
        "# Search Log:",
        "## Search metadata",
        "## Source queries",
        "## Deduplication ledger",
    ],
    "screening": [
        "# Screening Log:",
        "## PRISMA Counts",
        "## Decision ledger",
    ],
    "evidence": [
        "# Evidence Table:",
        "## Extraction matrix",
    ],
    "report": [
        "# Systematic Literature Review:",
        "## Protocol",
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


def _read_file(path: Path, label: str, errors: List[str]) -> str:
    if not path.exists():
        errors.append(f"{label} file not found: {path}")
        return ""
    return path.read_text(encoding="utf-8")


def _check_headings(content: str, label: str, required: List[str], errors: List[str]) -> None:
    for heading in required:
        if heading not in content:
            errors.append(f"{label}: missing required heading '{heading}'")


def _extract_domain(protocol_md: str) -> str | None:
    match = re.search(r"\|\s*Domain\s*\|\s*(.*?)\s*\|", protocol_md, flags=re.IGNORECASE)
    if not match:
        return None
    return match.group(1).strip()


def _parse_non_negative_int(raw: str, metric: str) -> int:
    cleaned = raw.replace(",", "").strip()
    if not re.fullmatch(r"\d+", cleaned):
        raise ValueError(f"Metric '{metric}' must be a non-negative integer. Got '{raw}'.")
    return int(cleaned)


def _parse_prisma_counts(screening_md: str) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for line in screening_md.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if len(cells) < 2:
            continue
        key = cells[0]
        value = cells[1]
        if key in {"Metric", "---"}:
            continue
        if key in REQUIRED_METRICS:
            if key in counts:
                raise ValueError(f"Metric '{key}' appears more than once.")
            counts[key] = _parse_non_negative_int(value, metric=key)

    missing = [metric for metric in REQUIRED_METRICS if metric not in counts]
    if missing:
        raise ValueError("Missing PRISMA metrics: " + ", ".join(missing))
    return counts


def _check_prisma_consistency(counts: Dict[str, int]) -> List[str]:
    issues: List[str] = []

    if counts["duplicates_removed"] > counts["records_identified"]:
        issues.append("duplicates_removed cannot exceed records_identified")

    if counts["records_screened"] != counts["records_identified"] - counts["duplicates_removed"]:
        issues.append("records_screened != records_identified - duplicates_removed")

    if counts["reports_sought_for_retrieval"] > counts["records_screened"]:
        issues.append("reports_sought_for_retrieval cannot exceed records_screened")

    if counts["records_excluded"] != counts["records_screened"] - counts["reports_sought_for_retrieval"]:
        issues.append("records_excluded != records_screened - reports_sought_for_retrieval")

    if counts["reports_not_retrieved"] > counts["reports_sought_for_retrieval"]:
        issues.append("reports_not_retrieved cannot exceed reports_sought_for_retrieval")

    if (
        counts["reports_assessed_for_eligibility"]
        != counts["reports_sought_for_retrieval"] - counts["reports_not_retrieved"]
    ):
        issues.append(
            "reports_assessed_for_eligibility != reports_sought_for_retrieval - reports_not_retrieved"
        )

    if counts["studies_included"] > counts["reports_assessed_for_eligibility"]:
        issues.append("studies_included cannot exceed reports_assessed_for_eligibility")

    if counts["reports_excluded"] != counts["reports_assessed_for_eligibility"] - counts["studies_included"]:
        issues.append("reports_excluded != reports_assessed_for_eligibility - studies_included")

    return issues


def _table_has_data_rows(markdown: str, section_heading: str) -> bool:
    idx = markdown.find(section_heading)
    if idx < 0:
        return False
    section_text = markdown[idx:].split("\n## ", 1)[0]
    rows = []
    for line in section_text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if not cells:
            continue
        if all(set(cell) <= {"-", ":"} for cell in cells):
            continue
        if cells[0].lower() in {"run_id", "study_id", "reason", "metric", "field"}:
            continue
        rows.append(cells)
    return len(rows) > 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate protocol/search/screening/evidence/report markdown files for required sections, "
            "mandatory fields, and PRISMA count consistency."
        )
    )
    parser.add_argument("--protocol", required=True, help="Path to <topic>.protocol.md")
    parser.add_argument("--search-log", required=True, help="Path to <topic>.search-log.md")
    parser.add_argument("--screening-log", required=True, help="Path to <topic>.screening-log.md")
    parser.add_argument("--evidence", required=True, help="Path to <topic>.evidence-table.md")
    parser.add_argument("--report", required=True, help="Path to <topic>.review.md")
    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    protocol_path = Path(args.protocol).expanduser().resolve()
    search_path = Path(args.search_log).expanduser().resolve()
    screening_path = Path(args.screening_log).expanduser().resolve()
    evidence_path = Path(args.evidence).expanduser().resolve()
    report_path = Path(args.report).expanduser().resolve()

    errors: List[str] = []

    protocol_md = _read_file(protocol_path, "protocol", errors)
    search_md = _read_file(search_path, "search-log", errors)
    screening_md = _read_file(screening_path, "screening-log", errors)
    evidence_md = _read_file(evidence_path, "evidence", errors)
    report_md = _read_file(report_path, "report", errors)

    if errors:
        print("Validation failed:")
        for err in errors:
            print(f"- {err}")
        return 1

    _check_headings(protocol_md, "protocol", REQUIRED_HEADINGS["protocol"], errors)
    _check_headings(search_md, "search-log", REQUIRED_HEADINGS["search"], errors)
    _check_headings(screening_md, "screening-log", REQUIRED_HEADINGS["screening"], errors)
    _check_headings(evidence_md, "evidence", REQUIRED_HEADINGS["evidence"], errors)
    _check_headings(report_md, "report", REQUIRED_HEADINGS["report"], errors)

    domain = _extract_domain(protocol_md)
    if not domain:
        errors.append("protocol: missing Domain value in metadata table")
    elif domain.lower() in {"tbd", "unset", "none", "n/a", "na", "unknown"}:
        errors.append(f"protocol: invalid Domain value '{domain}'")

    if not _table_has_data_rows(search_md, "## Source queries"):
        errors.append("search-log: Source queries table has no data rows")

    if not _table_has_data_rows(evidence_md, "## Extraction matrix"):
        errors.append("evidence: Extraction matrix table has no data rows")

    try:
        counts = _parse_prisma_counts(screening_md)
        issues = _check_prisma_consistency(counts)
        for issue in issues:
            errors.append(f"screening-log: {issue}")
    except ValueError as exc:
        errors.append(f"screening-log: {exc}")

    if errors:
        print("Validation failed:")
        for err in errors:
            print(f"- {err}")
        return 1

    print("Validation passed: review pack is structurally consistent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
