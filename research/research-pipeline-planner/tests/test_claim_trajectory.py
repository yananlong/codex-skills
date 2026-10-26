#!/usr/bin/env python3
"""Regression tests for the shared decision vocabulary (D2) and claim trajectory (D1)."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from claim_trajectory import (  # noqa: E402
    REPAIR_ACTIONS,
    check_contribution_floor,
    check_repair,
    check_trajectory,
    narrowings_needing_review,
    parse_action_text,
)
from validate_research_commitment import validate_commitment  # noqa: E402

NARROWING = {
    "claim_id": "C1",
    "change_class": "scope_narrowing",
    "content_lost": "the claim no longer covers the second synthetic shift",
    "alternatives_considered": ["add_evidence: a third seed did not separate the hypotheses"],
    "restoring_evidence": "a shift benchmark with matched difficulty",
}


def committed(**extra):
    data = {
        "schema_version": "1.0", "paper_id": "paper-1", "identity_version": 1, "status": "committed",
        "main_question": "Does the synthetic estimator stay calibrated?",
        "central_object_or_phenomenon": "a synthetic estimator", "contribution_class": "method",
        "minimum_publishable_claim": "calibration holds on one shift",
        "primary_evidence_obligation": "a held-out shift", "intended_audience": "methods readers",
        "permitted_refinements": [], "pivot_triggers": ["fails on all shifts"],
        "kill_conditions": ["equivalent to a known estimator"], "successor_idea_policy": "park",
        "next_mandatory_evidence_artifact": "results/shift.json", "reconsideration_gate": "G1",
        "selection_history": [], "predecessor_failures": [], "last_change_class": "D2",
        "last_change_rationale": "narrowed after the shift audit",
    }
    data.update(extra)
    return data


class VocabularyTests(unittest.TestCase):
    def test_action_text_parses_with_or_without_backticks(self):
        self.assertEqual(parse_action_text("`add_evidence`: run a second seed"), ("add_evidence", "run a second seed"))
        self.assertEqual(parse_action_text("narrow - drop the second shift"), ("narrow", "drop the second shift"))
        self.assertEqual(parse_action_text("stop"), ("stop", ""))
        self.assertEqual(parse_action_text("rerun with more seeds")[0], None)

    def test_narrowing_is_listed_after_claim_preserving_repairs(self):
        self.assertLess(REPAIR_ACTIONS.index("add_evidence"), REPAIR_ACTIONS.index("narrow"))
        self.assertLess(REPAIR_ACTIONS.index("lower_assurance"), REPAIR_ACTIONS.index("narrow"))

    def test_repair_accepts_enum_and_warns_on_legacy_or_free_text(self):
        errors, warnings = [], []
        self.assertEqual(check_repair({"action": "sharpen_comparator", "note": "x"}, "f", errors, warnings), "sharpen_comparator")
        self.assertEqual(check_repair("drop", "f", errors, warnings), "stop")
        self.assertIsNone(check_repair("we will think about it", "f", errors, warnings))
        self.assertEqual(errors, [])
        self.assertEqual(len(warnings), 2)
        check_repair({"action": "smaller_claim"}, "f", errors, warnings)
        check_repair("", "f", errors, warnings)
        self.assertEqual(len(errors), 2)


class TrajectoryTests(unittest.TestCase):
    def test_content_losing_change_needs_loss_alternatives_and_restoring_evidence(self):
        errors: list[str] = []
        check_trajectory({"claim_id": "C1", "change_class": "scope_narrowing"}, "t", errors)
        joined = " ".join(errors)
        for field in ("content_lost", "alternatives_considered", "restoring_evidence"):
            self.assertIn(field, joined)
        errors = []
        check_trajectory(NARROWING, "t", errors)
        self.assertEqual(errors, [])

    def test_precision_needs_only_claim_and_class(self):
        errors: list[str] = []
        check_trajectory({"claim_id": "C1", "change_class": "precision"}, "t", errors)
        self.assertEqual(errors, [])

    def test_identity_drift_names_its_pivot_request(self):
        errors: list[str] = []
        record = dict(NARROWING, change_class="identity_drift")
        check_trajectory(record, "t", errors)
        self.assertTrue(any("pivot_request" in error for error in errors))
        errors = []
        check_trajectory(dict(record, pivot_request="PV-0001"), "t", errors)
        self.assertEqual(errors, [])

    def test_floor_must_be_able_to_fail(self):
        errors: list[str] = []
        check_contribution_floor({"statement": "a calibrated estimator under one shift"}, "f", errors)
        self.assertTrue(any("non_vacuity_outcome" in error for error in errors))


class CommitmentTests(unittest.TestCase):
    def test_floor_absent_from_a_committed_commitment_warns(self):
        warnings: list[str] = []
        self.assertEqual(validate_commitment(committed(), warnings), [])
        self.assertTrue(any("contribution_floor" in warning for warning in warnings))

    def test_floor_present_validates(self):
        floor = {
            "statement": "a calibrated estimator under one realistic shift",
            "non_vacuity_outcome": "calibration error above the baseline on the held-out shift",
            "invariants": ["the estimator stays model-agnostic"],
            "status": "unchecked",
        }
        warnings: list[str] = []
        self.assertEqual(validate_commitment(committed(contribution_floor=floor), warnings), [])
        self.assertFalse(any("contribution_floor" in warning for warning in warnings))

    def test_second_narrowing_requires_a_project_review(self):
        history = [
            {"decision": "narrow", "rationale": "first shift failed", "trajectory": NARROWING},
            {"decision": "narrow", "rationale": "second shift failed", "trajectory": NARROWING},
        ]
        errors = validate_commitment(committed(selection_history=history))
        self.assertTrue(any("narrowed 2 times" in error for error in errors), errors)
        self.assertEqual(narrowings_needing_review(history), {"C1": 2})

        review = {
            "decision": "project-review", "claim_id": "C1", "route_action": "continue",
            "rationale": "the retained claim still meets the floor",
        }
        self.assertEqual(validate_commitment(committed(selection_history=history + [review])), [])

        floor = {"statement": "s", "non_vacuity_outcome": "o"}
        errors = validate_commitment(committed(selection_history=history + [review], contribution_floor=floor))
        self.assertTrue(any("floor_status" in error for error in errors), errors)

        third = {"decision": "narrow", "rationale": "third", "trajectory": NARROWING}
        errors = validate_commitment(committed(selection_history=history + [review, third]))
        self.assertTrue(any("narrowed 3 times" in error for error in errors), errors)

    def test_project_review_route_action_is_closed(self):
        review = {"decision": "project-review", "claim_id": "C1", "route_action": "keep going", "rationale": "r"}
        errors = validate_commitment(committed(selection_history=[review]))
        self.assertTrue(any("route_action" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
