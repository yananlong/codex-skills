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
VALIDATE = ROOT / "scripts" / "validate_research_pack.py"
RUNTIME = ROOT / "scripts" / "harness_runtime.py"


class ResearchPackTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.pack = Path(self.temp.name) / "suite"
        self.env = dict(os.environ, HARNESS_DISABLE_FSYNC="1")

    def tearDown(self):
        self.temp.cleanup()

    def run_cmd(self, *args: str, expect: int = 0):
        cp = subprocess.run([sys.executable, *args], text=True, capture_output=True, env=self.env)
        self.assertEqual(cp.returncode, expect, msg=f"stdout:\n{cp.stdout}\nstderr:\n{cp.stderr}")
        return cp

    def init(self, *extra: str):
        self.run_cmd(str(INIT), str(self.pack), *extra)

    def validate(self, expect: int = 0):
        return self.run_cmd(str(VALIDATE), str(self.pack), "--profile", "harness", expect=expect)

    def add_start_submit(self):
        self.run_cmd(str(RUNTIME), "--root", str(self.pack), "add", "--work-item-id", "WI-1", "--stage", "ideation", "--owner-skill", "worker", "--objective", "Do work", "--acceptance-check", "Artifact exists", "--expected-artifact", "ideation/out.md", "--write-scope", "ideation/")
        self.run_cmd(str(RUNTIME), "--root", str(self.pack), "start", "WI-1", "--actor", "worker")
        (self.pack / "ideation/out.md").write_text("ok")
        episode = {"schema_version":"1.0","episode_id":"EP-WI-1-A1","work_item_id":"WI-1","attempt":1,"owner_skill":"worker","objective":"Do work","artifacts":["ideation/out.md"],"verification":[{"check_id":"AC1","result":"pass","evidence":"ideation/out.md"}],"failures":[],"tool_calls":[],"observed_usage":{"max_tool_calls":0},"outcome":"completed","transition_request":"approve","summary":"done"}
        path = self.pack / "episodes/EP-WI-1-A1.json"
        path.write_text(json.dumps(episode))
        self.run_cmd(str(RUNTIME), "--root", str(self.pack), "submit", "WI-1", "--episode", str(path), "--actor", "worker")
        return path

    def test_default_initializer_validates(self):
        self.init()
        cp = self.validate()
        self.assertIn("digest-anchored evidence", cp.stdout)

    def test_legacy_initializer_validates(self):
        self.init("--legacy")
        cp = self.run_cmd(str(VALIDATE), str(self.pack), "--profile", "legacy")
        self.assertIn("legacy research-suite", cp.stdout)

    def test_force_removes_stale_harness_evidence_and_preserves_stage_outputs(self):
        self.init()
        sentinel = self.pack / "ideation/valuable-result.md"
        sentinel.write_text("keep me")
        (self.pack / "episodes/stale.json").write_text("{}")
        (self.pack / "checkpoints/stale.json").write_text("{}")
        self.init("--force")
        self.assertTrue(sentinel.exists())
        self.assertFalse((self.pack / "episodes/stale.json").exists())
        self.assertFalse((self.pack / "checkpoints/stale.json").exists())
        self.validate()

    def test_reset_stage_artifacts_is_explicit_and_destructive(self):
        self.init()
        sentinel = self.pack / "ideation/valuable-result.md"
        sentinel.write_text("delete me")
        self.init("--force", "--reset-stage-artifacts")
        self.assertFalse(sentinel.exists())

    def test_reset_stage_artifacts_requires_force(self):
        cp = self.run_cmd(str(INIT), str(self.pack), "--reset-stage-artifacts", expect=1)
        self.assertIn("requires --force", cp.stderr)

    def test_force_legacy_removes_harness_artifacts_but_preserves_stage_outputs(self):
        self.init()
        sentinel = self.pack / "ideation/valuable-result.md"
        sentinel.write_text("keep me")
        self.init("--force", "--legacy")
        self.assertTrue(sentinel.exists())
        for name in ("HARNESS_STATE.json", "work-items.json", "harness-events.jsonl", "episodes", "checkpoints"):
            self.assertFalse((self.pack / name).exists())

    def test_orphan_episode_rejected(self):
        self.init()
        (self.pack / "episodes/orphan.json").write_text("{}")
        cp = self.validate(expect=1)
        self.assertIn("orphan episode", cp.stdout)

    def test_nested_orphan_evidence_rejected(self):
        self.init()
        nested_episode = self.pack / "episodes/nested/orphan.json"
        nested_checkpoint = self.pack / "checkpoints/nested/orphan.json"
        nested_episode.parent.mkdir()
        nested_checkpoint.parent.mkdir()
        nested_episode.write_text("{}")
        nested_checkpoint.write_text("{}")
        cp = self.validate(expect=1)
        self.assertIn("episodes/nested/orphan.json", cp.stdout)
        self.assertIn("checkpoints/nested/orphan.json", cp.stdout)

    def test_mutated_episode_rejected(self):
        self.init()
        path = self.add_start_submit()
        self.validate()
        data = json.loads(path.read_text())
        data["summary"] = "mutated"
        path.write_text(json.dumps(data))
        cp = self.validate(expect=1)
        self.assertIn("episode digest mismatch", cp.stdout)

    def test_orphan_and_mutated_checkpoint_rejected(self):
        self.init()
        (self.pack / "checkpoints/orphan.json").write_text("{}")
        cp = self.validate(expect=1)
        self.assertIn("orphan checkpoint", cp.stdout)
        (self.pack / "checkpoints/orphan.json").unlink()
        self.run_cmd(str(RUNTIME), "--root", str(self.pack), "checkpoint", "--checkpoint-id", "cp1", "--reason", "save", "--actor", "planner")
        path = self.pack / "checkpoints/cp1.json"
        data = json.loads(path.read_text())
        data["reason"] = "mutated"
        path.write_text(json.dumps(data))
        cp = self.validate(expect=1)
        self.assertIn("checkpoint digest mismatch", cp.stdout)


if __name__ == "__main__":
    unittest.main()
