#!/usr/bin/env python3
"""Regression tests for the four-file paper-context evidence-map helper."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "paper_context_artifacts.py"
PACK_VALIDATOR = Path(__file__).resolve().parents[1] / "scripts" / "validate_review_pack.py"
FILES = (
    "literature-context.md",
    "literature-context-search-log.md",
    "literature-context-evidence-table.md",
)


class PaperContextTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.out = Path(self.temp.name) / "context"
        cp = self.run_cmd("init", "--out-dir", str(self.out), "--target-paper", "Synthetic Paper", "--domain", "Synthetic domain")
        self.assertEqual(cp.returncode, 0, cp.stdout + cp.stderr)
        self.decision_path = self.out / "literature-context-decision.json"

    def tearDown(self) -> None:
        self.temp.cleanup()

    def run_cmd(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable, str(SCRIPT), *args], text=True, capture_output=True)

    def validate(self, *extra: str) -> subprocess.CompletedProcess[str]:
        return self.run_cmd("validate", "--out-dir", str(self.out), *extra)

    def decision(self) -> dict:
        return json.loads(self.decision_path.read_text())

    def fill(self) -> None:
        for name in FILES:
            path = self.out / name
            path.write_text(path.read_text().replace("TODO", "synthetic entry"))
        decision = self.decision()
        decision.update(
            contextualization_rating=2,
            impact_evidence_rating=3,
            coverage_confidence_rating=2,
            closest_prior_work=["P1 synthetic"],
            limits_of_search=["Single synthetic source"],
        )
        self.decision_path.write_text(json.dumps(decision))

    def test_scaffold_ratings_start_null(self) -> None:
        decision = self.decision()
        for field in ("contextualization_rating", "impact_evidence_rating", "coverage_confidence_rating"):
            self.assertIsNone(decision[field])
        self.assertNotIn("| TODO | TODO | 3 |", (self.out / "literature-context.md").read_text())

    def test_untouched_scaffold_fails_validation(self) -> None:
        cp = self.validate()
        self.assertEqual(cp.returncode, 1, cp.stdout + cp.stderr)
        self.assertIn("literature-context.md still has", cp.stdout)
        self.assertIn("TODO placeholder", cp.stdout)
        self.assertIn("contextualization_rating is unset (null)", cp.stdout)

    def test_draft_flag_allows_todos_and_null_ratings(self) -> None:
        cp = self.validate("--draft")
        self.assertEqual(cp.returncode, 0, cp.stdout + cp.stderr)

    def test_filled_bundle_passes(self) -> None:
        self.fill()
        cp = self.validate()
        self.assertEqual(cp.returncode, 0, cp.stdout + cp.stderr)

    def test_single_remaining_todo_fails(self) -> None:
        self.fill()
        evidence = self.out / "literature-context-evidence-table.md"
        evidence.write_text(evidence.read_text() + "| P2 | TODO | | | | | | | |\n")
        cp = self.validate()
        self.assertEqual(cp.returncode, 1, cp.stdout + cp.stderr)
        self.assertIn("literature-context-evidence-table.md still has 1 TODO", cp.stdout)

    def test_search_runs_hold_one_query_with_honest_counts(self) -> None:
        self.fill()
        log = self.out / "literature-context-search-log.md"
        filled = log.read_text()
        self.assertEqual(self.validate().returncode, 0)
        log.write_text(filled.replace(
            "| synthetic entry | synthetic entry | synthetic entry | synthetic entry | evaluate target paper claim |",
            "| synthetic entry | synthetic entry | query one; query two | synthetic entry | evaluate target paper claim |",
        ))
        cp = self.validate()
        self.assertEqual(cp.returncode, 1, cp.stdout)
        self.assertIn("one query per row", cp.stdout)
        log.write_text(filled.replace("| evaluate target paper claim | 0 |", "| evaluate target paper claim | many |"))
        cp = self.validate()
        self.assertEqual(cp.returncode, 1, cp.stdout)
        self.assertIn("results_inspected must be the number", cp.stdout)

    def test_legacy_search_runs_validate_with_a_warning(self) -> None:
        self.fill()
        log = self.out / "literature-context-search-log.md"
        text = log.read_text()
        start = text.index("## Search Runs")
        end = text.index("## Inclusion Decisions")
        legacy = (
            "## Search Runs\n\n| run_id | date | source | query_string | filters | purpose | records_returned | retained | notes |\n"
            "| --- | --- | --- | --- | --- | --- | ---: | ---: | --- |\n"
            "| run-001 | 2024-01-01 | synthetic index | synthetic query | none | evaluate | 40 | 2 | |\n\n"
        )
        log.write_text(text[:start] + legacy + text[end:])
        cp = self.validate()
        self.assertEqual(cp.returncode, 0, cp.stdout)
        self.assertIn("warning: literature-context-search-log.md Search Runs uses the older columns", cp.stdout)

    def test_list_fields_and_mode_are_type_checked(self) -> None:
        self.fill()
        decision = self.decision()
        decision["limits_of_search"] = "one synthetic sentence"
        decision["closest_prior_work"] = {"P1": "synthetic"}
        del decision["mode"]
        self.decision_path.write_text(json.dumps(decision))
        cp = self.validate()
        self.assertEqual(cp.returncode, 1, cp.stdout + cp.stderr)
        self.assertIn("limits_of_search must be a list", cp.stdout)
        self.assertIn("closest_prior_work must be a list", cp.stdout)
        self.assertIn("mode must equal paper_context_evidence_map", cp.stdout)


    def promote(self, *extra: str) -> tuple[subprocess.CompletedProcess[str], Path]:
        pack = Path(self.temp.name) / "pack"
        return self.run_cmd("promote", "--out-dir", str(self.out), "--pack-dir", str(pack), *extra), pack

    def validate_pack(self, pack: Path) -> subprocess.CompletedProcess[str]:
        stem = pack / "synthetic-paper"
        return subprocess.run(
            [
                sys.executable, str(PACK_VALIDATOR),
                "--protocol", f"{stem}.protocol.md", "--search-log", f"{stem}.search-log.md",
                "--recall-audit", f"{stem}.recall-audit.md", "--corpus-manifest", f"{stem}.corpus-manifest.json",
                "--screening-log", f"{stem}.screening-log.md", "--evidence", f"{stem}.evidence-table.md",
                "--report", f"{stem}.review.md",
            ],
            text=True, capture_output=True,
        )

    def test_promote_carries_rows_verbatim_and_fails_pack_validation(self) -> None:
        evidence = self.out / "literature-context-evidence-table.md"
        evidence.write_text(evidence.read_text().replace(
            "| P1 | TODO | TODO | published / preprint / submission | TODO | closest prior work / benchmark norm / impact evidence | TODO | TODO | TODO |",
            "| P1 | Roe et al. 2023 | https://example.org/roe | published | Synthetic Venue 2023 | closest prior work | a learned score | small benchmark | overlaps scoring |",
        ))
        cp, pack = self.promote()
        self.assertEqual(cp.returncode, 0, cp.stdout + cp.stderr)
        self.assertIn("carried evidence rows: 1", cp.stdout)
        stem = pack / "synthetic-paper"
        evidence_md = Path(f"{stem}.evidence-table.md").read_text()
        self.assertIn("| P1 | Roe et al. 2023 | https://example.org/roe |", evidence_md)
        self.assertIn("Promoted on", evidence_md)
        manifest = json.loads(Path(f"{stem}.corpus-manifest.json").read_text())
        self.assertEqual(manifest["promoted_from"]["paper_context_dir"], str(self.out.resolve()))
        self.assertEqual(manifest["assurance_verdict"], "insufficient")
        validation = self.validate_pack(pack)
        self.assertEqual(validation.returncode, 1, validation.stdout + validation.stderr)
        self.assertIn("evidence row 1.work_type is still a TODO placeholder", validation.stdout)

    def test_promote_skips_placeholder_rows(self) -> None:
        cp, pack = self.promote()
        self.assertEqual(cp.returncode, 0, cp.stdout + cp.stderr)
        self.assertIn("carried evidence rows: 0", cp.stdout)
        self.assertIn("carried search runs: 0", cp.stdout)
        self.assertNotIn("Carried over", Path(f"{pack / 'synthetic-paper'}.search-log.md").read_text())

    def test_promote_requires_a_topic(self) -> None:
        decision = self.decision()
        decision["target_paper"] = None
        self.decision_path.write_text(json.dumps(decision))
        cp, _ = self.promote()
        self.assertEqual(cp.returncode, 2, cp.stdout + cp.stderr)
        self.assertIn("pass --topic", cp.stderr)

if __name__ == "__main__":
    unittest.main()
