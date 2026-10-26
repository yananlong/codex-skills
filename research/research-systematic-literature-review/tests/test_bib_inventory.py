#!/usr/bin/env python3
"""Regression tests for the manuscript citation inventory (bib_inventory.py)."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
SCRIPT = SKILL / "scripts" / "bib_inventory.py"
FIXTURE = SKILL / "tests" / "fixtures" / "bib-inventory"
MANIFEST_RECORD_FIELDS = {"record_id", "canonical_citation", "publication_url", "publication_status", "question_ids"}


class BibInventoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.out = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def run_inventory(self, *extra: str) -> tuple[subprocess.CompletedProcess[str], dict, str]:
        md = self.out / "citation-audit.md"
        js = self.out / "bib-inventory.json"
        cp = subprocess.run(
            [sys.executable, str(SCRIPT), "--tex", str(FIXTURE / "main.tex"), "--out-md", str(md), "--out-json", str(js), *extra],
            text=True,
            capture_output=True,
        )
        data = json.loads(js.read_text()) if js.exists() else {}
        text = md.read_text() if md.exists() else ""
        return cp, data, text

    def test_follows_includes_and_cite_variants(self) -> None:
        cp, data, _ = self.run_inventory()
        self.assertEqual(cp.returncode, 0, cp.stdout + cp.stderr)
        self.assertEqual(data["tex_files"], ["main.tex", "sections/intro.tex", "sections/methods.tex", "appendix/proofs.tex"])
        self.assertEqual(
            set(data["cited_keys"]),
            {
                "alpha2020", "beta:2021-x", "gamma_et.al/2019", "Delta2018", "epsilon2022", "zeta2017",
                "missing2023", "eta2016", "theta2015", "iota2014", "Alpha2020", "kappa2013", "lambda2012",
            },
        )
        self.assertNotIn("commented:out", data["cited_keys"])
        self.assertEqual(data["bib_files"], ["refs-a.bib", "refs-b.bib"])

    def test_reports_missing_unused_duplicate_and_unresolved_includes(self) -> None:
        _, data, text = self.run_inventory()
        self.assertEqual(data["missing_keys"], ["missing2023", "Alpha2020"])
        self.assertEqual(data["unused_keys"], ["unused2010"])
        self.assertNotIn("commented-entry", data["unused_keys"])
        self.assertEqual(data["duplicate_keys"], {"alpha2020": ["refs-a.bib", "refs-b.bib"]})
        self.assertTrue(any("sections/missing-section" in warning for warning in data["warnings"]))
        self.assertFalse(any("figure-not-a-tex-file" in warning for warning in data["warnings"]))
        self.assertIn("| missing2023 | missing-entry |", text)
        self.assertIn("| unused2010 | unused |", text)
        self.assertIn("case differs from entry alpha2020", text)

    def test_records_are_corpus_manifest_shaped(self) -> None:
        _, data, text = self.run_inventory()
        records = {record["record_id"]: record for record in data["records"]}
        self.assertEqual(len(records), 11)
        for record in records.values():
            self.assertTrue(MANIFEST_RECORD_FIELDS <= set(record), record)
            self.assertEqual(record["question_ids"], [])
            self.assertEqual(record["disposition"], "resolved")
        self.assertEqual(records["alpha2020"]["publication_url"], "https://doi.org/10.0000/synthetic.alpha")
        self.assertEqual(records["alpha2020"]["publication_status"], "published")
        self.assertEqual(records["epsilon2022"]["publication_url"], "https://doi.org/10.0000/eps")
        self.assertEqual(records["gamma_et.al/2019"]["publication_url"], "https://arxiv.org/abs/1901.00001")
        self.assertEqual(records["gamma_et.al/2019"]["publication_status"], "preprint")
        self.assertEqual(records["beta:2021-x"]["publication_url"], "https://example.org/beta")
        self.assertIn("A Synthetic Study of Things", records["alpha2020"]["canonical_citation"])
        self.assertIn("| alpha2020 | resolved | Author | 2020 | A Synthetic Study of Things | doi:10.0000/synthetic.alpha |", text)

    def test_fail_on_missing_and_explicit_bib(self) -> None:
        cp, _, _ = self.run_inventory("--fail-on-missing")
        self.assertEqual(cp.returncode, 1, cp.stdout + cp.stderr)
        self.assertIn("missing entry: missing2023", cp.stdout)
        cp, data, _ = self.run_inventory("--bib", str(FIXTURE / "refs-b.bib"))
        self.assertEqual(cp.returncode, 0, cp.stdout + cp.stderr)
        self.assertIn("beta:2021-x", data["missing_keys"])
        self.assertNotIn("unused2010", data["unused_keys"])


if __name__ == "__main__":
    unittest.main()
