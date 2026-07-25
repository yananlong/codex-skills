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


class HarnessRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.env = dict(os.environ, HARNESS_DISABLE_FSYNC="1")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def run_cli(self, *args: str, expect: int = 0) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--root", str(self.root), *args],
            text=True,
            capture_output=True,
            check=False,
            env=self.env,
        )
        self.assertEqual(result.returncode, expect, msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")
        return result

    def add(self, item: str = "WI-001", owner: str = "research-idea-discovery", depends: str | None = None, attempt_budget: int = 2, tool_call_budget: int = 20) -> None:
        args = [
            "add", "--work-item-id", item, "--stage", "ideation", "--owner-skill", owner,
            "--objective", f"Objective {item}", "--acceptance-check", "Artifact exists",
            "--expected-artifact", f"ideation/{item}.md", "--write-scope", "ideation/",
            "--attempt-budget", str(attempt_budget), "--tool-call-budget", str(tool_call_budget),
        ]
        if depends:
            args += ["--depends-on", depends]
        self.run_cli(*args)

    def start(self, item: str = "WI-001", owner: str = "research-idea-discovery", key: str | None = None) -> None:
        args = ["start", item, "--actor", owner]
        if key:
            args += ["--idempotency-key", key]
        self.run_cli(*args)

    def write_episode(self, item: str = "WI-001", owner: str = "research-idea-discovery", *, outcome: str = "completed", request: str = "approve", failures: list | None = None, tool_calls: int = 0) -> Path:
        (self.root / "ideation").mkdir(exist_ok=True)
        (self.root / "episodes").mkdir(exist_ok=True)
        artifact = f"ideation/{item}.md"
        (self.root / artifact).write_text("# artifact\n", encoding="utf-8")
        episode = {
            "schema_version": "1.0",
            "episode_id": f"EP-{item}-A1",
            "work_item_id": item,
            "attempt": 1,
            "owner_skill": owner,
            "objective": f"Objective {item}",
            "artifacts": [artifact] if outcome == "completed" else [],
            "verification": [{"check_id": "AC1", "result": "pass", "evidence": artifact}] if outcome == "completed" else [],
            "failures": failures or [],
            "tool_calls": [{"tool": "search"} for _ in range(tool_calls)],
            "observed_usage": {"max_tool_calls": tool_calls},
            "outcome": outcome,
            "transition_request": request,
            "summary": "episode",
        }
        path = self.root / "episodes" / f"EP-{item}-A1.json"
        path.write_text(json.dumps(episode), encoding="utf-8")
        return path

    def submit(self, episode: Path, item: str = "WI-001", owner: str = "research-idea-discovery", key: str | None = None, expect: int = 0):
        args = ["submit", item, "--episode", str(episode), "--actor", owner]
        if key:
            args += ["--idempotency-key", key]
        return self.run_cli(*args, expect=expect)

    def test_clean_transition_and_replay(self):
        self.add(); self.start(); ep = self.write_episode(); self.submit(ep)
        self.run_cli("verify", "WI-001", "--decision", "approve", "--evidence", "checked", "--actor", "research-pipeline-planner")
        before = json.loads((self.root / "work-items.json").read_text())
        self.run_cli("replay")
        self.assertEqual(before, json.loads((self.root / "work-items.json").read_text()))
        self.assertEqual(before["items"][0]["state"], "completed")

    def test_invalid_start_does_not_poison_log(self):
        self.add(); self.start()
        lines = (self.root / "harness-events.jsonl").read_text().splitlines()
        result = self.run_cli("start", "WI-001", "--actor", "research-idea-discovery", "--idempotency-key", "new-key", expect=1)
        self.assertIn("cannot start", result.stderr)
        self.assertEqual(lines, (self.root / "harness-events.jsonl").read_text().splitlines())
        self.run_cli("replay")

    def test_start_is_idempotent(self):
        self.add(); self.start(key="same"); self.start(key="same")
        events = [json.loads(x) for x in (self.root / "harness-events.jsonl").read_text().splitlines()]
        self.assertEqual(sum(e["event_type"] == "work_item_started" for e in events), 1)

    def test_conflicting_start_idempotency_is_rejected(self):
        self.add(); self.start(key="same")
        self.add(item="WI-002", owner="research-results-auditor")
        result = self.run_cli("start", "WI-002", "--actor", "research-results-auditor", "--idempotency-key", "same", expect=1)
        self.assertIn("different start request", result.stderr)

    def test_submit_is_idempotent(self):
        self.add(); self.start(); ep = self.write_episode(); self.submit(ep, key="submit-key"); self.submit(ep, key="submit-key")
        events = [json.loads(x) for x in (self.root / "harness-events.jsonl").read_text().splitlines()]
        self.assertEqual(sum(e["event_type"] == "episode_submitted" for e in events), 1)

    def test_partial_episode_cannot_request_approve(self):
        self.add(); self.start(); ep = self.write_episode(outcome="partial", request="approve")
        result = self.submit(ep, expect=1)
        self.assertIn("must occur together", result.stderr)

    def test_failed_episode_requires_failure_record(self):
        self.add(); self.start(); ep = self.write_episode(outcome="failed", request="block")
        result = self.submit(ep, expect=1)
        self.assertIn("record at least one failure", result.stderr)

    def test_failure_entries_must_be_substantive_objects(self):
        self.add(); self.start()
        ep = self.write_episode(outcome="failed", request="block", failures=[None])
        result = self.submit(ep, expect=1)
        self.assertIn("must be an object", result.stderr)
        ep = self.write_episode(
            outcome="failed", request="block", failures=[{"category": "execution", "reason": ""}]
        )
        result = self.submit(ep, expect=1)
        self.assertIn("reason must be a substantive string", result.stderr)

    def test_episode_must_be_direct_child_of_episodes(self):
        self.add(); self.start(); ep = self.write_episode()
        nested = self.root / "episodes/nested" / ep.name
        nested.parent.mkdir()
        ep.replace(nested)
        result = self.submit(nested, expect=1)
        self.assertIn("direct child of episodes", result.stderr)

    def test_episode_mutation_blocks_approval(self):
        self.add(); self.start(); ep = self.write_episode(); self.submit(ep)
        data = json.loads(ep.read_text()); data["summary"] = "mutated"; ep.write_text(json.dumps(data))
        result = self.run_cli("verify", "WI-001", "--decision", "approve", "--evidence", "checked", "--actor", "research-pipeline-planner", expect=1)
        self.assertIn("episode digest changed", result.stderr)

    def test_artifact_mutation_blocks_approval(self):
        self.add(); self.start(); ep = self.write_episode(); self.submit(ep)
        (self.root / "ideation/WI-001.md").write_text("mutated")
        result = self.run_cli("verify", "WI-001", "--decision", "approve", "--evidence", "checked", "--actor", "research-pipeline-planner", expect=1)
        self.assertIn("artifact digest changed", result.stderr)

    def test_pause_blocks_state_changes_but_allows_record(self):
        self.add(); self.run_cli("pause", "--reason", "stop", "--actor", "planner")
        result = self.run_cli("start", "WI-001", "--actor", "research-idea-discovery", expect=1)
        self.assertIn("run is paused", result.stderr)
        self.run_cli("record", "--category", "note", "--note", "still observable", "--actor", "planner")
        self.run_cli("resume", "--reason", "continue", "--actor", "planner")
        self.start()

    def test_checkpoint_path_traversal_and_overwrite_rejected(self):
        result = self.run_cli("checkpoint", "--checkpoint-id", "../escape", "--reason", "x", "--actor", "planner", expect=1)
        self.assertIn("checkpoint id", result.stderr)
        self.run_cli("checkpoint", "--checkpoint-id", "safe", "--reason", "x", "--actor", "planner")
        result = self.run_cli("checkpoint", "--checkpoint-id", "safe", "--reason", "x", "--actor", "planner", expect=1)
        self.assertIn("already exists", result.stderr)

    def test_blocking_non_active_item_preserves_active_item(self):
        self.add(); self.add(item="WI-002", owner="research-results-auditor"); self.start()
        self.run_cli("fail", "WI-002", "--reason", "cancel", "--actor", "planner")
        state = json.loads((self.root / "HARNESS_STATE.json").read_text())
        self.assertEqual(state["active_work_item_id"], "WI-001")
        self.assertEqual(state["status"], "blocked")

    def test_owner_is_enforced(self):
        self.add()
        result = self.run_cli("start", "WI-001", "--actor", "wrong", expect=1)
        self.assertIn("owner skill", result.stderr)
        self.start(); ep = self.write_episode()
        result = self.submit(ep, owner="wrong", expect=1)
        self.assertIn("owner skill", result.stderr)

    def test_tool_budget_applies_to_failed_episode(self):
        self.add(tool_call_budget=1); self.start(); ep = self.write_episode(outcome="failed", request="block", failures=[{"category": "execution", "reason": "x"}], tool_calls=2)
        result = self.submit(ep, expect=1)
        self.assertIn("tool-call budget", result.stderr)

    def test_tampered_event_log_is_rejected(self):
        self.add(); lines = (self.root / "harness-events.jsonl").read_text().splitlines(); event = json.loads(lines[0]); event["details"]["work_item"]["objective"] = "tampered"; lines[0] = json.dumps(event); (self.root / "harness-events.jsonl").write_text("\n".join(lines) + "\n")
        result = self.run_cli("replay", expect=1); self.assertIn("event hash mismatch", result.stderr)

    def test_dependency_readiness_after_completion(self):
        self.add(); self.add(item="WI-002", owner="research-results-auditor", depends="WI-001")
        self.start(); ep = self.write_episode(); self.submit(ep)
        self.run_cli("verify", "WI-001", "--decision", "approve", "--evidence", "checked", "--actor", "planner")
        items = json.loads((self.root / "work-items.json").read_text())["items"]
        self.assertEqual({i["work_item_id"]: i["state"] for i in items}["WI-002"], "ready")


if __name__ == "__main__":
    unittest.main()
