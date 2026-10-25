"""Tests for the citation key checker."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from check_draft_citations import draft_keys, keys_from_bib, keys_from_inventory  # noqa: E402


class KeyTests(unittest.TestCase):
    def test_latex_and_markdown_keys(self) -> None:
        text = (
            "As shown \\citep[see][p. 3]{doe2021, roe2020} and \\textcite{poe2019}. % \\cite{commented}\n"
            "Markdown cites [@smith2018; @jones2017] and @lee2016. Not an email a@b.c. [CITATION NEEDED: baseline]\n"
        )
        keys = [k for _, k in draft_keys(text)]
        self.assertEqual(keys, ["doe2021", "roe2020", "poe2019", "smith2018", "jones2017", "lee2016"])

    def test_bib_and_inventory_sources(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bib = Path(tmp) / "refs.bib"
            bib.write_text("@article{doe2021,\n title={X}}\n@comment{ignored}\n@Book{ roe2020 , title={Y}}\n")
            self.assertEqual(keys_from_bib(bib), {"doe2021", "roe2020"})
            inv = Path(tmp) / "bib-inventory.json"
            inv.write_text(json.dumps({"entries": [{"key": "poe2019", "status": "resolved"}, {"key": "gone2000", "status": "missing-entry"}]}))
            self.assertEqual(keys_from_inventory(inv), {"poe2019"})

    def test_cli_exit_codes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "refs.bib").write_text("@article{doe2021, title={X}}\n")
            draft = root / "d.tex"
            draft.write_text("See \\cite{doe2021} and \\cite{nope2022}.\n")
            cmd = [sys.executable, str(SCRIPTS / "check_draft_citations.py"), str(draft), "--bib", str(root / "refs.bib")]
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 1)
            self.assertIn("unresolved line 1: nope2022", result.stdout)
            (root / "extra.txt").write_text("nope2022\n")
            result = subprocess.run(cmd + ["--keys", str(root / "extra.txt")], capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0, result.stdout)


if __name__ == "__main__":
    unittest.main()
