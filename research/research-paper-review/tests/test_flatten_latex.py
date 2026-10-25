#!/usr/bin/env python3
"""Synthetic LaTeX tree fixture for flatten_latex.py."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FLATTEN = ROOT / "scripts" / "flatten_latex.py"

MAIN = r"""\documentclass{article}
\usepackage{amsmath}
\title{Synthetic Paper\thanks{placeholder}}
\begin{document}
\maketitle
% a comment-only line that must not reach the body
\input{sections/intro}
\include{sections/method}
Closing line.
\end{document}
"""

INTRO = r"""\section{Introduction}
Intro sentence alpha. % trailing comment
"""

METHOD = r"""\section{Method}
Method sentence beta.
"""

RETIRED = r"""\section{Old Draft}
Retired sentence gamma.
"""


class FlattenLatexTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.tree = Path(self.temp.name) / "paper"
        (self.tree / "sections").mkdir(parents=True)
        (self.tree / "main.tex").write_text(MAIN, encoding="utf-8")
        (self.tree / "sections" / "intro.tex").write_text(INTRO, encoding="utf-8")
        (self.tree / "sections" / "method.tex").write_text(METHOD, encoding="utf-8")
        (self.tree / "sections" / "retired.tex").write_text(RETIRED, encoding="utf-8")
        self.out = Path(self.temp.name) / "review"

    def tearDown(self) -> None:
        self.temp.cleanup()

    def run_flatten(self, source: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(FLATTEN), str(source), "--output-dir", str(self.out)],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_flattens_tree_with_source_map_and_exclusions(self) -> None:
        result = self.run_flatten(self.tree)  # root detected from the directory
        self.assertEqual(result.returncode, 0, result.stderr)

        body = (self.out / "full_text.md").read_text(encoding="utf-8").splitlines()
        text = "\n".join(body)
        self.assertNotIn("\\documentclass", text)
        self.assertNotIn("\\usepackage", text)
        self.assertNotIn("comment", text)
        self.assertNotIn("Retired sentence", text)
        self.assertLess(text.index("Intro sentence alpha."), text.index("Method sentence beta."))
        self.assertLess(text.index("Method sentence beta."), text.index("Closing line."))

        report = json.loads((self.out / "latex_source_map.json").read_text(encoding="utf-8"))
        self.assertEqual(report["root"], "main.tex")
        self.assertEqual(report["title"], "Synthetic Paper")
        self.assertEqual(report["excluded_unreferenced_tex"], ["sections/retired.tex"])
        self.assertEqual(report["missing_inputs"], [])
        method_line = body.index("Method sentence beta.") + 1
        self.assertEqual(report["source_map"][str(method_line)], "sections/method.tex:2")
        closing_line = body.index("Closing line.") + 1
        self.assertEqual(report["source_map"][str(closing_line)], "main.tex:9")
        self.assertEqual(len(report["source_map"]), len(body))

        metadata = json.loads((self.out / "metadata.json").read_text(encoding="utf-8"))
        self.assertEqual(metadata["title"], "Synthetic Paper")
        self.assertEqual(metadata["excluded_tex_files"], ["sections/retired.tex"])

    def test_replaces_documentclass_title_in_existing_metadata(self) -> None:
        self.out.mkdir(parents=True)
        (self.out / "metadata.json").write_text(
            json.dumps({"title": "\\documentclass{article}", "slug": "demo"}), encoding="utf-8"
        )
        result = self.run_flatten(self.tree / "main.tex")
        self.assertEqual(result.returncode, 0, result.stderr)
        metadata = json.loads((self.out / "metadata.json").read_text(encoding="utf-8"))
        self.assertEqual(metadata["title"], "Synthetic Paper")
        self.assertEqual(metadata["slug"], "demo")


if __name__ == "__main__":
    unittest.main()
