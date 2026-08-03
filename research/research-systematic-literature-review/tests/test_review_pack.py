#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INIT = ROOT / "scripts" / "init_review_pack.py"
VALIDATE = ROOT / "scripts" / "validate_review_pack.py"


class ReviewPackTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.slug = "example"
        self.run_cmd(
            str(INIT),
            "--topic", "Example",
            "--domain", "Machine learning",
            "--review-profile", "bounded-systematic",
            "--out-dir", str(self.root),
            "--intended-decision", "Decide whether to commit the paper route",
            "--domain-adapter", "methodological",
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def run_cmd(self, *args: str, expect: int = 0):
        cp = subprocess.run([sys.executable, *args], text=True, capture_output=True, check=False)
        self.assertEqual(cp.returncode, expect, msg=f"stdout:\n{cp.stdout}\nstderr:\n{cp.stderr}")
        return cp

    def paths(self) -> dict[str, Path]:
        return {
            "protocol": self.root / f"{self.slug}.protocol.md",
            "search": self.root / f"{self.slug}.search-log.md",
            "recall": self.root / f"{self.slug}.recall-audit.md",
            "manifest": self.root / f"{self.slug}.corpus-manifest.json",
            "screening": self.root / f"{self.slug}.screening-log.md",
            "evidence": self.root / f"{self.slug}.evidence-table.md",
            "report": self.root / f"{self.slug}.review.md",
        }

    def validate(self, expect: int = 0):
        p = self.paths()
        return self.run_cmd(
            str(VALIDATE),
            "--protocol", str(p["protocol"]),
            "--search-log", str(p["search"]),
            "--recall-audit", str(p["recall"]),
            "--corpus-manifest", str(p["manifest"]),
            "--screening-log", str(p["screening"]),
            "--evidence", str(p["evidence"]),
            "--report", str(p["report"]),
            expect=expect,
        )

    def make_valid_bounded(self) -> None:
        p = self.paths()
        today = date.today().isoformat()
        search = p["search"].read_text()
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
            "benchmark-dataset-tracing", "prior-review-harvesting", "grey-literature",
            "zotero-cross-check",
        ):
            search = search.replace(
                f"| {channel} | required | TODO | 0 | 0 | 0 | 0 |",
                f"| {channel} | performed | completed within boundary | 1 | 1 | 0 | 0 |",
            )
        p["search"].write_text(search)

        recall = p["recall"].read_text()
        recall = recall.replace("TODO yes / no", "no, unavailable because no separate custodian was available")
        recall = recall.replace("TODO", "completed")
        recall = recall.replace("- Verdict: insufficient", "- Verdict: adequate-for-bounded-claims")
        p["recall"].write_text(recall)

        screening = p["screening"].read_text()
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
        p["screening"].write_text(screening)

        evidence = p["evidence"].read_text().replace(
            "| | | | 0 | | | published/preprint | | empirical/theoretical/method/benchmark/review | Broad context implied by the topic and domain unless explicitly narrowed | | | | low/moderate/high | | |",
            "| P1 | Doe et al. 2024 | https://example.org/p1 | 2024 | Venue | 10.1/example | published | | method | ML | analysis | positive result | none | high | direct | |",
        )
        p["evidence"].write_text(evidence)

        manifest = json.loads(p["manifest"].read_text())
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
        question = manifest["coverage_questions"][0]
        question.update(
            status="answered",
            record_ids=["P1"],
            answer_summary="The included work supports the bounded methodological conclusion.",
            residual_gap="External settings remain outside the reviewed boundary.",
            closure_reason="The declared bounded question is answered by the frozen corpus.",
        )
        p["manifest"].write_text(json.dumps(manifest))

        report = p["report"].read_text().replace("TODO", "completed")
        report = report.replace(
            "- Assurance verdict: insufficient",
            "- Assurance verdict: adequate-for-bounded-claims",
        )
        p["report"].write_text(report)

    def test_fresh_systematic_scaffold_fails(self):
        cp = self.validate(expect=1)
        self.assertIn("source query", cp.stdout)
        self.assertIn("canonical_citation", cp.stdout)

    def test_valid_bounded_pack_passes(self):
        self.make_valid_bounded()
        cp = self.validate()
        self.assertIn("adequate-for-bounded-claims", cp.stdout)

    def test_placeholder_seed_does_not_satisfy_recall_assurance(self):
        self.make_valid_bounded()
        search = self.paths()["search"]
        search.write_text(search.read_text().replace("Doe et al. 2024", "TODO", 1))
        cp = self.validate(expect=1)
        self.assertIn("canonical_citation", cp.stdout)

    def test_unfinished_channel_blocks_adequate_verdict(self):
        self.make_valid_bounded()
        search = self.paths()["search"]
        search.write_text(
            search.read_text().replace(
                "| forward-citation | performed | completed within boundary | 1 | 1 | 0 | 0 |",
                "| forward-citation | required | pending | 0 | 0 | 0 | 0 |",
            )
        )
        cp = self.validate(expect=1)
        self.assertIn("unfinished", cp.stdout)

    def test_missing_publication_url_fails(self):
        self.make_valid_bounded()
        evidence = self.paths()["evidence"]
        evidence.write_text(evidence.read_text().replace("https://example.org/p1", "", 1))
        cp = self.validate(expect=1)
        self.assertIn("publication_url", cp.stdout)

    def test_comprehensive_verdict_requires_independent_search_review(self):
        self.make_valid_bounded()
        p = self.paths()
        p["protocol"].write_text(p["protocol"].read_text().replace("bounded-systematic", "comprehensive-systematic"))
        p["recall"].write_text(
            p["recall"].read_text()
            .replace("bounded-systematic", "comprehensive-systematic")
            .replace("adequate-for-bounded-claims", "adequate-for-comprehensive-claim")
        )
        manifest = json.loads(p["manifest"].read_text())
        manifest["review_profile"] = "comprehensive-systematic"
        manifest["assurance_verdict"] = "adequate-for-comprehensive-claim"
        p["manifest"].write_text(json.dumps(manifest))
        p["report"].write_text(
            p["report"].read_text().replace(
                "adequate-for-bounded-claims", "adequate-for-comprehensive-claim"
            )
        )
        cp = self.validate(expect=1)
        self.assertIn("performed search-strategy review", cp.stdout)

    def test_missing_reciprocal_question_link_fails(self):
        self.make_valid_bounded()
        search = self.paths()["search"]
        search.write_text(search.read_text().replace("| CQ-001 | example method |", "| CQ-002 | example method |"))
        cp = self.validate(expect=1)
        self.assertIn("unknown coverage questions: CQ-002", cp.stdout)
        self.assertIn("does not reciprocally reference coverage question CQ-001", cp.stdout)

    def test_question_cannot_reference_unknown_record(self):
        self.make_valid_bounded()
        manifest_path = self.paths()["manifest"]
        manifest = json.loads(manifest_path.read_text())
        manifest["coverage_questions"][0]["record_ids"] = ["P404"]
        manifest_path.write_text(json.dumps(manifest))
        cp = self.validate(expect=1)
        self.assertIn("references unknown corpus records: P404", cp.stdout)

    def test_record_must_reciprocally_reference_question(self):
        self.make_valid_bounded()
        manifest_path = self.paths()["manifest"]
        manifest = json.loads(manifest_path.read_text())
        manifest["records"][0]["question_ids"] = []
        manifest_path.write_text(json.dumps(manifest))
        cp = self.validate(expect=1)
        self.assertIn("must reference at least one coverage question", cp.stdout)
        self.assertIn("does not reciprocally reference coverage question CQ-001", cp.stdout)

    def test_question_must_reciprocally_reference_record(self):
        self.make_valid_bounded()
        manifest_path = self.paths()["manifest"]
        manifest = json.loads(manifest_path.read_text())
        manifest["coverage_questions"][0]["record_ids"] = []
        manifest_path.write_text(json.dumps(manifest))
        cp = self.validate(expect=1)
        self.assertIn("does not reciprocally reference corpus record P1", cp.stdout)

    def test_blocked_critical_question_requires_mitigation_and_scope_consequence(self):
        self.make_valid_bounded()
        manifest_path = self.paths()["manifest"]
        manifest = json.loads(manifest_path.read_text())
        question = manifest["coverage_questions"][0]
        question.update(
            critical_for_novelty=True,
            status="blocked",
            record_ids=[],
            answer_summary="",
            residual_gap="Access to the benchmark archive is unavailable.",
            closure_reason="The archive could not be accessed.",
            blocked_mitigation="",
            scope_consequence="",
        )
        manifest_path.write_text(json.dumps(manifest))
        cp = self.validate(expect=1)
        self.assertIn("blocked_mitigation must be substantive", cp.stdout)
        self.assertIn("scope_consequence must be substantive", cp.stdout)

    def test_post_freeze_question_requires_reciprocal_amendment(self):
        self.make_valid_bounded()
        manifest_path = self.paths()["manifest"]
        manifest = json.loads(manifest_path.read_text())
        question = manifest["coverage_questions"][0]
        question["created_after_freeze"] = True
        question["amendment_id"] = "AMD-1"
        manifest_path.write_text(json.dumps(manifest))
        cp = self.validate(expect=1)
        self.assertIn("references unknown amendment_id AMD-1", cp.stdout)

    def test_coverage_question_amendment_must_be_reciprocal(self):
        self.make_valid_bounded()
        manifest_path = self.paths()["manifest"]
        manifest = json.loads(manifest_path.read_text())
        manifest["post_freeze_amendments"].append({
            "amendment_id": "AMD-1",
            "kind": "coverage-question",
            "question_id": "CQ-001",
            "reason": "A material question was added after freeze.",
            "effect_on_conclusions": "No effect after follow-up search.",
        })
        manifest_path.write_text(json.dumps(manifest))
        cp = self.validate(expect=1)
        self.assertIn("does not reciprocally reference amendment AMD-1", cp.stdout)

    def test_comprehensive_verdict_rejects_unresolved_high_priority_novelty_question(self):
        self.make_valid_bounded()
        p = self.paths()
        p["protocol"].write_text(p["protocol"].read_text().replace("bounded-systematic", "comprehensive-systematic"))
        p["recall"].write_text(
            p["recall"].read_text()
            .replace("bounded-systematic", "comprehensive-systematic")
            .replace("adequate-for-bounded-claims", "adequate-for-comprehensive-claim")
        )
        manifest = json.loads(p["manifest"].read_text())
        manifest["review_profile"] = "comprehensive-systematic"
        manifest["assurance_verdict"] = "adequate-for-comprehensive-claim"
        manifest["search_strategy_review"] = {
            "performed": True,
            "independence": "independent reviewer",
            "notes": "A separate reviewer challenged the strategy.",
        }
        question = manifest["coverage_questions"][0]
        question.update(critical_for_novelty=True, status="searching", record_ids=[], answer_summary="", closure_reason="")
        p["manifest"].write_text(json.dumps(manifest))
        p["report"].write_text(p["report"].read_text().replace("adequate-for-bounded-claims", "adequate-for-comprehensive-claim"))
        cp = self.validate(expect=1)
        self.assertIn("comprehensive assurance cannot retain unresolved", cp.stdout)

    def test_rapid_scan_does_not_inherit_systematic_closure_gate(self):
        self.make_valid_bounded()
        p = self.paths()
        for key in ("protocol", "recall"):
            p[key].write_text(p[key].read_text().replace("bounded-systematic", "rapid-scan"))
        manifest = json.loads(p["manifest"].read_text())
        manifest["review_profile"] = "rapid-scan"
        manifest["assurance_verdict"] = "insufficient"
        manifest["coverage_questions"][0].update(
            critical_for_novelty=True,
            status="searching",
            answer_summary="",
            closure_reason="",
        )
        p["manifest"].write_text(json.dumps(manifest))
        p["recall"].write_text(p["recall"].read_text().replace("adequate-for-bounded-claims", "insufficient"))
        p["report"].write_text(p["report"].read_text().replace("adequate-for-bounded-claims", "insufficient"))
        cp = self.validate()
        self.assertIn("rapid-scan", cp.stdout)


if __name__ == "__main__":
    unittest.main()
