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
            "scope": "Frozen held-out test only.",
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
                "selection_rule": "Include every experiment run bound to C1 for paper P1 identity version 1.",
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

    def validate(
        self, profile: str = "linked", expect: int = 0, extra: tuple[str, ...] = ()
    ) -> subprocess.CompletedProcess[str]:
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
        cmd += list(extra)
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

    def test_accepted_narrowing_requires_a_trajectory_record(self) -> None:
        audit = self.audit["audits"][0]
        audit["predecessor_failures"] = [
            {"failure_id": "F1", "status": "accepted_with_narrowing", "rationale": "the second shift is dropped"}
        ]
        self.write_all()
        cp = self.validate(expect=1)
        self.assertIn("needs a trajectory record", cp.stdout)
        cp = self.validate(profile="structural")
        self.assertIn("the linked profile requires it", cp.stdout)
        audit["trajectory"] = {"claim_id": audit["claim_id"], "change_class": "precision"}
        self.write_all()
        cp = self.validate(expect=1)
        self.assertIn("cannot be precision", cp.stdout)
        audit["trajectory"] = {
            "claim_id": audit["claim_id"],
            "change_class": "scope_narrowing",
            "content_lost": "coverage of the second shift",
            "alternatives_considered": ["lower_assurance: keep the claim as exploratory"],
            "restoring_evidence": "a matched second-shift benchmark",
        }
        self.write_all()
        self.validate()

    def test_free_text_corrective_action_warns(self) -> None:
        self.audit["audits"][0]["minimum_corrective_action"] = "look into it"
        self.write_all()
        cp = self.validate()
        self.assertIn("free text without a repair action", cp.stdout)
        self.audit["audits"][0]["minimum_corrective_action"] = "add_evidence: run the held-out shift"
        self.write_all()
        cp = self.validate()
        self.assertNotIn("free text without a repair action", cp.stdout)

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

    def add_conflicting_run(self) -> None:
        item = json.loads(json.dumps(self.work_items["items"][0]))
        item["work_item_id"] = "WI-B2"
        item["episodes"][0]["episode_id"] = "EP2"
        item["episodes"][0]["episode_digest"] = "c" * 64
        item["episodes"][0]["artifact_digests"] = {"results/B2.json": "d" * 64}
        run = item["episodes"][0]["experiment_run"]
        run.update(
            run_id="RUN2",
            block_id="B2",
            gate_id="G2",
            gate_result="fail",
            scientific_disposition="falsifies_claim",
        )
        run["claim_effects"][0].update(effect="kill", scope="held-out test")
        verification = item["verifications"][0]
        verification.update(
            episode_id="EP2",
            gate_results={"G2": "fail"},
            scientific_disposition="falsifies_claim",
        )
        self.work_items["items"].append(item)

    def test_linked_profile_rejects_standalone_source_mode(self) -> None:
        record = self.audit["audits"][0]
        record["source_mode"] = "standalone"
        record["source_runs"] = []
        record["evidence_artifacts"][0].update(source="audit", digest="")
        self.write_all()
        cp = self.validate(expect=1)
        self.assertIn("linked profile requires source_mode=orchestrated", cp.stdout)

    def test_omitted_eligible_run_is_rejected(self) -> None:
        self.add_conflicting_run()
        self.write_all()
        cp = self.validate(expect=1)
        self.assertIn("omits eligible source runs", cp.stdout)
        self.assertIn("RUN2", cp.stdout)

    def test_explicit_run_exclusion_with_rationale_passes(self) -> None:
        self.add_conflicting_run()
        self.audit["audits"][0]["run_selection"]["excluded_runs"] = [
            {"run_id": "RUN2", "rationale": "Different predeclared diagnostic condition."}
        ]
        self.write_all()
        self.validate()

    def test_operational_support_requires_every_check_to_pass(self) -> None:
        record = self.audit["audits"][0]
        record["requested_assurance_class"] = "operational_high_stakes"
        record["attained_assurance_class"] = "operational_high_stakes"
        record["verdict"] = "supports_operational_high_stakes_claim"
        record["independence"] = {
            "self_review": False,
            "dimensions": ["context", "data", "implementation", "evaluation", "advancement_authority"],
            "evidence": "Materially separate execution, evaluation, and advancement authorities.",
        }
        for check in record["check_results"]:
            check["status"] = "pass"
            if check["check_id"] == "snapshot_continuity":
                check["status"] = "not_assessed"
        self.narrative_path.write_text(
            "# Results Audit\n\n## Audit A1\n\n- Bounded verdict: supports_operational_high_stakes_claim\n",
            encoding="utf-8",
        )
        self.audit_path.write_text(json.dumps(self.audit), encoding="utf-8")
        cp = self.validate(expect=1)
        self.assertIn("snapshot_continuity", cp.stdout)

    def test_complete_audit_requires_scope(self) -> None:
        del self.audit["audits"][0]["scope"]
        self.write_all()
        cp = self.validate(expect=1)
        self.assertIn(".scope must be substantive", cp.stdout)

    def test_submitted_claim_scope_must_match_source_run(self) -> None:
        self.audit["audits"][0]["source_runs"][0]["submitted_claim_scope"] = "all tasks"
        self.write_all()
        cp = self.validate(expect=1)
        self.assertIn("submitted_claim_scope disagrees", cp.stdout)


    def init_fresh(self) -> Path:
        fresh = self.root / "fresh"
        cp = subprocess.run([sys.executable, str(INIT), str(fresh)], text=True, capture_output=True)
        self.assertEqual(cp.returncode, 0, cp.stderr)
        return fresh

    def run_validator(self, audit: Path, narrative: Path, *extra: str, expect: int = 0):
        cp = subprocess.run(
            [sys.executable, str(VALIDATE), "--audit", str(audit), "--narrative", str(narrative), *extra],
            text=True,
            capture_output=True,
        )
        self.assertEqual(cp.returncode, expect, msg=f"stdout:\n{cp.stdout}\nstderr:\n{cp.stderr}")
        return cp

    def test_empty_draft_reports_zero_audits_not_pass(self) -> None:
        fresh = self.init_fresh()
        cp = self.run_validator(fresh / "results-audit.json", fresh / "results-audit.md")
        self.assertIn("Draft: 0 audits", cp.stdout)
        self.assertNotIn("Validation passed", cp.stdout)

    def test_untouched_init_narrative_does_not_anchor_a_real_audit(self) -> None:
        fresh = self.init_fresh()
        record = self.audit_record()
        record.update(verdict="inconclusive", audited_claim_effect="inconclusive")
        self.audit["audits"] = [record]
        (fresh / "results-audit.json").write_text(json.dumps(self.audit), encoding="utf-8")
        cp = self.run_validator(fresh / "results-audit.json", fresh / "results-audit.md", expect=1)
        self.assertIn("missing exact heading '## Audit A1'", cp.stdout)

    def write_evidence(self, content: bytes = b'{"metric": 0}\n') -> str:
        import hashlib

        target = self.root / "results" / "B1.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        return hashlib.sha256(content).hexdigest()

    def test_root_accepts_matching_digest(self) -> None:
        self.audit["audits"][0]["evidence_artifacts"][0]["digest"] = self.write_evidence()
        self.write_all()
        cp = self.validate(profile="structural", extra=("--root", str(self.root)))
        self.assertIn("checked against files", cp.stdout)

    def test_root_rejects_mismatched_digest(self) -> None:
        self.write_evidence()
        cp = self.validate(profile="structural", expect=1, extra=("--root", str(self.root)))
        self.assertIn("digest does not match file bytes for results/B1.json", cp.stdout)

    def test_root_rejects_missing_evidence_path(self) -> None:
        cp = self.validate(profile="structural", expect=1, extra=("--root", str(self.root)))
        self.assertIn("does not exist under --root: results/B1.json", cp.stdout)

    def test_without_root_pass_message_discloses_unchecked_digests(self) -> None:
        cp = self.validate(profile="structural")
        self.assertIn("digests not checked against files", cp.stdout)

    def test_older_source_revision_downgrades_digest_mismatch(self) -> None:
        git = ["git", "-C", str(self.root), "-c", "user.name=t", "-c", "user.email=t@example.invalid"]
        if subprocess.run(["git", "--version"], capture_output=True).returncode != 0:
            self.skipTest("git unavailable")
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        self.audit["audits"][0]["evidence_artifacts"][0]["digest"] = self.write_evidence(b"old\n")
        subprocess.run([*git, "add", "-A"], check=True)
        subprocess.run([*git, "commit", "-q", "-m", "old"], check=True)
        old = subprocess.run([*git, "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()
        self.write_evidence(b"new\n")
        subprocess.run([*git, "commit", "-q", "-am", "new"], check=True)
        self.audit["source_revision"] = old
        self.write_all()
        cp = self.validate(profile="structural", extra=("--root", str(self.root)))
        self.assertIn(f"warning: audit A1 experiment evidence digest does not match", cp.stdout)
        self.assertIn(old, cp.stdout)
        self.audit["source_revision"] = subprocess.run(
            [*git, "rev-parse", "HEAD"], check=True, capture_output=True, text=True
        ).stdout.strip()
        self.write_all()
        self.validate(profile="structural", expect=1, extra=("--root", str(self.root)))

    def lightweight_audit(self) -> None:
        record = self.audit_record()
        record.update(
            source_mode="standalone",
            requested_assurance_class="exploratory",
            attained_assurance_class="exploratory",
            verdict="inconclusive",
            audited_claim_effect="inconclusive",
            source_runs=[],
        )
        record["check_results"] = [
            check for check in record["check_results"]
            if check["check_id"] not in {"snapshot_continuity", "independence"}
        ]
        self.audit["audits"] = [record]
        del self.audit["paper_id"]
        self.narrative_path.write_text("## Audit A1\n\n- Bounded verdict: inconclusive\n", encoding="utf-8")
        self.audit_path.write_text(json.dumps(self.audit), encoding="utf-8")

    def test_standalone_exploratory_audit_needs_no_paper_id_or_solo_checks(self) -> None:
        self.lightweight_audit()
        self.validate(profile="structural")

    def test_confirmatory_standalone_audit_still_requires_paper_id_and_all_checks(self) -> None:
        self.lightweight_audit()
        self.audit["audits"][0]["requested_assurance_class"] = "confirmatory"
        self.audit_path.write_text(json.dumps(self.audit), encoding="utf-8")
        cp = self.validate(profile="structural", expect=1)
        self.assertIn("requires substantive paper_id", cp.stdout)
        self.assertIn("missing required checks: independence, snapshot_continuity", cp.stdout)


if __name__ == "__main__":
    unittest.main()
