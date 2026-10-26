#!/usr/bin/env python3
"""Synthetic fixtures for review_schema.py, resolve_review_artifacts.py, and the engine pin."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import _engine  # noqa: E402
import resolve_review_artifacts as resolver  # noqa: E402
from review_schema import load_issues, normalise_issue, normalise_summary  # noqa: E402


def write(path: Path, data) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(data if isinstance(data, str) else json.dumps(data), encoding="utf-8")
    return path


def state(round_no, open_issues=(), resolved=()):
    return {
        "version": "1.0", "target": "synthetic draft", "round": round_no, "status": "open", "summary": "s",
        "source_artifacts": [], "open_issues": list(open_issues), "resolved_issues": list(resolved),
        "accepted_risks": [],
    }


class SchemaTests(unittest.TestCase):
    def test_aliases_map_and_unmapped_fields_are_kept(self):
        issue = normalise_issue({
            "issue_id": "X1", "issue": "Synthetic gap", "explanation": "e", "quote": "q", "location": "Sec 2",
            "impact": 4, "confidence": "3", "recommendation": "add a table", "custom": 1,
        })
        self.assertEqual(issue["id"], "X1")
        self.assertEqual(issue["title"], "Synthetic gap")
        self.assertEqual(issue["severity"], "major")
        self.assertEqual(issue["confidence_rating"], 3)
        self.assertEqual(issue["source_section"], "Sec 2")
        self.assertEqual(issue["required_action"], "add a table")
        self.assertEqual(issue["extra"], {"custom": 1})
        self.assertEqual(issue["_problems"], [])
        self.assertEqual(issue["_aliases"]["source_quote"], "quote")

    def test_severity_words_and_prose_impact(self):
        self.assertEqual(normalise_issue({"title": "t", "severity": "Blocking"})["severity"], "major")
        self.assertEqual(normalise_issue({"title": "t", "severity": "Major-Addressable"})["severity"], "major")
        self.assertEqual(normalise_issue({"title": "t", "severity": "Misunderstanding"})["severity"], "minor")
        problems = normalise_issue({"title": "t", "impact": "large in prose"})["_problems"]
        self.assertTrue(any("severity" in problem for problem in problems))

    def test_closed_references_are_notes_and_filled_by_id(self):
        path = write(Path(self.tmp.name) / "REVIEW_STATE.json", state(
            2,
            open_issues=[{"id": "R1", "title": "Open gap", "severity": "minor", "status": "open"}],
            resolved=[{"id": "R1", "status": "resolved", "resolution": "fixed"},
                      {"id": "R9", "status": "resolved", "resolution": "fixed earlier"}],
        ))
        layout, issues, _ = load_issues(path)
        self.assertEqual(layout, "review_loop_state")
        r1_closed, r9 = issues[1], issues[2]
        self.assertEqual(r1_closed["title"], "Open gap")
        self.assertEqual(r9["_problems"], [])
        self.assertTrue(r9["_notes"])

    def test_extended_state_lists_are_read(self):
        data = state(3)
        data["carried_round2_issues"] = [{"id": "C1", "title": "Carried", "severity": "major"}]
        layout, issues, _ = load_issues(write(Path(self.tmp.name) / "s.json", data))
        self.assertEqual(layout, "review_loop_state_extended")
        self.assertEqual(issues[0]["extra"]["source_list"], "carried_round2_issues")

    def test_issue_board_rows_become_issues(self):
        board = (
            "# Issue Board\n\n| Issue ID | Reviewer | Internal issue IDs | Severity | Category | Strategy | Stance | Status "
            "| Shared with | Evidence source | Notes |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n"
            "| EXT-a-1 | a | R1, R4 | major | baseline | add_evidence | concede | open | | results/b.json | Missing baseline |\n"
        )
        layout, issues, _ = load_issues(write(Path(self.tmp.name) / "issue-board.md", board))
        self.assertEqual(layout, "rebuttal_issue_board")
        self.assertEqual(issues[0]["title"], "Missing baseline")
        self.assertEqual(issues[0]["prior_issue_ids"], ["R1", "R4"])
        self.assertEqual(issues[0]["origin"], "reviewer a")

    def test_bundle_layouts_are_named(self):
        native = write(Path(self.tmp.name) / "a" / "final_issues.json", [
            {"title": "t", "quote": "q", "explanation": "e", "comment_type": "c", "impact_rating": 3, "confidence_rating": 4}])
        claude = write(Path(self.tmp.name) / "b" / "final_issues.json", [
            {"title": "t", "quote": "q", "explanation": "e", "comment_type": "c", "severity": "minor"}])
        self.assertEqual(load_issues(native)[0], "paper_review_native")
        self.assertEqual(load_issues(claude)[0], "openaireview_claude")

    def test_summary_aliases_and_strict_ratings(self):
        summary, aliases, problems = normalise_summary({
            "overall_score_1_to_5": 3, "decision_relevance_rating": 4, "confidence_score_1_to_5": 2,
            "top_open_issue_ids": ["R1"]})
        self.assertEqual(problems, [])
        self.assertEqual(aliases["overall_paper_rating"], "overall_score_1_to_5")
        _, _, problems = normalise_summary({
            "overall_paper_rating": "3", "decision_relevance_rating": 4, "rating_confidence": 2, "top_blockers": []})
        self.assertTrue(any("overall_paper_rating" in problem for problem in problems))

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.tmp.cleanup()


class ResolverTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def layouts(self):
        return {unit.layout for unit in resolver.find_units(self.root)}

    def test_every_known_layout_is_classified(self):
        ws = self.root / "review_results" / "demo_review"
        write(ws / "final_issues.json", [])
        write(ws / "round-1" / "REVIEW_STATE.json", state(1))
        write(self.root / "proj" / "review-loop" / "round-2" / "REVIEW_STATE.json", state(2))
        write(self.root / "proj" / "review-loop" / "round-2" / "paper-review" / "final_issues.json", [])
        write(self.root / "dated" / "review-loop" / "round-2026-01-05-blind" / "REVIEW_STATE.json", state(4))
        write(self.root / "labelled" / "reviews" / "venue-review-3" / "REVIEW_STATE.json", state(3))
        write(self.root / "flat" / "review-loop" / "REVIEW_STATE.json", state(1))
        write(self.root / "other" / "review" / "final_issues.json", [])
        write(self.root / "reb" / "issue-board.md", "# Issue Board\n")
        self.assertEqual(self.layouts(), {
            "canonical_workspace", "canonical_round", "numbered_round", "nested_bundle", "dated_round",
            "labelled_round", "flat_state", "bundle", "issue_board"})

    def test_latest_round_prefers_state_round_then_folder(self):
        loop = self.root / "review-loop"
        write(loop / "round-2" / "REVIEW_STATE.json", state(2))
        write(loop / "round-2026-03-01" / "REVIEW_STATE.json", state(5))
        write(loop / "round-3" / "REVIEW_STATE.json", {k: v for k, v in state(3).items() if k != "round"})
        units = resolver.find_units(self.root)
        newest = resolver.latest_round(units)
        self.assertTrue(newest.path.endswith("round-2026-03-01"))
        self.assertEqual(resolver.next_round_dir(loop, units), loop / "round-6")

    def test_next_round_cli_canonical_and_ambiguity(self):
        script = SCRIPTS / "resolve_review_artifacts.py"
        cp = subprocess.run([sys.executable, str(script), "--root", str(self.root), "--next-round", "--slug", "demo"],
                            capture_output=True, text=True)
        self.assertEqual(cp.stdout.strip(), str(self.root / "review_results" / "demo_review" / "round-1"))
        write(self.root / "a" / "review-loop" / "round-1" / "REVIEW_STATE.json", state(1))
        write(self.root / "b" / "review-loop" / "round-4" / "REVIEW_STATE.json", state(4))
        cp = subprocess.run([sys.executable, str(script), "--root", str(self.root), "--next-round"],
                            capture_output=True, text=True)
        self.assertEqual(cp.returncode, 2)
        self.assertIn("--review-dir", cp.stderr)
        cp = subprocess.run([sys.executable, str(script), "--root", str(self.root), "--next-round",
                             "--review-dir", str(self.root / "b" / "review-loop" / "round-4")], capture_output=True, text=True)
        self.assertEqual(cp.stdout.strip(), str(self.root / "b" / "review-loop" / "round-5"))
        cp = subprocess.run([sys.executable, str(script), "--root", str(self.root), "--json"], capture_output=True, text=True)
        self.assertEqual(len(json.loads(cp.stdout)["reviews"]), 2)


class EnginePinTests(unittest.TestCase):
    def test_install_specs_are_pinned(self):
        self.assertEqual(_engine.build_install_spec("pypi", "ignored", []), f"openaireview=={_engine.ENGINE_VERSION}")
        spec = _engine.build_install_spec("github", _engine.ENGINE_COMMIT, ["mistral"])
        self.assertIn(f"@{_engine.ENGINE_COMMIT}", spec)
        self.assertTrue(_engine.is_pinned("github", _engine.ENGINE_TAG))
        self.assertFalse(_engine.is_pinned("github", "main"))

    def test_default_venv_is_versioned_and_outside_the_skill(self):
        env = {key: value for key, value in os.environ.items() if key != "OPENAIREVIEW_VENV"}
        env["XDG_DATA_HOME"] = "/tmp/synthetic-data-home"
        code = "import _engine; print(_engine.DEFAULT_VENV)"
        out = subprocess.run([sys.executable, "-c", code], cwd=SCRIPTS, env=env, capture_output=True, text=True).stdout.strip()
        self.assertEqual(out, f"/tmp/synthetic-data-home/codex-skills/openaireview-{_engine.ENGINE_VERSION}")
        with self.assertRaises(SystemExit):
            _engine.ensure_virtualenv(_engine.SKILL_DIR / ".openaireview-venv")

    def test_pin_problem(self):
        self.assertIsNone(_engine.pin_problem(_engine.ENGINE_VERSION, {"pinned": True}))
        self.assertIn("--reinstall", _engine.pin_problem("0.0.1", {"pinned": True}))
        self.assertIsNone(_engine.pin_problem("0.0.1", {"pinned": False}))
        self.assertIsNotNone(_engine.pin_problem(None, None))


if __name__ == "__main__":
    unittest.main()
