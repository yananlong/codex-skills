#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import shutil
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
CONTEXT_SCRIPT = RESEARCH_ROOT / "research-systematic-literature-review" / "scripts" / "paper_context_artifacts.py"
ASSURANCE = NOVELTY_ROOT / "scripts" / "novelty_assurance.py"
SLR_PRESENT = LIT_INIT.exists()


def run_python(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, *args], text=True, capture_output=True)


TEMPLATE_SEARCH_ROW = "| YYYY-MM-DD | | | | | falsify framing / method / protocol / artifact / result | 0 | | | |"


def log_one_search(pack: Path, row: str | None = None) -> None:
    """Replace the search-log template row with one dated synthetic search."""
    row = row or (
        f"| {date.today().isoformat()} | synthetic ranking objective prior work | web search | general web | "
        "none | falsify method | 10 | Synthetic Work 1 | Synthetic Work 1 | |"
    )
    log = pack / "search-log.md"
    log.write_text(log.read_text().replace(TEMPLATE_SEARCH_ROW, row))


class StandaloneNoveltyTests(unittest.TestCase):
    """Behaviour that must hold with only research-novelty-review installed (QI-03)."""

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.skill = self.root / "skills" / "research-novelty-review"
        shutil.copytree(NOVELTY_ROOT, self.skill, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        self.init = self.skill / "scripts" / "init_novelty_pack.py"
        self.validator = self.skill / "scripts" / "validate_novelty_pack.py"
        self.pack = self.root / "pack"
        cp = run_python(str(self.init), str(self.pack))
        self.assertEqual(cp.returncode, 0, cp.stdout + cp.stderr)
        self.decision_path = self.pack / "novelty-decision.json"
        self.report_path = self.pack / "novelty-report.md"

    def tearDown(self) -> None:
        self.temp.cleanup()

    def validate(self, *extra: str) -> subprocess.CompletedProcess[str]:
        return run_python(
            str(self.validator),
            "--decision", str(self.decision_path),
            "--report", str(self.report_path),
            "--prior-art-matrix", str(self.pack / "prior-art-matrix.md"),
            "--search-log", str(self.pack / "search-log.md"),
            *extra,
        )

    def add_prior_art_rows(self, count: int) -> None:
        rows = "".join(
            f"| Synthetic Work {index} | Synthetic Venue 2024 | scoring step | 2 | the ranking objective | a shared loss |\n"
            for index in range(1, count + 1)
        )
        matrix = self.pack / "prior-art-matrix.md"
        matrix.write_text(matrix.read_text().replace("| | | | 1-5 | | |\n", rows))

    def complete(self, rating: int | None, rows: int | None = None) -> None:
        if rows is None:
            rows = max((rating or 1) - 1, 0)
        self.add_prior_art_rows(rows)
        log_one_search(self.pack)
        decision = json.loads(self.decision_path.read_text())
        decision.update(
            status="complete",
            novelty_decision_rating=rating,
            impact_positioning_rating=rating,
            decision_confidence_rating=rating,
            narrowest_defensible_positioning="A bounded synthetic contribution.",
            what_would_change_the_decision="A closer synthetic prior method.",
        )
        self.decision_path.write_text(json.dumps(decision))
        report = self.report_path.read_text()
        value = "" if rating is None else f" {rating}"
        for label in ("Novelty decision", "Impact positioning", "Decision confidence"):
            report = report.replace(f"{label} rating (1-5):\n", f"{label} rating (1-5):{value}\n")
        report = report.replace("- Narrowest defensible positioning:", "- Narrowest defensible positioning: A bounded synthetic contribution.")
        report = report.replace("- What would change the decision:", "- What would change the decision: A closer synthetic prior method.")
        self.report_path.write_text(report)

    def test_search_log_rows_are_dated_single_queries_with_honest_columns(self) -> None:
        self.complete(2)
        self.assertEqual(self.validate().returncode, 0)
        log = self.pack / "search-log.md"
        good = log.read_text()
        log.write_text(good.replace(date.today().isoformat(), "last week"))
        cp = self.validate()
        self.assertIn("Date must be the search date", cp.stdout)
        log.write_text(good.replace("synthetic ranking objective prior work", "query one; query two"))
        cp = self.validate()
        self.assertIn("one query per row", cp.stdout)
        log.write_text(good.replace("| 10 |", "| many |"))
        cp = self.validate()
        self.assertIn("Results inspected must be the number", cp.stdout)

    def test_complete_unlinked_review_needs_a_logged_search(self) -> None:
        self.complete(2)
        log = self.pack / "search-log.md"
        lines = [line for line in log.read_text().splitlines() if "synthetic ranking objective" not in line]
        log.write_text("\n".join(lines) + "\n")
        cp = self.validate()
        self.assertEqual(cp.returncode, 1)
        self.assertIn("needs at least one logged search", cp.stdout)

    def test_legacy_search_log_validates_with_a_warning(self) -> None:
        self.complete(2)
        (self.pack / "search-log.md").write_text(
            "# Search Log\n\n| Query | Source | Filters | Purpose | Closest hits | Notes |\n"
            "| --- | --- | --- | --- | --- | --- |\n| synthetic query | web | none | falsify | Synthetic Work 1 | |\n"
        )
        cp = self.validate()
        self.assertEqual(cp.returncode, 0, cp.stdout)
        self.assertIn("warning: search-log.md uses the older columns", cp.stdout)

    def test_claim_trajectory_records_are_validated(self) -> None:
        self.complete(2)
        self.assertEqual(self.validate().returncode, 0)
        decision = json.loads(self.decision_path.read_text())
        decision["claim_trajectory"] = [{"claim_id": "C1", "change_class": "scope_narrowing"}]
        self.decision_path.write_text(json.dumps(decision))
        cp = self.validate()
        self.assertEqual(cp.returncode, 1, cp.stdout)
        self.assertIn("claim_trajectory[1].content_lost", cp.stdout)
        decision["claim_trajectory"] = [{
            "claim_id": "C1",
            "change_class": "scope_narrowing",
            "content_lost": "the claim to a general ranking method",
            "alternatives_considered": ["sharpen_comparator: separate the synthetic prior method by its loss"],
            "restoring_evidence": "a comparison showing the loss matters on a second task",
        }]
        self.decision_path.write_text(json.dumps(decision))
        self.assertEqual(self.validate().returncode, 0)

    def test_help_runs_without_literature_review_sibling(self) -> None:
        self.assertFalse((self.root / "skills" / "research-systematic-literature-review").exists())
        cp = run_python(str(self.validator), "--help")
        self.assertEqual(cp.returncode, 0, cp.stdout + cp.stderr)
        self.assertIn("--assurance-profile", cp.stdout)

    def test_structural_validation_runs_without_literature_review_sibling(self) -> None:
        cp = self.validate()
        self.assertEqual(cp.returncode, 0, cp.stdout + cp.stderr)
        self.complete(3)
        cp = self.validate()
        self.assertEqual(cp.returncode, 0, cp.stdout + cp.stderr)

    def test_linked_mode_names_missing_sibling_skill(self) -> None:
        self.complete(3)
        decision = json.loads(self.decision_path.read_text())
        decision["literature_assurance"]["mode"] = "linked"
        self.decision_path.write_text(json.dumps(decision))
        cp = self.validate("--assurance-profile", "linked")
        self.assertEqual(cp.returncode, 1, cp.stdout + cp.stderr)
        self.assertIn("requires the research-systematic-literature-review skill installed alongside", cp.stdout)
        self.assertNotIn("Traceback", cp.stderr)

    def test_scaffold_ratings_start_null(self) -> None:
        decision = json.loads(self.decision_path.read_text())
        for field in ("novelty_decision_rating", "impact_positioning_rating", "decision_confidence_rating"):
            self.assertIsNone(decision[field])
        self.assertIn("- Novelty decision rating (1-5):\n", self.report_path.read_text())

    def test_complete_status_rejects_null_ratings(self) -> None:
        self.complete(None)
        cp = self.validate()
        self.assertEqual(cp.returncode, 1, cp.stdout + cp.stderr)
        self.assertIn("novelty_decision_rating must be an integer from 1 to 5 when status is complete", cp.stdout)

    def test_rating_five_without_prior_art_rows_fails(self) -> None:
        self.complete(5, rows=0)
        cp = self.validate()
        self.assertEqual(cp.returncode, 1, cp.stdout + cp.stderr)
        self.assertIn("novelty rating 5 exceeds the structural cap of 3", cp.stdout)
        self.assertIn("needs at least 4 filled prior-art row(s)", cp.stdout)

    def test_rating_three_with_two_rows_passes_structural(self) -> None:
        self.complete(3, rows=2)
        cp = self.validate()
        self.assertEqual(cp.returncode, 0, cp.stdout + cp.stderr)
        self.assertIn("within the structural cap of 3", cp.stdout)

    def test_rating_three_with_one_row_fails(self) -> None:
        self.complete(3, rows=1)
        cp = self.validate()
        self.assertEqual(cp.returncode, 1, cp.stdout + cp.stderr)
        self.assertIn("needs at least 2 filled prior-art row(s)", cp.stdout)
        self.assertIn("found 1", cp.stdout)

    def test_rating_four_in_structural_mode_names_both_routes(self) -> None:
        self.complete(4)
        cp = self.validate()
        self.assertEqual(cp.returncode, 1, cp.stdout + cp.stderr)
        self.assertIn("exceeds the structural cap of 3", cp.stdout)
        self.assertIn("link --pack-dir", cp.stdout)
        self.assertIn("--assurance-profile linked", cp.stdout)
        self.assertIn("link --context", cp.stdout)

    def test_rating_one_needs_no_rows(self) -> None:
        self.complete(1, rows=0)
        cp = self.validate()
        self.assertEqual(cp.returncode, 0, cp.stdout + cp.stderr)

    def test_context_mode_names_missing_sibling_skill(self) -> None:
        self.complete(3)
        decision = json.loads(self.decision_path.read_text())
        decision["literature_assurance"] = {"mode": "context", "context_dir": "ctx", "context_sha256": {}}
        self.decision_path.write_text(json.dumps(decision))
        cp = self.validate()
        self.assertEqual(cp.returncode, 1, cp.stdout + cp.stderr)
        self.assertIn("context mode requires the research-systematic-literature-review skill", cp.stdout)
        self.assertNotIn("Traceback", cp.stderr)


@unittest.skipUnless(SLR_PRESENT, "research-systematic-literature-review sibling not installed")
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
            f"| run-001 | {today} | database | TODO | TODO | primary question | CQ-001 | TODO | TODO | 0 | TODO | 0 | 0 | | |",
            f"| run-001 | {today} | database | Semantic Scholar API | Semantic Scholar | core method | CQ-001 | example method | none | 2 | doi:10.0000/synthetic.1 | 2 | 1 | alternate term | none |",
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
        report = report.replace("Novelty decision rating (1-5):\n", f"Novelty decision rating (1-5): {rating}\n")
        report = report.replace("Impact positioning rating (1-5):\n", "Impact positioning rating (1-5): 3\n")
        report = report.replace("Decision confidence rating (1-5):\n", "Decision confidence rating (1-5): 3\n")
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

    def test_link_helper_binds_pack_that_validates_linked(self) -> None:
        fresh = self.root / "linked-novelty"
        self.run_cmd(str(NOVELTY_INIT), str(fresh), "--link", str(self.lit))
        decision_path = fresh / "novelty-decision.json"
        decision = json.loads(decision_path.read_text())
        self.assertEqual(decision["literature_assurance"]["mode"], "linked")
        self.assertEqual(
            decision["literature_assurance"]["corpus_manifest_sha256"],
            hashlib.sha256(self.literature_paths()["corpus_manifest"].read_bytes()).hexdigest(),
        )
        decision.update(
            status="complete", novelty_decision_rating=4, impact_positioning_rating=3, decision_confidence_rating=3,
            narrowest_defensible_positioning="A bounded synthetic contribution.",
            what_would_change_the_decision="A closer synthetic prior method.",
        )
        decision_path.write_text(json.dumps(decision))
        report_path = fresh / "novelty-report.md"
        report = report_path.read_text()
        self.assertIn("- Literature assurance mode: linked", report)
        report = report.replace("Novelty decision rating (1-5):\n", "Novelty decision rating (1-5): 4\n")
        report = report.replace("Impact positioning rating (1-5):\n", "Impact positioning rating (1-5): 3\n")
        report = report.replace("Decision confidence rating (1-5):\n", "Decision confidence rating (1-5): 3\n")
        report = report.replace("- Narrowest defensible positioning:", "- Narrowest defensible positioning: A bounded synthetic contribution.")
        report = report.replace("- What would change the decision:", "- What would change the decision: A closer synthetic prior method.")
        report_path.write_text(report)
        self.run_cmd(
            str(NOVELTY_VALIDATE),
            "--decision", str(decision_path), "--report", str(report_path),
            "--prior-art-matrix", str(fresh / "prior-art-matrix.md"),
            "--search-log", str(fresh / "search-log.md"),
            "--assurance-profile", "linked",
        )

    def test_corpus_identity_fields_must_match(self) -> None:
        self.decision["literature_assurance"]["corpus_version"] = 99
        self.write_decision()
        cp = self.validate(expect=1)
        self.assertIn("corpus_version does not match", cp.stdout)


@unittest.skipUnless(SLR_PRESENT, "research-systematic-literature-review sibling not installed")
class ContextModeAndMigrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.context = self.root / "context"
        self.run_cmd(
            str(CONTEXT_SCRIPT), "init", "--out-dir", str(self.context),
            "--target-paper", "Synthetic widget ranking", "--domain", "machine learning",
            "--target-community", "Synthetic Venue",
        )
        for name in ("literature-context.md", "literature-context-search-log.md", "literature-context-evidence-table.md"):
            path = self.context / name
            path.write_text(path.read_text().replace("TODO", "synthetic entry"))
        decision_path = self.context / "literature-context-decision.json"
        context_decision = json.loads(decision_path.read_text())
        context_decision.update(
            contextualization_rating=4, impact_evidence_rating=3, coverage_confidence_rating=4,
            closest_prior_work=["Synthetic Work 1"], related_work_omissions=[],
            benchmark_context_gaps=[], limits_of_search=["one database"],
        )
        decision_path.write_text(json.dumps(context_decision))
        self.novelty = self.root / "novelty"
        self.run_cmd(str(NOVELTY_INIT), str(self.novelty), "--link-context", str(self.context))
        self.decision_path = self.novelty / "novelty-decision.json"
        self.report_path = self.novelty / "novelty-report.md"

    def tearDown(self) -> None:
        self.temp.cleanup()

    def run_cmd(self, *args: str, expect: int = 0) -> subprocess.CompletedProcess[str]:
        cp = subprocess.run([sys.executable, *args], text=True, capture_output=True)
        self.assertEqual(cp.returncode, expect, cp.stdout + cp.stderr)
        return cp

    def rate(self, rating: int, rows: int) -> None:
        matrix = self.novelty / "prior-art-matrix.md"
        filled = "".join(
            f"| Synthetic Work {index} | Synthetic Venue 2024 | scoring step | 2 | the objective | a shared loss |\n"
            for index in range(1, rows + 1)
        )
        matrix.write_text(matrix.read_text().replace("| | | | 1-5 | | |\n", filled))
        decision = json.loads(self.decision_path.read_text())
        decision.update(
            status="complete", novelty_decision_rating=rating, impact_positioning_rating=3,
            decision_confidence_rating=3,
            narrowest_defensible_positioning="A bounded synthetic contribution.",
            what_would_change_the_decision="A closer synthetic prior method.",
        )
        self.decision_path.write_text(json.dumps(decision))
        report = self.report_path.read_text()
        report = report.replace("Novelty decision rating (1-5):\n", f"Novelty decision rating (1-5): {rating}\n")
        report = report.replace("Impact positioning rating (1-5):\n", "Impact positioning rating (1-5): 3\n")
        report = report.replace("Decision confidence rating (1-5):\n", "Decision confidence rating (1-5): 3\n")
        report = report.replace("- Narrowest defensible positioning:", "- Narrowest defensible positioning: A bounded synthetic contribution.")
        report = report.replace("- What would change the decision:", "- What would change the decision: A closer synthetic prior method.")
        self.report_path.write_text(report)

    def validate(self, expect: int = 0) -> subprocess.CompletedProcess[str]:
        return self.run_cmd(
            str(NOVELTY_VALIDATE),
            "--decision", str(self.decision_path), "--report", str(self.report_path),
            "--prior-art-matrix", str(self.novelty / "prior-art-matrix.md"),
            "--search-log", str(self.novelty / "search-log.md"),
            expect=expect,
        )

    def test_context_mode_with_valid_context_passes_rating_four(self) -> None:
        self.rate(4, rows=3)
        cp = self.validate()
        self.assertIn("bound paper context was revalidated", cp.stdout)

    def test_context_mode_still_needs_prior_art_rows(self) -> None:
        self.rate(4, rows=1)
        cp = self.validate(expect=1)
        self.assertIn("needs at least 3 filled prior-art row(s)", cp.stdout)

    def test_context_edit_after_binding_fails_until_relinked(self) -> None:
        self.rate(4, rows=3)
        evidence = self.context / "literature-context-evidence-table.md"
        evidence.write_text(evidence.read_text() + "\n")
        cp = self.validate(expect=1)
        self.assertIn("does not match the bound file", cp.stdout)
        self.assertIn("link --context", cp.stdout)
        self.run_cmd(str(ASSURANCE), "link", "--decision", str(self.decision_path), "--context", str(self.context))
        self.validate()

    def test_context_with_placeholders_fails(self) -> None:
        self.rate(4, rows=3)
        context = self.context / "literature-context.md"
        context.write_text(context.read_text() + "\n- Reviewer constraints: TODO\n")
        self.run_cmd(str(ASSURANCE), "link", "--decision", str(self.decision_path), "--context", str(self.context))
        cp = self.validate(expect=1)
        self.assertIn("bound paper context fails validation", cp.stdout)

    def test_low_coverage_context_cannot_carry_rating_four(self) -> None:
        decision_path = self.context / "literature-context-decision.json"
        context_decision = json.loads(decision_path.read_text())
        context_decision["coverage_confidence_rating"] = 2
        decision_path.write_text(json.dumps(context_decision))
        self.run_cmd(str(ASSURANCE), "link", "--decision", str(self.decision_path), "--context", str(self.context))
        self.rate(4, rows=3)
        cp = self.validate(expect=1)
        self.assertIn("coverage_confidence_rating of at least 3", cp.stdout)
        self.rate_three_after_lowering()

    def rate_three_after_lowering(self) -> None:
        decision = json.loads(self.decision_path.read_text())
        decision["novelty_decision_rating"] = 3
        self.decision_path.write_text(json.dumps(decision))
        self.report_path.write_text(self.report_path.read_text().replace("Novelty decision rating (1-5): 4", "Novelty decision rating (1-5): 3"))
        self.validate()

    def write_pre_11(self, rating: int) -> Path:
        legacy = self.root / "legacy"
        legacy.mkdir()
        self.run_cmd(str(NOVELTY_INIT), str(legacy))
        log_one_search(legacy)
        decision = {
            "novelty_decision_rating": rating,
            "impact_positioning_rating": 4,
            "decision_confidence_rating": 3,
            "narrowest_defensible_positioning": "A bounded synthetic contribution.",
            "what_would_change_the_decision": "A closer synthetic prior method.",
            "top_kill_shot_objections": [],
            "literature_context_used": [],
            "paper_review_summary_used": "",
            "claims_to_qualify": [],
            "missing_prior_work": [],
            "review_findings_to_add": [],
        }
        (legacy / "novelty-decision.json").write_text(json.dumps(decision))
        report = legacy / "novelty-report.md"
        text = report.read_text()
        text = text.replace("Novelty decision rating (1-5):\n", f"Novelty decision rating (1-5): {rating}\n")
        text = text.replace("Impact positioning rating (1-5):\n", "Impact positioning rating (1-5): 4\n")
        text = text.replace("Decision confidence rating (1-5):\n", "Decision confidence rating (1-5): 3\n")
        text = text.replace("- Narrowest defensible positioning:", "- Narrowest defensible positioning: A bounded synthetic contribution.")
        text = text.replace("- What would change the decision:", "- What would change the decision: A closer synthetic prior method.")
        for label in ("Literature assurance mode", "Literature assurance verdict", "Unresolved high-priority novelty-critical questions"):
            text = "\n".join(line for line in text.splitlines() if not line.startswith(f"- {label}")) + "\n"
        report.write_text(text)
        return legacy

    def legacy_validate(self, legacy: Path, expect: int) -> subprocess.CompletedProcess[str]:
        return self.run_cmd(
            str(NOVELTY_VALIDATE),
            "--decision", str(legacy / "novelty-decision.json"), "--report", str(legacy / "novelty-report.md"),
            "--prior-art-matrix", str(legacy / "prior-art-matrix.md"),
            "--search-log", str(legacy / "search-log.md"),
            expect=expect,
        )

    def test_pre_11_decision_names_the_migrate_helper(self) -> None:
        legacy = self.write_pre_11(5)
        cp = self.legacy_validate(legacy, expect=1)
        self.assertIn("predates schema 1.1", cp.stdout)
        self.assertIn("novelty_assurance.py migrate", cp.stdout)

    def test_migration_caps_rating_and_records_original(self) -> None:
        legacy = self.write_pre_11(5)
        self.run_cmd(str(ASSURANCE), "migrate", "--decision", str(legacy / "novelty-decision.json"))
        decision = json.loads((legacy / "novelty-decision.json").read_text())
        self.assertEqual(decision["schema_version"], "1.1")
        self.assertEqual(decision["status"], "complete")
        self.assertEqual(decision["novelty_decision_rating"], 3)
        self.assertEqual(decision["impact_positioning_rating"], 4)
        self.assertEqual(decision["migration"]["original_novelty_decision_rating"], 5)
        self.assertEqual(decision["literature_assurance"]["mode"], "unlinked")
        self.assertIn("Novelty decision rating (1-5): 3", (legacy / "novelty-report.md").read_text())
        cp = self.legacy_validate(legacy, expect=1)
        self.assertIn("needs at least 2 filled prior-art row(s)", cp.stdout)
        self.assertNotIn("predates schema", cp.stdout)

    def test_migration_with_matrix_caps_to_rows_and_validates(self) -> None:
        legacy = self.write_pre_11(4)
        matrix = legacy / "prior-art-matrix.md"
        matrix.write_text(matrix.read_text().replace(
            "| | | | 1-5 | | |\n",
            "| Synthetic Work 1 | Synthetic Venue 2024 | scoring step | 2 | the objective | a shared loss |\n",
        ))
        self.run_cmd(
            str(ASSURANCE), "migrate", "--decision", str(legacy / "novelty-decision.json"),
            "--prior-art-matrix", str(matrix),
        )
        decision = json.loads((legacy / "novelty-decision.json").read_text())
        self.assertEqual(decision["novelty_decision_rating"], 2)
        self.legacy_validate(legacy, expect=0)

    def test_migration_never_raises_a_rating(self) -> None:
        for rating in (1, 2, 3):
            legacy = self.write_pre_11(rating)
            self.run_cmd(str(ASSURANCE), "migrate", "--decision", str(legacy / "novelty-decision.json"))
            decision = json.loads((legacy / "novelty-decision.json").read_text())
            self.assertEqual(decision["novelty_decision_rating"], rating)
            self.assertEqual(decision["migration"]["original_novelty_decision_rating"], rating)
            shutil.rmtree(legacy)

    def test_migrating_a_current_decision_is_refused(self) -> None:
        cp = self.run_cmd(str(ASSURANCE), "migrate", "--decision", str(self.decision_path), expect=1)
        self.assertIn("already schema 1.1", cp.stderr)


if __name__ == "__main__":
    unittest.main()
