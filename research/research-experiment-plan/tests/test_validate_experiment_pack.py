#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "validate_experiment_pack.py"
INIT = Path(__file__).resolve().parents[1] / "scripts" / "init_experiment_pack.py"
DRIFT = Path(__file__).resolve().parents[1] / "scripts" / "check_plan_drift.py"


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
            "block_id":"B1","paper_role":"main","claim_ids":["C1"],"decision_gate_id":"G1",
            "anti_claims_ruled_out":["No improvement"],
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
            "predecessor_failures":[],
            "execution":{
                "mode":"command",
                "entrypoint":{"argv":["python","run_b1.py"],"cwd":"."},
                "declared_inputs":[{"path":"data/test.jsonl","snapshot":"digest-at-start"}],
                "declared_evaluator_artifacts":[{"path":"evaluation/score.py","snapshot":"digest-at-start"}],
                "required_outputs":[{"path":"results/B1.json","kind":"metrics"}],
            },
            "lineage_policy":{"allowed_relations":["baseline","replication","ablation","technical_retry"]},
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
- Decision gate ID: G1
- Expected implementation entrypoint: run_b1.py
- Expected command or notebook: python run_b1.py
- Output artifacts to produce: results/B1.json
- Auditor-facing checks: verify split and accounting
- Intended lineage relation: baseline
- Parent run ID or rationale: no parent; baseline
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

    def test_repair_action_enum_and_legacy_values(self):
        self.claims[0]["decision_if_unproven"] = {"action": "sharpen_comparator", "note": "add the matched baseline"}
        self.write_all()
        cp = self.run_validator()
        self.assertNotIn("decision_if_unproven", cp.stdout)
        self.claims[0]["decision_if_unproven"] = "drop"
        self.write_all()
        cp = self.run_validator()
        self.assertIn("legacy value 'drop'", cp.stdout)
        self.claims[0]["decision_if_unproven"] = {"action": "smaller_claim"}
        self.write_all()
        cp = self.run_validator(expect=1)
        self.assertIn("decision_if_unproven.action must be one of", cp.stdout)

    def test_gate_revise_cell_without_action_warns(self):
        self.write_all()
        cp = self.run_validator()
        self.assertIn("'Revise if' does not name a repair action", cp.stdout)
        gates = self.paths["decision-gates"].read_text().replace(
            "| result inconclusive |", "| `add_evidence`: rerun with a second seed |"
        )
        self.paths["decision-gates"].write_text(gates)
        cp = self.run_validator()
        self.assertNotIn("Revise if", cp.stdout)

    def set_tracker(self, rows: list[str], kind_column: bool = True) -> None:
        header = "| Run ID | Block ID | Gate ID | Purpose | Priority | Status | Owner | Dependency | Output artifact | Notes |"
        rule = "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"
        if kind_column:
            header += " Kind |"
            rule += " --- |"
        self.paths["tracker"].write_text("# Experiment Tracker\n" + "\n".join([header, rule, *rows]) + "\n")

    def drift(self, *extra, expect=0):
        args = [sys.executable, str(DRIFT), "--run-blocks", str(self.paths["run-blocks"]),
                "--tracker", str(self.paths["tracker"]), *extra]
        cp = subprocess.run(args, text=True, capture_output=True)
        self.assertEqual(cp.returncode, expect, msg=f"stdout:\n{cp.stdout}\nstderr:\n{cp.stderr}")
        return cp

    def test_tracker_without_kind_column_still_validates(self):
        self.write_all()
        self.set_tracker(["| R1 | B1 | G1 | primary | must-run | planned | owner | | results/B1.json | |"], kind_column=False)
        self.run_validator()

    def test_unplanned_run_may_name_an_undeclared_block(self):
        self.write_all()
        self.set_tracker([
            "| R1 | B1 | G1 | primary | must-run | planned | owner | | results/B1.json | | planned |",
            "| X1 | probe | - | sanity probe | - | analyzed | owner | | results/x1.json | | diagnostic |",
        ])
        self.run_validator()
        self.set_tracker([
            "| R1 | B1 | G1 | primary | must-run | planned | owner | | results/B1.json | | planned |",
            "| X1 | probe | - | sanity probe | - | analyzed | owner | | results/x1.json | | |",
        ])
        cp = self.run_validator(expect=1)
        self.assertIn("mark the row's Kind as unplanned", cp.stdout)
        self.set_tracker(["| R1 | B1 | G1 | primary | must-run | planned | owner | | results/B1.json | | sideways |"])
        cp = self.run_validator(expect=1)
        self.assertIn("invalid kind 'sideways'", cp.stdout)

    def test_drift_report_lists_each_kind_of_drift(self):
        self.write_all()
        self.set_tracker([
            "| R0 | B1 | G1 | retry first | must-run | analyzed | owner | | results/r0.json | | retry |",
            "| X1 | probe | - | sanity probe | - | analyzed | owner | | results/x1.json | | diagnostic |",
            "| X2 | ghost | - | forgotten | - | analyzed | owner | | results/x2.json | | planned |",
            "| X3 | B1 | G1 | precursor deciding | - | analyzed | owner | | | | precursor |",
        ])
        cp = self.drift("--json")
        report = json.loads(cp.stdout)
        self.assertEqual(report["undeclared_runs_marked_planned"], ["X2 (block 'ghost', kind planned, status analyzed)"])
        self.assertEqual(len(report["undeclared_runs_by_kind"]), 1)
        self.assertEqual(len(report["kind_contradictions"]), 2)
        self.assertEqual(report["must_run_blocks_never_run"], [])
        self.drift("--fail-on-drift", expect=1)

    def test_drift_reports_must_run_blocks_that_never_ran_and_audit_mismatches(self):
        self.write_all()
        self.set_tracker(["| R1 | B1 | G1 | primary | must-run | planned | owner | | results/B1.json | | planned |"])
        audit = self.root / "results-audit.json"
        audit.write_text(json.dumps({"audits": [{"audit_id": "A1", "source_runs": [{"run_id": "R1", "block_id": "B1", "run_kind": "unplanned"}],
                                                  "standalone_runs": [{"run_id": "S9", "path": "s9.json"}]}]}))
        results = self.root / "results"
        results.mkdir()
        (results / "B1.json").write_text("{}")
        (results / "stray.json").write_text("{}")
        report = json.loads(self.drift("--json", "--audit", str(audit), "--results-dir", str(results)).stdout)
        self.assertEqual(report["must_run_blocks_never_run"], ["B1"])
        self.assertIn("R1: audit A1 records kind unplanned, the tracker planned", report["kind_contradictions"])
        self.assertEqual(report["audited_runs_missing_from_tracker"], ["S9 (audit A1, kind planned)"])
        self.assertEqual(report["unreferenced_result_files"], ["stray.json"])
        self.set_tracker(["| R1 | B1 | G1 | primary | must-run | completed / audited | owner | | results/B1.json | | unplanned |"])
        report = json.loads(self.drift("--json").stdout)
        self.assertEqual(report["must_run_blocks_never_run"], [])
        cp = self.drift()
        self.assertIn("Plan drift: 0 item(s)", cp.stdout)

    def test_initialized_pack_passes_structural_profile(self):
        init_root = self.root / "fresh"
        cp = subprocess.run([sys.executable, str(INIT), str(init_root)], text=True, capture_output=True)
        self.assertEqual(cp.returncode, 0, cp.stderr)
        args = [sys.executable, str(SCRIPT)]
        for name in self.paths:
            args += [f"--{name}", str(init_root / self.paths[name].name)]
        cp = subprocess.run(args, text=True, capture_output=True)
        self.assertEqual(cp.returncode, 0, msg=f"stdout:\n{cp.stdout}\nstderr:\n{cp.stderr}")

    def test_valid_confirmatory_pack(self):
        cp = self.run_validator()
        self.assertIn("decision-gate bindings", cp.stdout)

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
        second = json.loads(json.dumps(self.blocks[0]))
        second.update(block_id="B2", claim_ids=["C1"], decision_gate_id="G2", dependencies=["B1"])
        second["execution"]["required_outputs"] = [{"path":"results/B2.json"}]
        second["expected_output_artifact"] = "results/B2.json"
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

    def test_unknown_block_gate_rejected(self):
        self.blocks[0]["decision_gate_id"] = "G9"
        self.write_all()
        cp = self.run_validator(expect=1)
        self.assertIn("unknown decision gate", cp.stdout)

    def test_gate_must_open_after_its_bound_block(self):
        text = self.paths["decision-gates"].read_text().replace("| G1 | B1 |", "| G1 | B9 |")
        self.paths["decision-gates"].write_text(text)
        cp = self.run_validator(expect=1)
        self.assertIn("unknown block", cp.stdout)

    def test_confirmatory_must_run_requires_execution(self):
        del self.blocks[0]["execution"]
        self.write_all()
        cp = self.run_validator(expect=1)
        self.assertIn("execution is required", cp.stdout)

    def test_required_output_must_match_expected_output(self):
        self.blocks[0]["execution"]["required_outputs"] = [{"path":"results/other.json"}]
        self.write_all()
        cp = self.run_validator(expect=1)
        self.assertIn("expected_output_artifact", cp.stdout)

    def test_lineage_policy_rejects_pivot(self):
        self.blocks[0]["lineage_policy"]["allowed_relations"].append("pivot")
        self.write_all()
        cp = self.run_validator(expect=1)
        self.assertIn("unsupported relations", cp.stdout)


    def init_args(self, init_root: Path, profile: str) -> list[str]:
        args = [sys.executable, str(SCRIPT)]
        for name in self.paths:
            args += [f"--{name}", str(init_root / self.paths[name].name)]
        return args + ["--assurance-profile", profile]

    def test_exploratory_profile_rejects_untouched_init_pack(self):
        init_root = self.root / "fresh"
        cp = subprocess.run([sys.executable, str(INIT), str(init_root)], text=True, capture_output=True)
        self.assertEqual(cp.returncode, 0, cp.stderr)
        cp = subprocess.run(self.init_args(init_root, "exploratory"), text=True, capture_output=True)
        self.assertEqual(cp.returncode, 1, msg=cp.stdout + cp.stderr)
        for text in (".claim must be", ".falsifier must be", ".success_criterion must be", ".metrics must be", "proceed if must be substantive"):
            self.assertIn(text, cp.stdout)

    def test_exploratory_profile_accepts_filled_pack(self):
        self.claims[0]["evidence_class"] = "exploratory"
        self.blocks[0]["evidence_class"] = "exploratory"
        self.write_all()
        cp = self.run_validator(profile="exploratory")
        self.assertIn("are filled in", cp.stdout)

    def test_exploratory_profile_rejects_empty_gate_cell(self):
        text = self.paths["decision-gates"].read_text().replace("| criterion fails |", "| |")
        self.paths["decision-gates"].write_text(text)
        cp = self.run_validator(profile="exploratory", expect=1)
        self.assertIn("stop if must be substantive", cp.stdout)

    def test_versioned_envelopes_are_accepted(self):
        self.paths["claim-map"].write_text(json.dumps({"schema_version": "1.0", "plan_version": "v2", "claims": self.claims}))
        self.paths["run-blocks"].write_text(json.dumps({"schema_version": "1.0", "plan_version": "v2", "blocks": self.blocks}))
        self.run_validator()
        self.paths["run-blocks"].write_text(json.dumps({"schema_version": "1.0", "items": self.blocks}))
        cp = self.run_validator(expect=1)
        self.assertIn("envelope must contain a 'blocks' array", cp.stdout)

    def test_history_table_under_tracker_heading_is_ignored(self):
        text = self.paths["tracker"].read_text() + """
Superseded rows (append-only history):

| Run ID | Block ID | Status |
| --- | --- | --- |
| R0 | B0 | dropped |
"""
        self.paths["tracker"].write_text(text)
        self.run_validator()


if __name__ == "__main__":
    unittest.main()
