"""Tests for the LaTeX before/after survival check."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from latex_visible_diff import compare, inventory  # noqa: E402

BEFORE = r"""\section{Results}\label{sec:results}
The scorer lowers error on family A \citep{doe2021,roe2020}. % audited: AUD-1
We report \slotA{} as the headline value. % slot macro, provenance in results/a.csv
See \cref{fig:ece} and Table~\ref{tab:main}.
"""


class InventoryTests(unittest.TestCase):
    def test_inventory_counts(self) -> None:
        inv = inventory(BEFORE)
        self.assertEqual(set(inv["cites"]), {"doe2021", "roe2020"})
        self.assertEqual(set(inv["labels"]), {"sec:results"})
        self.assertEqual(set(inv["refs"]), {"fig:ece", "tab:main"})
        self.assertIn("slotA", inv["macros"])
        self.assertEqual(inv["comment_lines"], 2)

    def test_faithful_revision_passes(self) -> None:
        after = BEFORE.replace("We report \\slotA{} as the headline value.", "The headline value is \\slotA{}.")
        report = compare(BEFORE, after, allow_dropped_comments=False)
        self.assertEqual(report["problems"], [])
        self.assertGreater(report["visible_similarity"], 0.8)

    def test_joined_line_and_lost_key_are_problems(self) -> None:
        after = (
            "\\section{Results}\\label{sec:results}\n"
            "The scorer lowers error on family A \\citep{doe2021}. We report \\slotA{} as the headline value.\n"
            "See \\cref{fig:ece} and Table~\\ref{tab:main}.\n"
        )
        report = compare(BEFORE, after, allow_dropped_comments=False)
        joined = "\n".join(report["problems"])
        self.assertIn("citation key 'roe2020'", joined)
        self.assertIn("comment-terminated lines fell from 2 to 0", joined)

    def test_cli_exit_code(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            before = Path(tmp) / "before.tex"
            after = Path(tmp) / "after.tex"
            before.write_text(BEFORE)
            after.write_text(BEFORE.replace("\\label{sec:results}", ""))
            result = subprocess.run([sys.executable, str(SCRIPTS / "latex_visible_diff.py"), str(before), str(after)], capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 1)
            self.assertIn("label 'sec:results'", result.stdout)
            after.write_text(BEFORE)
            result = subprocess.run([sys.executable, str(SCRIPTS / "latex_visible_diff.py"), str(before), str(after)], capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0, result.stdout)


if __name__ == "__main__":
    unittest.main()
