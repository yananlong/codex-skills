"""Tests for the ledger-to-outline builder and checker."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from outline_from_ledger import assign, check, render, sections_from_ledger  # noqa: E402

CLAIMS = [
    {"id": "PC-1", "text": "Error falls on family A.", "status": "ready", "sections": ["results", "abstract"], "evidence": ["results/a.csv"]},
    {"id": "PC-2", "text": "The effect holds on family C.", "status": "careful", "sections": ["Results"], "limitations": ["one seed"], "evidence": []},
    {"id": "PC-3", "text": "The scorer is optimal.", "status": "blocked", "sections": ["results"], "missing_evidence": ["a proof"]},
    {"id": "PC-4", "text": "Dropped.", "status": "excluded", "sections": ["results"]},
    {"id": "LIT-S1", "text": "Prior work calibrates once.", "status": "ready", "sections": ["related_work"], "evidence": ["Doe 2021"]},
    {"id": "C9", "text": "Planned claim.", "status": "blocked", "sections": ["appendix"], "missing_evidence": ["an audit"]},
]


class RenderTests(unittest.TestCase):
    def test_assignment_follows_sections_and_skips_excluded(self) -> None:
        placed = assign(CLAIMS, ["method", "results", "related_work", "abstract"])
        self.assertEqual([c["id"] for c in placed["results"]], ["PC-1", "PC-2", "PC-3"])
        self.assertEqual([c["id"] for c in placed["abstract"]], ["PC-1"])
        self.assertEqual([c["id"] for c in placed["related_work"]], ["LIT-S1"])
        self.assertEqual([c["id"] for c in placed["unassigned"]], ["C9"])
        self.assertEqual(placed["method"], [])

    def test_render_marks_statuses(self) -> None:
        text = render(CLAIMS, ["results", "related_work", "abstract"], "manuscript")
        self.assertIn("- Error falls on family A. [PC-1] <- results/a.csv", text)
        self.assertIn("Drafting order: Results, Related Work, Abstract", text)
        self.assertIn("[PC-2] (careful: one seed)", text)
        self.assertIn("- [EVIDENCE NEEDED: a proof] where [PC-3] would go", text)
        self.assertNotIn("PC-4", text)
        self.assertIn("## Unplaced ledger entries", text)
        self.assertIn("## Questions for the author", text)
        self.assertLess(text.index("## 1. Results"), text.index("## 3. Abstract"))


    def test_plan_sections_win_when_bindings_name_them(self) -> None:
        claims = [
            {"id": "PC-1", "text": "A.", "status": "ready", "sections": ["4", "Structural Redundancy"], "source": {"kind": "paper_plan.bindings"}},
            {"id": "PC-2", "text": "B.", "status": "careful", "sections": ["s2"], "source": {"kind": "paper_plan.bindings"}},
            {"id": "PC-3", "text": "C.", "status": "excluded", "sections": ["Appendix Z"], "source": {"kind": "paper_plan.bindings"}},
            {"id": "C1", "text": "D.", "status": "blocked", "sections": ["results"], "source": {"kind": "results_audit"}},
        ]
        self.assertEqual(sections_from_ledger(claims), ["s2", "4", "structural_redundancy"])
        self.assertEqual(sections_from_ledger(CLAIMS), [])
        text = render(claims, sections_from_ledger(claims), "manuscript", plan_order=True)
        self.assertIn("## 1. Section 2", text)
        self.assertIn("## 2. Section 4", text)
        self.assertIn("## 3. Structural Redundancy", text)
        self.assertIn("follow the paper plan's own labels", text)
        self.assertIn("[C1]", text[text.index("## Unplaced"):])


class CheckTests(unittest.TestCase):
    def test_clean_outline_passes(self) -> None:
        outline = render(CLAIMS, ["results", "related_work", "abstract"], "manuscript")
        self.assertEqual(check(outline, CLAIMS), [])

    def test_unplaced_ready_claim_is_reported(self) -> None:
        outline = render(CLAIMS, ["results", "abstract"], "manuscript")  # LIT-S1 lands under Unplaced
        problems = check(outline, CLAIMS)
        self.assertEqual(len(problems), 1)
        self.assertIn("[LIT-S1] (ready) is still unplaced", problems[0])
        self.assertIn("Drafting order: Results, Abstract", outline)

    def test_drift_is_reported(self) -> None:
        outline = (
            "## 1. Results\n"
            "- Error falls on family A. [PC-1]\n"
            "- The scorer is optimal. [PC-3]\n"
            "- Something new. [PC-7]\n"
            "- Dropped. [PC-4]\n"
        )
        problems = check(outline, CLAIMS)
        joined = "\n".join(problems)
        self.assertIn("[PC-3] appears without an evidence marker", joined)
        self.assertIn("[PC-7] is not in the ledger", joined)
        self.assertIn("excluded claim [PC-4]", joined)
        self.assertIn("ledger claim [PC-2] (careful) has no paragraph", joined)
        self.assertIn("ledger claim [LIT-S1] (ready) has no paragraph", joined)
        self.assertEqual(len(problems), 5)

    def test_ids_with_symbols_and_author_brackets(self) -> None:
        claims = [
            {"id": "LIT-Smith & Jones 2020", "text": "A.", "status": "ready", "sections": ["related_work"], "source": {"kind": "literature.evidence_table"}},
            {"id": "1", "text": "B.", "status": "ready", "sections": ["results"], "source": {"kind": "results_audit"}},
        ]
        outline = render(claims, ["results", "related_work"], "manuscript")
        self.assertEqual(check(outline, claims), [])
        edited = outline + "- An author's line [see Table 2] with a note [PC-9].\n"
        problems = check(edited, claims)
        self.assertEqual(problems, ["line " + str(len(edited.splitlines())) + ": [PC-9] is not in the ledger"])

    def test_cli_build_then_check(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ledger = root / "claim-ledger.json"
            ledger.write_text(json.dumps({"claims": CLAIMS}))
            outline = root / "outline.md"
            result = subprocess.run(
                [sys.executable, str(SCRIPTS / "outline_from_ledger.py"), "--ledger", str(ledger), "--out", str(outline), "--piece", "manuscript"],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("outline: 7 sections", result.stdout)
            result = subprocess.run(
                [sys.executable, str(SCRIPTS / "outline_from_ledger.py"), "--ledger", str(ledger), "--check", str(outline)],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout)
            outline.write_text(outline.read_text().replace("[PC-1]", "[PC-1] [ZZ-1]"))
            result = subprocess.run(
                [sys.executable, str(SCRIPTS / "outline_from_ledger.py"), "--ledger", str(ledger), "--check", str(outline)],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("[ZZ-1] is not in the ledger", result.stdout)


if __name__ == "__main__":
    unittest.main()
