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
        self.commitment = self.root / "research-commitment.json"
        self.claim_map = self.root / "claim-map.json"
        self.results_audit = self.root / "results-audit.json"
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
            "evidence_artifacts": ["results/B1.json"],
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
        self.commitment_data = {"paper_id": "P1", "identity_version": 1}
        self.claim_map_data = [{"claim_id": "C1", "claim": "Method improves accuracy"}]
        self.audit_data = {
            "schema_version": "1.0",
            "paper_id": "P1",
            "identity_version": 1,
            "status": "complete",
            "audits": [
                {
                    "audit_id": "A1",
                    "claim_id": "C1",
                    "verdict": "supports_confirmatory_claim",
                    "attained_assurance_class": "confirmatory",
                    "audited_claim_effect": "strengthen",
                    "evidence_artifacts": [
                        {"path": "results/B1.json", "kind": "metrics", "source": "experiment", "digest": "b" * 64}
                    ],
                }
            ],
        }
        self.write_all()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def write_all(self) -> None:
        self.plan.write_text(
            """# Paper Plan
## Header
- Paper ID: P1
- Identity version: 1
- Plan status: complete
## Structure
1. Results
## Section Notes
- Results carry PC1.
## Evidence Boundary
JSON is canonical.
""",
            encoding="utf-8",
        )
        c = self.claim
        self.matrix.write_text(
            """# Claims-Evidence Matrix
| Paper claim ID | Claim | Type | Evidence mode | Support status | Manuscript action | Required assurance | Source claim IDs | Audit IDs | Planned sections | Exhibit IDs | Citation need IDs | Limitation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
"""
            + f"| {c['paper_claim_id']} | {c['claim']} | {c['claim_type']} | {c['evidence_mode']} | {c['support_status']} | {c['manuscript_action']} | {c['required_assurance_class']} | {', '.join(c['source_claim_ids'])} | {', '.join(c['audit_ids'])} | {', '.join(c['planned_sections'])} | {', '.join(c['exhibit_ids'])} | {', '.join(c['citation_need_ids'])} | {'; '.join(c['limitations'])} |\n",
            encoding="utf-8",
        )
        self.figure.write_text(
            """# Figure Plan
| Exhibit ID | Purpose | Paper claim IDs | Priority | Status | Notes |
| --- | --- | --- | --- | --- | --- |
| F1 | Main comparison | PC1 | mandatory | planned | Frozen test |
""",
            encoding="utf-8",
        )
        self.citation.write_text(
            """# Citation Plan
| Citation need ID | Paper claim IDs | Citation need | Source status | Notes |
| --- | --- | --- | --- | --- |
| N1 | PC1 | Benchmark context | verify | Do not use as empirical support |
""",
            encoding="utf-8",
        )
        self.bindings.write_text(json.dumps(self.binding_data), encoding="utf-8")
        self.commitment.write_text(json.dumps(self.commitment_data), encoding="utf-8")
        self.claim_map.write_text(json.dumps(self.claim_map_data), encoding="utf-8")
        self.results_audit.write_text(json.dumps(self.audit_data), encoding="utf-8")

    def validate(self, profile: str = "linked", expect: int = 0) -> subprocess.CompletedProcess[str]:
        cmd = [
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
            "--assurance-profile",
            profile,
        ]
        if profile == "linked":
            cmd += [
                "--commitment",
                str(self.commitment),
                "--claim-map",
                str(self.claim_map),
                "--results-audit",
                str(self.results_audit),
            ]
        cp = subprocess.run(cmd, text=True, capture_output=True)
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

    def test_valid_linked_empirical_claim_passes(self) -> None:
        cp = self.validate()
        self.assertIn("assurance thresholds", cp.stdout)

    def test_supported_claim_requires_adequate_positive_audit(self) -> None:
        self.audit_data["audits"][0]["attained_assurance_class"] = "exploratory"
        self.audit_data["audits"][0]["verdict"] = "supports_exploratory_follow_up"
        self.write_all()
        cp = self.validate(expect=1)
        self.assertIn("required assurance class confirmatory", cp.stdout)

    def test_negative_audit_blocks_assertion(self) -> None:
        audit = self.audit_data["audits"][0]
        audit["verdict"] = "does_not_support_claim"
        audit["audited_claim_effect"] = "kill"
        self.write_all()
        cp = self.validate(expect=1)
        self.assertIn("cannot be asserted", cp.stdout)

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

    def test_audit_must_target_a_source_claim(self) -> None:
        self.claim["source_claim_ids"] = ["C2"]
        self.claim_map_data.append({"claim_id": "C2", "claim": "Other claim"})
        self.write_all()
        cp = self.validate(expect=1)
        self.assertIn("outside source_claim_ids", cp.stdout)

    def test_matrix_status_divergence_rejected(self) -> None:
        self.write_all()
        text = self.matrix.read_text(encoding="utf-8").replace("| supported | assert |", "| partial | assert |")
        self.matrix.write_text(text, encoding="utf-8")
        cp = self.validate(expect=1)
        self.assertIn("Support status disagrees", cp.stdout)

    def test_unknown_exhibit_and_citation_ids_rejected(self) -> None:
        self.claim["exhibit_ids"] = ["F9"]
        self.claim["citation_need_ids"] = ["N9"]
        self.write_all()
        cp = self.validate(expect=1)
        self.assertIn("unknown exhibit ID F9", cp.stdout)
        self.assertIn("unknown citation need ID N9", cp.stdout)

    def test_identity_mismatch_rejected(self) -> None:
        self.binding_data["identity_version"] = 2
        self.write_all()
        cp = self.validate(expect=1)
        self.assertIn("identity_version does not match commitment", cp.stdout)

    def test_theoretical_claim_can_be_supported_by_artifact_without_audit(self) -> None:
        self.claim.update(
            evidence_mode="theoretical",
            required_assurance_class="none",
            source_claim_ids=[],
            audit_ids=[],
            evidence_artifacts=["proof/main-theorem.md"],
            citation_need_ids=[],
        )
        self.write_all()
        self.validate()

    def test_empirical_evidence_artifact_must_come_from_linked_audit(self) -> None:
        self.claim["evidence_artifacts"] = ["results/unreviewed.json"]
        self.write_all()
        cp = self.validate(expect=1)
        self.assertIn("absent from linked audits", cp.stdout)

    def test_complete_matrix_rejects_extra_noncanonical_claim(self) -> None:
        self.write_all()
        with self.matrix.open("a", encoding="utf-8") as handle:
            handle.write(
                "| PC9 | Unsupported extra claim | primary | empirical | supported | assert | confirmatory | C1 | A1 | Results | F1 | N1 | |\n"
            )
        cp = self.validate(expect=1)
        self.assertIn("noncanonical claim rows: PC9", cp.stdout)

    def test_qualified_claim_requires_explicit_limitation(self) -> None:
        self.claim["manuscript_action"] = "qualify"
        self.write_all()
        cp = self.validate(expect=1)
        self.assertIn("qualify requires explicit limitations", cp.stdout)

    def test_contradicted_status_rejects_adequate_positive_audit(self) -> None:
        self.claim["support_status"] = "contradicted"
        self.claim["manuscript_action"] = "omit"
        self.claim["limitations"] = ["Conflicting result"]
        negative = json.loads(json.dumps(self.audit_data["audits"][0]))
        negative["audit_id"] = "A2"
        negative["verdict"] = "does_not_support_claim"
        negative["audited_claim_effect"] = "kill"
        self.audit_data["audits"].append(negative)
        self.claim["audit_ids"].append("A2")
        self.write_all()
        cp = self.validate(expect=1)
        self.assertIn("cannot be marked contradicted while adequate positive", cp.stdout)


if __name__ == "__main__":
    unittest.main()
