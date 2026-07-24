#!/usr/bin/env python3
"""Integration tests for research-pack initialization and validation."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INIT = ROOT / "scripts" / "init_research_pack.py"
VALIDATE = ROOT / "scripts" / "validate_research_pack.py"


class ResearchPackIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.pack = Path(self.temp.name) / "suite"

    def tearDown(self) -> None:
        self.temp.cleanup()

    def run_command(self, *args: str, expect: int = 0) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            [sys.executable, *args],
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

    def test_default_initializer_creates_valid_harness_pack(self) -> None:
        self.run_command(str(INIT), str(self.pack))
        result = self.run_command(str(VALIDATE), str(self.pack), "--profile", "harness")
        self.assertIn("event chain", result.stdout)
        state = json.loads((self.pack / "HARNESS_STATE.json").read_text())
        self.assertEqual(state["status"], "initialized")
        self.assertEqual(state["last_event_id"], "EV-000001")
        self.assertTrue((self.pack / "episodes").is_dir())
        self.assertTrue((self.pack / "checkpoints").is_dir())

    def test_auto_profile_detects_harness_pack(self) -> None:
        self.run_command(str(INIT), str(self.pack))
        result = self.run_command(str(VALIDATE), str(self.pack))
        self.assertIn("harness layout", result.stdout)

    def test_projection_drift_fails_validation(self) -> None:
        self.run_command(str(INIT), str(self.pack))
        state_path = self.pack / "HARNESS_STATE.json"
        state = json.loads(state_path.read_text())
        state["status"] = "completed"
        state_path.write_text(json.dumps(state), encoding="utf-8")
        result = self.run_command(
            str(VALIDATE), str(self.pack), "--profile", "harness", expect=1
        )
        self.assertIn("does not match replayed event state", result.stdout)

    def test_legacy_initializer_remains_supported(self) -> None:
        self.run_command(str(INIT), str(self.pack), "--legacy")
        result = self.run_command(str(VALIDATE), str(self.pack), "--profile", "legacy")
        self.assertIn("legacy research-suite layout", result.stdout)
        self.assertFalse((self.pack / "HARNESS_STATE.json").exists())


if __name__ == "__main__":
    unittest.main()
