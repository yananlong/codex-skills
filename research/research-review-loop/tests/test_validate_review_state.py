#!/usr/bin/env python3
"""Synthetic fixtures for validate_review_state.py and the importer's canonical defaults."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
VALIDATE = SCRIPTS / "validate_review_state.py"
INIT = SCRIPTS / "init_review_loop.py"


def canonical_state(**extra):
    data = {
        "version": "1.0", "target": "synthetic draft", "round": 2, "status": "open", "summary": "s",
        "source_artifacts": [],
        "open_issues": [{"id": "R1", "title": "Gap", "severity": "major", "status": "open", "evidence": "e"}],
        "resolved_issues": [{"id": "R0", "status": "resolved", "resolution": "fixed in round 1"}],
        "accepted_risks": [],
    }
    data.update(extra)
    return data


class ValidateReviewStateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def run_validate(self, data, *flags):
        path = self.root / "round-2" / "REVIEW_STATE.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data))
        return subprocess.run([sys.executable, str(VALIDATE), str(path.parent), *flags], capture_output=True, text=True)

    def test_canonical_state_passes_strict(self):
        cp = self.run_validate(canonical_state(), "--strict")
        self.assertEqual(cp.returncode, 0, cp.stdout)
        self.assertIn("closed reference", cp.stdout)

    def test_legacy_names_warn_by_default_and_fail_strict(self):
        data = canonical_state()
        data["open_issues"] = [{"id": "R1", "issue": "Gap", "impact": 5, "fix": "add a run", "status": "open"}]
        del data["summary"]
        cp = self.run_validate(data)
        self.assertEqual(cp.returncode, 0, cp.stdout)
        self.assertIn("legacy field names", cp.stdout)
        cp = self.run_validate(data, "--strict")
        self.assertEqual(cp.returncode, 1)
        self.assertIn("outside the canonical issue schema", cp.stdout)
        self.assertIn("missing top-level fields: summary", cp.stdout)

    def test_open_issue_without_severity_and_duplicate_ids_fail(self):
        data = canonical_state()
        data["open_issues"].append({"id": "R2", "title": "No severity", "status": "open"})
        data["open_issues"].append({"id": "R1", "title": "Again", "severity": "minor", "status": "open"})
        cp = self.run_validate(data)
        self.assertEqual(cp.returncode, 1)
        self.assertIn("issue R2: no severity", cp.stdout)
        self.assertIn("duplicate issue id R1 in open_issues", cp.stdout)

    def test_importer_writes_round_one_in_the_bundle_workspace_and_passes_strict(self):
        bundle = self.root / "review_results" / "demo_review"
        bundle.mkdir(parents=True)
        (bundle / "final_issues.json").write_text(json.dumps([
            {"id": "F1", "title": "Gap", "quote": "q", "explanation": "e", "impact_rating": 4,
             "comment_type": "methodology", "reviewer_note": "kept"}]))
        cp = subprocess.run([sys.executable, str(INIT), "--from-paper-review", str(self.root)], capture_output=True, text=True)
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        state_path = bundle / "round-1" / "REVIEW_STATE.json"
        self.assertTrue(state_path.exists(), cp.stdout)
        state = json.loads(state_path.read_text())
        self.assertEqual(state["open_issues"][0]["extra"], {"reviewer_note": "kept"})
        self.assertEqual(state["open_issues"][0]["comment_type"], "methodology")
        self.assertNotIn("departure", cp.stdout)
        check = subprocess.run([sys.executable, str(VALIDATE), str(state_path), "--strict"], capture_output=True, text=True)
        self.assertEqual(check.returncode, 0, check.stdout)
        cp = subprocess.run([sys.executable, str(INIT), "--from-state", str(state_path)], capture_output=True, text=True)
        self.assertEqual(cp.returncode, 0, cp.stderr)
        self.assertTrue((bundle / "round-2" / "REVIEW_STATE.json").exists())


if __name__ == "__main__":
    unittest.main()
