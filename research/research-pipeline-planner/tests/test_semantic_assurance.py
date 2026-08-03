#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import semantic_assurance as semantic


def commitment(
    paper_id: str = "paper-a",
    version: int = 1,
    *,
    main_question: str = "Does method A improve target Y?",
    central_object: str = "method A",
    contribution_class: str = "method",
    evidence_obligation: str = "Frozen held-out experiment",
    minimum_claim: str = "Method A improves Y in scope S.",
    last_change: str = "D0",
    status: str = "committed",
) -> dict:
    return {
        "schema_version": "1.0",
        "paper_id": paper_id,
        "identity_version": version,
        "status": status,
        "main_question": main_question,
        "central_object_or_phenomenon": central_object,
        "contribution_class": contribution_class,
        "minimum_publishable_claim": minimum_claim,
        "primary_evidence_obligation": evidence_obligation,
        "intended_audience": "ML researchers",
        "permitted_refinements": ["Narrow the benchmark scope"],
        "pivot_triggers": ["Primary experiment falsifies the route"],
        "kill_conditions": ["No measurable signal"],
        "successor_idea_policy": "park",
        "next_mandatory_evidence_artifact": "results/B1.json",
        "reconsideration_gate": "G1",
        "selection_history": [],
        "predecessor_failures": [],
        "last_change_class": last_change,
        "last_change_rationale": "Recorded transition",
    }


def transition(before_id: str, after_id: str, before: dict, after: dict, declared: str) -> dict:
    changes = semantic.exact_diff(before, after)
    floor = semantic.computed_drift_floor(before, after, changes)
    item = {
        "transition_id": f"CT-{before_id}-{after_id}",
        "from_snapshot_id": before_id,
        "to_snapshot_id": after_id,
        "before_digest": semantic.canonical_digest(before),
        "after_digest": semantic.canonical_digest(after),
        "declared_change_class": declared,
        "computed_change_class": floor,
        "computed_field_changes": changes,
        "trigger_id": None,
        "authorization": None,
        "switching_cost": "",
        "discarded_evidence": [],
        "successor_project_assessment": "",
    }
    if floor in {"D3", "D4"}:
        item.update(
            {
                "trigger_id": "PT-1",
                "switching_cost": "Prior artifacts require reassessment.",
                "successor_project_assessment": "A separate project was considered.",
                "authorization": {
                    "authorization_id": f"AUTH-{before_id}-{after_id}",
                    "decision": "authorize-D3" if floor == "D3" else "close-and-create-D4",
                    "before_digest": semantic.canonical_digest(before),
                    "after_digest": semantic.canonical_digest(after),
                    "rationale": "The deterministic drift floor requires explicit authorization.",
                    "self_review": True,
                },
            }
        )
    if floor == "D4":
        closure = {
            "paper_id": before["paper_id"],
            "status": "closed",
            "closure_rationale": "The old route was closed before successor initialization.",
        }
        closure["closure_digest"] = semantic.canonical_digest(closure)
        item["old_lineage_closure"] = closure
    return item


def valid_transition_pack() -> tuple[dict, dict]:
    before = commitment()
    after = commitment(version=2, main_question="Does method A improve target Y under shift Z?", last_change="D3")
    history = {
        "schema_version": "1.0",
        "snapshots": [
            {"snapshot_id": "S1", "commitment": before},
            {"snapshot_id": "S2", "commitment": after},
        ],
    }
    ledger = {"schema_version": "1.0", "transitions": [transition("S1", "S2", before, after, "D3")]}
    return history, ledger


def valid_literature_pack() -> tuple[dict, dict, str, str, dict]:
    records = [
        {"record_id": "R1", "title": "Foundational work"},
        {"record_id": "R2", "title": "Closest recent work"},
        {"record_id": "R3", "title": "Critical competing work"},
        {"record_id": "R4", "title": "Negative evidence"},
    ]
    questions = []
    basis = []
    for index, perspective in enumerate(sorted(semantic.REQUIRED_PERSPECTIVES), 1):
        question_id = f"CQ-{index:02d}"
        questions.append(
            {
                "question_id": question_id,
                "perspective": perspective,
                "priority": "high" if perspective in semantic.DEFAULT_CRITICAL_PERSPECTIVES else "medium",
                "critical_for_novelty": perspective in semantic.DEFAULT_CRITICAL_PERSPECTIVES,
                "status": "answered",
                "search_run_ids": [f"RUN-{index:02d}"],
                "record_ids": ["R1"],
            }
        )
        basis.append(
            {
                "perspective": perspective,
                "applicability": "required",
                "question_ids": [question_id],
                "rationale": "Required by the review profile.",
            }
        )
    challenge = {
        "schema_version": "1.0",
        "mode": "withheld",
        "custodian": "separate challenge curator",
        "challenge_records": [
            {"record_id": "R2", "importance": 2.0},
            {"record_id": "R3", "importance": 1.0},
        ],
        "initially_missed_record_ids": [],
        "recovered_record_ids": ["R2", "R3"],
        "critical_paper_recall": 1.0,
        "importance_weighted_recall": 1.0,
        "search_repairs": [],
    }
    manifest = {
        "schema_version": "1.1",
        "review_profile": "bounded-systematic",
        "records": records,
        "seed_ids": ["R1", "R2", "R3"],
        "coverage_questions": questions,
        "post_freeze_amendments": [],
        "semantic_assurance": {
            "schema_version": "1.0",
            "coverage_basis": basis,
            "seed_classifications": [
                {"record_id": "R1", "classes": ["foundational"]},
                {"record_id": "R2", "classes": ["closest-recent"]},
                {"record_id": "R3", "classes": ["competing-or-critical"]},
            ],
            "challenge_evaluation": {"mode": "withheld", "challenge_digest": semantic.canonical_digest(challenge)},
            "criticality_decisions": [],
            "saturation_evidence": [],
            "narrow_topic_exception": None,
        },
    }
    novelty = {
        "novelty_decision_rating": 4,
        "top_kill_shot_objections": ["R3 may already subsume the proposed contribution."],
        "what_would_change_the_decision": "A theorem in R3 covering the exact scope would lower the rating.",
        "missing_prior_work": [],
    }
    critical_ids = [
        q["question_id"] for q in questions if q["priority"] == "high" and q["critical_for_novelty"]
    ]
    prior_art = (
        "# Prior-Art Matrix\n"
        "| Record ID | Work | Overlap | Threat | Surviving distinction | Coverage question IDs |\n"
        "| --- | --- | --- | --- | --- | --- |\n"
        f"| R3 | Critical competing work | Same problem and close method | kill-shot | Different frozen decision target | {', '.join(critical_ids)} |\n"
    )
    all_questions = ", ".join(q["question_id"] for q in questions)
    search_log = (
        "# Novelty Search Log\n"
        "| Run ID | Round | Query or delegation | Source | Corpus record IDs | Coverage question IDs |\n"
        "| --- | --- | --- | --- | --- | --- |\n"
        f"| RUN-01 | 1 | Direct terminology and foundational ancestry | database-a | R1, R2 | {all_questions} |\n"
        f"| RUN-02 | 1 | Competing terminology and negative evidence | database-b | R3, R4 | {all_questions} |\n"
        f"| RUN-03 | 2 | Citation and author-cluster repair | citation-search | R1, R2, R3, R4 | {all_questions} |\n"
    )
    return manifest, novelty, prior_art, search_log, challenge


def scope(scope_id: str = "S1", population: str = "held-out cases") -> dict:
    return {
        "scope_id": scope_id,
        "population": population,
        "environment": "frozen evaluator v1",
        "intervention": "method A",
        "comparator": "baseline B",
        "outcomes": ["accuracy", "failure rate"],
        "time_or_version": "2026-08 freeze",
        "exclusions": [],
    }


def make_run(
    run_id: str,
    outcome: str,
    *,
    evidence_class: str = "confirmatory",
    technical_validity: str = "valid",
    exclusion_class: str | None = None,
) -> tuple[dict, dict]:
    run = {
        "run_id": run_id,
        "semantic_assurance": {
            "claim_id": "C1",
            "scope_id": "S1",
            "eligibility_rule_id": "ER1",
            "technical_validity": technical_validity,
            "outcome_class": outcome,
            "exclusion_class": exclusion_class,
            "complete_outcome_accounting": True,
            "hidden_truth_access": "blinded",
            "material_deviations": [],
        },
    }
    item = {
        "work_item_id": f"WI-{run_id}",
        "status": "complete",
        "semantic_assurance": {
            "evidence_class": evidence_class,
            "claim_frozen_before_outcome": True,
            "decision_rule_frozen_before_outcome": True,
            "selection_rule_frozen_before_outcome": True,
            "outcome_inspected_before_freeze": False,
        },
        "episodes": [{"experiment_run": run}],
    }
    source = {
        "run_id": run_id,
        "claim_id": "C1",
        "scope_id": "S1",
        "eligibility_rule_id": "ER1",
        "technical_validity": technical_validity,
        "outcome_class": outcome,
    }
    return item, source


def valid_evidence_pack(include_adverse: bool = False) -> tuple[dict, dict, dict]:
    item_positive, source_positive = make_run("RUN-P", "positive")
    items = [item_positive]
    sources = [source_positive]
    dispositions = []
    limitations = []
    if include_adverse:
        item_negative, source_negative = make_run("RUN-N", "negative")
        items.append(item_negative)
        sources.append(source_negative)
        dispositions.append(
            {
                "run_id": "RUN-N",
                "rationale": "The adverse result narrows the population claim.",
                "manuscript_consequence": "qualify",
            }
        )
        limitations.append("One same-scope run was adverse and is reported explicitly.")
    work_items = {"items": items}
    audit = {
        "scope_registry": [scope()],
        "eligibility_rules": [
            {
                "rule_id": "ER1",
                "frozen_before_outcome": True,
                "description": "Include all same-scope runs completing measurement under the frozen protocol.",
            }
        ],
        "audits": [
            {
                "audit_id": "A1",
                "claim_id": "C1",
                "scope_id": "S1",
                "attained_assurance_class": "confirmatory",
                "verdict": "supports_confirmatory_claim",
                "source_runs": sources,
                "run_selection": {"excluded_runs": []},
                "adverse_evidence_dispositions": dispositions,
                "limitations": limitations,
            }
        ],
    }
    paper = {
        "scope_registry": [scope()],
        "claims": [
            {
                "paper_claim_id": "PC1",
                "scope_id": "S1",
                "evidence_mode": "empirical",
                "manuscript_action": "qualify" if include_adverse else "assert",
                "audit_ids": ["A1"],
                "audit_exclusions": [],
                "limitations": limitations.copy(),
            }
        ],
    }
    return audit, paper, work_items


class CommitmentTransitionTests(unittest.TestCase):
    def test_exact_d3_transition_passes(self) -> None:
        history, ledger = valid_transition_pack()
        self.assertEqual(semantic.validate_commitment_transitions(history, ledger), [])

    def test_declared_d3_above_floor_still_requires_d3_version_and_authorization(self) -> None:
        before = commitment()
        after = commitment(minimum_claim="Narrower bounded claim.", last_change="D3")
        history = {"schema_version": "1.0", "snapshots": [
            {"snapshot_id": "S1", "commitment": before},
            {"snapshot_id": "S2", "commitment": after},
        ]}
        item = transition("S1", "S2", before, after, "D3")
        item["authorization"] = None
        errors = semantic.validate_commitment_transitions(history, {"schema_version": "1.0", "transitions": [item]})
        self.assertTrue(any("D3 must keep paper_id and increment identity_version" in error for error in errors))
        self.assertTrue(any("authorization must be an object" in error for error in errors))

    def test_self_labeled_d2_cannot_hide_d3(self) -> None:
        history, ledger = valid_transition_pack()
        ledger["transitions"][0]["declared_change_class"] = "D2"
        history["snapshots"][1]["commitment"]["last_change_class"] = "D2"
        errors = semantic.validate_commitment_transitions(history, ledger)
        self.assertTrue(any("weaker than computed drift floor D3" in error for error in errors))

    def test_authorization_cannot_be_reused(self) -> None:
        a = commitment()
        b = commitment(version=2, main_question="New question", last_change="D3")
        c = commitment(version=3, main_question="Another new question", last_change="D3")
        history = {"schema_version": "1.0", "snapshots": [
            {"snapshot_id": "S1", "commitment": a},
            {"snapshot_id": "S2", "commitment": b},
            {"snapshot_id": "S3", "commitment": c},
        ]}
        t1 = transition("S1", "S2", a, b, "D3")
        t2 = transition("S2", "S3", b, c, "D3")
        t2["authorization"]["authorization_id"] = t1["authorization"]["authorization_id"]
        errors = semantic.validate_commitment_transitions(history, {"schema_version": "1.0", "transitions": [t1, t2]})
        self.assertTrue(any("is reused" in error for error in errors))

    def test_before_digest_mismatch_fails(self) -> None:
        history, ledger = valid_transition_pack()
        ledger["transitions"][0]["before_digest"] = "0" * 64
        errors = semantic.validate_commitment_transitions(history, ledger)
        self.assertTrue(any("before_digest" in error for error in errors))

    def test_d3_requires_monotonic_version(self) -> None:
        history, ledger = valid_transition_pack()
        history["snapshots"][1]["commitment"]["identity_version"] = 4
        t = transition("S1", "S2", history["snapshots"][0]["commitment"], history["snapshots"][1]["commitment"], "D3")
        errors = semantic.validate_commitment_transitions(history, {"schema_version": "1.0", "transitions": [t]})
        self.assertTrue(any("increment identity_version by one" in error for error in errors))

    def test_d4_requires_old_lineage_closure(self) -> None:
        before = commitment()
        after = commitment(paper_id="paper-b", version=1, main_question="Successor question", last_change="D4")
        history = {"schema_version": "1.0", "snapshots": [
            {"snapshot_id": "S1", "commitment": before},
            {"snapshot_id": "S2", "commitment": after},
        ]}
        item = transition("S1", "S2", before, after, "D4")
        item.pop("old_lineage_closure")
        errors = semantic.validate_commitment_transitions(history, {"schema_version": "1.0", "transitions": [item]})
        self.assertTrue(any("old_lineage_closure is required" in error for error in errors))

    def test_exact_d4_passes(self) -> None:
        before = commitment()
        after = commitment(paper_id="paper-b", version=1, main_question="Successor question", last_change="D4")
        history = {"schema_version": "1.0", "snapshots": [
            {"snapshot_id": "S1", "commitment": before},
            {"snapshot_id": "S2", "commitment": after},
        ]}
        ledger = {"schema_version": "1.0", "transitions": [transition("S1", "S2", before, after, "D4")]}
        self.assertEqual(semantic.validate_commitment_transitions(history, ledger), [])

    def test_active_old_identity_work_item_fails(self) -> None:
        history, ledger = valid_transition_pack()
        work_items = {"items": [{"work_item_id": "WI-old", "status": "running", "paper_id": "paper-a", "identity_version": 1}]}
        errors = semantic.validate_commitment_transitions(history, ledger, work_items)
        self.assertTrue(any("stale paper identity" in error for error in errors))


class LiteratureSemanticTests(unittest.TestCase):
    def test_valid_strong_novelty_pack_passes(self) -> None:
        values = valid_literature_pack()
        self.assertEqual(semantic.validate_literature_semantics(*values), [])

    def test_one_seed_one_paper_cannot_authorize_rating_four(self) -> None:
        manifest, novelty, prior, search, challenge = valid_literature_pack()
        manifest["records"] = manifest["records"][:1]
        manifest["seed_ids"] = ["R1"]
        manifest["semantic_assurance"]["seed_classifications"] = [{"record_id": "R1", "classes": ["foundational"]}]
        errors = semantic.validate_literature_semantics(manifest, novelty, prior, search, challenge)
        self.assertTrue(any("at least three declared seeds" in error for error in errors))

    def test_one_query_search_cannot_authorize_rating_four(self) -> None:
        manifest, novelty, prior, search, challenge = valid_literature_pack()
        lines = search.splitlines()
        one_row = "\n".join(lines[:3] + [lines[3]]) + "\n"
        errors = semantic.validate_literature_semantics(manifest, novelty, prior, one_row, challenge)
        self.assertTrue(any("at least three search runs" in error for error in errors))

    def test_required_perspective_cannot_be_omitted(self) -> None:
        manifest, novelty, prior, search, challenge = valid_literature_pack()
        manifest["semantic_assurance"]["coverage_basis"].pop()
        errors = semantic.validate_literature_semantics(manifest, novelty, prior, search, challenge)
        self.assertTrue(any("omits required perspectives" in error for error in errors))

    def test_saturation_after_one_round_fails(self) -> None:
        manifest, novelty, prior, search, challenge = valid_literature_pack()
        question = manifest["coverage_questions"][0]
        question["status"] = "saturated"
        manifest["semantic_assurance"]["saturation_evidence"] = [
            {"question_id": question["question_id"], "mode": "rounds", "rounds": [{"run_id": question["search_run_ids"][0], "included_yield": 1}]}
        ]
        errors = semantic.validate_literature_semantics(manifest, novelty, prior, search, challenge)
        self.assertTrue(any("at least two search rounds" in error for error in errors))

    def test_criticality_downgrade_requires_decision(self) -> None:
        manifest, novelty, prior, search, challenge = valid_literature_pack()
        question = next(
            item for item in manifest["coverage_questions"]
            if item["perspective"] in semantic.DEFAULT_CRITICAL_PERSPECTIVES
        )
        question["priority"] = "medium"
        question["critical_for_novelty"] = False
        errors = semantic.validate_literature_semantics(manifest, novelty, prior, search, challenge)
        self.assertTrue(any("without a recorded decision" in error for error in errors))

    def test_empty_prior_art_matrix_fails(self) -> None:
        manifest, novelty, _, search, challenge = valid_literature_pack()
        errors = semantic.validate_literature_semantics(manifest, novelty, "# Prior-Art Matrix\n", search, challenge)
        self.assertTrue(any("requires at least one substantive row" in error for error in errors))

    def test_title_only_novelty_search_log_fails(self) -> None:
        manifest, novelty, prior, _, challenge = valid_literature_pack()
        errors = semantic.validate_literature_semantics(manifest, novelty, prior, "# Novelty Search Log\n", challenge)
        self.assertTrue(any("requires substantive query" in error for error in errors))

    def test_rating_four_requires_kill_shot_objection(self) -> None:
        manifest, novelty, prior, search, challenge = valid_literature_pack()
        novelty["top_kill_shot_objections"] = []
        errors = semantic.validate_literature_semantics(manifest, novelty, prior, search, challenge)
        self.assertTrue(any("kill-shot objection" in error for error in errors))

    def test_missed_challenge_requires_repair(self) -> None:
        manifest, novelty, prior, search, challenge = valid_literature_pack()
        challenge["initially_missed_record_ids"] = ["R3"]
        manifest["semantic_assurance"]["challenge_evaluation"]["challenge_digest"] = semantic.canonical_digest(challenge)
        errors = semantic.validate_literature_semantics(manifest, novelty, prior, search, challenge)
        self.assertTrue(any("require search repair" in error for error in errors))

    def test_missed_challenge_with_repair_passes(self) -> None:
        manifest, novelty, prior, search, challenge = valid_literature_pack()
        challenge["initially_missed_record_ids"] = ["R3"]
        challenge["search_repairs"] = [{"repair_id": "SR-1", "recovered_record_ids": ["R3"]}]
        manifest["semantic_assurance"]["challenge_evaluation"]["challenge_digest"] = semantic.canonical_digest(challenge)
        self.assertEqual(semantic.validate_literature_semantics(manifest, novelty, prior, search, challenge), [])

    def test_independent_search_review_cannot_be_self_review(self) -> None:
        manifest, novelty, prior, search, challenge = valid_literature_pack()
        challenge.update(
            {
                "mode": "independent-review",
                "independence": {
                    "self_review": True,
                    "dimensions": ["context", "evaluation", "advancement_authority"],
                },
            }
        )
        manifest["semantic_assurance"]["challenge_evaluation"]["challenge_digest"] = semantic.canonical_digest(challenge)
        errors = semantic.validate_literature_semantics(manifest, novelty, prior, search, challenge)
        self.assertTrue(any("cannot be self-review" in error for error in errors))


class EvidenceSemanticTests(unittest.TestCase):
    def test_valid_confirmatory_chain_passes(self) -> None:
        self.assertEqual(semantic.validate_evidence_semantics(*valid_evidence_pack()), [])

    def test_valid_adverse_same_scope_run_is_included_and_disposed(self) -> None:
        self.assertEqual(semantic.validate_evidence_semantics(*valid_evidence_pack(include_adverse=True)), [])

    def test_adverse_same_scope_run_forbids_unqualified_paper_assertion(self) -> None:
        audit, paper, work_items = valid_evidence_pack(include_adverse=True)
        paper["claims"][0]["manuscript_action"] = "assert"
        errors = semantic.validate_evidence_semantics(audit, paper, work_items)
        self.assertTrue(any("forbids an unqualified manuscript assertion" in error for error in errors))

    def test_adverse_same_scope_run_cannot_be_excluded(self) -> None:
        audit, paper, work_items = valid_evidence_pack()
        negative_item, _ = make_run("RUN-N", "negative")
        work_items["items"].append(negative_item)
        audit["audits"][0]["run_selection"]["excluded_runs"] = [
            {
                "run_id": "RUN-N",
                "eligibility_rule_id": "ER1",
                "exclusion_class": "protocol-ineligible-configuration",
                "evidence_paths": ["failures/RUN-N.json"],
                "rationale": "Attempted outcome-informed exclusion.",
            }
        ]
        negative_item["episodes"][0]["experiment_run"]["semantic_assurance"]["exclusion_class"] = "protocol-ineligible-configuration"
        errors = semantic.validate_evidence_semantics(audit, paper, work_items)
        self.assertTrue(any("scientific outcomes cannot be excluded" in error for error in errors))

    def test_technical_failure_can_be_controlled_exclusion(self) -> None:
        audit, paper, work_items = valid_evidence_pack()
        failed_item, _ = make_run(
            "RUN-F", "technical-failure", technical_validity="invalid-before-measurement", exclusion_class="executor-failure-before-measurement"
        )
        work_items["items"].append(failed_item)
        audit["audits"][0]["run_selection"]["excluded_runs"] = [
            {
                "run_id": "RUN-F",
                "eligibility_rule_id": "ER1",
                "exclusion_class": "executor-failure-before-measurement",
                "evidence_paths": ["failures/RUN-F.json"],
                "rationale": "Executor failed before any outcome was measured.",
            }
        ]
        self.assertEqual(semantic.validate_evidence_semantics(audit, paper, work_items), [])

    def test_exploratory_source_cannot_be_promoted_to_confirmatory(self) -> None:
        audit, paper, work_items = valid_evidence_pack()
        work_items["items"][0]["semantic_assurance"]["evidence_class"] = "exploratory"
        errors = semantic.validate_evidence_semantics(audit, paper, work_items)
        self.assertTrue(any("exceeds source-derived cap" in error for error in errors))

    def test_outcome_inspection_before_freeze_caps_assurance(self) -> None:
        audit, paper, work_items = valid_evidence_pack()
        work_items["items"][0]["semantic_assurance"]["outcome_inspected_before_freeze"] = True
        errors = semantic.validate_evidence_semantics(audit, paper, work_items)
        self.assertTrue(any("exceeds source-derived cap" in error for error in errors))

    def test_adverse_run_requires_explicit_disposition(self) -> None:
        audit, paper, work_items = valid_evidence_pack(include_adverse=True)
        audit["audits"][0]["adverse_evidence_dispositions"] = []
        errors = semantic.validate_evidence_semantics(audit, paper, work_items)
        self.assertTrue(any("omits explicit disposition" in error for error in errors))

    def test_self_review_cannot_attain_independent_assurance(self) -> None:
        audit, paper, work_items = valid_evidence_pack()
        audit["audits"][0]["attained_assurance_class"] = "independently_verified"
        work_items["items"][0]["semantic_assurance"].update(
            {
                "evidence_class": "independently_verified",
                "independence": {
                    "self_review": True,
                    "dimensions": ["context", "data", "implementation", "evaluation", "advancement_authority"],
                },
            }
        )
        errors = semantic.validate_evidence_semantics(audit, paper, work_items)
        self.assertTrue(any("exceeds source-derived cap" in error for error in errors))

    def test_materially_independent_source_can_attain_independent_assurance(self) -> None:
        audit, paper, work_items = valid_evidence_pack()
        audit["audits"][0]["attained_assurance_class"] = "independently_verified"
        work_items["items"][0]["semantic_assurance"].update(
            {
                "evidence_class": "independently_verified",
                "independence": {
                    "self_review": False,
                    "dimensions": ["context", "data", "implementation", "evaluation", "advancement_authority"],
                },
            }
        )
        self.assertEqual(semantic.validate_evidence_semantics(audit, paper, work_items), [])

    def test_same_semantic_scope_cannot_use_two_ids(self) -> None:
        audit, paper, work_items = valid_evidence_pack()
        duplicate = scope("S2")
        audit["scope_registry"].append(duplicate)
        errors = semantic.validate_evidence_semantics(audit, paper, work_items)
        self.assertTrue(any("semantically identical scopes use different IDs" in error for error in errors))

    def test_asserted_claim_requires_exact_audit_scope(self) -> None:
        audit, paper, work_items = valid_evidence_pack()
        paper["scope_registry"].append(scope("S2", population="deployment cohort"))
        paper["claims"][0]["scope_id"] = "S2"
        errors = semantic.validate_evidence_semantics(audit, paper, work_items)
        self.assertTrue(any("must use exact same structured scope" in error for error in errors))

    def test_scope_exclusion_requires_exact_changed_dimensions(self) -> None:
        audit, paper, work_items = valid_evidence_pack()
        second = copy.deepcopy(audit["audits"][0])
        second["audit_id"] = "A2"
        second["scope_id"] = "S2"
        audit["audits"].append(second)
        audit["scope_registry"].append(scope("S2", population="deployment cohort"))
        paper["scope_registry"].append(scope("S2", population="deployment cohort"))
        paper["claims"][0]["audit_exclusions"] = [
            {"audit_id": "A2", "differing_dimensions": ["environment"], "rationale": "Different cohort."}
        ]
        errors = semantic.validate_evidence_semantics(audit, paper, work_items)
        self.assertTrue(any("must equal exact structured scope differences" in error for error in errors))


class RealFixtureTests(unittest.TestCase):
    @property
    def fixture_root(self) -> Path:
        return Path(__file__).resolve().parent / "fixtures" / "pr15"

    def test_real_fixture_index_declares_required_cases(self) -> None:
        fixture = json.loads((self.fixture_root / "real-project-regressions.json").read_text(encoding="utf-8"))
        self.assertEqual(semantic.validate_fixture_index(fixture), [])

    def test_normality_milieu_locked_history_classifies_d3_then_d2(self) -> None:
        fixture = json.loads((self.fixture_root / "normality-milieu-transitions.json").read_text(encoding="utf-8"))
        self.assertEqual(semantic.validate_commitment_transitions(fixture["history"], fixture["ledger"]), [])
        self.assertEqual(
            [entry["computed_change_class"] for entry in fixture["ledger"]["transitions"]],
            ["D3", "D2"],
        )

    def test_llm_triangulation_locked_history_preserves_repairs_and_detects_successor(self) -> None:
        fixture = json.loads((self.fixture_root / "llm-triangulation-transitions.json").read_text(encoding="utf-8"))
        self.assertEqual(semantic.validate_commitment_transitions(fixture["history"], fixture["ledger"]), [])
        self.assertEqual(
            [entry["computed_change_class"] for entry in fixture["ledger"]["transitions"]],
            ["D1", "D2", "D4"],
        )


if __name__ == "__main__":
    unittest.main()
