#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "validate_experiment_pack.py"


class ExperimentValidatorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.paths = {
            "plan": self.root / "experiment-plan.md",
            "tracker": self.root / "experiment-tracker.md",
            "claim-map": self.root / "claim-map.json",
            "run-blocks": self.root / "run-blocks.json",
            "decision-gates": self.root / "decision-gates.md",
            "bridge": self.root / "execution-bridge.md",
        }
        self.claims = [{
            "claim_id":"C1","priority":"primary","claim":"Method improves accuracy",
            "why_it_matters":"Central contribution","minimum_convincing_evidence":"Predeclared improvement",
            "anti_claim":"No improvement","falsifier":"Difference is non-positive",
            "decision_if_unproven":"reframe","linked_blocks":["B1"],
            "current_evidence_class":"exploratory","evidence_class":"confirmatory",
            "decision_rule":"Mean difference > 0","loss_contract":"Count all failures and misses",
            "falsification_test":"Upper confidence bound <= 0",
            "selection_history":["Frozen before targeted outcomes"],"predecessor_failures":[]
        }]
        self.blocks = [{
            "block_id":"B1","paper_role":"main","claim_ids":["C1"],"anti_claims_ruled_out":["No improvement"],
            "why_this_block_exists":"Tests the primary claim","dataset_split_task":"Frozen held-out test split",
            "systems_compared":["proposed","baseline"],"fixed_factors":["data"],"variable_factors":["method"],
            "metrics":["accuracy"],"setup_details":"Same compute and preprocessing","seeds":3,
            "success_criterion":"Mean difference > 0","minimum_effect_size":"0.01",
            "failure_interpretation":"Reframe claim","expected_output_artifact":"results/B1.json",
            "compute_budget":"10 GPU hours","dependencies":[],"priority":"must-run",
            "current_evidence_class":"exploratory","evidence_class":"confirmatory",
            "selection_rule":"All frozen cases","non_vacuity_check":"At least one case differs",
            "complete_outcome_accounting":"Count success, miss, skip, null, retry, timeout and failure",
            "hidden_information_controls":"No oracle labels in model context","independence_requirements":[],
            "independence_evidence":"","operational_threat_model":"","operational_harms":"",
            "predecessor_failures":[]
        }]
        self.write_all()

    def tearDown(self):
        self.temp.cleanup()

    def write_all(self):
        self.paths["plan"].write_text("""# Experiment Plan
## Context
x
## Claim Map
x
## Experimental Storyline
x
## Non-Vacuity Preflight
x
## Experiment Blocks
x
## Run Order
| Order | Block | Purpose | Dependency | Gate ID | Stop / go gate | Est. cost |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | B1 | primary | | G1 | proceed if positive | 10 |
## Decision Gates
x
## Risks and Confounds
x
""")
        self.paths["tracker"].write_text("""# Experiment Tracker
| Run ID | Block ID | Gate ID | Purpose | Priority | Status | Owner | Dependency | Output artifact | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| R1 | B1 | G1 | primary | must-run | planned | owner | | results/B1.json | |
""")
        self.paths["decision-gates"].write_text("""# Decision Gates
| Gate ID | Opens after | Decision question | Proceed if | Revise if | Stop if | Owner |
| --- | --- | --- | --- | --- | --- | --- |
| G1 | B1 | Does B1 support C1? | criterion passes | result inconclusive | criterion fails | owner |
""")
        self.paths["bridge"].write_text("""# Execution Bridge
## Block Hand-off
### B1
- Claim IDs: C1
- Expected implementation entrypoint: run_b1.py
- Expected command or notebook: python run_b1.py
- Output artifacts to produce: results/B1.json
- Auditor-facing checks: verify split and accounting
- Hidden information unavailable to the evaluated system: held-out labels
- Failure, skip, null, timeout, and retry states to retain: all states
- Idempotency and restart requirements: stable run ID and atomic outputs
""")
        self.paths["claim-map"].write_text(json.dumps(self.claims))
        self.paths["run-blocks"].write_text(json.dumps(self.blocks))

    def run_validator(self, profile="confirmatory", expect=0):
        args = [sys.executable, str(SCRIPT)]
        for name, path in self.paths.items():
            args += [f"--{name}", str(path)]
        args += ["--assurance-profile", profile]
        cp = subprocess.run(args, text=True, capture_output=True)
        self.assertEqual(cp.returncode, expect, msg=f"stdout:\n{cp.stdout}\nstderr:\n{cp.stderr}")
        return cp

    def test_valid_confirmatory_pack(self):
        cp = self.run_validator()
        self.assertIn("evidence-class ordering", cp.stdout)

    def test_confirmatory_claim_cannot_link_only_exploratory_block(self):
        self.blocks[0]["evidence_class"] = "exploratory"
        self.write_all()
        cp = self.run_validator(expect=1)
        self.assertIn("no linked block at or above", cp.stdout)

    def test_links_must_be_reciprocal_from_claim(self):
        self.blocks[0]["claim_ids"] = []
        self.write_all()
        cp = self.run_validator(expect=1)
        self.assertIn("not reciprocal", cp.stdout)

    def test_links_must_be_reciprocal_from_block(self):
        self.claims[0]["linked_blocks"] = []
        self.write_all()
        cp = self.run_validator(expect=1)
        self.assertIn("not reciprocal", cp.stdout)

    def test_confirmatory_does_not_require_independence(self):
        self.blocks[0]["independence_requirements"] = []
        self.blocks[0]["independence_evidence"] = ""
        self.write_all()
        self.run_validator()

    def test_independently_verified_requires_independence(self):
        self.claims[0]["evidence_class"] = "independently_verified"
        self.blocks[0]["evidence_class"] = "independently_verified"
        self.write_all()
        cp = self.run_validator(expect=1)
        self.assertIn("independence_requirements", cp.stdout)

    def test_operational_requires_threat_model_and_harms(self):
        self.claims[0]["evidence_class"] = "operational_high_stakes"
        self.blocks[0]["evidence_class"] = "operational_high_stakes"
        self.blocks[0]["independence_requirements"]=["separate evaluator"]
        self.blocks[0]["independence_evidence"]="Independent team"
        self.write_all()
        cp = self.run_validator(expect=1)
        self.assertIn("operational_threat_model", cp.stdout)
        self.assertIn("operational_harms", cp.stdout)

    def test_dependency_cycle_rejected(self):
        second = dict(self.blocks[0])
        second.update(block_id="B2", claim_ids=["C1"], dependencies=["B1"])
        self.blocks[0]["dependencies"]=["B2"]
        self.blocks.append(second)
        self.claims[0]["linked_blocks"].append("B2")
        self.write_all()
        cp = self.run_validator(expect=1)
        self.assertIn("dependency cycle", cp.stdout)

    def test_tracker_unknown_gate_rejected(self):
        text = self.paths["tracker"].read_text().replace("| R1 | B1 | G1 |", "| R1 | B1 | G9 |")
        self.paths["tracker"].write_text(text)
        cp = self.run_validator(expect=1)
        self.assertIn("unknown gate", cp.stdout)

    def test_bridge_must_be_substantive(self):
        text = self.paths["bridge"].read_text().replace("python run_b1.py", "")
        self.paths["bridge"].write_text(text)
        cp = self.run_validator(expect=1)
        self.assertIn("Expected command or notebook", cp.stdout)

    def test_bridge_heading_must_match_exact_block_id(self):
        text = self.paths["bridge"].read_text().replace("### B1", "### B10")
        self.paths["bridge"].write_text(text)
        cp = self.run_validator(expect=1)
        self.assertIn("missing section for B1", cp.stdout)

    def test_invalid_evidence_class_is_controlled_validation_error(self):
        self.claims[0]["evidence_class"] = "bogus"
        self.write_all()
        cp = self.run_validator(expect=1)
        self.assertIn("evidence_class", cp.stdout)
        self.assertNotIn("Traceback", cp.stderr)


if __name__ == "__main__":
    unittest.main()
