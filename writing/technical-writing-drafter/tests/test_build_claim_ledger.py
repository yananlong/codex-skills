"""Tests for the claim ledger builder."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from build_claim_ledger import SourceError, build, from_evidence_table, from_issue_board, parse_pipe_table  # noqa: E402

BINDINGS = {
    "schema_version": "1.0",
    "claims": [
        {"paper_claim_id": "PC-1", "claim": "The scorer lowers error on family A.", "evidence_mode": "empirical",
         "support_status": "supported", "manuscript_action": "assert", "planned_sections": ["results"],
         "evidence_artifacts": ["results/a.csv"], "limitations": [], "missing_evidence": []},
        {"paper_claim_id": "PC-2", "claim": "The effect holds on family C.", "evidence_mode": "empirical",
         "support_status": "partial", "manuscript_action": "qualify", "planned_sections": ["results", "limitations"],
         "evidence_artifacts": ["results/c.csv"], "limitations": ["one seed"], "missing_evidence": ["more seeds"]},
        {"paper_claim_id": "PC-3", "claim": "The scorer is optimal.", "evidence_mode": "theoretical",
         "support_status": "blocked", "manuscript_action": "limitation", "missing_evidence": ["a proof"]},
        {"paper_claim_id": "PC-4", "claim": "Dropped.", "evidence_mode": "empirical", "support_status": "withdrawn",
         "manuscript_action": "omit"},
    ],
}

AUDIT = {
    "schema_version": "1.0",
    "status": "complete",
    "audits": [
        {"audit_id": "AUD-1", "claim_id": "C1", "claim_text": "Error falls on family A.", "scope": "family A, seeds 1-3",
         "verdict": "supported", "audited_claim_effect": "strengthen",
         "evidence_artifacts": [{"path": "results/a.csv", "kind": "table"}], "limitations": []},
        {"audit_id": "AUD-2", "claim_id": "C2", "claim_text": "Error falls on family C.", "scope": "family C",
         "verdict": "inconclusive", "audited_claim_effect": "inconclusive", "evidence_artifacts": [], "limitations": ["one seed"]},
    ],
}

EVIDENCE_TABLE = """# Evidence table

| study_id | canonical_citation | fetch_status | rung | key_result | quote |
| --- | --- | --- | --- | --- | --- |
| S1 | Doe 2021 | read | 1 | Calibration drops error by a third. | "error fell by 33%" |
| S2 | Roe 2020 | read | 3 | Practitioners prefer temperature scaling. | "we prefer it" |
| S3 | Poe 2019 | abstract-only | 1 | Something. | |
| S4 | Moe 2018 | read | 2 | No quote here. | |
"""

ISSUE_BOARD = """# Issue board

issue_id | reviewer | internal_issue_ids | severity | category | strategy | status | shared_with

| issue_id | reviewer | internal_issue_ids | severity | category | strategy | status | shared_with | summary |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| EXT-R2-1 | R2 | | major | claims | concede and narrow | decided | all | contribution overclaimed |
| EXT-R2-2 | R2 | | minor | clarity | clarify | open | all | notation unclear |
| EXT-R3-1 | R3 | | major | experiments | | undecided | all | missing baseline |
"""


class LedgerRuleTests(unittest.TestCase):
    def test_bindings_statuses(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "claim-evidence-bindings.json"
            path.write_text(json.dumps(BINDINGS))
            ledger = build({"bindings": [path]})
            by_id = {item["id"]: item for item in ledger}
            self.assertEqual(by_id["PC-1"]["status"], "ready")
            self.assertEqual(by_id["PC-2"]["status"], "careful")
            self.assertEqual(by_id["PC-2"]["limitations"], ["one seed"])
            self.assertEqual(by_id["PC-3"]["status"], "blocked")
            self.assertEqual(by_id["PC-3"]["support"], "missing")
            self.assertEqual(by_id["PC-4"]["status"], "excluded")
            self.assertEqual([item["id"] for item in ledger], ["PC-1", "PC-2", "PC-3", "PC-4"])

    def test_audit_effects(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "results-audit.json"
            path.write_text(json.dumps(AUDIT))
            ledger = build({"results_audit": [path]})
            by_id = {item["id"]: item for item in ledger}
            self.assertEqual(by_id["C1"]["status"], "ready")
            self.assertEqual(by_id["C1"]["evidence"], ["results/a.csv"])
            self.assertIn("scope: family A, seeds 1-3", by_id["C1"]["notes"])
            self.assertEqual(by_id["C2"]["status"], "blocked")

    def test_evidence_table_rules(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "topic.evidence-table.md"
            path.write_text(EVIDENCE_TABLE)
            ledger = from_evidence_table(path)
            by_id = {item["id"]: item for item in ledger}
            self.assertEqual(by_id["LIT-S1"]["status"], "ready")
            self.assertEqual(by_id["LIT-S2"]["status"], "careful")
            self.assertEqual(by_id["LIT-S3"]["status"], "blocked")
            self.assertEqual(by_id["LIT-S4"]["status"], "blocked")
            self.assertIn("no verbatim quote", by_id["LIT-S4"]["missing_evidence"][0])

    def test_issue_board_rules(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "issue-board.md"
            path.write_text(ISSUE_BOARD)
            ledger = from_issue_board(path)
            by_id = {item["id"]: item for item in ledger}
            self.assertEqual(by_id["RESP-EXT-R2-1"]["status"], "ready")
            self.assertEqual(by_id["RESP-EXT-R2-2"]["status"], "careful")
            self.assertEqual(by_id["RESP-EXT-R3-1"]["status"], "blocked")
            self.assertEqual(by_id["RESP-EXT-R2-1"]["text"], "contribution overclaimed")

    def test_issue_board_from_init_rebuttal_pack_header_is_read(self) -> None:
        board = (
            "# Issue board\n\n"
            "| Issue ID | Reviewer | Internal issue IDs | Severity | Category | Strategy | Stance | Status | Shared with | Evidence source | Notes |\n"
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n"
            "| EXT-xK3p-1 | xK3p | F3 | major | claims | concede and narrow | agree | decided | all | audit | overclaim |\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "issue-board.md"
            path.write_text(board)
            ledger = from_issue_board(path)
            self.assertEqual(ledger[0]["id"], "RESP-EXT-xK3p-1")
            self.assertEqual(ledger[0]["status"], "ready")
            self.assertIn("strategy: concede and narrow", ledger[0]["notes"])

    def test_pipe_table_ignores_non_table_lines(self) -> None:
        rows = parse_pipe_table(ISSUE_BOARD)
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0]["issue_id"], "EXT-R2-1")

    def test_malformed_source_is_skipped_visibly(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "claim-evidence-bindings.json"
            bad.write_text("{\"claims\": \"nope\"}")
            good = Path(tmp) / "results-audit.json"
            good.write_text(json.dumps(AUDIT))
            skipped: list[str] = []
            ledger = build({"bindings": [bad], "results_audit": [good]}, skipped)
            self.assertEqual(len(ledger), 2)
            self.assertEqual(len(skipped), 1)
            self.assertIn("expected a list", skipped[0])
            with self.assertRaises(SourceError):
                from_evidence_table(Path(tmp) / "missing.md")

    def test_free_form_evidence_table_rows_are_careful(self) -> None:
        table = (
            "# Evidence\n\n"
            "| Work | Status | Target and method | Strongest overlap | Remaining gap | Publication URL |\n"
            "| --- | --- | --- | --- | --- | --- |\n"
            "| Doe et al. (2021), *A Title* | ACL 2021 | Perturbs scoring choices. | Overlaps on ranking. | No audit. | https://example.org/a |\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "topic.evidence-table.md"
            path.write_text(table)
            ledger = from_evidence_table(path)
            self.assertEqual(len(ledger), 1)
            self.assertEqual(ledger[0]["status"], "careful")
            self.assertEqual(ledger[0]["id"], "LIT-Doe et al. 2021, A Title")
            self.assertEqual(ledger[0]["text"], "Perturbs scoring choices.")
            self.assertIn("predates the fetch_status/quote columns", ledger[0]["missing_evidence"][0])

    def test_bindings_take_precedence_over_audits_with_the_same_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bindings = Path(tmp) / "claim-evidence-bindings.json"
            audit = Path(tmp) / "results-audit.json"
            shared = dict(BINDINGS)
            shared["claims"] = [dict(BINDINGS["claims"][0], paper_claim_id="C1")]
            bindings.write_text(json.dumps(shared))
            audit.write_text(json.dumps(AUDIT))
            ledger = build({"bindings": [bindings], "results_audit": [audit]})
            audit_entry = next(item for item in ledger if item["source"]["kind"] == "results_audit" and item["id"] == "C1")
            self.assertIn("assert through the binding", audit_entry["notes"])


class CliTests(unittest.TestCase):
    def test_cli_from_intake(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "claim-evidence-bindings.json").write_text(json.dumps(BINDINGS))
            (root / "topic.evidence-table.md").write_text(EVIDENCE_TABLE)
            intake = {
                "root": str(root),
                "artifacts": [
                    {"path": "claim-evidence-bindings.json", "kind": "paper_plan.bindings"},
                    {"path": "topic.evidence-table.md", "kind": "literature.evidence_table"},
                ],
            }
            (root / "writing-intake.json").write_text(json.dumps(intake))
            out_json = root / "claim-ledger.json"
            out_md = root / "claim-ledger.md"
            result = subprocess.run(
                [sys.executable, str(SCRIPTS / "build_claim_ledger.py"), "--intake", str(root / "writing-intake.json"),
                 "--out-json", str(out_json), "--out-md", str(out_md)],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("ledger: ready 2, careful 2, blocked 3, excluded 1", result.stdout)
            self.assertEqual(len(json.loads(out_json.read_text())["claims"]), 8)
            self.assertIn("| ready | PC-1 |", out_md.read_text())

    def test_cli_with_no_claims_exits_one(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "claim-evidence-bindings.json"
            path.write_text(json.dumps({"claims": []}))
            result = subprocess.run(
                [sys.executable, str(SCRIPTS / "build_claim_ledger.py"), "--bindings", str(path)],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("no source yielded a claim", result.stderr)


if __name__ == "__main__":
    unittest.main()
