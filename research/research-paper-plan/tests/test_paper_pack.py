#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INIT = ROOT / "scripts" / "init_paper_pack.py"
VALIDATE = ROOT / "scripts" / "validate_paper_pack.py"


class PaperPackTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.plan = self.root / "paper-plan.md"
        self.matrix = self.root / "claims-evidence-matrix.md"
        self.bindings = self.root / "claim-evidence-bindings.json"
        self.figure = self.root / "figure-plan.md"
        self.citation = self.root / "citation-plan.md"
        self.claim = {
            "paper_claim_id": "PC1",
            "claim": "The method improves accuracy on the frozen held-out task.",
            "claim_type": "primary",
            "evidence_mode": "empirical",
            "support_status": "supported",
            "manuscript_action": "assert",
            "required_assurance_class": "confirmatory",
            "source_claim_ids": ["C1"],
            "audit_ids": ["A1"],
            "audit_exclusions": [],
            "evidence_artifacts": ["results/B1.json"],
            "nonempirical_evidence_artifacts": [],
            "planned_sections": ["Results"],
            "exhibit_ids": ["F1"],
            "citation_need_ids": ["N1"],
            "limitations": [],
            "missing_evidence": [],
            "scope": "Frozen held-out task only.",
            "rationale": "A confirmatory linked audit supports the bounded empirical claim.",
        }
        self.binding_data = {
            "schema_version": "1.0",
            "paper_id": "P1",
            "identity_version": 1,
            "status": "complete",
            "claims": [self.claim],
        }
        self.write_all()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def write_all(self) -> None:
        self.plan.write_text(
            "# Paper Plan\n## Header\n- Paper ID: P1\n## Structure\n1. Results\n"
            "## Section Notes\n- Results carry PC1.\n## Evidence Boundary\nJSON is canonical.\n",
            encoding="utf-8",
        )
        c = self.claim
        exclusions = ", ".join(item["audit_id"] for item in c.get("audit_exclusions", []))
        self.matrix.write_text(
            "# Claims-Evidence Matrix\n"
            "| Paper claim ID | Claim | Type | Evidence mode | Support status | Manuscript action | Required assurance | Source claim IDs | Audit IDs | Excluded audit IDs | Planned sections | Exhibit IDs | Citation need IDs | Limitation |\n"
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n"
            f"| {c['paper_claim_id']} | {c['claim']} | {c['claim_type']} | {c['evidence_mode']} | "
            f"{c['support_status']} | {c['manuscript_action']} | {c['required_assurance_class']} | "
            f"{', '.join(c['source_claim_ids'])} | {', '.join(c['audit_ids'])} | {exclusions} | "
            f"{', '.join(c['planned_sections'])} | {', '.join(c['exhibit_ids'])} | "
            f"{', '.join(c['citation_need_ids'])} | {'; '.join(c['limitations'])} |\n",
            encoding="utf-8",
        )
        figure_rows = "| F1 | Main comparison | PC1 | mandatory | planned | Frozen test |\n" if "F1" in c["exhibit_ids"] else ""
        self.figure.write_text(
            "# Figure Plan\n"
            "| Exhibit ID | Purpose | Paper claim IDs | Priority | Status | Notes |\n"
            "| --- | --- | --- | --- | --- | --- |\n"
            + figure_rows,
            encoding="utf-8",
        )
        citation_rows = (
            "| N1 | PC1 | Benchmark context | verify | Do not use as empirical support |\n"
            if "N1" in c["citation_need_ids"]
            else ""
        )
        self.citation.write_text(
            "# Citation Plan\n"
            "| Citation need ID | Paper claim IDs | Citation need | Source status | Notes |\n"
            "| --- | --- | --- | --- | --- |\n"
            + citation_rows,
            encoding="utf-8",
        )
        self.bindings.write_text(json.dumps(self.binding_data), encoding="utf-8")

    def validate(self, expect: int = 0) -> subprocess.CompletedProcess[str]:
        cp = subprocess.run(
            [
                sys.executable,
                str(VALIDATE),
                "--plan",
                str(self.plan),
                "--matrix",
                str(self.matrix),
                "--bindings",
                str(self.bindings),
                "--figure-plan",
                str(self.figure),
                "--citation-plan",
                str(self.citation),
            ],
            text=True,
            capture_output=True,
        )
        self.assertEqual(cp.returncode, expect, msg=f"stdout:\n{cp.stdout}\nstderr:\n{cp.stderr}")
        return cp

    def test_initializer_passes_structural_profile(self) -> None:
        fresh = self.root / "fresh"
        cp = subprocess.run([sys.executable, str(INIT), str(fresh)], text=True, capture_output=True)
        self.assertEqual(cp.returncode, 0, cp.stderr)
        cp = subprocess.run(
            [
                sys.executable,
                str(VALIDATE),
                "--plan",
                str(fresh / "paper-plan.md"),
                "--matrix",
                str(fresh / "claims-evidence-matrix.md"),
                "--bindings",
                str(fresh / "claim-evidence-bindings.json"),
                "--figure-plan",
                str(fresh / "figure-plan.md"),
                "--citation-plan",
                str(fresh / "citation-plan.md"),
            ],
            text=True,
            capture_output=True,
        )
        self.assertEqual(cp.returncode, 0, cp.stdout + cp.stderr)

    def test_valid_structural_pack_passes(self) -> None:
        self.validate()

    def test_partial_claim_requires_qualification_and_gaps(self) -> None:
        self.claim["support_status"] = "partial"
        self.claim["manuscript_action"] = "assert"
        self.write_all()
        cp = self.validate(expect=1)
        self.assertIn("partial claim must be qualified", cp.stdout)
        self.assertIn("requires limitations and missing_evidence", cp.stdout)

    def test_blocked_claim_cannot_be_asserted(self) -> None:
        self.claim["support_status"] = "blocked"
        self.claim["manuscript_action"] = "assert"
        self.claim["audit_ids"] = []
        self.claim["missing_evidence"] = ["Run confirmatory evaluation"]
        self.write_all()
        cp = self.validate(expect=1)
        self.assertIn("blocked claim cannot be asserted", cp.stdout)

    def test_matrix_status_divergence_rejected(self) -> None:
        self.write_all()
        self.matrix.write_text(
            self.matrix.read_text(encoding="utf-8").replace("| supported | assert |", "| partial | assert |"),
            encoding="utf-8",
        )
        cp = self.validate(expect=1)
        self.assertIn("Support status disagrees", cp.stdout)

    def test_excluded_audit_ids_are_reciprocal(self) -> None:
        self.claim["audit_exclusions"] = [
            {
                "audit_id": "A2",
                "scope_difference": "External deployment cohort versus frozen held-out task.",
                "rationale": "The paper claim is intentionally narrower.",
            }
        ]
        self.write_all()
        text = self.matrix.read_text(encoding="utf-8").replace("| A1 | A2 |", "| A1 | A3 |")
        self.matrix.write_text(text, encoding="utf-8")
        cp = self.validate(expect=1)
        self.assertIn("Excluded audit IDs disagrees with JSON", cp.stdout)

    def test_limitation_text_is_exactly_reciprocal(self) -> None:
        self.claim["limitations"] = ["Frozen held-out task only.", "Single benchmark family."]
        self.write_all()
        self.matrix.write_text(
            self.matrix.read_text(encoding="utf-8").replace("Frozen held-out task only.; Single benchmark family.", "Frozen held-out task only."),
            encoding="utf-8",
        )
        cp = self.validate(expect=1)
        self.assertIn("field Limitation disagrees with JSON", cp.stdout)

    def test_markdown_cannot_invent_figure_or_citation_links(self) -> None:
        self.claim["exhibit_ids"] = []
        self.claim["citation_need_ids"] = []
        self.write_all()
        self.figure.write_text(self.figure.read_text(encoding="utf-8") + "| F1 | Main comparison | PC1 | mandatory | planned | Frozen test |\n", encoding="utf-8")
        self.citation.write_text(self.citation.read_text(encoding="utf-8") + "| N1 | PC1 | Benchmark context | verify | Context only |\n", encoding="utf-8")
        cp = self.validate(expect=1)
        self.assertIn("canonical JSON does not list that exhibit", cp.stdout)
        self.assertIn("canonical JSON does not list that citation need", cp.stdout)

    def test_unknown_exhibit_and_citation_ids_rejected(self) -> None:
        self.claim["exhibit_ids"] = ["F9"]
        self.claim["citation_need_ids"] = ["N9"]
        self.write_all()
        cp = self.validate(expect=1)
        self.assertIn("unknown exhibit ID F9", cp.stdout)
        self.assertIn("unknown citation need ID N9", cp.stdout)

    def test_mixed_claim_requires_nonempirical_component(self) -> None:
        self.claim["evidence_mode"] = "mixed"
        self.claim["citation_need_ids"] = []
        self.claim["nonempirical_evidence_artifacts"] = []
        self.write_all()
        cp = self.validate(expect=1)
        self.assertIn("mixed claim requires a nonempirical evidence component", cp.stdout)

    def test_theoretical_claim_can_use_artifact_without_audit(self) -> None:
        self.claim.update(
            evidence_mode="theoretical",
            required_assurance_class="none",
            source_claim_ids=[],
            audit_ids=[],
            evidence_artifacts=["proofs/theorem-1.md"],
            citation_need_ids=[],
        )
        self.write_all()
        self.validate()


if __name__ == "__main__":
    unittest.main()
