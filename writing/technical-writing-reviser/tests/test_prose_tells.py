"""Tests for the machine-prose tell scanner."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from prose_tells import scan, strip_markup  # noqa: E402

TELL_HEAVY = """Importantly, this is not just a tool \u2014 it is a paradigm shift. Our framework leverages a robust,
nuanced, and comprehensive approach, underscoring the crucial role of evaluation. It is worth noting that
results may potentially generalize. This suggests that the method matters. The results speak for themselves.

**Key insight:** the landscape is rapidly evolving, paving the way for future work. Isn't that the point?
"""

CLEAN = """We evaluate the calibration method on three held-out task families with one model family. The
method reduces the expected calibration error on two of the three families, and the third shows no
measurable change. We attribute the difference to label noise in the third family, which the appendix
quantifies. The remaining experiments test whether the reduction survives a change of scorer.
"""


class ProseTellsTests(unittest.TestCase):
    def test_tell_heavy_text_is_flagged_across_categories(self) -> None:
        report = scan(TELL_HEAVY)
        for category in ("dash", "contrast_negation", "signpost_adverb", "inflation", "participial_tail",
                         "meta_commentary", "hedge_stack", "this_opener", "bold_leadin", "rhetorical_question",
                         "kicker", "tricolon_possible"):
            self.assertIn(category, report.counts, category)
        self.assertGreater(report.total_density(), 100)

    def test_clean_technical_prose_is_nearly_silent(self) -> None:
        report = scan(CLEAN)
        self.assertLess(report.total_density(), 15, report.counts)
        self.assertNotIn("inflation", report.counts)
        self.assertNotIn("contrast_negation", report.counts)

    def test_latex_markup_is_stripped_before_scanning(self) -> None:
        latex = (
            "We report results~\\cite{crucial2024} in Table~\\ref{tab:robust}. % robust comment \u2014 ignored\n"
            "The estimate is $\\delta = 0.1$ and \\emph{holds} under the stated hypotheses.\n"
        )
        cleaned = strip_markup(latex)
        self.assertNotIn("crucial2024", cleaned)
        self.assertNotIn("robust comment", cleaned)
        self.assertIn("holds", cleaned)
        report = scan(latex)
        self.assertNotIn("dash", report.counts)
        self.assertNotIn("inflation", report.counts)

    def test_markdown_code_and_links_are_not_scanned(self) -> None:
        text = "See [the robust guide](https://example.org) and run `leverage --all` to proceed.\n\n```\ncrucial = pivotal\n```\n"
        report = scan(text)
        self.assertEqual(report.counts.get("inflation", 0), 1)  # only the link text word 'robust'

    def test_cli_baseline_comparison_and_fail_flag(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "before.md").write_text(CLEAN, encoding="utf-8")
            (root / "after.md").write_text(TELL_HEAVY, encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPTS / "prose_tells.py"), str(root / "after.md"),
                 "--baseline", str(root / "before.md"), "--fail-if-worse"],
                capture_output=True, text=True, check=False, timeout=30,
            )
            self.assertEqual(result.returncode, 1, result.stdout)
            self.assertIn("WORSE", result.stdout)
            self.assertIn("higher tell density", result.stderr)
            result = subprocess.run(
                [sys.executable, str(SCRIPTS / "prose_tells.py"), str(root / "before.md"),
                 "--baseline", str(root / "after.md"), "--fail-if-worse", "--format", "json"],
                capture_output=True, text=True, check=False, timeout=30,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertIn("baseline", payload)
            self.assertLess(payload["total_density_per_1k"], payload["baseline"]["total_density_per_1k"])

    def test_uniform_rhythm_and_anaphora_are_reported_as_possible(self) -> None:
        text = ("The model reads the input once. The model writes the output twice. The model stores the state after. "
                "The model reports the result then.\n")
        report = scan(text)
        self.assertIn("uniform_rhythm", report.counts)
        self.assertIn("anaphora_possible", report.counts)


if __name__ == "__main__":
    unittest.main()
