#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RESEARCH_ROOT = Path(__file__).resolve().parents[2]
AUDIT_VALIDATOR = RESEARCH_ROOT / "research-results-auditor" / "scripts" / "validate_results_audit.py"
PAPER_VALIDATOR = RESEARCH_ROOT / "research-paper-plan" / "scripts" / "validate_paper_pack.py"


class ResultAuditPaperBindingIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.digest_episode = "a" * 64
        self.digest_result = "b" * 64
        self.paths = {
            "commitment": self.root / "research-commitment.json",
            "claim_map": self.root / "claim-map.json",
            "work_items": self.root / "work-items.json",
            "audit_json": self.root / "results-audit.json",
            "audit_md": self.root / "results-audit.md",
            "paper_plan": self.root / "paper-plan.md",
            "matrix": self.root / "claims-evidence-matrix.md",
            "bindings": self.root / "claim-evidence-bindings.json",
            "figure": self.root / "figure-plan.md",
            "citation": self.root / "citation-plan.md",
        }
        self.commitment = {"paper_id": "P1", "identity_version": 1}
        self.claim_map = [{"claim_id": "C1", "claim": "Method improves accuracy"}]
        self.work_items = {
            "items": [
                {
                    "work_item_id": "WI-B1",
                    "experiment_binding": {"paper_id": "P1", "identity_version": 1, "claim_ids": ["C1"]},
                    "episodes": [
                        {
                            "episode_id": "EP1",
                            "episode_digest": self.digest_episode,
                            "artifact_digests": {"results/B1.json": self.digest_result},
                            "experiment_run": {
                                "run_id": "RUN1",
                                "block_id": "B1",
                                "gate_id": "G1",
                                "gate_result": "pass",
                                "scientific_disposition": "supports_claim",
                                "relation": "baseline",
                                "parent_run_id": None,
                                "claim_effects": [
                                    {"claim_id": "C1", "effect": "strengthen", "scope": "held-out test"}
                                ],
                            },
                        }
                    ],
                    "verifications": [
                        {
                            "episode_id": "EP1",
                            "decision": "approve",
                            "gate_results": {"G1": "pass"},
                            "scientific_disposition": "supports_claim",
                            "self_review": False,
                            "evidence": "Verifier inspected the run and artifacts.",
                        }
                    ],
                }
            ]
        }
        checks = [
            {
                "check_id": check_id,
                "status": "not_assessed" if check_id == "independence" else "pass",
                "rationale": f"Checked {check_id}",
                "evidence_paths": ["results/B1.json"],
            }
            for check_id in (
                "protocol_integrity",
                "metric_validity",
                "baseline_fairness",
                "outcome_accounting",
                "inferential_support",
                "confound_control",
                "provenance",
                "snapshot_continuity",
                "independence",
            )
        ]
        self.audit_record = {
            "audit_id": "A1",
            "claim_id": "C1",
            "claim_text": "Method improves accuracy on the frozen held-out task.",
            "scope": "Frozen held-out task only.",
            "source_mode": "orchestrated",
            "requested_assurance_class": "confirmatory",
            "attained_assurance_class": "confirmatory",
            "verdict": "supports_confirmatory_claim",
            "audited_claim_effect": "strengthen",
            "source_runs": [
                {
                    "work_item_id": "WI-B1",
                    "episode_id": "EP1",
                    "episode_digest": self.digest_episode,
                    "run_id": "RUN1",
                    "block_id": "B1",
                    "gate_id": "G1",
                    "gate_result": "pass",
                    "scientific_disposition": "supports_claim",
                    "lineage_relation": "baseline",
                    "parent_run_id": None,
                    "submitted_claim_effect": "strengthen",
                    "submitted_claim_scope": "held-out test",
                    "verification_decision": "approve",
                    "verified_gate_result": "pass",
                    "verified_scientific_disposition": "supports_claim",
                    "verification_self_review": False,
                }
            ],
            "run_selection": {
                "selection_rule": "Include every eligible run for the paper identity and source claim.",
                "excluded_runs": [],
            },
            "evidence_artifacts": [
                {
                    "path": "results/B1.json",
                    "kind": "metrics",
                    "source": "experiment",
                    "digest": self.digest_result,
                }
            ],
            "check_results": checks,
            "independence": {"self_review": True, "dimensions": [], "evidence": ""},
            "limitations": ["Frozen held-out task only."],
            "predecessor_failures": [],
            "minimum_corrective_action": "Preserve scope and report all outcomes.",
            "narrative_anchor": "results-audit.md#A1",
        }
        self.paper_claim = {
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
            "planned_sections": ["Results"],
            "exhibit_ids": ["F1"],
            "citation_need_ids": [],
            "limitations": [],
            "missing_evidence": [],
            "scope": "Frozen held-out task only.",
            "rationale": "The linked confirmatory audit supports this bounded claim.",
        }
        self.write_all()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def write_all(self) -> None:
        self.paths["commitment"].write_text(json.dumps(self.commitment), encoding="utf-8")
        self.paths["claim_map"].write_text(json.dumps(self.claim_map), encoding="utf-8")
        self.paths["work_items"].write_text(json.dumps(self.work_items), encoding="utf-8")
        self.paths["audit_json"].write_text(
            json.dumps(
                {
                    "schema_version": "1.0",
                    "paper_id": "P1",
                    "identity_version": 1,
                    "status": "complete",
                    "audits": [self.audit_record],
                }
            ),
            encoding="utf-8",
        )
        self.paths["audit_md"].write_text(
            f"# Results Audit\n\n## Audit A1\n\n- Bounded verdict: {self.audit_record['verdict']}\n",
            encoding="utf-8",
        )
        self.paths["paper_plan"].write_text(
            "# Paper Plan\n## Header\n- Paper ID: P1\n## Structure\n1. Results\n## Section Notes\n- PC1\n## Evidence Boundary\nJSON is canonical.\n",
            encoding="utf-8",
        )
        c = self.paper_claim
        self.paths["matrix"].write_text(
            "# Claims-Evidence Matrix\n"
            "| Paper claim ID | Claim | Type | Evidence mode | Support status | Manuscript action | Required assurance | Source claim IDs | Audit IDs | Excluded audit IDs | Planned sections | Exhibit IDs | Citation need IDs | Limitation |\n"
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n"
            f"| PC1 | {c['claim']} | {c['claim_type']} | {c['evidence_mode']} | {c['support_status']} | {c['manuscript_action']} | {c['required_assurance_class']} | C1 | A1 | | Results | F1 | | {'; '.join(c['limitations'])} |\n",
            encoding="utf-8",
        )
        self.paths["bindings"].write_text(
            json.dumps(
                {
                    "schema_version": "1.0",
                    "paper_id": "P1",
                    "identity_version": 1,
                    "status": "complete",
                    "claims": [self.paper_claim],
                }
            ),
            encoding="utf-8",
        )
        self.paths["figure"].write_text(
            "# Figure Plan\n"
            "| Exhibit ID | Purpose | Paper claim IDs | Priority | Status | Notes |\n"
            "| --- | --- | --- | --- | --- | --- |\n"
            "| F1 | Main comparison | PC1 | mandatory | planned | Frozen test |\n",
            encoding="utf-8",
        )
        self.paths["citation"].write_text(
            "# Citation Plan\n"
            "| Citation need ID | Paper claim IDs | Citation need | Source status | Notes |\n"
            "| --- | --- | --- | --- | --- |\n",
            encoding="utf-8",
        )

    def run_audit_validator(self, expect: int = 0) -> subprocess.CompletedProcess[str]:
        cp = subprocess.run(
            [
                sys.executable,
                str(AUDIT_VALIDATOR),
                "--audit",
                str(self.paths["audit_json"]),
                "--narrative",
                str(self.paths["audit_md"]),
                "--assurance-profile",
                "linked",
                "--commitment",
                str(self.paths["commitment"]),
                "--claim-map",
                str(self.paths["claim_map"]),
                "--work-items",
                str(self.paths["work_items"]),
            ],
            text=True,
            capture_output=True,
        )
        self.assertEqual(cp.returncode, expect, cp.stdout + cp.stderr)
        return cp

    def run_paper_validator(self, expect: int = 0) -> subprocess.CompletedProcess[str]:
        cp = subprocess.run(
            [
                sys.executable,
                str(PAPER_VALIDATOR),
                "--plan",
                str(self.paths["paper_plan"]),
                "--matrix",
                str(self.paths["matrix"]),
                "--bindings",
                str(self.paths["bindings"]),
                "--figure-plan",
                str(self.paths["figure"]),
                "--citation-plan",
                str(self.paths["citation"]),
                "--assurance-profile",
                "linked",
                "--commitment",
                str(self.paths["commitment"]),
                "--claim-map",
                str(self.paths["claim_map"]),
                "--results-audit",
                str(self.paths["audit_json"]),
                "--results-audit-narrative",
                str(self.paths["audit_md"]),
                "--work-items",
                str(self.paths["work_items"]),
            ],
            text=True,
            capture_output=True,
        )
        self.assertEqual(cp.returncode, expect, cp.stdout + cp.stderr)
        return cp

    def test_confirmatory_audit_to_asserted_paper_claim_chain(self) -> None:
        self.run_audit_validator()
        self.run_paper_validator()

    def test_downgraded_audit_blocks_confirmatory_manuscript_assertion(self) -> None:
        self.audit_record["attained_assurance_class"] = "exploratory"
        self.audit_record["verdict"] = "supports_exploratory_follow_up"
        self.write_all()
        self.run_audit_validator()
        cp = self.run_paper_validator(expect=1)
        self.assertIn("lacks a positive same-scope audit at required assurance class confirmatory", cp.stdout)

    def test_negative_audit_requires_nonassertive_manuscript_action(self) -> None:
        self.audit_record["verdict"] = "does_not_support_claim"
        self.audit_record["audited_claim_effect"] = "kill"
        self.write_all()
        self.run_audit_validator()
        cp = self.run_paper_validator(expect=1)
        self.assertIn("cannot be asserted", cp.stdout)


if __name__ == "__main__":
    unittest.main()
