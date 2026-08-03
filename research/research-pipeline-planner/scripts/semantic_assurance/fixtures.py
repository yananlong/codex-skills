from __future__ import annotations

import math
from typing import Any

from .common import DRIFT_RANK, meaningful


def validate_fixture_index(fixtures: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(fixtures, dict) or fixtures.get("schema_version") != "1.0":
        return ["real-project fixture index must be a schema_version 1.0 object"]
    projects = fixtures.get("project_histories")
    domains = fixtures.get("literature_challenges")
    evidence = fixtures.get("evidence_selection")
    if not isinstance(projects, list) or len(projects) < 2:
        errors.append("fixture index requires at least two real-project histories")
    else:
        names = {entry.get("project") for entry in projects if isinstance(entry, dict)}
        if not {"Normality Milieu", "LLM Triangulation"}.issubset(names):
            errors.append("fixtures must include Normality Milieu and LLM Triangulation")
        for index, entry in enumerate(projects, 1):
            label = f"project_histories[{index}]"
            if not isinstance(entry, dict):
                errors.append(f"{label} must be an object")
                continue
            if not meaningful(entry.get("source_basis")):
                errors.append(f"{label}.source_basis must be substantive")
            transitions = entry.get("expected_transitions")
            if not isinstance(transitions, list) or not transitions:
                errors.append(f"{label}.expected_transitions must be non-empty")
            elif any(item.get("expected_class") not in DRIFT_RANK for item in transitions if isinstance(item, dict)):
                errors.append(f"{label} contains invalid expected drift class")
    if not isinstance(domains, list) or len(domains) < 3:
        errors.append("fixture index requires at least three literature challenge domains")
    else:
        for index, entry in enumerate(domains, 1):
            label = f"literature_challenges[{index}]"
            if not isinstance(entry, dict) or not meaningful(entry.get("domain")):
                errors.append(f"{label} must name a domain")
                continue
            if not isinstance(entry.get("visible_seed_ids"), list) or not entry.get("visible_seed_ids"):
                errors.append(f"{label}.visible_seed_ids must be non-empty")
            if not isinstance(entry.get("withheld_critical_ids"), list) or not entry.get("withheld_critical_ids"):
                errors.append(f"{label}.withheld_critical_ids must be non-empty")
            if not isinstance(entry.get("expected_repair"), bool):
                errors.append(f"{label}.expected_repair must be boolean")
            withheld = set(map(str, entry.get("withheld_critical_ids", [])))
            initial = set(map(str, entry.get("initially_recovered_ids", [])))
            final = set(map(str, entry.get("post_repair_recovered_ids", [])))
            if not initial.issubset(withheld) or not final.issubset(withheld):
                errors.append(f"{label} recovered IDs must belong to the withheld set")
            baseline_recall = 1.0 if not withheld else len(initial) / len(withheld)
            final_recall = 1.0 if not withheld else len(final) / len(withheld)
            if not math.isclose(float(entry.get("baseline_recall", -1)), baseline_recall, rel_tol=0, abs_tol=1e-12):
                errors.append(f"{label}.baseline_recall is inconsistent")
            if not math.isclose(float(entry.get("post_repair_recall", -1)), final_recall, rel_tol=0, abs_tol=1e-12):
                errors.append(f"{label}.post_repair_recall is inconsistent")
            if final != withheld:
                errors.append(f"{label} does not recover the complete locked critical set")
            repairs = entry.get("search_repairs")
            if entry.get("expected_repair") is True:
                if not isinstance(repairs, list) or not repairs or final_recall <= baseline_recall:
                    errors.append(f"{label} expected a documented recall-improving search repair")
            elif final_recall != baseline_recall:
                errors.append(f"{label} reports an unexpected recall change without a planned repair")
    if not isinstance(evidence, dict):
        errors.append("fixture index requires evidence_selection object")
    else:
        outcomes = set(map(str, evidence.get("outcome_classes", [])))
        if not {"positive", "negative", "null", "technical-failure"}.issubset(outcomes):
            errors.append("evidence-selection fixture must include positive, negative, null, and technical-failure outcomes")
        if evidence.get("adverse_run_exclusion_expected") is not False:
            errors.append("evidence-selection fixture must expect adverse valid runs to remain included")
    return errors
