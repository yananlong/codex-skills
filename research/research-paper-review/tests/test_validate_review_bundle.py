#!/usr/bin/env python3
"""Structure-only fixtures for validate_review_bundle.py provenance families."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATE = ROOT / "scripts" / "validate_review_bundle.py"

VALID_SUMMARY = {
    "overall_paper_rating": 3,
    "decision_relevance_rating": 4,
    "rating_confidence": 3,
    "top_blockers": ["ISSUE-1"],
}


def severity_issue(n: int) -> dict:
    return {
        "title": f"Issue {n}",
        "quote": f"placeholder sentence {n}",
        "explanation": "synthetic explanation",
        "comment_type": "technical",
        "severity": "major" if n == 1 else "minor",
    }


def rated_issue(n: int) -> dict:
    issue = severity_issue(n)
    issue.pop("severity")
    issue.update({"impact_rating": 4, "confidence_rating": 3})
    return issue


class ValidateReviewBundleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "review_results"
        self.review_dir = self.root / "demo_review"

    def tearDown(self) -> None:
        self.temp.cleanup()

    def write_json(self, path: Path, data) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def make_bundle(self, issues: list[dict], metadata: dict | None = None) -> None:
        d = self.review_dir
        (d / "sections").mkdir(parents=True, exist_ok=True)
        (d / "summary.md").write_text("# Summary\n", encoding="utf-8")
        (d / "overall_assessment.txt").write_text("synthetic\n", encoding="utf-8")
        (d / "full_text.md").write_text("placeholder sentence 1\n", encoding="utf-8")
        self.write_json(d / "metadata.json", metadata or {"title": "Demo", "slug": "demo"})
        self.write_json(d / "sections" / "index.json", [{"file": "01_intro.md"}])
        self.write_json(d / "final_issues.json", issues)

    def run_validator(self, *extra: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(VALIDATE), "--review-dir", str(self.review_dir), *extra],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_openaireview_claude_bundle_without_summary_passes(self) -> None:
        self.make_bundle([severity_issue(1), severity_issue(2)])
        result = self.run_validator()
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("Inferred family: openaireview_claude", result.stdout)

    def test_openaireview_claude_rejects_root_summary_when_asserted(self) -> None:
        self.make_bundle([severity_issue(1)])
        self.write_json(self.review_dir / "review_summary.json", VALID_SUMMARY)
        result = self.run_validator("--family", "openaireview_claude")
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("Inferred family: codex_native", result.stdout)
        self.assertIn("carry no root review_summary.json", result.stdout)

    def test_codex_native_bundle_passes_and_requires_ratings(self) -> None:
        self.make_bundle([rated_issue(1), rated_issue(2)])
        self.write_json(self.review_dir / "review_summary.json", VALID_SUMMARY)
        result = self.run_validator()
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("Inferred family: codex_native", result.stdout)

        self.write_json(self.review_dir / "final_issues.json", [severity_issue(1)])
        failed = self.run_validator()
        self.assertEqual(failed.returncode, 1, failed.stdout)
        self.assertIn("Inferred family: codex_native", failed.stdout)
        self.assertIn("missing required rating keys", failed.stdout)

    def test_hybrid_sibling_rounds_use_newest_valid_summary(self) -> None:
        self.make_bundle([severity_issue(1)])
        self.write_json(self.root / "round-1" / "review_summary.json", VALID_SUMMARY)
        self.write_json(self.root / "round-1" / "REVIEW_STATE.json", {"round": 1})
        # Newer round with drifted summary keys must be skipped, not chosen.
        self.write_json(self.root / "round-2" / "review_summary.json", {"overall_score_1_to_5": 3})
        result = self.run_validator()
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("Inferred family: review_loop_hybrid", result.stdout)
        self.assertIn(str(self.root / "round-1" / "review_summary.json"), result.stdout)
        self.assertIn("skipped round summary", result.stdout)

    def test_hybrid_metadata_round_summaries_resolve(self) -> None:
        self.make_bundle(
            [severity_issue(1)],
            metadata={"title": "Demo", "round_summaries": {"round-3": "round-3/review_summary.json"}},
        )
        self.write_json(self.review_dir / "round-3" / "review_summary.json", VALID_SUMMARY)
        result = self.run_validator()
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("Inferred family: review_loop_hybrid", result.stdout)

    def test_hybrid_without_valid_summary_fails_and_reports_family(self) -> None:
        self.make_bundle([severity_issue(1)])
        self.write_json(self.root / "round-1" / "REVIEW_STATE.json", {"round": 1})
        self.write_json(self.root / "round-1" / "review_summary.json", {"overall_score_1_to_5": 3})
        result = self.run_validator()
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("Inferred family: review_loop_hybrid", result.stdout)
        self.assertIn("resolvable valid round summary", result.stdout)
        first_pass = self.run_validator("--family", "openaireview_claude")
        self.assertEqual(first_pass.returncode, 0, first_pass.stdout)


if __name__ == "__main__":
    unittest.main()
