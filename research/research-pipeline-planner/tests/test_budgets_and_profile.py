#!/usr/bin/env python3
"""Regression tests for split attempt budgets and the supervised profile (D5)."""
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
RUNTIME = SCRIPTS / "harness_runtime.py"
INIT = SCRIPTS / "init_research_pack.py"
VALIDATE = SCRIPTS / "validate_research_pack.py"
sys.path.insert(0, str(SCRIPTS))
os.environ.setdefault("HARNESS_DISABLE_FSYNC", "1")

import harness_runtime  # noqa: E402

WORKER = "research-idea-discovery"
OWNER = "pat-owner"


class BudgetCase(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "suite"
        self.env = dict(os.environ, HARNESS_DISABLE_FSYNC="1")
        self.cmd(str(INIT), str(self.root))

    def tearDown(self):
        self.temp.cleanup()

    def cmd(self, *args: str, expect: int = 0):
        cp = subprocess.run([sys.executable, *args], text=True, capture_output=True, env=self.env)
        self.assertEqual(cp.returncode, expect, msg=f"stdout:\n{cp.stdout}\nstderr:\n{cp.stderr}")
        return cp

    def rt(self, *args: str, expect: int = 0):
        return self.cmd(str(RUNTIME), "--root", str(self.root), *args, expect=expect)

    def item(self, wid: str = "WI-1") -> dict:
        items = json.loads((self.root / "work-items.json").read_text())["items"]
        return next(item for item in items if item["work_item_id"] == wid)

    def add(self, *extra: str) -> None:
        self.rt(
            "add", "--work-item-id", "WI-1", "--stage", "ideation", "--owner-skill", WORKER,
            "--objective", "o", "--acceptance-check", "c", "--expected-artifact", "ideation/a.md",
            "--write-scope", "ideation/", *extra,
        )

    def episode(self, attempt: int, outcome: str, categories: list[str]) -> Path:
        (self.root / "ideation").mkdir(exist_ok=True)
        (self.root / "ideation/a.md").write_text("artifact\n")
        completed = outcome == "completed"
        data = {
            "schema_version": "1.0", "episode_id": f"EP-WI-1-A{attempt}", "work_item_id": "WI-1",
            "attempt": attempt, "owner_skill": WORKER, "objective": "o",
            "artifacts": ["ideation/a.md"] if completed else [],
            "verification": [{"check_id": "AC1", "result": "pass", "evidence": "e"}] if completed else [],
            "failures": [{"category": category, "reason": "r"} for category in categories],
            "tool_calls": [], "observed_usage": {"max_tool_calls": 0}, "outcome": outcome,
            "transition_request": "approve" if completed else "revise", "summary": "s",
        }
        path = self.root / f"episodes/EP-WI-1-A{attempt}.json"
        path.write_text(json.dumps(data))
        return path

    def attempt_and_revise(self, attempt: int, outcome: str, categories: list[str]) -> None:
        self.rt("start", "WI-1", "--actor", WORKER)
        self.rt("submit", "WI-1", "--episode", str(self.episode(attempt, outcome, categories)), "--actor", WORKER)
        self.rt("verify", "WI-1", "--decision", "revise", "--evidence", "read it", "--actor", OWNER)


class SplitBudgetTests(BudgetCase):
    def test_crashes_spend_the_technical_budget_only(self):
        self.add("--attempt-budget", "1", "--technical-attempt-budget", "3")
        for attempt in (1, 2):
            self.rt("start", "WI-1", "--actor", WORKER)
            self.rt("fail", "WI-1", "--retryable", "--reason", "the job crashed", "--actor", WORKER)
            item = self.item()
            self.assertEqual((item["technical_attempts"], item["scientific_attempts"], item["state"]), (attempt, 0, "ready"))
        self.rt("start", "WI-1", "--actor", WORKER)
        self.rt("fail", "WI-1", "--retryable", "--reason", "the job crashed", "--actor", WORKER)
        self.assertEqual(self.item()["state"], "blocked")
        self.cmd(str(VALIDATE), str(self.root))

    def test_judged_revision_spends_the_scientific_budget(self):
        self.add("--attempt-budget", "2")
        self.attempt_and_revise(1, "completed", [])
        item = self.item()
        self.assertEqual((item["technical_attempts"], item["scientific_attempts"], item["state"]), (0, 1, "ready"))
        self.attempt_and_revise(2, "completed", [])
        self.assertEqual(self.item()["state"], "blocked")
        self.cmd(str(VALIDATE), str(self.root))

    def test_failed_episode_is_technical_only_when_every_category_is(self):
        self.add("--attempt-budget", "3")
        self.attempt_and_revise(1, "failed", ["Tool/connector failure", "execution_resource"])
        self.assertEqual((self.item()["technical_attempts"], self.item()["scientific_attempts"]), (1, 0))
        self.attempt_and_revise(2, "failed", ["timeout", "scientific/evidential"])
        self.assertEqual((self.item()["technical_attempts"], self.item()["scientific_attempts"]), (1, 1))
        self.cmd(str(VALIDATE), str(self.root))

    def test_technical_budget_must_be_positive(self):
        cp = self.rt(
            "add", "--work-item-id", "WI-1", "--stage", "ideation", "--owner-skill", WORKER, "--objective", "o",
            "--acceptance-check", "c", "--expected-artifact", "ideation/a.md", "--write-scope", "ideation/",
            "--technical-attempt-budget", "0", expect=1,
        )
        self.assertIn("--technical-attempt-budget", cp.stderr)

    def test_pre_split_item_keeps_one_shared_budget_and_replays_unchanged(self):
        legacy = {
            "work_item_id": "WI-1", "stage": "ideation", "owner_skill": WORKER, "objective": "o",
            "context_manifest": [], "expected_artifacts": ["ideation/a.md"],
            "acceptance_checks": [{"check_id": "AC1", "criterion": "c"}], "dependencies": [],
            "activation_conditions": [], "attempt_budget": 2, "tool_call_budget": 20,
            "write_scope": ["ideation/"], "permission_policy": "least_privilege", "predecessor_failures": [],
            "evidence_class": "exploratory", "enforcement_scope": "repository_validation_only",
        }
        harness_runtime.commit_event(self.root, "work_item_added", "research-pipeline-planner", "WI-1", {"work_item": legacy})
        for _ in range(2):
            self.rt("start", "WI-1", "--actor", WORKER)
            self.rt("fail", "WI-1", "--retryable", "--reason", "crash", "--actor", WORKER)
        item = self.item()
        self.assertEqual(item["state"], "blocked")
        self.assertNotIn("technical_attempts", item)
        before = (self.root / "work-items.json").read_text()
        self.rt("replay")
        self.assertEqual(before, (self.root / "work-items.json").read_text())
        self.cmd(str(VALIDATE), str(self.root))


class SupervisedProfileTests(BudgetCase):
    def test_profile_is_the_owners_decision(self):
        cp = self.rt("set-profile", "supervised", "--reason", "r", "--actor", "research-pipeline-planner", expect=1)
        self.assertIn("owner's decision", cp.stderr)
        self.rt("set-profile", "supervised", "--reason", "every run is checked by hand", "--actor", OWNER)
        state = json.loads((self.root / "HARNESS_STATE.json").read_text())
        self.assertEqual(state["profile"], "supervised")
        self.cmd(str(VALIDATE), str(self.root))

    def test_supervised_verifier_transitions_need_the_owner(self):
        self.add()
        self.rt("set-profile", "supervised", "--reason", "r", "--actor", OWNER)
        self.rt("start", "WI-1", "--actor", WORKER)
        self.rt("submit", "WI-1", "--episode", str(self.episode(1, "completed", [])), "--actor", WORKER)
        cp = self.rt("verify", "WI-1", "--decision", "approve", "--evidence", "e", "--actor", "research-pipeline-planner", expect=1)
        self.assertIn("supervised", cp.stderr)
        cp = self.rt("verify", "WI-1", "--decision", "approve", "--evidence", "e", "--actor", WORKER, "--self-review", expect=1)
        self.assertIn("supervised", cp.stderr)
        with self.assertRaises(SystemExit) as raised:
            harness_runtime.commit_event(
                self.root, "verification_approved", "research-pipeline-planner", "WI-1",
                {"decision": "approve", "evidence": "e", "self_review": False, "episode_id": "EP-WI-1-A1"},
            )
        self.assertIn("supervised", str(raised.exception))
        self.rt("verify", "WI-1", "--decision", "approve", "--evidence", "read the artifact", "--actor", OWNER)
        self.assertEqual(self.item()["state"], "completed")
        self.cmd(str(VALIDATE), str(self.root))

    def test_autonomous_keeps_todays_behaviour(self):
        self.add()
        self.rt("start", "WI-1", "--actor", WORKER)
        self.rt("submit", "WI-1", "--episode", str(self.episode(1, "completed", [])), "--actor", WORKER)
        self.rt("verify", "WI-1", "--decision", "approve", "--evidence", "e", "--actor", "research-pipeline-planner")
        self.assertEqual(self.item()["state"], "completed")


if __name__ == "__main__":
    unittest.main()
