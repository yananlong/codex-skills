#!/usr/bin/env python3
"""Regression tests for the research-suite harness runtime."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "harness_runtime.py"


class HarnessRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def run_cli(self, *args: str, expect: int = 0) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--root", str(self.root), *args],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(
            result.returncode,
            expect,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}",
        )
        return result

    def add_and_start(self, attempt_budget: int = 2, tool_call_budget: int = 20) -> None:
        self.run_cli(
            "add",
            "--work-item-id",
            "WI-001",
            "--stage",
            "ideation",
            "--owner-skill",
            "research-idea-discovery",
            "--objective",
            "Select one falsifiable idea",
            "--acceptance-check",
            "Selected artifact exists",
            "--expected-artifact",
            "ideation/selected-idea.md",
            "--write-scope",
            "ideation/",
            "--attempt-budget",
            str(attempt_budget),
            "--tool-call-budget",
            str(tool_call_budget),
        )
        self.run_cli("start", "WI-001", "--actor", "research-idea-discovery")

    def write_episode(
        self,
        *,
        objective: str = "Select one falsifiable idea",
        artifacts: list[str] | None = None,
        tool_calls: int = 0,
    ) -> Path:
        (self.root / "ideation").mkdir(exist_ok=True)
        (self.root / "episodes").mkdir(exist_ok=True)
        (self.root / "ideation" / "selected-idea.md").write_text(
            "# Selected Idea\n", encoding="utf-8"
        )
        artifact_list = artifacts if artifacts is not None else ["ideation/selected-idea.md"]
        episode = {
            "schema_version": "1.0",
            "episode_id": "EP-WI-001-A1",
            "work_item_id": "WI-001",
            "attempt": 1,
            "owner_skill": "research-idea-discovery",
            "objective": objective,
            "artifacts": artifact_list,
            "verification": [
                {
                    "check_id": "AC1",
                    "result": "pass",
                    "evidence": "ideation/selected-idea.md",
                }
            ],
            "failures": [],
            "tool_calls": [{"tool": "search"} for _ in range(tool_calls)],
            "observed_usage": {"max_tool_calls": tool_calls},
            "outcome": "completed",
            "transition_request": "approve",
            "summary": "Completed bounded work item.",
        }
        path = self.root / "episodes" / "EP-WI-001-A1.json"
        path.write_text(json.dumps(episode), encoding="utf-8")
        return path

    def test_clean_transition_and_replay(self) -> None:
        self.add_and_start()
        episode = self.write_episode(tool_calls=1)
        self.run_cli(
            "submit",
            "WI-001",
            "--episode",
            str(episode),
            "--actor",
            "research-idea-discovery",
        )
        self.run_cli(
            "verify",
            "WI-001",
            "--decision",
            "approve",
            "--evidence",
            "Artifact and acceptance check inspected.",
            "--actor",
            "research-pipeline-planner",
            "--self-review",
        )
        state_before = json.loads((self.root / "HARNESS_STATE.json").read_text())
        items_before = json.loads((self.root / "work-items.json").read_text())
        self.run_cli("replay")
        self.assertEqual(
            state_before,
            json.loads((self.root / "HARNESS_STATE.json").read_text()),
        )
        self.assertEqual(
            items_before,
            json.loads((self.root / "work-items.json").read_text()),
        )
        self.assertEqual(items_before["items"][0]["state"], "completed")

    def test_frozen_objective_cannot_drift(self) -> None:
        self.add_and_start()
        episode = self.write_episode(objective="Changed objective after seeing results")
        result = self.run_cli(
            "submit",
            "WI-001",
            "--episode",
            str(episode),
            "--actor",
            "research-idea-discovery",
            expect=1,
        )
        self.assertIn("objective differs", result.stderr)
        state = json.loads((self.root / "work-items.json").read_text())
        self.assertEqual(state["items"][0]["state"], "running")

    def test_attempt_budget_blocks_repeated_failure(self) -> None:
        self.add_and_start(attempt_budget=1)
        self.run_cli(
            "fail",
            "WI-001",
            "--reason",
            "tool timeout",
            "--retryable",
            "--actor",
            "research-idea-discovery",
        )
        items = json.loads((self.root / "work-items.json").read_text())
        self.assertEqual(items["items"][0]["state"], "blocked")

    def test_tampered_event_log_is_rejected(self) -> None:
        self.add_and_start()
        events_path = self.root / "harness-events.jsonl"
        events = events_path.read_text(encoding="utf-8").splitlines()
        tampered = json.loads(events[0])
        tampered["details"]["work_item"]["objective"] = "tampered"
        events[0] = json.dumps(tampered, sort_keys=True)
        events_path.write_text("\n".join(events) + "\n", encoding="utf-8")
        result = self.run_cli("replay", expect=1)
        self.assertIn("event hash mismatch", result.stderr)

    def test_projection_drift_is_repaired_by_replay(self) -> None:
        self.add_and_start()
        state_path = self.root / "HARNESS_STATE.json"
        state = json.loads(state_path.read_text())
        state["status"] = "completed"
        state_path.write_text(json.dumps(state), encoding="utf-8")
        self.run_cli("replay")
        repaired = json.loads(state_path.read_text())
        self.assertEqual(repaired["status"], "running")

    def test_expected_artifact_is_mandatory(self) -> None:
        self.add_and_start()
        episode = self.write_episode(artifacts=[])
        result = self.run_cli(
            "submit",
            "WI-001",
            "--episode",
            str(episode),
            "--actor",
            "research-idea-discovery",
            expect=1,
        )
        self.assertIn("must list artifacts", result.stderr)

    def test_write_scope_is_enforced(self) -> None:
        self.add_and_start()
        (self.root / "outside.md").write_text("outside", encoding="utf-8")
        episode = self.write_episode(
            artifacts=["ideation/selected-idea.md", "outside.md"]
        )
        result = self.run_cli(
            "submit",
            "WI-001",
            "--episode",
            str(episode),
            "--actor",
            "research-idea-discovery",
            expect=1,
        )
        self.assertIn("outside declared write scope", result.stderr)

    def test_tool_call_budget_is_enforced(self) -> None:
        self.add_and_start(tool_call_budget=1)
        episode = self.write_episode(tool_calls=2)
        result = self.run_cli(
            "submit",
            "WI-001",
            "--episode",
            str(episode),
            "--actor",
            "research-idea-discovery",
            expect=1,
        )
        self.assertIn("exceeds the work item tool-call budget", result.stderr)


if __name__ == "__main__":
    unittest.main()
