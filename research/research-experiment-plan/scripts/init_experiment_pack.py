#!/usr/bin/env python3
"""Create deterministic scaffolds for experiment planning."""

from __future__ import annotations

import argparse
from pathlib import Path


FILE_TEMPLATES = {
    "experiment-plan.md": """# Experiment Plan

## Context

- Problem:
- Evaluation goal:
- Operating mode: standalone / orchestrated
- Upstream artifacts used:
- Main constraints:
- Dominant contribution:
- Critical reviewer concern:
- Current evidence class: exploratory
- Requested evidence class: exploratory
- Outcome-informed selection history:
- Material predecessor failures:

## Claim Map

| Claim ID | Type | Why it matters | Minimum convincing evidence | Anti-claim to rule out | Falsifier | Decision if unproven |
| --- | --- | --- | --- | --- | --- | --- |
| C1 | primary / supporting | | | | | |

## Experimental Storyline

| Block | Role | Paper placement | Why it exists |
| --- | --- | --- | --- |
| main-anchor | anchor / novelty / simplicity / frontier / failure-analysis | main / appendix / cut | |

## Non-Vacuity Preflight

- Discriminating case:
- Plausible comparator win:
- Complete loss or outcome contract:
- Case-selection independence:
- Skip, failure, null, and retry accounting:
- Gate result: pass / revise / exploratory-only

## Experiment Blocks

### Block 1

- Block ID:
- Claim tested:
- Anti-claim ruled out:
- Why this block exists:
- Dataset / split / task:
- Systems compared:
- Fixed factors:
- Variable factors:
- Metrics:
- Setup details:
- Seeds:
- Success criterion:
- Minimum effect size or threshold:
- Failure interpretation:
- Table / figure target:
- Expected output artifact:
- Compute budget:
- Dependencies:
- Priority: must-run / nice-to-have / defer
- Current evidence class: exploratory
- Requested evidence class: exploratory
- Selection rule:
- Non-vacuity check:
- Complete outcome accounting:
- Hidden-information controls:
- Independence requirements:
- Independence evidence:
- Predecessor failures:

## Run Order

| Order | Block | Purpose | Dependency | Gate ID | Stop / go gate | Est. cost |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | | | | G1 | | |

## Decision Gates

| Gate ID | Opens after | Decision question | Proceed if | Revise if | Stop if |
| --- | --- | --- | --- | --- | --- |
| G1 | Block 1 | | | | |

## Risks and Confounds

- Risk:
- Mitigation:
""",
    "experiment-tracker.md": """# Experiment Tracker

| Run ID | Block ID | Gate ID | Purpose | Priority | Status | Owner | Dependency | Output artifact | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| R001 | B1 | G1 | | must-run | planned | | | | |
""",
    "claim-map.json": """[
  {
    "claim_id": "C1",
    "priority": "primary",
    "claim": "",
    "why_it_matters": "",
    "minimum_convincing_evidence": "",
    "anti_claim": "",
    "falsifier": "",
    "decision_if_unproven": "reframe",
    "linked_blocks": [
      "B1"
    ],
    "current_evidence_class": "exploratory",
    "evidence_class": "exploratory",
    "decision_rule": "",
    "loss_contract": "",
    "falsification_test": "",
    "selection_history": [
      "No task-relevant outcomes inspected at initialization."
    ],
    "predecessor_failures": []
  }
]
""",
    "run-blocks.json": """[
  {
    "block_id": "B1",
    "paper_role": "main",
    "claim_ids": [
      "C1"
    ],
    "anti_claims_ruled_out": [],
    "why_this_block_exists": "",
    "dataset_split_task": "",
    "systems_compared": [],
    "fixed_factors": [],
    "variable_factors": [],
    "metrics": [],
    "setup_details": "",
    "seeds": 3,
    "success_criterion": "",
    "minimum_effect_size": "",
    "failure_interpretation": "",
    "expected_output_artifact": "",
    "compute_budget": "",
    "dependencies": [],
    "priority": "must-run",
    "current_evidence_class": "exploratory",
    "evidence_class": "exploratory",
    "selection_rule": "",
    "non_vacuity_check": "",
    "complete_outcome_accounting": "",
    "hidden_information_controls": "",
    "independence_requirements": [],
    "independence_evidence": "",
    "operational_threat_model": "",
    "operational_harms": "",
    "predecessor_failures": []
  }
]
""",
    "decision-gates.md": """# Decision Gates

| Gate ID | Opens after | Decision question | Proceed if | Revise if | Stop if | Owner |
| --- | --- | --- | --- | --- | --- | --- |
| G1 | B1 | | | | | |
""",
    "execution-bridge.md": """# Execution Bridge

## Block Hand-off

### B1

- Claim IDs:
- Current evidence class: exploratory
- Requested evidence class: exploratory
- Inputs required:
- Expected implementation entrypoint:
- Expected command or notebook:
- Output artifacts to produce:
- Auditor-facing checks:
- Hidden information unavailable to the evaluated system:
- Failure, skip, null, timeout, and retry states to retain:
- Idempotency and restart requirements:
- Known blockers:
""",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target_dir", type=Path, help="Directory where the pack will be created.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing files.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.target_dir.mkdir(parents=True, exist_ok=True)

    existing = [name for name in FILE_TEMPLATES if (args.target_dir / name).exists()]
    if existing and not args.force:
        raise SystemExit(
            "Refusing to overwrite existing files without --force: " + ", ".join(sorted(existing))
        )

    for name, content in FILE_TEMPLATES.items():
        path = args.target_dir / name
        path.write_text(content, encoding="utf-8")
        print(f"created {path}")


if __name__ == "__main__":
    main()
