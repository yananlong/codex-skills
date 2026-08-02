#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INIT = ROOT / "scripts" / "init_research_pack.py"
RUNTIME = ROOT / "scripts" / "harness_runtime.py"
VALIDATE = ROOT / "scripts" / "validate_research_pack.py"


class ExperimentPackIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.suite = Path(self.temp.name) / "suite"
        self.env = dict(os.environ, HARNESS_DISABLE_FSYNC="1")
        self.run_cmd([sys.executable, str(INIT), str(self.suite)])
        for name in ("data", "evaluation", "results"):
            (self.suite / name).mkdir(exist_ok=True)
        (self.suite / "data/test.jsonl").write_text('{"x":1}\n', encoding="utf-8")
        (self.suite / "evaluation/score.py").write_text("print('ok')\n", encoding="utf-8")
        claims = [{"claim_id": "C1", "linked_blocks": ["B1", "B2"]}]
        blocks = [
            self.block("B1", "G1", "results/B1.json"),
            self.block("B2", "G2", "results/B2.json"),
        ]
        (self.suite / "experiment-plan/claim-map.json").write_text(json.dumps(claims), encoding="utf-8")
        (self.suite / "experiment-plan/run-blocks.json").write_text(json.dumps(blocks), encoding="utf-8")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def run_cmd(self, args: list[str], expect: int = 0) -> subprocess.CompletedProcess[str]:
        cp = subprocess.run(args, text=True, capture_output=True, env=self.env)
        self.assertEqual(cp.returncode, expect, msg=f"stdout:\n{cp.stdout}\nstderr:\n{cp.stderr}")
        return cp

    def cli(self, *args: str, expect: int = 0):
        return self.run_cmd([sys.executable, str(RUNTIME), "--root", str(self.suite), *args], expect)

    def block(self, block_id: str, gate_id: str, output: str) -> dict:
        return {
            "block_id": block_id,
            "claim_ids": ["C1"],
            "decision_gate_id": gate_id,
            "expected_output_artifact": output,
            "execution": {
                "mode": "command",
                "entrypoint": {"argv": ["python", f"run_{block_id}.py"], "cwd": "."},
                "declared_inputs": [{"path": "data/test.jsonl", "snapshot": "digest-at-start"}],
                "declared_evaluator_artifacts": [
                    {"path": "evaluation/score.py", "snapshot": "digest-at-start"}
                ],
                "required_outputs": [{"path": output}],
            },
            "lineage_policy": {"allowed_relations": ["baseline", "technical_retry", "ablation"]},
        }

    def add(self, item: str, block: str, *, depends: str | None = None, activation: str | None = None) -> None:
        args = [
            "add", "--work-item-id", item, "--stage", "experiment-plan",
            "--owner-skill", "research-experiment-runner", "--objective", f"Run {block}",
            "--acceptance-check", "output exists", "--expected-artifact", f"results/{block}.json",
            "--write-scope", "results/", "--experiment-run-blocks", "experiment-plan/run-blocks.json",
            "--experiment-claim-map", "experiment-plan/claim-map.json", "--experiment-block-id", block,
            "--commitment", "research-commitment.json",
        ]
        if depends:
            args += ["--depends-on", depends]
        if activation:
            args += ["--activation-condition", activation]
        self.cli(*args)

    def complete(self, item: str, block: str, gate_result: str, disposition: str, effect: str) -> None:
        self.cli("start", item, "--actor", "research-experiment-runner")
        output = f"results/{block}.json"
        (self.suite / output).write_text('{"metric":1}\n', encoding="utf-8")
        episode = {
            "schema_version": "1.0", "episode_id": f"EP-{item}-A1", "work_item_id": item,
            "attempt": 1, "owner_skill": "research-experiment-runner", "objective": f"Run {block}",
            "artifacts": [output], "verification": [{"check_id": "AC1", "result": "pass", "evidence": output}],
            "failures": [], "tool_calls": [], "observed_usage": {"max_tool_calls": 0},
            "outcome": "completed", "transition_request": "approve", "summary": "done",
            "experiment_run": {
                "run_id": f"RUN-{block}-001", "block_id": block, "relation": "baseline",
                "parent_run_id": None, "gate_id": f"G{block[1:]}", "gate_result": gate_result,
                "scientific_disposition": disposition,
                "claim_effects": [{"claim_id": "C1", "effect": effect, "scope": "fixture"}],
                "interpretation": "fixture result",
            },
        }
        path = self.suite / "episodes" / f"EP-{item}-A1.json"
        path.write_text(json.dumps(episode), encoding="utf-8")
        self.cli("submit", item, "--episode", str(path), "--actor", "research-experiment-runner")
        self.cli(
            "verify", item, "--decision", "approve", "--evidence", "inspected",
            "--gate-result", f"G{block[1:]}={gate_result}",
            "--scientific-disposition", disposition, "--actor", "research-pipeline-planner",
        )

    def validate(self, expect: int = 0):
        return self.run_cmd(
            [sys.executable, str(VALIDATE), str(self.suite), "--profile", "harness"],
            expect,
        )

    def test_completed_experiment_suite_validates(self):
        self.add("WI-B1", "B1")
        self.complete("WI-B1", "B1", "pass", "supports_claim", "strengthen")
        cp = self.validate()
        self.assertIn("experiment bindings", cp.stdout)

    def test_pack_validation_detects_post_completion_snapshot_mutation(self):
        self.add("WI-B1", "B1")
        self.complete("WI-B1", "B1", "pass", "supports_claim", "strengthen")
        (self.suite / "evaluation/score.py").write_text("print('changed')\n", encoding="utf-8")
        cp = self.validate(expect=1)
        self.assertIn("declared snapshot digest mismatch", cp.stdout)

    def test_failed_gate_keeps_conditioned_item_queued_and_pack_valid(self):
        self.add("WI-B1", "B1")
        self.add("WI-B2", "B2", depends="WI-B1", activation="WI-B1:G1:pass")
        self.complete("WI-B1", "B1", "fail", "falsifies_claim", "kill")
        self.validate()
        items = json.loads((self.suite / "work-items.json").read_text())["items"]
        states = {item["work_item_id"]: item["state"] for item in items}
        self.assertEqual(states["WI-B2"], "queued")


if __name__ == "__main__":
    unittest.main()
