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
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
import validate_research_pack as pack_validator
from harness_common import event_hash

INIT = SCRIPTS / "init_research_pack.py"
RUNTIME = SCRIPTS / "harness_runtime.py"
VALIDATE = SCRIPTS / "validate_research_pack.py"


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

    def rewrite_events(self, mutator, expect: int = 0):
        path = self.suite / "harness-events.jsonl"
        events = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        mutator(events)
        previous = None
        for index, event in enumerate(events, 1):
            event["event_id"] = f"EV-{index:06d}"
            event["previous_event_hash"] = previous
            event.pop("event_hash", None)
            event["event_hash"] = event_hash(event)
            previous = event["event_hash"]
        path.write_text(
            "\n".join(json.dumps(event, sort_keys=True) for event in events) + "\n",
            encoding="utf-8",
        )
        return self.cli("replay", expect=expect)

    def test_completed_experiment_suite_validates(self):
        self.add("WI-B1", "B1")
        self.complete("WI-B1", "B1", "pass", "supports_claim", "strengthen")
        cp = self.validate()
        self.assertIn("experiment bindings", cp.stdout)

    def test_pack_rejects_event_projection_that_disagrees_with_episode(self):
        self.add("WI-B1", "B1")
        self.complete("WI-B1", "B1", "fail", "falsifies_claim", "kill")

        def mutate(events):
            for event in events:
                if event["event_type"] == "episode_submitted":
                    run = event["details"]["experiment_run"]
                    run["gate_result"] = "pass"
                    run["scientific_disposition"] = "supports_claim"
                    run["claim_effects"] = [
                        {"claim_id": "C1", "effect": "strengthen", "scope": "tampered projection"}
                    ]
                if event["event_type"] == "verification_approved":
                    event["details"]["gate_results"] = {"G1": "pass"}
                    event["details"]["scientific_disposition"] = "supports_claim"

        self.rewrite_events(mutate)
        cp = self.validate(expect=1)
        self.assertIn("does not match the digest-anchored episode", cp.stdout)

    def test_pack_rejects_undisclosed_same_role_verification_event(self):
        self.add("WI-B1", "B1")
        self.complete("WI-B1", "B1", "pass", "supports_claim", "strengthen")

        def mutate(events):
            approval = next(
                event for event in events if event["event_type"] == "verification_approved"
            )
            approval["actor"] = "research-experiment-runner"
            approval["details"]["self_review"] = False

        cp = self.rewrite_events(mutate, expect=1)
        self.assertIn("explicitly marked self-review", cp.stderr)

    def test_post_completion_revisions_do_not_rewrite_historical_snapshot(self):
        self.add("WI-B1", "B1")
        self.complete("WI-B1", "B1", "pass", "supports_claim", "strengthen")
        (self.suite / "evaluation/score.py").write_text("print('changed')\n", encoding="utf-8")
        blocks = json.loads((self.suite / "experiment-plan/run-blocks.json").read_text())
        blocks[0]["setup_note"] = "later planning revision"
        (self.suite / "experiment-plan/run-blocks.json").write_text(json.dumps(blocks), encoding="utf-8")
        cp = self.validate()
        self.assertIn("event-recorded start/submission digest equality", cp.stdout)

    def test_failed_gate_keeps_conditioned_item_queued_and_pack_valid(self):
        self.add("WI-B1", "B1")
        self.add("WI-B2", "B2", depends="WI-B1", activation="WI-B1:G1:pass")
        self.complete("WI-B1", "B1", "fail", "falsifies_claim", "kill")
        self.validate()
        items = json.loads((self.suite / "work-items.json").read_text())["items"]
        states = {item["work_item_id"]: item["state"] for item in items}
        self.assertEqual(states["WI-B2"], "queued")

    def test_pack_checks_submission_snapshot_for_every_attempt(self):
        self.add("WI-B1", "B1")
        self.cli("start", "WI-B1", "--actor", "research-experiment-runner")
        failed_episode = {
            "schema_version": "1.0", "episode_id": "EP-WI-B1-A1", "work_item_id": "WI-B1",
            "attempt": 1, "owner_skill": "research-experiment-runner", "objective": "Run B1",
            "artifacts": [], "verification": [],
            "failures": [{"category": "execution", "reason": "process crashed before output"}],
            "tool_calls": [], "observed_usage": {"max_tool_calls": 0},
            "outcome": "failed", "transition_request": "revise", "summary": "execution failed",
            "experiment_run": {
                "run_id": "RUN-B1-FAIL", "block_id": "B1", "relation": "baseline",
                "parent_run_id": None, "gate_id": "G1", "gate_result": "not_applicable",
                "scientific_disposition": "diagnostic_only",
                "claim_effects": [
                    {"claim_id": "C1", "effect": "unchanged", "scope": "no result produced"}
                ],
                "interpretation": "The execution failed before scientific output was produced.",
            },
        }
        failed_path = self.suite / "episodes/EP-WI-B1-A1.json"
        failed_path.write_text(json.dumps(failed_episode), encoding="utf-8")
        self.cli(
            "submit", "WI-B1", "--episode", str(failed_path),
            "--actor", "research-experiment-runner",
        )
        self.cli(
            "verify", "WI-B1", "--decision", "revise", "--evidence", "failure inspected",
            "--actor", "research-pipeline-planner",
        )
        self.cli("start", "WI-B1", "--actor", "research-experiment-runner")

        def mutate(events):
            first_submission = next(
                event for event in events if event["event_type"] == "episode_submitted"
            )
            first_submission["details"]["verified_execution_snapshot"]["declared_inputs"][
                "data/test.jsonl"
            ] = "0" * 64

        self.rewrite_events(mutate)
        cp = self.validate(expect=1)
        self.assertIn("submission snapshot does not match its start event", cp.stdout)

    def test_pack_integrity_rejects_activation_gate_not_owned_by_predecessor(self):
        self.add("WI-B1", "B1")
        self.add("WI-B2", "B2", depends="WI-B1", activation="WI-B1:G1:pass")
        projected = json.loads((self.suite / "work-items.json").read_text())
        projected["items"][1]["activation_conditions"][0]["gate_id"] = "G9"
        errors: list[str] = []
        pack_validator.validate_experiment_integrity(self.suite, projected, errors)
        self.assertTrue(
            any("does not match the predecessor's bound decision gate" in error for error in errors),
            errors,
        )

    def test_failed_attempt_retry_lineage_validates_end_to_end(self):
        self.add("WI-B1", "B1")
        self.cli("start", "WI-B1", "--actor", "research-experiment-runner")
        failed_episode = {
            "schema_version": "1.0", "episode_id": "EP-WI-B1-A1", "work_item_id": "WI-B1",
            "attempt": 1, "owner_skill": "research-experiment-runner", "objective": "Run B1",
            "artifacts": [], "verification": [],
            "failures": [{"category": "execution", "reason": "process crashed before output"}],
            "tool_calls": [], "observed_usage": {"max_tool_calls": 0},
            "outcome": "failed", "transition_request": "revise", "summary": "execution failed",
            "experiment_run": {
                "run_id": "RUN-B1-FAIL", "block_id": "B1", "relation": "baseline",
                "parent_run_id": None, "gate_id": "G1", "gate_result": "not_applicable",
                "scientific_disposition": "diagnostic_only",
                "claim_effects": [{"claim_id": "C1", "effect": "unchanged", "scope": "no result produced"}],
                "interpretation": "The execution failed before scientific output was produced.",
            },
        }
        failed_path = self.suite / "episodes/EP-WI-B1-A1.json"
        failed_path.write_text(json.dumps(failed_episode), encoding="utf-8")
        self.cli(
            "submit", "WI-B1", "--episode", str(failed_path),
            "--actor", "research-experiment-runner",
        )
        self.cli(
            "verify", "WI-B1", "--decision", "revise", "--evidence", "failure inspected",
            "--actor", "research-pipeline-planner",
        )

        self.cli("start", "WI-B1", "--actor", "research-experiment-runner")
        output = "results/B1.json"
        (self.suite / output).write_text('{"metric":1}\n', encoding="utf-8")
        retry_episode = {
            "schema_version": "1.0", "episode_id": "EP-WI-B1-A2", "work_item_id": "WI-B1",
            "attempt": 2, "owner_skill": "research-experiment-runner", "objective": "Run B1",
            "artifacts": [output],
            "verification": [{"check_id": "AC1", "result": "pass", "evidence": output}],
            "failures": [], "tool_calls": [], "observed_usage": {"max_tool_calls": 0},
            "outcome": "completed", "transition_request": "approve", "summary": "retry completed",
            "experiment_run": {
                "run_id": "RUN-B1-RETRY", "block_id": "B1", "relation": "technical_retry",
                "parent_run_id": "RUN-B1-FAIL", "gate_id": "G1", "gate_result": "pass",
                "scientific_disposition": "supports_claim",
                "claim_effects": [{"claim_id": "C1", "effect": "strengthen", "scope": "fixture"}],
                "interpretation": "The corrected execution produced the planned result.",
            },
        }
        retry_path = self.suite / "episodes/EP-WI-B1-A2.json"
        retry_path.write_text(json.dumps(retry_episode), encoding="utf-8")
        self.cli(
            "submit", "WI-B1", "--episode", str(retry_path),
            "--actor", "research-experiment-runner",
        )
        self.cli(
            "verify", "WI-B1", "--decision", "approve", "--evidence", "retry inspected",
            "--gate-result", "G1=pass", "--scientific-disposition", "supports_claim",
            "--actor", "research-pipeline-planner",
        )
        cp = self.validate()
        self.assertIn("experiment bindings", cp.stdout)
        lineage = json.loads(self.cli("experiment-lineage", "--block-id", "B1").stdout)
        self.assertIn(
            {"parent_run_id": "RUN-B1-FAIL", "child_run_id": "RUN-B1-RETRY"},
            lineage["edges"],
        )


if __name__ == "__main__":
    unittest.main()
