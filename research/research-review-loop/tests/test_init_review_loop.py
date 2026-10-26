#!/usr/bin/env python3
"""Structure-only fixtures for init_review_loop.py round continuation and seeding."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INIT = ROOT / "scripts" / "init_review_loop.py"


def issue(issue_id: str, status: str) -> dict:
    return {
        "id": issue_id,
        "severity": "major",
        "impact_rating": 4,
        "confidence_rating": 3,
        "title": f"Synthetic issue {issue_id}",
        "status": status,
        "evidence": "synthetic evidence",
        "required_action": "synthetic action",
        "source_quote": "placeholder sentence",
        "source_section": "Section 1",
        "related_sections": [],
        "origin": "synthetic",
        "custom_note": "kept verbatim",
    }


class InitReviewLoopTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def run_init(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(INIT), *args], capture_output=True, text=True, check=False
        )

    def write_json(self, path: Path, data) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return path

    def test_continue_from_state_preserves_ids_and_increments_round(self) -> None:
        prior = {
            "version": "1.0",
            "target": "demo draft",
            "round": 3,
            "status": "open",
            "summary": "prior",
            "source_artifacts": ["synthetic/final_issues.json"],
            "open_issues": [issue("F1", "open"), issue("R2-4", "open")],
            "resolved_issues": [issue("F7", "resolved")],
            "accepted_risks": [issue("F9", "accepted")],
        }
        state_path = self.write_json(self.root / "loop" / "round-3" / "REVIEW_STATE.json", prior)
        result = self.run_init("--from-state", str(state_path))
        self.assertEqual(result.returncode, 0, result.stderr)

        new_state_path = self.root / "loop" / "round-4" / "REVIEW_STATE.json"
        self.assertTrue(new_state_path.exists(), result.stdout)
        state = json.loads(new_state_path.read_text(encoding="utf-8"))
        self.assertEqual(state["round"], 4)
        self.assertEqual(state["target"], "demo draft")
        self.assertEqual(state["open_issues"], prior["open_issues"])
        self.assertEqual(state["resolved_issues"], prior["resolved_issues"])
        self.assertEqual(state["accepted_risks"], prior["accepted_risks"])
        self.assertEqual(state["source_artifacts"][0], str(state_path.resolve()))
        # The prior round is untouched.
        self.assertEqual(json.loads(state_path.read_text(encoding="utf-8")), prior)

    def test_explicit_round_and_seeding_preserves_incoming_ids(self) -> None:
        issues = [
            {"id": "F1", "title": "A", "source_quote": "q1", "explanation": "e1", "impact_rating": 5},
            {"title": "B", "quote": "q2", "evidence": "e2", "severity": "minor"},
        ]
        issues_path = self.write_json(self.root / "bundle" / "final_issues.json", issues)
        out = self.root / "loop" / "round-7"
        result = self.run_init(str(out), "--round", "7", "--from-paper-review", str(issues_path))
        self.assertEqual(result.returncode, 0, result.stderr)
        state = json.loads((out / "REVIEW_STATE.json").read_text(encoding="utf-8"))
        self.assertEqual(state["round"], 7)
        self.assertEqual([i["id"] for i in state["open_issues"]], ["F1", "PR1"])
        first, second = state["open_issues"]
        self.assertEqual(first["source_quote"], "q1")
        self.assertEqual(first["severity"], "major")
        self.assertEqual(second["source_quote"], "q2")
        self.assertEqual(second["evidence"], "e2")

    def test_empty_required_field_fails_and_lists_issue_ids(self) -> None:
        issues = [
            {"id": "F1", "title": "A", "quote": "q1", "explanation": "e1", "severity": "major"},
            {"id": "F2", "title": "B", "explanation": "e2", "impact": "prose impact", "confidence": 4},
        ]
        issues_path = self.write_json(self.root / "bundle" / "final_issues.json", issues)
        out = self.root / "loop" / "round-1"
        result = self.run_init(str(out), "--from-paper-review", str(issues_path))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("source_quote", result.stderr)
        self.assertIn("severity", result.stderr)
        self.assertIn("F2", result.stderr)
        self.assertFalse((out / "REVIEW_STATE.json").exists())


if __name__ == "__main__":
    unittest.main()
