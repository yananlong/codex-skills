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
INIT_COMMITMENT = ROOT / "scripts" / "init_research_commitment.py"
VALIDATE_COMMITMENT = ROOT / "scripts" / "validate_research_commitment.py"
INIT_PACK = ROOT / "scripts" / "init_research_pack.py"
VALIDATE_PACK = ROOT / "scripts" / "validate_research_pack.py"


class ResearchCommitmentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "suite"
        self.env = dict(os.environ, HARNESS_DISABLE_FSYNC="1")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def run_cmd(self, *args: str, expect: int = 0):
        cp = subprocess.run(
            [sys.executable, *args],
            text=True,
            capture_output=True,
            env=self.env,
            check=False,
        )
        self.assertEqual(cp.returncode, expect, msg=f"stdout:\n{cp.stdout}\nstderr:\n{cp.stderr}")
        return cp

    def test_initializer_and_active_commitment_validate(self):
        self.run_cmd(str(INIT_COMMITMENT), str(self.root), "--paper-id", "paper-1")
        path = self.root / "research-commitment.json"
        self.run_cmd(str(VALIDATE_COMMITMENT), str(path))
        data = json.loads(path.read_text())
        data.update(
            status="committed",
            main_question="What is the effect?",
            central_object_or_phenomenon="the target phenomenon",
            minimum_publishable_claim="The effect is measurable.",
            primary_evidence_obligation="A frozen held-out evaluation.",
            intended_audience="ML researchers",
            next_mandatory_evidence_artifact="results/heldout.json",
            reconsideration_gate="G1",
            pivot_triggers=["fatal prior art"],
            kill_conditions=["no measurable signal"],
        )
        path.write_text(json.dumps(data))
        self.run_cmd(str(VALIDATE_COMMITMENT), str(path))

    def test_d3_requires_authorized_selection_history(self):
        self.run_cmd(str(INIT_COMMITMENT), str(self.root), "--paper-id", "paper-1")
        path = self.root / "research-commitment.json"
        data = json.loads(path.read_text())
        data.update(
            status="committed",
            main_question="Question",
            central_object_or_phenomenon="Object",
            minimum_publishable_claim="Claim",
            primary_evidence_obligation="Evidence",
            intended_audience="Audience",
            next_mandatory_evidence_artifact="result.json",
            reconsideration_gate="G1",
            pivot_triggers=["trigger"],
            kill_conditions=["kill"],
            last_change_class="D3",
            last_change_rationale="Route changed",
        )
        path.write_text(json.dumps(data))
        cp = self.run_cmd(str(VALIDATE_COMMITMENT), str(path), expect=1)
        self.assertIn("authorized pivot", cp.stdout)
        data["selection_history"] = [
            {"decision": "authorize-D3", "rationale": "Fatal defect in incumbent route"}
        ]
        path.write_text(json.dumps(data))
        self.run_cmd(str(VALIDATE_COMMITMENT), str(path))

    def test_pack_force_preserves_commitment_and_explicit_reset_replaces_it(self):
        self.run_cmd(str(INIT_PACK), str(self.root), "--paper-id", "paper-1")
        path = self.root / "research-commitment.json"
        data = json.loads(path.read_text())
        data["main_question"] = "Preserve me"
        path.write_text(json.dumps(data))
        self.run_cmd(str(INIT_PACK), str(self.root), "--force")
        self.assertEqual(json.loads(path.read_text())["main_question"], "Preserve me")
        self.run_cmd(str(INIT_PACK), str(self.root), "--force", "--reset-commitment")
        self.assertEqual(json.loads(path.read_text())["main_question"], "")

    def test_harness_requires_commitment_but_legacy_remains_compatible(self):
        self.run_cmd(str(INIT_PACK), str(self.root), "--paper-id", "paper-1")
        (self.root / "research-commitment.json").unlink()
        cp = self.run_cmd(str(VALIDATE_PACK), str(self.root), "--profile", "harness", expect=1)
        self.assertIn("missing commitment", cp.stdout)
        self.run_cmd(str(INIT_PACK), str(self.root), "--force", "--legacy")
        (self.root / "research-commitment.json").unlink()
        self.run_cmd(str(VALIDATE_PACK), str(self.root), "--profile", "legacy")

    def test_non_object_and_extra_fields_fail_cleanly(self):
        self.root.mkdir(parents=True)
        path = self.root / "research-commitment.json"
        path.write_text("[]")
        cp = self.run_cmd(str(VALIDATE_COMMITMENT), str(path), expect=1)
        self.assertIn("JSON object", cp.stdout)
        self.run_cmd(str(INIT_COMMITMENT), str(self.root), "--paper-id", "paper-1", "--force")
        data = json.loads(path.read_text())
        data["unexpected"] = True
        path.write_text(json.dumps(data))
        cp = self.run_cmd(str(VALIDATE_COMMITMENT), str(path), expect=1)
        self.assertIn("unsupported fields", cp.stdout)


if __name__ == "__main__":
    unittest.main()
