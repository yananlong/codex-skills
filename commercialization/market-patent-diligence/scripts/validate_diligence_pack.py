#!/usr/bin/env python3
"""Validate a market and patent diligence pack."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REQUIRED_SECTIONS = {
    "scope": [
        "## Asset or thesis",
        "## Search posture",
        "## Search spine",
        "## Decision the diligence informs",
    ],
    "source-log": [
        "## Retrieval context",
        "## Source log",
        "## Unverified but material claims",
    ],
    "patent-landscape": [
        "## Patent search strategy",
        "## Patent families and records",
        "## Assignee and citation signals",
        "## Legal caveats",
    ],
    "market-map": [
        "## Market and buyer hypotheses",
        "## Purchase and budget evidence",
        "## Market evidence limits",
    ],
    "competitor-substitute-map": [
        "## Competitor and substitute classes",
        "## Incumbent and partner targets",
    ],
    "regulatory-procurement-funding": [
        "## Regulatory, reimbursement, standards, and compliance",
        "## Procurement and public purchasing",
        "## Funding and translational programs",
    ],
    "evidence-ledger": [
        "## Evidence ledger",
        "## Weak links",
    ],
}

REQUIRED_HANDOFF_FIELDS = [
    "case",
    "asset_or_thesis",
    "coverage",
    "retrieval_dates",
    "strongest_signals",
    "weakest_assumptions",
    "patent_landscape_confidence",
    "market_evidence_confidence",
    "recommended_next_skill",
    "questions_for_next_skill",
    "limits",
]

ALLOWED_NEXT_SKILLS = {
    "commercialize-academic-research",
    "research-systematic-literature-review",
    "research-novelty-review",
    "research-results-auditor",
    "research-experiment-plan",
    "none",
}


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def validate(case_dir: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    if not case_dir.exists() or not case_dir.is_dir():
        return [f"diligence directory not found: {case_dir}"], warnings

    case = case_dir.name
    for suffix, sections in REQUIRED_SECTIONS.items():
        filename = f"{case}.{suffix}.md"
        path = case_dir / filename
        if not path.exists():
            errors.append(f"missing required file: {filename}")
            continue
        text = read(path)
        if not text.strip():
            errors.append(f"empty required file: {filename}")
        for section in sections:
            if section not in text:
                errors.append(f"{filename}: missing {section!r}")

    handoff_path = case_dir / f"{case}.handoff-to-commercialization.json"
    if not handoff_path.exists():
        errors.append(f"missing required file: {handoff_path.name}")
    else:
        try:
            handoff = json.loads(read(handoff_path))
        except json.JSONDecodeError as exc:
            errors.append(f"{handoff_path.name}: invalid JSON: {exc}")
        else:
            for field in REQUIRED_HANDOFF_FIELDS:
                if field not in handoff:
                    errors.append(f"{handoff_path.name}: missing field {field!r}")
            next_skill = handoff.get("recommended_next_skill")
            if next_skill not in ALLOWED_NEXT_SKILLS:
                warnings.append(
                    f"{handoff_path.name}: recommended_next_skill is not a known sibling skill"
                )

    source_log = case_dir / f"{case}.source-log.md"
    if source_log.exists():
        text = read(source_log)
        if "Reliability" not in text or "Limitation" not in text:
            warnings.append(f"{source_log.name}: source log should include reliability and limitation columns")

    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a market and patent diligence pack.")
    parser.add_argument("case_dir")
    args = parser.parse_args()
    errors, warnings = validate(Path(args.case_dir).resolve())

    for warning in warnings:
        print(f"[WARN] {warning}")
    for error in errors:
        print(f"[ERROR] {error}")
    if errors:
        return 1
    print("[OK] diligence pack structure is valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
