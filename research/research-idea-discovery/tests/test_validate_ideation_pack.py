#!/usr/bin/env python3
"""Regression tests for the ideation pack validator, including route-level re-ideation (D9)."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
INIT = SCRIPTS / "init_ideation_pack.py"
VALIDATE = SCRIPTS / "validate_ideation_pack.py"


def idea(idea_id: str = "IDEA-001", **extra) -> dict:
    record = {
        "idea_id": idea_id,
        "title": "Synthetic calibration probe",
        "summary": "A synthetic probe for estimator calibration under shift.",
        "hypothesis": "Calibration error grows with shift magnitude.",
        "contribution_type": "diagnostic",
        "source_basis": ["synthetic note"],
        "assumptions": ["shift magnitude is measurable"],
        "novelty_questions": ["Has a synthetic probe like this been published?"],
        "minimum_validation": "Run the probe on two synthetic shifts.",
        "disconfirming_evidence": "Calibration error is flat across shifts.",
        "kill_criteria": "No measurable trend on either shift.",
        "closest_work": ["Synthetic Work 1"],
        "differentiation": "Targets shift magnitude rather than shift type.",
        "scores": {"clarity": 4, "novelty_signal": 3, "feasibility": 4, "testability": 4, "significance": 3},
        "risk": "medium",
        "estimated_effort": "weeks",
        "status": "selected",
        "rationale": "Cheapest test of the live route.",
        "blocking_questions": ["Which shifts count?"],
    }
    record.update(extra)
    return record


ROUTE = {
    "evidence_class": "exploratory",
    "predecessor_failures": [{"failure_id": "F1", "disposition": "targeted"}],
    "switching_cost": {"discarded": "the second benchmark run", "new_burden": "a shift-magnitude metric"},
    "identity_change_class": "D2",
    "next_skill": "research-novelty-review",
}


class IdeationValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.pack = Path(self.temp.name) / "ideation"
        subprocess.run([sys.executable, str(INIT), str(self.pack)], check=True, capture_output=True)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def write(self, ideas: list[dict], **decision) -> None:
        (self.pack / "idea-scores.json").write_text(json.dumps({"topic": "synthetic", "scoring_scale": "1-5", "ideas": ideas}))
        data = {
            "ideation_mode": "fresh",
            "decision": "proceed_to_novelty_review",
            "selected_idea_ids": [record["idea_id"] for record in ideas if record.get("status") == "selected"],
            "confidence": "medium",
            "novelty_check_status": "quick_signal_only",
            "rationale": "synthetic",
            "next_skill": "research-novelty-review",
            "required_handoffs": ["selected-idea.md"],
            "limits": ["synthetic"],
        }
        data.update(decision)
        for key in [key for key, value in data.items() if value is ...]:
            del data[key]
        (self.pack / "ideation-decision.json").write_text(json.dumps(data))

    def validate(self, expect: int) -> subprocess.CompletedProcess[str]:
        cp = subprocess.run([sys.executable, str(VALIDATE), str(self.pack)], text=True, capture_output=True)
        self.assertEqual(cp.returncode, expect, cp.stdout + cp.stderr)
        return cp

    def test_initialized_pack_passes_with_allow_empty(self) -> None:
        cp = subprocess.run([sys.executable, str(VALIDATE), str(self.pack), "--allow-empty"], text=True, capture_output=True)
        self.assertEqual(cp.returncode, 0, cp.stdout)
        self.assertNotIn("warning", cp.stdout)

    def test_fresh_ideation_needs_no_route_fields(self) -> None:
        self.write([idea()])
        cp = self.validate(0)
        self.assertIn("fresh ideation", cp.stdout)

    def test_fresh_ideation_still_checks_route_fields_when_present(self) -> None:
        self.write([idea(evidence_class="anecdotal")])
        cp = self.validate(1)
        self.assertIn("evidence_class must be one of", cp.stdout)

    def test_legacy_pack_without_mode_warns(self) -> None:
        self.write([idea()], ideation_mode=...)
        cp = self.validate(0)
        self.assertIn("warning: ideation-decision.json has no ideation_mode", cp.stdout)

    def test_route_level_requires_the_failing_route_and_every_field(self) -> None:
        self.write([idea()], ideation_mode="route_level")
        cp = self.validate(1)
        self.assertIn("must name the failing_route", cp.stdout)
        self.assertIn("must record evidence_class, predecessor_failures, switching_cost", cp.stdout)
        self.write([idea(**ROUTE)], ideation_mode="route_level", failing_route="the second-shift benchmark route")
        self.validate(0)

    def test_rejected_ideas_do_not_need_route_fields(self) -> None:
        self.write(
            [idea(**ROUTE), idea("IDEA-002", status="rejected")],
            ideation_mode="route_level", failing_route="the second-shift benchmark route",
        )
        self.validate(0)

    def test_resolved_failure_needs_evidence(self) -> None:
        route = dict(ROUTE, predecessor_failures=[{"failure_id": "F1", "disposition": "resolved"}])
        self.write([idea(**route)], ideation_mode="route_level", failing_route="route")
        cp = self.validate(1)
        self.assertIn("names the evidence that resolved it", cp.stdout)

    def test_switching_cost_names_both_sides(self) -> None:
        route = dict(ROUTE, switching_cost={"discarded": "the second run"})
        self.write([idea(**route)], ideation_mode="route_level", failing_route="route")
        cp = self.validate(1)
        self.assertIn("what work is discarded and what new burden appears", cp.stdout)

    def test_d3_idea_goes_to_the_planner_as_a_pivot_request(self) -> None:
        route = dict(ROUTE, identity_change_class="D3")
        self.write([idea(**route)], ideation_mode="route_level", failing_route="route")
        cp = self.validate(1)
        self.assertIn("pivot_request_needed: true", cp.stdout)
        self.assertIn("goes to research-pipeline-planner", cp.stdout)
        self.assertIn("set next_skill to research-pipeline-planner", cp.stdout)
        route = dict(ROUTE, identity_change_class="D3", next_skill="research-pipeline-planner", pivot_request_needed=True)
        self.write(
            [idea(**route)], ideation_mode="route_level", failing_route="route",
            decision="request_pivot", next_skill="research-pipeline-planner",
        )
        self.validate(0)

    def test_request_pivot_needs_a_pivot_idea(self) -> None:
        self.write([idea(**ROUTE)], ideation_mode="route_level", failing_route="route",
                   decision="request_pivot", next_skill="research-pipeline-planner")
        cp = self.validate(1)
        self.assertIn("request_pivot requires a selected idea", cp.stdout)

    def test_idea_may_route_to_paper_review_or_stop(self) -> None:
        for next_skill in ("research-paper-review", "stop"):
            self.write([idea(**dict(ROUTE, next_skill=next_skill))], ideation_mode="route_level", failing_route="route")
            self.validate(0)
        self.write([idea(**dict(ROUTE, next_skill="research-something-else"))], ideation_mode="route_level", failing_route="route")
        cp = self.validate(1)
        self.assertIn("next_skill must be one of", cp.stdout)


if __name__ == "__main__":
    unittest.main()
