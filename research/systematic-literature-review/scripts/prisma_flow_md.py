#!/usr/bin/env python3
"""Parse PRISMA counts from a screening log Markdown file and emit flow accounting Markdown."""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date
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


def _parse_non_negative_int(raw: str, metric: str) -> int:
    cleaned = raw.replace(",", "").strip()
    if not re.fullmatch(r"\d+", cleaned):
        raise ValueError(f"Metric '{metric}' must be a non-negative integer. Got: '{raw}'")
    value = int(cleaned)
    return value


def _extract_counts(markdown: str) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for line in markdown.splitlines():
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
                raise ValueError(f"Metric '{key}' appears more than once in screening log.")
            counts[key] = _parse_non_negative_int(value, metric=key)

    missing = [metric for metric in REQUIRED_METRICS if metric not in counts]
    if missing:
        raise ValueError(
            "Missing required PRISMA metric(s): " + ", ".join(missing) + ". "
            "Ensure the screening log contains the standardized PRISMA Counts table."
        )

    return counts


def _validate_consistency(counts: Dict[str, int]) -> List[str]:
    errors: List[str] = []

    if counts["duplicates_removed"] > counts["records_identified"]:
        errors.append("duplicates_removed cannot exceed records_identified")

    expected_records_screened = counts["records_identified"] - counts["duplicates_removed"]
    if counts["records_screened"] != expected_records_screened:
        errors.append(
            "records_screened must equal records_identified - duplicates_removed "
            f"({expected_records_screened})"
        )

    if counts["reports_sought_for_retrieval"] > counts["records_screened"]:
        errors.append("reports_sought_for_retrieval cannot exceed records_screened")

    expected_records_excluded = counts["records_screened"] - counts["reports_sought_for_retrieval"]
    if counts["records_excluded"] != expected_records_excluded:
        errors.append(
            "records_excluded must equal records_screened - reports_sought_for_retrieval "
            f"({expected_records_excluded})"
        )

    if counts["reports_not_retrieved"] > counts["reports_sought_for_retrieval"]:
        errors.append("reports_not_retrieved cannot exceed reports_sought_for_retrieval")

    expected_eligibility = counts["reports_sought_for_retrieval"] - counts["reports_not_retrieved"]
    if counts["reports_assessed_for_eligibility"] != expected_eligibility:
        errors.append(
            "reports_assessed_for_eligibility must equal reports_sought_for_retrieval "
            f"- reports_not_retrieved ({expected_eligibility})"
        )

    if counts["studies_included"] > counts["reports_assessed_for_eligibility"]:
        errors.append("studies_included cannot exceed reports_assessed_for_eligibility")

    expected_reports_excluded = counts["reports_assessed_for_eligibility"] - counts["studies_included"]
    if counts["reports_excluded"] != expected_reports_excluded:
        errors.append(
            "reports_excluded must equal reports_assessed_for_eligibility - studies_included "
            f"({expected_reports_excluded})"
        )

    return errors


def _render_flow_markdown(counts: Dict[str, int], source_path: Path) -> str:
    generated = date.today().isoformat()
    return f"""## PRISMA flow accounting

Generated on {generated} from `{source_path}`.

| Stage | Count |
| --- | ---: |
| Records identified | {counts['records_identified']} |
| Duplicates removed | {counts['duplicates_removed']} |
| Records screened | {counts['records_screened']} |
| Records excluded | {counts['records_excluded']} |
| Reports sought for retrieval | {counts['reports_sought_for_retrieval']} |
| Reports not retrieved | {counts['reports_not_retrieved']} |
| Reports assessed for eligibility | {counts['reports_assessed_for_eligibility']} |
| Reports excluded | {counts['reports_excluded']} |
| Studies included | {counts['studies_included']} |

### Consistency checks

- records_screened = records_identified - duplicates_removed
- records_excluded = records_screened - reports_sought_for_retrieval
- reports_assessed_for_eligibility = reports_sought_for_retrieval - reports_not_retrieved
- reports_excluded = reports_assessed_for_eligibility - studies_included
"""


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate PRISMA flow accounting Markdown from a standardized screening log."
    )
    parser.add_argument("--screening-log", required=True, help="Path to <topic>.screening-log.md")
    parser.add_argument("--out", required=True, help="Output markdown file path")
    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    screening_path = Path(args.screening_log).expanduser().resolve()
    out_path = Path(args.out).expanduser().resolve()

    if not screening_path.exists():
        print(f"ERROR: screening log not found: {screening_path}", file=sys.stderr)
        return 1

    try:
        markdown = screening_path.read_text(encoding="utf-8")
        counts = _extract_counts(markdown)
        consistency_errors = _validate_consistency(counts)
        if consistency_errors:
            details = "\n- " + "\n- ".join(consistency_errors)
            raise ValueError("PRISMA counts are inconsistent:" + details)

        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(_render_flow_markdown(counts, source_path=screening_path), encoding="utf-8")
        print(f"Generated PRISMA flow markdown: {out_path}")
        return 0
    except Exception as exc:  # pylint: disable=broad-except
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
