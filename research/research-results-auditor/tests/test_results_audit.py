#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INIT = ROOT / "scripts" / "init_results_audit.py"
VALIDATE = ROOT / "scripts" / "validate_results_audit.py"


class ResultsAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.audit_path = self.root / "results-audit.json"
        self.narrative_path = self.root / "results-audit.md"
        self.commitment_path = self.root / "research-commitment.json"
        self.claim_map_path = self.root / "claim-map.json"
        self.work_items_path = self.root / "work-items.json"
        self.digest_episode = "a" * 64
        self.digest_result = "b" * 64
        self.commitment = {"paper_id": "P1", "identity_version": 1}
        self.claim_map = [{"claim_id": "C1", "claim": "Method improves accuracy"}]
        self.work_items = {
            "items": [
                {
                    "work_item_id": "WI-B1",
                    "experiment_binding": {
                        "paper_id": "P1",
                        "identity_version": 1,
                        "claim_ids": ["C1"],
                    },
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
                            "evidence": "Independent verifier inspected the declared artifacts.",
                        }
                    ],
                }
            ]
        }
        self.audit = {
            "schema_version": "1.0",
            "paper_id": "P1",
            "identity_version": 1,
            "status": "complete",
            "audits": [self.audit_record()],
        }
        self.write_all()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def audit_record(self) -> dict:
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
        return {
            "audit_id": "A1",
            "claim_id": "C1",
            "claim_text": "Method improves accuracy on the frozen held-out test.",
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
                    "verification_decision": "approve",
                    "verified_gate_result": "pass",
                    "verified_scientific_disposition": "supports_claim",
                    "verification_self_review": False,
                }
            ],
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
            "limitations": ["Applies only to the frozen held-out setting."],
            "predecessor_failures": [],
            "minimum_corrective_action": "Preserve the frozen scope and report all outcomes.",
            "narrative_anchor": "results-audit.md#A1",
        }

    def write_all(self) -> None:
        self.audit_path.write_text(json.dumps(self.audit), encoding="utf-8")
        self.narrative_path.write_text(
            "# Results Audit\n\n## Audit A1\n\n- Bounded verdict: supports_confirmatory_claim\n",
            encoding="utf-8",
        )
        self.commitment_path.write_text(json.dumps(self.commitment), encoding="utf-8")
        self.claim_map_path.write_text(json.dumps(self.claim_map), encoding="utf-8")
        self.work_items_path.write_text(json.dumps(self.work_items), encoding="utf-8")

    def validate(self, profile: str = "linked", expect: int = 0) -> subprocess.CompletedProcess[str]:
        cmd = [
            sys.executable,
            str(VALIDATE),
            "--audit",
            str(self.audit_path),
            "--narrative",
            str(self.narrative_path),
            "--assurance-profile",
            profile,
        ]
        if profile == "linked":
            cmd += [
                "--commitment",
                str(self.commitment_path),
                "--claim-map",
                str(self.claim_map_path),
                "--work-items",
                str(self.work_items_path),
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
                "--audit",
                str(fresh / "results-audit.json"),
                "--narrative",
                str(fresh / "results-audit.md"),
            ],
            text=True,
            capture_output=True,
        )
        self.assertEqual(cp.returncode, 0, cp.stdout + cp.stderr)

    def test_valid_linked_audit_passes(self) -> None:
        cp = self.validate()
        self.assertIn("source runs", cp.stdout)

    def test_confirmatory_verdict_requires_decisive_checks(self) -> None:
        for check in self.audit["audits"][0]["check_results"]:
            if check["check_id"] == "outcome_accounting":
                check["status"] = "inconclusive"
        self.write_all()
        cp = self.validate(expect=1)
        self.assertIn("outcome_accounting", cp.stdout)

    def test_independent_verdict_rejects_self_review(self) -> None:
        record = self.audit["audits"][0]
        record["requested_assurance_class"] = "independently_verified"
        record["attained_assurance_class"] = "independently_verified"
        record["verdict"] = "independently_verified"
        for check in record["check_results"]:
            if check["check_id"] == "independence":
                check["status"] = "pass"
        self.narrative_path.write_text(
            "# Results Audit\n\n## Audit A1\n\n- Bounded verdict: independently_verified\n",
            encoding="utf-8",
        )
        self.audit_path.write_text(json.dumps(self.audit), encoding="utf-8")
        cp = self.validate(expect=1)
        self.assertIn("cannot be self-review", cp.stdout)

    def test_source_run_projection_mismatch_rejected(self) -> None:
        self.audit["audits"][0]["source_runs"][0]["gate_result"] = "fail"
        self.write_all()
        cp = self.validate(expect=1)
        self.assertIn("gate_result disagrees", cp.stdout)

    def test_experiment_evidence_digest_mismatch_rejected(self) -> None:
        self.audit["audits"][0]["evidence_artifacts"][0]["digest"] = "c" * 64
        self.write_all()
        cp = self.validate(expect=1)
        self.assertIn("evidence digest mismatch", cp.stdout)

    def test_negative_verdict_cannot_strengthen_claim(self) -> None:
        self.audit["audits"][0]["verdict"] = "does_not_support_claim"
        self.narrative_path.write_text(
            "# Results Audit\n\n## Audit A1\n\n- Bounded verdict: does_not_support_claim\n",
            encoding="utf-8",
        )
        self.audit_path.write_text(json.dumps(self.audit), encoding="utf-8")
        cp = self.validate(expect=1)
        self.assertIn("cannot strengthen", cp.stdout)

    def test_narrative_must_record_exact_verdict(self) -> None:
        self.narrative_path.write_text("# Results Audit\n\n## Audit A1\n", encoding="utf-8")
        cp = self.validate(expect=1)
        self.assertIn("exact bounded verdict", cp.stdout)

    def test_duplicate_audit_ids_rejected(self) -> None:
        self.audit["audits"].append(json.loads(json.dumps(self.audit["audits"][0])))
        self.write_all()
        cp = self.validate(expect=1)
        self.assertIn("duplicate audit_id", cp.stdout)

    def test_audit_check_paths_must_reference_declared_evidence(self) -> None:
        self.audit["audits"][0]["check_results"][0]["evidence_paths"] = ["results/missing.json"]
        self.write_all()
        cp = self.validate(expect=1)
        self.assertIn("unknown audit artifacts", cp.stdout)

    def test_positive_orchestrated_verdict_requires_approved_source(self) -> None:
        self.audit["audits"][0]["source_runs"][0]["verification_decision"] = "revise"
        self.audit["audits"][0]["source_runs"][0]["verified_gate_result"] = None
        self.audit["audits"][0]["source_runs"][0]["verified_scientific_disposition"] = None
        self.work_items["items"][0]["verifications"][0].update(
            decision="revise", gate_results=None, scientific_disposition=None
        )
        self.write_all()
        cp = self.validate(expect=1)
        self.assertIn("requires an approved source run", cp.stdout)

    def test_verifier_projection_mismatch_rejected(self) -> None:
        self.audit["audits"][0]["source_runs"][0]["verification_self_review"] = True
        self.write_all()
        cp = self.validate(expect=1)
        self.assertIn("verification_self_review disagrees", cp.stdout)


if __name__ == "__main__":
    unittest.main()
