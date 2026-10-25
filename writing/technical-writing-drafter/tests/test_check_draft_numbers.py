"""Tests for the draft number tracer."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from check_draft_numbers import check, extract_draft_numbers, matches, source_values  # noqa: E402


class ExtractTests(unittest.TestCase):
    def test_skips_structure_numbers_years_and_citations(self) -> None:
        text = (
            "As Section 3 and Table 2 show, error falls to 12.3\\% in 2024 [12] on 1,200 examples.\n"
            "Figure 4 and Eq. 7 agree; see \\cite{doe2021} and \\ref{fig:5}. Appendix B, step 2. % 88 in a comment\n"
            "[EVIDENCE NEEDED: 95% interval]\n"
        )
        tokens = [token for _, token in extract_draft_numbers(text)]
        self.assertEqual(tokens, ["12.3%", "1,200"])

    def test_latex_comment_is_ignored(self) -> None:
        text = "The gain is \\emph{0.42} % and 99 in the comment\n"
        tokens = [token for _, token in extract_draft_numbers(text)]
        self.assertEqual(tokens, ["0.42"])

    def test_markdown_footnote_and_code_span_are_ignored(self) -> None:
        text = "The gain is 0.42, see footnote[^3] and `code 77` and [a link](http://x/12).\n"
        tokens = [token for _, token in extract_draft_numbers(text)]
        self.assertEqual(tokens, ["0.42"])


    def test_latex_quotes_do_not_swallow_text(self) -> None:
        text = (
            "We call this `triangulation' in \\section{Method}.\n"
            "Error falls to 7.1\\% on 48 items.\n"
            "The `second' quote closes here, with 0.42 after it.\n"
        )
        tokens = [token for _, token in extract_draft_numbers(text)]
        self.assertEqual(tokens, ["7.1%", "48", "0.42"])


class MatchTests(unittest.TestCase):
    def test_rounding_and_percent_conversion(self) -> None:
        sources = {0.8234, 1200.0, 3.14159}
        self.assertTrue(matches("82.3%", sources))
        self.assertTrue(matches("82%", sources))
        self.assertTrue(matches("0.82", sources))
        self.assertTrue(matches("1,200", sources))
        self.assertTrue(matches("3.14", sources))
        self.assertFalse(matches("3.15", sources))
        self.assertFalse(matches("91.5%", sources))
        self.assertFalse(matches("9.9%", {0.071}))
        self.assertTrue(matches("7.1%", {0.071}))

    def test_source_values_from_json_csv_and_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.json").write_text(json.dumps({"audits": [{"metric": 0.5, "note": "n=48", "ok": True}]}))
            (root / "b.csv").write_text("name,ece\nfamA,0.071\nfamB,\"1,024\"\n")
            (root / "c.md").write_text("| run | acc |\n| --- | --- |\n| r1 | 0.903 |\n")
            values = source_values(root / "a.json") | source_values(root / "b.csv") | source_values(root / "c.md")
            self.assertEqual(values, {0.5, 48.0, 0.071, 1024.0, 0.903})


class CheckTests(unittest.TestCase):
    def test_check_reports_untraced_and_markers(self) -> None:
        draft = "Error is 7.1% on family A and 9.9% on family B. [CITATION NEEDED: baseline paper]\n"
        report = check(draft, {0.071}, set())
        self.assertEqual([t["token"] for t in report["traced"]], ["7.1%"])
        self.assertEqual([t["token"] for t in report["untraced"]], ["9.9%"])
        self.assertEqual(report["markers"][0]["marker"], "[CITATION NEEDED: baseline paper]")

    def test_allow_list(self) -> None:
        report = check("We train for 300 epochs with error 7.1%.", {0.071}, {"300"})
        self.assertEqual(report["untraced"], [])

    def test_cli_exit_codes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            draft = root / "draft.md"
            source = root / "results.csv"
            source.write_text("metric,value\nece,0.071\n")
            draft.write_text("Error is 7.1% here and 12.5% there.\n")
            cmd = [sys.executable, str(SCRIPTS / "check_draft_numbers.py"), str(draft), "--source", str(source)]
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 1)
            self.assertIn("untraced line 1: 12.5%", result.stdout)
            result = subprocess.run(cmd + ["--allow-untraced", "--format", "json"], capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(json.loads(result.stdout)["untraced"][0]["token"], "12.5%")
            result = subprocess.run(cmd + ["--allow", "12.5%"], capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0, result.stdout)


if __name__ == "__main__":
    unittest.main()
