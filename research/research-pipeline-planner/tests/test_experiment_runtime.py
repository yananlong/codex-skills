#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "harness_runtime.py"


class ExperimentRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.env = dict(os.environ, HARNESS_DISABLE_FSYNC="1")
        for name in ("experiment-plan", "data", "evaluation", "results", "episodes"):
            (self.root / name).mkdir(parents=True, exist_ok=True)
        (self.root / "data/test.jsonl").write_text('{"x":1}\n', encoding="utf-8")
        (self.root / "evaluation/score.py").write_text("print('score')\n", encoding="utf-8")
        self.commitment = {
            "schema_version": "1.0",
            "paper_id": "fixture-paper",
            "identity_version": 1,
            "status": "committed",
        }
        self.claims = [{"claim_id": "C1", "linked_blocks": ["B1", "B2"]}]
        self.blocks = [
            self.block("B1", "G1", "results/B1.json"),
            self.block("B2", "G2", "results/B2.json", dependencies=["B1"]),
        ]
        self.write_plans()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def block(self, block_id: str, gate_id: str, output: str, dependencies: list[str] | None = None) -> dict:
        return {
            "block_id": block_id,
            "claim_ids": ["C1"],
            "decision_gate_id": gate_id,
            "expected_output_artifact": output,
            "dependencies": dependencies or [],
            "execution": {
                "mode": "command",
                "entrypoint": {"argv": ["python", f"scripts/{block_id.lower()}.py"], "cwd": "."},
                "declared_inputs": [{"path": "data/test.jsonl", "snapshot": "digest-at-start"}],
                "declared_evaluator_artifacts": [
                    {"path": "evaluation/score.py", "snapshot": "digest-at-start"}
                ],
                "required_outputs": [{"path": output, "kind": "metrics"}],
            },
            "lineage_policy": {
                "allowed_relations": [
                    "baseline", "replication", "ablation", "parameter_variation",
                    "negative_control", "sensitivity", "alternative_hypothesis",
                    "technical_retry",
                ]
            },
        }

    def write_plans(self) -> None:
        (self.root / "research-commitment.json").write_text(json.dumps(self.commitment), encoding="utf-8")
        (self.root / "experiment-plan/claim-map.json").write_text(json.dumps(self.claims), encoding="utf-8")
        (self.root / "experiment-plan/run-blocks.json").write_text(json.dumps(self.blocks), encoding="utf-8")

    def run_cli(self, *args: str, expect: int = 0) -> subprocess.CompletedProcess[str]:
        cp = subprocess.run(
            [sys.executable, str(SCRIPT), "--root", str(self.root), *args],
            text=True,
            capture_output=True,
            check=False,
            env=self.env,
        )
        self.assertEqual(cp.returncode, expect, msg=f"stdout:\n{cp.stdout}\nstderr:\n{cp.stderr}")
        return cp

    def add_experiment(
        self,
        item: str,
        block: str,
        *,
        depends: str | None = None,
        activation: str | None = None,
    ) -> None:
        output = f"results/{block}.json"
        args = [
            "add", "--work-item-id", item, "--stage", "experiment-plan",
            "--owner-skill", "research-experiment-runner", "--objective", f"Run {block}",
            "--acceptance-check", "Required output exists", "--expected-artifact", output,
            "--write-scope", "results/", "--experiment-run-blocks", "experiment-plan/run-blocks.json",
            "--experiment-claim-map", "experiment-plan/claim-map.json",
            "--experiment-block-id", block, "--commitment", "research-commitment.json",
        ]
        if depends:
            args += ["--depends-on", depends]
        if activation:
            args += ["--activation-condition", activation]
        self.run_cli(*args)

    def start(self, item: str) -> None:
        self.run_cli("start", item, "--actor", "research-experiment-runner")

    def episode(
        self,
        item: str,
        block: str,
        run_id: str,
        *,
        relation: str = "baseline",
        parent_run_id: str | None = None,
        parent_rationale: str | None = None,
        gate_result: str = "pass",
        disposition: str = "supports_claim",
        effect: str = "strengthen",
    ) -> Path:
        output = f"results/{block}.json"
        (self.root / output).write_text(json.dumps({"metric": 1}), encoding="utf-8")
        run = {
            "run_id": run_id,
            "block_id": block,
            "relation": relation,
            "parent_run_id": parent_run_id,
            "gate_id": f"G{block[1:]}",
            "gate_result": gate_result,
            "scientific_disposition": disposition,
            "claim_effects": [{"claim_id": "C1", "effect": effect, "scope": "fixture scope"}],
            "interpretation": "Fixture interpretation.",
        }
        if parent_rationale is not None:
            run["parent_rationale"] = parent_rationale
        data = {
            "schema_version": "1.0",
            "episode_id": f"EP-{item}-A1",
            "work_item_id": item,
            "attempt": 1,
            "owner_skill": "research-experiment-runner",
            "objective": f"Run {block}",
            "artifacts": [output],
            "verification": [{"check_id": "AC1", "result": "pass", "evidence": output}],
            "failures": [],
            "tool_calls": [],
            "observed_usage": {"max_tool_calls": 0},
            "outcome": "completed",
            "transition_request": "approve",
            "summary": "completed",
            "experiment_run": run,
        }
        path = self.root / "episodes" / f"EP-{item}-A1.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        return path

    def submit(self, item: str, episode: Path, expect: int = 0):
        return self.run_cli(
            "submit", item, "--episode", str(episode),
            "--actor", "research-experiment-runner", expect=expect,
        )

    def verify(self, item: str, gate: str, result: str, disposition: str, expect: int = 0):
        return self.run_cli(
            "verify", item, "--decision", "approve", "--evidence", "inspected",
            "--gate-result", f"{gate}={result}",
            "--scientific-disposition", disposition,
            "--actor", "research-pipeline-planner", expect=expect,
        )

    def states(self) -> dict[str, str]:
        items = json.loads((self.root / "work-items.json").read_text())["items"]
        return {item["work_item_id"]: item["state"] for item in items}

    def test_scientifically_negative_completed_run_does_not_unlock_pass_condition(self):
        self.add_experiment("WI-B1", "B1")
        self.add_experiment("WI-B2", "B2", depends="WI-B1", activation="WI-B1:G1:pass")
        self.start("WI-B1")
        ep = self.episode(
            "WI-B1", "B1", "RUN-B1-001", gate_result="fail",
            disposition="falsifies_claim", effect="kill",
        )
        self.submit("WI-B1", ep)
        self.verify("WI-B1", "G1", "fail", "falsifies_claim")
        self.assertEqual(self.states()["WI-B1"], "completed")
        self.assertEqual(self.states()["WI-B2"], "queued")

    def test_gate_pass_unlocks_conditioned_downstream_item(self):
        self.add_experiment("WI-B1", "B1")
        self.add_experiment("WI-B2", "B2", depends="WI-B1", activation="WI-B1:G1:pass")
        self.start("WI-B1")
        ep = self.episode("WI-B1", "B1", "RUN-B1-001")
        self.submit("WI-B1", ep)
        self.verify("WI-B1", "G1", "pass", "supports_claim")
        self.assertEqual(self.states()["WI-B2"], "ready")

    def test_experiment_submission_is_idempotent(self):
        self.add_experiment("WI-B1", "B1")
        self.start("WI-B1")
        ep = self.episode("WI-B1", "B1", "RUN-B1-001")
        self.submit("WI-B1", ep)
        cp = self.submit("WI-B1", ep)
        self.assertIn("already submitted", cp.stdout)
        events = [
            json.loads(line)
            for line in (self.root / "harness-events.jsonl").read_text().splitlines()
        ]
        self.assertEqual(sum(event["event_type"] == "episode_submitted" for event in events), 1)

    def test_declared_input_mutation_blocks_submission(self):
        self.add_experiment("WI-B1", "B1")
        self.start("WI-B1")
        (self.root / "data/test.jsonl").write_text('{"x":2}\n', encoding="utf-8")
        ep = self.episode("WI-B1", "B1", "RUN-B1-001")
        cp = self.submit("WI-B1", ep, expect=1)
        self.assertIn("declared snapshot changed", cp.stderr)

    def test_bound_plan_digest_mutation_blocks_start(self):
        self.add_experiment("WI-B1", "B1")
        self.blocks[0]["decision_gate_id"] = "G9"
        self.write_plans()
        cp = self.run_cli("start", "WI-B1", "--actor", "research-experiment-runner", expect=1)
        self.assertIn("run-blocks digest changed", cp.stderr)

    def test_duplicate_run_id_rejected(self):
        self.add_experiment("WI-B1", "B1")
        self.start("WI-B1")
        ep = self.episode("WI-B1", "B1", "RUN-DUP")
        self.submit("WI-B1", ep)
        self.verify("WI-B1", "G1", "pass", "supports_claim")
        self.add_experiment("WI-B2", "B2", depends="WI-B1")
        self.start("WI-B2")
        ep2 = self.episode("WI-B2", "B2", "RUN-DUP")
        cp = self.submit("WI-B2", ep2, expect=1)
        self.assertIn("duplicate experiment run ID", cp.stderr)

    def test_technical_retry_requires_parent(self):
        self.add_experiment("WI-B1", "B1")
        self.start("WI-B1")
        ep = self.episode(
            "WI-B1", "B1", "RUN-B1-002", relation="technical_retry",
            disposition="diagnostic_only", effect="unchanged", gate_result="not_applicable",
        )
        cp = self.submit("WI-B1", ep, expect=1)
        self.assertIn("requires parent_run_id", cp.stderr)

    def test_baseline_cannot_have_parent(self):
        self.add_experiment("WI-B1", "B1")
        self.start("WI-B1")
        ep = self.episode("WI-B1", "B1", "RUN-B1-001", parent_run_id="RUN-X")
        cp = self.submit("WI-B1", ep, expect=1)
        self.assertIn("baseline experiment run cannot have", cp.stderr)

    def test_activation_predecessor_must_also_be_dependency(self):
        self.add_experiment("WI-B1", "B1")
        cp = self.run_cli(
            "add", "--work-item-id", "WI-B2", "--stage", "experiment-plan",
            "--owner-skill", "research-experiment-runner", "--objective", "Run B2",
            "--acceptance-check", "Required output exists", "--expected-artifact", "results/B2.json",
            "--write-scope", "results/", "--experiment-run-blocks", "experiment-plan/run-blocks.json",
            "--experiment-claim-map", "experiment-plan/claim-map.json", "--experiment-block-id", "B2",
            "--commitment", "research-commitment.json", "--activation-condition", "WI-B1:G1:pass",
            expect=1,
        )
        self.assertIn("must also be supplied with --depends-on", cp.stderr)

    def test_verifier_gate_result_must_match_submitted_run(self):
        self.add_experiment("WI-B1", "B1")
        self.start("WI-B1")
        ep = self.episode("WI-B1", "B1", "RUN-B1-001")
        self.submit("WI-B1", ep)
        cp = self.verify("WI-B1", "G1", "fail", "supports_claim", expect=1)
        self.assertIn("matching --gate-result", cp.stderr)

    def test_lineage_projection_is_replay_deterministic(self):
        self.add_experiment("WI-B1", "B1")
        self.start("WI-B1")
        ep = self.episode("WI-B1", "B1", "RUN-B1-001")
        self.submit("WI-B1", ep)
        self.verify("WI-B1", "G1", "pass", "supports_claim")
        first = self.run_cli("experiment-lineage", "--block-id", "B1").stdout
        self.run_cli("replay")
        second = self.run_cli("experiment-lineage", "--block-id", "B1").stdout
        self.assertEqual(first, second)
        self.assertEqual(json.loads(first)["nodes"][0]["run_id"], "RUN-B1-001")


if __name__ == "__main__":
    unittest.main()
