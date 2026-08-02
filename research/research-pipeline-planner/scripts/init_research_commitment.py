#!/usr/bin/env python3
"""Initialize the canonical paper-level research commitment artifact."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

CONTRIBUTION_CLASSES = (
    "theory", "method", "protocol", "benchmark", "dataset",
    "empirical-finding", "position", "mixed",
)
PAPER_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,191}$")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target_dir", type=Path)
    parser.add_argument("--paper-id", required=True)
    parser.add_argument("--contribution-class", default="mixed", choices=CONTRIBUTION_CLASSES)
    parser.add_argument("--force", action="store_true", help="Explicitly replace an existing commitment file.")
    args = parser.parse_args()
    if not PAPER_ID_RE.fullmatch(args.paper_id):
        raise SystemExit("--paper-id must use letters, numbers, dot, underscore, colon, or hyphen")
    root = args.target_dir.expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    path = root / "research-commitment.json"
    if path.exists() and not args.force:
        raise SystemExit(f"Refusing to overwrite {path}; use --force only for an intentional reset")
    data = {
        "schema_version": "1.0",
        "paper_id": args.paper_id,
        "identity_version": 1,
        "status": "exploring",
        "main_question": "",
        "central_object_or_phenomenon": "",
        "contribution_class": args.contribution_class,
        "minimum_publishable_claim": "",
        "primary_evidence_obligation": "",
        "intended_audience": "",
        "permitted_refinements": [],
        "pivot_triggers": [],
        "kill_conditions": [],
        "successor_idea_policy": "park",
        "next_mandatory_evidence_artifact": "",
        "reconsideration_gate": "",
        "selection_history": [],
        "predecessor_failures": [],
        "last_change_class": "D0",
        "last_change_rationale": "initialized",
    }
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"created {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
