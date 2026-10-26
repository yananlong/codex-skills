#!/usr/bin/env python3
"""Regression tests for owner re-approval on drift (D3) and identity events in the chain (D4)."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INIT = ROOT / "scripts" / "init_research_pack.py"
VALIDATE = ROOT / "scripts" / "validate_research_pack.py"
RUNTIME = ROOT / "scripts" / "harness_runtime.py"
VALIDATE_COMMITMENT = ROOT / "scripts" / "validate_research_commitment.py"

OWNER = "pat-owner"
WORKER = "research-idea-discovery"


class SuiteCase(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.pack = Path(self.temp.name) / "suite"
        self.env = dict(os.environ, HARNESS_DISABLE_FSYNC="1")
        self.run_cmd(str(INIT), str(self.pack))

    def tearDown(self):
        self.temp.cleanup()

    def run_cmd(self, *args: str, expect: int = 0):
        cp = subprocess.run([sys.executable, *args], text=True, capture_output=True, env=self.env)
        self.assertEqual(cp.returncode, expect, msg=f"stdout:\n{cp.stdout}\nstderr:\n{cp.stderr}")
        return cp

    def runtime(self, *args: str, expect: int = 0):
        return self.run_cmd(str(RUNTIME), "--root", str(self.pack), *args, expect=expect)

    def validate(self, expect: int = 0):
        return self.run_cmd(str(VALIDATE), str(self.pack), "--profile", "harness", expect=expect)

    def submit_artifact(self, item: str = "WI-1", body: str = "first version\n") -> Path:
        self.runtime(
            "add", "--work-item-id", item, "--stage", "ideation", "--owner-skill", WORKER,
            "--objective", "Do work", "--acceptance-check", "Artifact exists",
            "--expected-artifact", f"ideation/{item}.md", "--write-scope", "ideation/",
        )
        self.runtime("start", item, "--actor", WORKER)
        artifact = self.pack / f"ideation/{item}.md"
        artifact.write_text(body)
        episode = {
            "schema_version": "1.0", "episode_id": f"EP-{item}-A1", "work_item_id": item, "attempt": 1,
            "owner_skill": WORKER, "objective": "Do work", "artifacts": [f"ideation/{item}.md"],
            "verification": [{"check_id": "AC1", "result": "pass", "evidence": f"ideation/{item}.md"}],
            "failures": [], "tool_calls": [], "observed_usage": {"max_tool_calls": 0},
            "outcome": "completed", "transition_request": "approve", "summary": "done",
        }
        path = self.pack / f"episodes/EP-{item}-A1.json"
        path.write_text(json.dumps(episode))
        self.runtime("submit", item, "--episode", str(path), "--actor", WORKER)
        return artifact

    def commitment(self) -> dict:
        return json.loads((self.pack / "research-commitment.json").read_text())

    def write_commitment(self, data: dict) -> None:
        (self.pack / "research-commitment.json").write_text(json.dumps(data, indent=2) + "\n")

    def committed(self) -> dict:
        data = self.commitment()
        data.update({
            "status": "committed",
            "main_question": "Does the synthetic estimator stay calibrated under shift?",
            "central_object_or_phenomenon": "a synthetic calibration estimator",
            "minimum_publishable_claim": "calibration holds on two synthetic shifts",
            "primary_evidence_obligation": "two shifted synthetic benchmarks",
            "intended_audience": "methods readers",
            "next_mandatory_evidence_artifact": "results-audit/shift.json",
            "reconsideration_gate": "after the shift audit",
            "pivot_triggers": ["calibration fails on both shifts"],
            "kill_conditions": ["the estimator is shown equivalent to a known one"],
            "last_change_class": "D1",
            "last_change_rationale": "committed after scoping",
        })
        return data


class ReapprovalTests(SuiteCase):
    def test_edited_artifact_fails_until_the_owner_reapproves(self):
        artifact = self.submit_artifact()
        self.validate()
        artifact.write_text("second version after a fix\n")
        cp = self.validate(expect=1)
        self.assertIn("(drifted since approval): ideation/WI-1.md", cp.stdout)
        self.assertIn("reapprove --path", cp.stdout)
        cp = self.runtime("reapprove", "--path", "ideation/WI-1.md", "--reason", "fixed a typo", "--actor", WORKER, expect=1)
        self.assertIn("owner's decision", cp.stderr)
        self.runtime("reapprove", "--path", "ideation/WI-1.md", "--reason", "fixed a typo", "--actor", OWNER)
        cp = self.validate()
        self.assertIn("1 path(s) accepted by re-approval", cp.stdout)

    def test_a_second_edit_after_reapproval_drifts_again(self):
        artifact = self.submit_artifact()
        artifact.write_text("second\n")
        self.runtime("reapprove", "--all-drifted", "--reason", "accept the fix", "--actor", OWNER)
        self.validate()
        artifact.write_text("third\n")
        cp = self.validate(expect=1)
        self.assertIn("(drifted since approval): ideation/WI-1.md", cp.stdout)

    def test_reapprove_refuses_paths_with_nothing_to_approve(self):
        self.submit_artifact()
        cp = self.runtime("reapprove", "--path", "ideation/WI-1.md", "--reason", "r", "--actor", OWNER, expect=1)
        self.assertIn("matches its recorded digest", cp.stderr)
        (self.pack / "ideation/other.md").write_text("x")
        cp = self.runtime("reapprove", "--path", "ideation/other.md", "--reason", "r", "--actor", OWNER, expect=1)
        self.assertIn("not digest-anchored", cp.stderr)
        cp = self.runtime("reapprove", "--all-drifted", "--reason", "r", "--actor", OWNER)
        self.assertIn("nothing has drifted", cp.stdout)
        cp = self.runtime("reapprove", "--path", "research-commitment.json", "--reason", "r", "--actor", OWNER, expect=1)
        self.assertIn("commitment-edit", cp.stderr)

    def test_withheld_artifact_passes_with_a_recorded_reason(self):
        artifact = self.submit_artifact()
        artifact.unlink()
        cp = self.validate(expect=1)
        self.assertIn("ideation/WI-1.md", cp.stdout)
        cp = self.runtime("reapprove", "--path", "ideation/WI-1.md", "--reason", "r", "--actor", OWNER, expect=1)
        self.assertIn("withhold", cp.stderr)
        self.runtime("withhold", "--path", "ideation/WI-1.md", "--reason", "private data kept off the repository", "--actor", OWNER)
        cp = self.validate()
        self.assertIn("1 path(s) withheld", cp.stdout)

    def test_verify_after_post_submission_edit_needs_reapproval(self):
        artifact = self.submit_artifact()
        artifact.write_text("edited before review\n")
        cp = self.runtime("verify", "WI-1", "--decision", "approve", "--evidence", "read it", "--actor", OWNER, expect=1)
        self.assertIn("changed after submission", cp.stderr)
        self.runtime("reapprove", "--path", "ideation/WI-1.md", "--reason", "reviewed the edit", "--actor", OWNER)
        self.runtime("verify", "WI-1", "--decision", "approve", "--evidence", "read it", "--actor", OWNER)
        self.validate()

    def test_mutated_episode_still_fails_without_reapproval(self):
        self.submit_artifact()
        episode = self.pack / "episodes/EP-WI-1-A1.json"
        data = json.loads(episode.read_text())
        data["summary"] = "rewritten"
        episode.write_text(json.dumps(data))
        cp = self.validate(expect=1)
        self.assertIn("episode digest mismatch", cp.stdout)

    def test_missing_empty_directories_are_not_required(self):
        for name in ("zotero", "literature-review", "novelty-review", "paper-review", "review-loop", "rebuttal", "checkpoints"):
            shutil.rmtree(self.pack / name)
        self.validate()


class IdentityTests(SuiteCase):
    def test_init_anchors_the_commitment(self):
        events = [json.loads(line) for line in (self.pack / "harness-events.jsonl").read_text().splitlines()]
        self.assertEqual(events[-1]["event_type"], "commitment_edited")
        cp = self.validate()
        self.assertNotIn("not anchored", cp.stdout)

    def test_exploration_edit_warns_and_commit_by_hand_fails(self):
        data = self.commitment()
        data["main_question"] = "an exploring question"
        self.write_commitment(data)
        cp = self.validate()
        self.assertIn("unrecorded exploration edit", cp.stdout)
        self.write_commitment(self.committed())
        cp = self.validate(expect=1)
        self.assertIn("drifted identity", cp.stdout)
        self.runtime("commitment-edit", "--change-class", "D1", "--reason", "committed after scoping", "--actor", "research-pipeline-planner")
        cp = self.validate()
        self.assertNotIn("drifted identity", cp.stdout)

    def test_identity_version_cannot_change_by_edit(self):
        self.write_commitment(self.committed())
        self.runtime("commitment-edit", "--change-class", "D1", "--reason", "commit", "--actor", OWNER)
        data = self.commitment()
        data["identity_version"] = 2
        data["last_change_class"] = "D2"
        self.write_commitment(data)
        cp = self.runtime("commitment-edit", "--change-class", "D2", "--reason", "bump", "--actor", OWNER, expect=1)
        self.assertIn("outside a pivot decision", cp.stderr)

    def test_d3_pivot_request_and_decision_bump_the_identity(self):
        self.write_commitment(self.committed())
        self.runtime("commitment-edit", "--change-class", "D1", "--reason", "commit", "--actor", OWNER)
        request = self.runtime(
            "pivot-request", "--change-class", "D3", "--defect", "the shift benchmark is invalid",
            "--why-not-repair", "no D0-D2 repair restores the evidence obligation",
            "--requested-disposition", "authorize-D3", "--actor", "research-results-auditor",
        ).stdout.strip()
        self.assertEqual(request, "PV-0001")
        cp = self.runtime("pivot-decision", request, "--decision", "authorize-D3", "--rationale", "r", "--actor", "research-pipeline-planner", expect=1)
        self.assertIn("owner's decision", cp.stderr)
        committed_bytes = (self.pack / "research-commitment.json").read_bytes()
        early = self.commitment()
        early["primary_evidence_obligation"] = "a replacement benchmark chosen before any decision"
        self.write_commitment(early)
        cp = self.runtime("commitment-edit", "--change-class", "D3", "--reason", "early", "--actor", OWNER, expect=1)
        self.assertIn("needs an authorized pivot decision", cp.stderr)
        (self.pack / "research-commitment.json").write_bytes(committed_bytes)
        self.runtime("pivot-decision", request, "--decision", "authorize-D3", "--rationale", "replace the benchmark", "--actor", OWNER)
        data = self.commitment()
        self.assertEqual(data["identity_version"], 2)
        self.assertEqual(data["last_change_class"], "D3")
        self.assertEqual(data["selection_history"][-1]["to_identity_version"], 2)
        self.run_cmd(str(VALIDATE_COMMITMENT), str(self.pack / "research-commitment.json"))
        self.validate()
        data["primary_evidence_obligation"] = "a replacement synthetic benchmark"
        self.write_commitment(data)
        self.runtime("commitment-edit", "--change-class", "D3", "--reason", "new evidence obligation", "--actor", OWNER)
        self.validate()
        cp = self.runtime("pivot-decision", request, "--decision", "authorize-D3", "--rationale", "again", "--actor", OWNER, expect=1)
        self.assertIn("no open pivot request", cp.stderr)

    def test_requester_cannot_decide_and_unrecorded_edits_block_a_decision(self):
        self.write_commitment(self.committed())
        self.runtime("commitment-edit", "--change-class", "D1", "--reason", "commit", "--actor", OWNER)
        request = self.runtime(
            "pivot-request", "--change-class", "D3", "--defect", "d", "--why-not-repair", "w",
            "--requested-disposition", "authorize-D3", "--actor", OWNER,
        ).stdout.strip()
        cp = self.runtime("pivot-decision", request, "--decision", "authorize-D3", "--rationale", "r", "--actor", OWNER, expect=1)
        self.assertIn("requested a pivot may not decide", cp.stderr)
        data = self.commitment()
        data["intended_audience"] = "a different audience"
        self.write_commitment(data)
        cp = self.runtime("pivot-decision", request, "--decision", "reject-pivot", "--rationale", "r", "--actor", "sam-coauthor", expect=1)
        self.assertIn("edits not recorded", cp.stderr)

    def test_d4_close_and_create_needs_a_new_paper_id(self):
        self.write_commitment(self.committed())
        self.runtime("commitment-edit", "--change-class", "D1", "--reason", "commit", "--actor", OWNER)
        request = self.runtime(
            "pivot-request", "--change-class", "D4", "--defect", "d", "--why-not-repair", "w",
            "--requested-disposition", "close-and-create-D4", "--actor", "research-pipeline-planner",
        ).stdout.strip()
        cp = self.runtime("pivot-decision", request, "--decision", "close-and-create-D4", "--rationale", "r", "--actor", OWNER, expect=1)
        self.assertIn("--to-paper-id", cp.stderr)
        cp = self.runtime("pivot-decision", request, "--decision", "authorize-D3", "--rationale", "r", "--actor", OWNER, expect=1)
        self.assertIn("does not answer a D4 request", cp.stderr)
        self.runtime("pivot-decision", request, "--decision", "close-and-create-D4", "--rationale", "successor paper", "--to-paper-id", "successor-paper", "--actor", OWNER)
        data = self.commitment()
        self.assertEqual((data["paper_id"], data["identity_version"]), ("successor-paper", 1))
        self.validate()

    def test_reject_pivot_keeps_the_identity(self):
        self.write_commitment(self.committed())
        self.runtime("commitment-edit", "--change-class", "D1", "--reason", "commit", "--actor", OWNER)
        request = self.runtime(
            "pivot-request", "--change-class", "D3", "--defect", "d", "--why-not-repair", "w",
            "--requested-disposition", "authorize-D3", "--actor", "research-pipeline-planner",
        ).stdout.strip()
        self.runtime("pivot-decision", request, "--decision", "reject-pivot", "--rationale", "repair is enough", "--actor", OWNER)
        data = self.commitment()
        self.assertEqual(data["identity_version"], 1)
        self.assertEqual(data["selection_history"][-1]["decision"], "reject-pivot")
        self.validate()

    def test_unanchored_commitment_warns(self):
        log = self.pack / "harness-events.jsonl"
        first = log.read_text().splitlines()[0]
        log.write_text(first + "\n")
        self.runtime("replay")
        cp = self.validate()
        self.assertIn("not anchored in the event chain", cp.stdout)


if __name__ == "__main__":
    unittest.main()
