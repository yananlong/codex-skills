"""Tests for the artifact inventory."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from inventory_artifacts import classify, summarize, walk  # noqa: E402


def make_project(root: Path) -> None:
    (root / "paper").mkdir()
    (root / "paper" / "claim-evidence-bindings.json").write_text("{}")
    (root / "paper" / "paper-plan.md").write_text("# plan")
    (root / "results").mkdir()
    (root / "results" / "results-audit.json").write_text("{}")
    (root / "results" / "ece.csv").write_text("a,b\n1,2\n")
    (root / "results" / "config.json").write_text("{}")
    (root / "lit").mkdir()
    (root / "lit" / "calibration.evidence-table.md").write_text("| study_id |\n| --- |\n")
    (root / "figures").mkdir()
    (root / "figures" / "fig1.pdf").write_text("")
    (root / "refs.pdf").write_text("")
    (root / "settings.json").write_text("{}")
    (root / "notes.md").write_text("notes")
    (root / ".git").mkdir()
    (root / ".git" / "results-audit.json").write_text("{}")
    (root / "__pycache__").mkdir()
    (root / "__pycache__" / "x.csv").write_text("")


class ClassifyTests(unittest.TestCase):
    def test_suite_artifacts_are_recognised(self) -> None:
        self.assertEqual(classify(Path("paper/claim-evidence-bindings.json")), ("paper_plan.bindings", "claims"))
        self.assertEqual(classify(Path("x/results-audit.json")), ("results_audit.json", "evidence"))
        self.assertEqual(classify(Path("lit/topic.evidence-table.md")), ("literature.evidence_table", "literature"))
        self.assertEqual(classify(Path("rebuttal/issue-board.md")), ("rebuttal.issue_board", "critique"))
        self.assertEqual(classify(Path("main.tex")), ("manuscript.latex", "source"))

    def test_bare_json_outside_results_is_ignored(self) -> None:
        self.assertIsNone(classify(Path("settings.json")))
        self.assertEqual(classify(Path("results/run1.json")), ("data.json", "data"))

    def test_pdf_outside_figures_is_a_document(self) -> None:
        self.assertEqual(classify(Path("figures/fig1.pdf")), ("figure", "figure"))
        self.assertEqual(classify(Path("refs.pdf")), ("document.pdf", "literature"))


class WalkTests(unittest.TestCase):
    def test_walk_skips_hidden_and_cache_dirs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_project(root)
            artifacts, truncated = walk(root, 1000)
            paths = {a.path for a in artifacts}
            self.assertFalse(truncated)
            self.assertIn("paper/claim-evidence-bindings.json", paths)
            self.assertIn("results/results-audit.json", paths)
            self.assertNotIn(".git/results-audit.json", paths)
            self.assertNotIn("__pycache__/x.csv", paths)
            self.assertNotIn("settings.json", paths)

    def test_skipped_dirs_are_pruned_and_max_files_counts_visited(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".venv" / "lib").mkdir(parents=True)
            for i in range(50):
                (root / ".venv" / "lib" / f"m{i}.py").write_text("")
            (root / "results").mkdir()
            (root / "results" / "results-audit.json").write_text("{}")
            for i in range(10):
                (root / f"plain{i}.cfg").write_text("")
            artifacts, truncated = walk(root, 5)
            self.assertTrue(truncated)
            self.assertLessEqual(len(artifacts), 5)
            artifacts, truncated = walk(root, 1000)
            self.assertFalse(truncated)
            self.assertEqual([a.path for a in artifacts], ["results/results-audit.json"])

    def test_summary_names_gaps(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "results").mkdir()
            (root / "results" / "scores.tsv").write_text("a\tb\n")
            artifacts, _ = walk(root, 1000)
            summary = summarize(artifacts)
            self.assertEqual(summary["claim_sources"], [])
            joined = " ".join(summary["gaps"])
            self.assertIn("no claim source", joined)
            self.assertIn("without a results audit", joined)
            self.assertIn("no literature artifact", joined)

    def test_bulky_data_folders_collapse_to_one_entry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for i in range(25):
                (root / "results" / "runs" / f"seed{i}").mkdir(parents=True)
                (root / "results" / "runs" / f"seed{i}" / "metrics.json").write_text("{}")
            (root / "results" / "summary.csv").write_text("a\n")
            artifacts, _ = walk(root, 1000)
            by_path = {a.path: a for a in artifacts}
            self.assertIn("results/runs/", by_path)
            self.assertEqual(by_path["results/runs/"].count, 25)
            self.assertIn("results/summary.csv", by_path)
            self.assertEqual(len(artifacts), 2)

    def test_multiple_claim_packs_are_flagged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for paper in ("paper-a", "paper-b"):
                (root / paper).mkdir()
                (root / paper / "claim-evidence-bindings.json").write_text("{}")
            artifacts, _ = walk(root, 1000)
            summary = summarize(artifacts)
            self.assertEqual(summary["claim_pack_dirs"], ["paper-a", "paper-b"])
            self.assertTrue(any("2 claim packs" in gap for gap in summary["gaps"]))

    def test_cli_writes_json_and_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_project(root)
            out_json = root / "writing-intake.json"
            out_md = root / "writing-intake.md"
            result = subprocess.run(
                [sys.executable, str(SCRIPTS / "inventory_artifacts.py"), str(root), "--out-json", str(out_json), "--out-md", str(out_md)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            record = json.loads(out_json.read_text())
            self.assertEqual(record["summary"]["claim_sources"], ["paper_plan.bindings", "results_audit.json"])
            self.assertIn("| claims | paper_plan.bindings |", out_md.read_text())


if __name__ == "__main__":
    unittest.main()
