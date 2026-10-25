#!/usr/bin/env python3
"""Regression tests for the four-file paper-context evidence-map helper."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "paper_context_artifacts.py"
FILES = (
    "literature-context.md",
    "literature-context-search-log.md",
    "literature-context-evidence-table.md",
)


class PaperContextTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.out = Path(self.temp.name) / "context"
        cp = self.run_cmd("init", "--out-dir", str(self.out), "--target-paper", "Synthetic Paper", "--domain", "Synthetic domain")
        self.assertEqual(cp.returncode, 0, cp.stdout + cp.stderr)
        self.decision_path = self.out / "literature-context-decision.json"

    def tearDown(self) -> None:
        self.temp.cleanup()

    def run_cmd(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable, str(SCRIPT), *args], text=True, capture_output=True)

    def validate(self, *extra: str) -> subprocess.CompletedProcess[str]:
        return self.run_cmd("validate", "--out-dir", str(self.out), *extra)

    def decision(self) -> dict:
        return json.loads(self.decision_path.read_text())

    def fill(self) -> None:
        for name in FILES:
            path = self.out / name
            path.write_text(path.read_text().replace("TODO", "synthetic entry"))
        decision = self.decision()
        decision.update(
            contextualization_rating=2,
            impact_evidence_rating=3,
            coverage_confidence_rating=2,
            closest_prior_work=["P1 synthetic"],
            limits_of_search=["Single synthetic source"],
        )
        self.decision_path.write_text(json.dumps(decision))

    def test_scaffold_ratings_start_null(self) -> None:
        decision = self.decision()
        for field in ("contextualization_rating", "impact_evidence_rating", "coverage_confidence_rating"):
            self.assertIsNone(decision[field])
        self.assertNotIn("| TODO | TODO | 3 |", (self.out / "literature-context.md").read_text())

    def test_untouched_scaffold_fails_validation(self) -> None:
        cp = self.validate()
        self.assertEqual(cp.returncode, 1, cp.stdout + cp.stderr)
        self.assertIn("literature-context.md still has", cp.stdout)
        self.assertIn("TODO placeholder", cp.stdout)
        self.assertIn("contextualization_rating is unset (null)", cp.stdout)

    def test_draft_flag_allows_todos_and_null_ratings(self) -> None:
        cp = self.validate("--draft")
        self.assertEqual(cp.returncode, 0, cp.stdout + cp.stderr)

    def test_filled_bundle_passes(self) -> None:
        self.fill()
        cp = self.validate()
        self.assertEqual(cp.returncode, 0, cp.stdout + cp.stderr)

    def test_single_remaining_todo_fails(self) -> None:
        self.fill()
        evidence = self.out / "literature-context-evidence-table.md"
        evidence.write_text(evidence.read_text() + "| P2 | TODO | | | | | | | |\n")
        cp = self.validate()
        self.assertEqual(cp.returncode, 1, cp.stdout + cp.stderr)
        self.assertIn("literature-context-evidence-table.md still has 1 TODO", cp.stdout)

    def test_list_fields_and_mode_are_type_checked(self) -> None:
        self.fill()
        decision = self.decision()
        decision["limits_of_search"] = "one synthetic sentence"
        decision["closest_prior_work"] = {"P1": "synthetic"}
        del decision["mode"]
        self.decision_path.write_text(json.dumps(decision))
        cp = self.validate()
        self.assertEqual(cp.returncode, 1, cp.stdout + cp.stderr)
        self.assertIn("limits_of_search must be a list", cp.stdout)
        self.assertIn("closest_prior_work must be a list", cp.stdout)
        self.assertIn("mode must equal paper_context_evidence_map", cp.stdout)


if __name__ == "__main__":
    unittest.main()
