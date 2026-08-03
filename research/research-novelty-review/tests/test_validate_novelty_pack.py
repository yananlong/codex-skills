#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

RESEARCH_ROOT = Path(__file__).resolve().parents[2]
NOVELTY_ROOT = Path(__file__).resolve().parents[1]
NOVELTY_INIT = NOVELTY_ROOT / "scripts" / "init_novelty_pack.py"
NOVELTY_VALIDATE = NOVELTY_ROOT / "scripts" / "validate_novelty_pack.py"
LIT_INIT = RESEARCH_ROOT / "research-systematic-literature-review" / "scripts" / "init_review_pack.py"


class NoveltyPackTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.lit = self.root / "literature"
        self.novelty = self.root / "novelty"
        self.run_cmd(
            str(LIT_INIT),
            "--topic", "Example",
            "--domain", "Machine learning",
            "--review-profile", "bounded-systematic",
            "--out-dir", str(self.lit),
            "--intended-decision", "Decide the novelty position",
            "--domain-adapter", "methodological",
        )
        self.make_valid_literature()
        self.run_cmd(str(NOVELTY_INIT), str(self.novelty))
        self.decision_path = self.novelty / "novelty-decision.json"
        self.report_path = self.novelty / "novelty-report.md"
        self.decision = json.loads(self.decision_path.read_text())
        self.bind_literature(rating=4)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def run_cmd(self, *args: str, expect: int = 0) -> subprocess.CompletedProcess[str]:
        cp = subprocess.run([sys.executable, *args], text=True, capture_output=True)
        self.assertEqual(cp.returncode, expect, cp.stdout + cp.stderr)
        return cp

    def literature_paths(self) -> dict[str, Path]:
        return {
            "protocol": self.lit / "example.protocol.md",
            "search_log": self.lit / "example.search-log.md",
            "recall_audit": self.lit / "example.recall-audit.md",
            "corpus_manifest": self.lit / "example.corpus-manifest.json",
            "screening_log": self.lit / "example.screening-log.md",
            "evidence": self.lit / "example.evidence-table.md",
            "report": self.lit / "example.review.md",
        }

    def make_valid_literature(self) -> None:
        p = self.literature_paths()
        today = date.today().isoformat()
        search = p["search_log"].read_text()
        search = search.replace(
            f"| run-001 | {today} | database | TODO | primary question | CQ-001 | TODO | TODO | 0 | 0 | 0 | | |",
            f"| run-001 | {today} | database | Semantic Scholar | core method | CQ-001 | example method | none | 2 | 2 | 1 | alternate term | none |",
        )
        search = search.replace(
            "| seed-001 | TODO | foundation / close anchor / expert seed | | no | TODO | TODO |",
            "| seed-001 | Doe et al. 2024 | close anchor | run-001 | yes | | |",
        )
        for channel in (
            "backward-citation", "forward-citation", "venue-census", "author-lab-expansion",
            "benchmark-dataset-tracing", "prior-review-harvesting", "grey-literature", "zotero-cross-check",
        ):
            search = search.replace(
                f"| {channel} | required | TODO | 0 | 0 | 0 | 0 |",
                f"| {channel} | performed | completed within boundary | 1 | 1 | 0 | 0 |",
            )
        p["search_log"].write_text(search)

        recall = p["recall_audit"].read_text()
        recall = recall.replace("TODO yes / no", "no, unavailable because no separate custodian was available")
        recall = recall.replace("TODO", "completed")
        recall = recall.replace("- Verdict: insufficient", "- Verdict: adequate-for-bounded-claims")
        p["recall_audit"].write_text(recall)

        screening = p["screening_log"].read_text()
        for old, new in (
            ("| records_identified | 0 |", "| records_identified | 1 |"),
            ("| records_screened | 0 |", "| records_screened | 1 |"),
            ("| reports_sought_for_retrieval | 0 |", "| reports_sought_for_retrieval | 1 |"),
            ("| reports_assessed_for_eligibility | 0 |", "| reports_assessed_for_eligibility | 1 |"),
            ("| studies_included | 0 |", "| studies_included | 1 |"),
        ):
            screening = screening.replace(old, new)
        screening = screening.replace(
            f"| | published/preprint/book/report/software | | | | | | title_abstract | include/exclude | | | {today} | |",
            f"| P1 | published | Doe et al. 2024 | https://example.org/p1 | 10.1/example | Venue | | full_text | include | eligible | reviewer | {today} | |",
        )
        p["screening_log"].write_text(screening)
        p["evidence"].write_text(
            p["evidence"].read_text().replace(
                "| | | | 0 | | | published/preprint | | empirical/theoretical/method/benchmark/review | Broad context implied by the topic and domain unless explicitly narrowed | | | | low/moderate/high | | |",
                "| P1 | Doe et al. 2024 | https://example.org/p1 | 2024 | Venue | 10.1/example | published | | method | ML | analysis | positive result | none | high | direct | |",
            )
        )
        manifest = json.loads(p["corpus_manifest"].read_text())
        manifest.update(
            freeze_date="2026-08-02",
            records=[{
                "record_id": "P1",
                "canonical_citation": "Doe et al. 2024",
                "publication_url": "https://example.org/p1",
                "publication_status": "published",
                "question_ids": ["CQ-001"],
            }],
            seed_ids=["seed-001"],
            assurance_verdict="adequate-for-bounded-claims",
        )
        manifest["search_strategy_review"]["notes"] = "Self-review only; assurance remains bounded."
        manifest["coverage_questions"][0].update(
            status="answered",
            record_ids=["P1"],
            answer_summary="The included work supports a bounded comparison.",
            residual_gap="External settings remain outside scope.",
            closure_reason="The frozen corpus answers the bounded question.",
        )
        p["corpus_manifest"].write_text(json.dumps(manifest))
        report = p["report"].read_text().replace("TODO", "completed")
        report = report.replace("- Assurance verdict: insufficient", "- Assurance verdict: adequate-for-bounded-claims")
        p["report"].write_text(report)

    def bind_literature(self, rating: int) -> None:
        paths = self.literature_paths()
        manifest = json.loads(paths["corpus_manifest"].read_text())
        self.decision.update(
            status="complete",
            novelty_decision_rating=rating,
            impact_positioning_rating=3,
            decision_confidence_rating=3,
            narrowest_defensible_positioning="A bounded methodological contribution on the frozen corpus.",
            what_would_change_the_decision="A closer prior method or unresolved critical overlap would lower the rating.",
        )
        self.decision["literature_assurance"] = {
            "mode": "linked",
            "paths": {
                key: str(Path("..") / path.relative_to(self.root))
                for key, path in paths.items()
            },
            "file_sha256": {
                key: hashlib.sha256(path.read_bytes()).hexdigest()
                for key, path in paths.items()
            },
            "corpus_manifest_sha256": hashlib.sha256(paths["corpus_manifest"].read_bytes()).hexdigest(),
            "corpus_version": manifest["corpus_version"],
            "review_profile": manifest["review_profile"],
            "assurance_verdict": manifest["assurance_verdict"],
            "unresolved_high_priority_novelty_question_ids": [],
        }
        self.write_decision()
        report = self.report_path.read_text()
        report = report.replace("Novelty decision rating (1-5): 3", f"Novelty decision rating (1-5): {rating}")
        report = report.replace("- Narrowest defensible positioning:", f"- Narrowest defensible positioning: {self.decision['narrowest_defensible_positioning']}")
        report = report.replace("- What would change the decision:", f"- What would change the decision: {self.decision['what_would_change_the_decision']}")
        report = report.replace("- Literature assurance mode: unlinked", "- Literature assurance mode: linked")
        report = report.replace("- Literature assurance verdict:", f"- Literature assurance verdict: {manifest['assurance_verdict']}")
        self.report_path.write_text(report)

    def write_decision(self) -> None:
        self.decision_path.write_text(json.dumps(self.decision, indent=2, sort_keys=True) + "\n")

    def refresh_file_digests(self) -> None:
        paths = self.literature_paths()
        assurance = self.decision["literature_assurance"]
        assurance["file_sha256"] = {
            key: hashlib.sha256(path.read_bytes()).hexdigest()
            for key, path in paths.items()
        }
        assurance["corpus_manifest_sha256"] = assurance["file_sha256"]["corpus_manifest"]

    def validate(self, profile: str = "linked", expect: int = 0) -> subprocess.CompletedProcess[str]:
        return self.run_cmd(
            str(NOVELTY_VALIDATE),
            "--decision", str(self.decision_path),
            "--report", str(self.report_path),
            "--prior-art-matrix", str(self.novelty / "prior-art-matrix.md"),
            "--search-log", str(self.novelty / "search-log.md"),
            "--assurance-profile", profile,
            expect=expect,
        )

    def test_fresh_scaffold_passes_structural_validation(self) -> None:
        fresh = self.root / "fresh-novelty"
        self.run_cmd(str(NOVELTY_INIT), str(fresh))
        self.run_cmd(
            str(NOVELTY_VALIDATE),
            "--decision", str(fresh / "novelty-decision.json"),
            "--report", str(fresh / "novelty-report.md"),
            "--prior-art-matrix", str(fresh / "prior-art-matrix.md"),
            "--search-log", str(fresh / "search-log.md"),
        )

    def test_rating_four_with_valid_bound_literature_passes(self) -> None:
        cp = self.validate()
        self.assertIn("exact bound literature pack was revalidated", cp.stdout)

    def test_manifest_digest_mismatch_fails(self) -> None:
        self.decision["literature_assurance"]["corpus_manifest_sha256"] = "0" * 64
        self.write_decision()
        cp = self.validate(expect=1)
        self.assertIn("sha256 does not match", cp.stdout)

    def test_non_manifest_file_mutation_breaks_exact_pack_binding(self) -> None:
        report = self.literature_paths()["report"]
        report.write_text(report.read_text() + "\nAdditional still-valid interpretation.\n")
        cp = self.validate(expect=1)
        self.assertIn("file_sha256.report does not match the bound file", cp.stdout)

    def test_linked_decision_cannot_use_structural_profile(self) -> None:
        cp = self.validate(profile="structural", expect=1)
        self.assertIn("mode=linked requires --assurance-profile linked", cp.stdout)

    def make_blocked_critical_question(self) -> None:
        manifest_path = self.literature_paths()["corpus_manifest"]
        manifest = json.loads(manifest_path.read_text())
        manifest["coverage_questions"][0].update(
            critical_for_novelty=True,
            status="blocked",
            answer_summary="",
            residual_gap="A proprietary comparison corpus is unavailable.",
            closure_reason="The source cannot be accessed within this review.",
            blocked_mitigation="Search public replications and disclose the missing corpus.",
            scope_consequence="Novelty claims exclude the unavailable proprietary corpus.",
        )
        manifest_path.write_text(json.dumps(manifest))
        assurance = self.decision["literature_assurance"]
        self.refresh_file_digests()
        assurance["unresolved_high_priority_novelty_question_ids"] = ["CQ-001"]
        self.write_decision()
        self.report_path.write_text(
            self.report_path.read_text().replace(
                "- Unresolved high-priority novelty-critical questions:",
                "- Unresolved high-priority novelty-critical questions: CQ-001",
            )
        )

    def test_strong_rating_rejects_unresolved_critical_question(self) -> None:
        self.make_blocked_critical_question()
        cp = self.validate(expect=1)
        self.assertIn("novelty rating 4 cannot retain unresolved", cp.stdout)

    def test_rating_three_with_uncertainty_requires_qualification(self) -> None:
        self.make_blocked_critical_question()
        self.decision["novelty_decision_rating"] = 3
        self.decision["claims_to_qualify"] = []
        self.write_decision()
        self.report_path.write_text(self.report_path.read_text().replace("rating (1-5): 4", "rating (1-5): 3", 1))
        cp = self.validate(expect=1)
        self.assertIn("requires claims_to_qualify", cp.stdout)
        self.decision["claims_to_qualify"] = ["Qualify the claim to public corpora covered by the review."]
        self.write_decision()
        self.validate()

    def test_declared_unresolved_ids_must_match_manifest(self) -> None:
        self.make_blocked_critical_question()
        self.decision["novelty_decision_rating"] = 3
        self.decision["claims_to_qualify"] = ["Qualify the corpus boundary."]
        self.decision["literature_assurance"]["unresolved_high_priority_novelty_question_ids"] = []
        self.write_decision()
        self.report_path.write_text(self.report_path.read_text().replace("rating (1-5): 4", "rating (1-5): 3", 1))
        cp = self.validate(expect=1)
        self.assertIn("unresolved question IDs do not match", cp.stdout)

    def test_bound_literature_pack_is_revalidated(self) -> None:
        search = self.literature_paths()["search_log"]
        search.write_text(search.read_text().replace("Semantic Scholar", "TODO"))
        cp = self.validate(expect=1)
        self.assertIn("upstream literature-review validation failed", cp.stdout)
        self.assertIn("source must be substantive", cp.stdout)

    def test_rating_five_requires_adequate_literature_verdict(self) -> None:
        manifest_path = self.literature_paths()["corpus_manifest"]
        manifest = json.loads(manifest_path.read_text())
        manifest["assurance_verdict"] = "insufficient"
        manifest_path.write_text(json.dumps(manifest))
        self.decision["novelty_decision_rating"] = 5
        assurance = self.decision["literature_assurance"]
        assurance["assurance_verdict"] = "insufficient"
        self.write_decision()
        report = self.report_path.read_text()
        report = report.replace("Novelty decision rating (1-5): 4", "Novelty decision rating (1-5): 5")
        report = report.replace("Literature assurance verdict: adequate-for-bounded-claims", "Literature assurance verdict: insufficient")
        self.report_path.write_text(report)
        recall = self.literature_paths()["recall_audit"]
        recall.write_text(recall.read_text().replace("- Verdict: adequate-for-bounded-claims", "- Verdict: insufficient"))
        review = self.literature_paths()["report"]
        review.write_text(review.read_text().replace("- Assurance verdict: adequate-for-bounded-claims", "- Assurance verdict: insufficient"))
        self.refresh_file_digests()
        self.write_decision()
        cp = self.validate(expect=1)
        self.assertIn("novelty rating 5 requires adequate literature assurance", cp.stdout)

    def test_corpus_identity_fields_must_match(self) -> None:
        self.decision["literature_assurance"]["corpus_version"] = 99
        self.write_decision()
        cp = self.validate(expect=1)
        self.assertIn("corpus_version does not match", cp.stdout)


if __name__ == "__main__":
    unittest.main()
