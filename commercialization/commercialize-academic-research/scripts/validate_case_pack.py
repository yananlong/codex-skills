#!/usr/bin/env python3
"""Validate a research-commercialization case pack structure."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REQUIRED_SECTIONS = {
    "context": [
        "## Research asset",
        "## Core technical claim",
        "## Constraints",
        "## Initial commercialization objective",
        "## Required analysis chain",
    ],
    "source-log": [
        "## Evidence posture",
        "## Search and source log",
        "## Source-backed facts",
        "## Assumptions where evidence is missing",
    ],
    "evidence-ledger": [
        "## Commercialization evidence table",
        "## Hypothesis ledger",
        "## Evidence log",
    ],
    "pain-points": [
        "## Candidate segments",
        "## Ranked problem theses",
        "## Stakeholder map",
    ],
    "options": [
        "## Initial wedge options",
        "## Commercialization path comparison",
        "## Sequence",
        "## Recommendation",
    ],
    "validation-plan": [
        "## Risk-retirement priorities",
        "## Experiments",
        "## Pilot gate",
        "## Immediate next steps",
    ],
    "decision-log": [
        "## Assumptions in force",
        "## Decisions made",
        "## Open questions",
    ],
}

CHAIN_LINKS = [
    "| Research claim |",
    "| Workflow pain |",
    "| Current workaround |",
    "| Buyer/budget |",
    "| Why now |",
    "| Evidence |",
    "| Weak link |",
    "| Validation test |",
]

PILOT_GATE_FIELDS = [
    "- Economic buyer:",
    "- Paid or conversion commitment:",
    "- Success metric:",
    "- Timeline:",
    "- Required data/integration access:",
    "- Adoption owner:",
    "- Decision after pilot:",
]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def validate(case_dir: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    if not case_dir.exists() or not case_dir.is_dir():
        return [f"case directory not found: {case_dir}"], warnings

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

    context = case_dir / f"{case}.context.md"
    if context.exists():
        text = read(context)
        for link in CHAIN_LINKS:
            if link not in text:
                errors.append(f"{context.name}: missing analysis-chain row {link!r}")

    validation_plan = case_dir / f"{case}.validation-plan.md"
    if validation_plan.exists():
        text = read(validation_plan)
        for field in PILOT_GATE_FIELDS:
            if field not in text:
                errors.append(f"{validation_plan.name}: missing pilot-gate field {field!r}")

    source_log = case_dir / f"{case}.source-log.md"
    if source_log.exists():
        text = read(source_log)
        if "official / regulator / customer / procurement / peer-reviewed" not in text:
            warnings.append(f"{source_log.name}: source-type legend may be incomplete")

    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a commercialization case pack.")
    parser.add_argument("case_dir")
    args = parser.parse_args()
    errors, warnings = validate(Path(args.case_dir).resolve())

    for warning in warnings:
        print(f"[WARN] {warning}")
    for error in errors:
        print(f"[ERROR] {error}")
    if errors:
        return 1
    print("[OK] Case pack structure is valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
