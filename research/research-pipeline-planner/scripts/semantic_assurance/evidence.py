from __future__ import annotations

from typing import Any

from .common import ADVERSE_OUTCOMES, ALLOWED_EXCLUSION_CLASSES, ASSURANCE_RANK, SCOPE_DIMENSIONS, canonical_digest, meaningful, validate_id


def scope_signature(scope: dict[str, Any]) -> str:
    normalized = {field: scope.get(field) for field in sorted(SCOPE_DIMENSIONS)}
    return canonical_digest(normalized)


def validate_scope_registry(value: Any, label: str, errors: list[str]) -> dict[str, dict[str, Any]]:
    if not isinstance(value, list):
        errors.append(f"{label} must be a list")
        return {}
    registry: dict[str, dict[str, Any]] = {}
    signatures: dict[str, str] = {}
    for index, scope in enumerate(value, 1):
        item_label = f"{label}[{index}]"
        if not isinstance(scope, dict):
            errors.append(f"{item_label} must be an object")
            continue
        scope_id = validate_id(scope.get("scope_id"), f"{item_label}.scope_id", errors)
        for field in SCOPE_DIMENSIONS - {"outcomes", "exclusions"}:
            if not meaningful(scope.get(field)):
                errors.append(f"{item_label}.{field} must be substantive")
        for field in ("outcomes", "exclusions"):
            if not isinstance(scope.get(field), list) or any(not meaningful(value) for value in scope.get(field, [])):
                errors.append(f"{item_label}.{field} must be a list of substantive strings")
        signature = scope_signature(scope)
        if scope_id in registry:
            errors.append(f"duplicate scope_id {scope_id}")
        registry[scope_id] = scope
        if signature in signatures and signatures[signature] != scope_id:
            errors.append(f"semantically identical scopes use different IDs: {signatures[signature]} and {scope_id}")
        signatures[signature] = scope_id
    return registry


def work_item_runs(work_items: Any) -> dict[str, tuple[dict[str, Any], dict[str, Any], dict[str, Any]]]:
    result: dict[str, tuple[dict[str, Any], dict[str, Any], dict[str, Any]]] = {}
    if not isinstance(work_items, dict):
        return result
    for item in work_items.get("items", []):
        if not isinstance(item, dict):
            continue
        for episode in item.get("episodes", []):
            if not isinstance(episode, dict):
                continue
            run = episode.get("experiment_run")
            if isinstance(run, dict) and meaningful(run.get("run_id")):
                result[str(run["run_id"])] = (item, episode, run)
    return result


def derived_run_assurance(item: dict[str, Any], run: dict[str, Any]) -> str:
    binding_semantic = item.get("semantic_assurance") if isinstance(item.get("semantic_assurance"), dict) else {}
    run_semantic = run.get("semantic_assurance") if isinstance(run.get("semantic_assurance"), dict) else {}
    evidence_class = str(binding_semantic.get("evidence_class", "exploratory"))
    rank = ASSURANCE_RANK.get(evidence_class, ASSURANCE_RANK["exploratory"])
    confirmatory_conditions = (
        binding_semantic.get("claim_frozen_before_outcome") is True
        and binding_semantic.get("decision_rule_frozen_before_outcome") is True
        and binding_semantic.get("selection_rule_frozen_before_outcome") is True
        and binding_semantic.get("outcome_inspected_before_freeze") is False
        and run_semantic.get("complete_outcome_accounting") is True
        and run_semantic.get("hidden_truth_access") in {"none", "blinded"}
        and not run_semantic.get("material_deviations")
    )
    if not confirmatory_conditions:
        rank = min(rank, ASSURANCE_RANK["exploratory"])
    if rank >= ASSURANCE_RANK["independently_verified"]:
        independence = binding_semantic.get("independence")
        if not isinstance(independence, dict) or independence.get("self_review") is not False:
            rank = min(rank, ASSURANCE_RANK["confirmatory"])
        else:
            dimensions = set(map(str, independence.get("dimensions", [])))
            required = {"context", "data", "implementation", "evaluation", "advancement_authority"}
            if not required.issubset(dimensions):
                rank = min(rank, ASSURANCE_RANK["confirmatory"])
    if rank >= ASSURANCE_RANK["operational_high_stakes"]:
        if not meaningful(binding_semantic.get("threat_model")) or not isinstance(binding_semantic.get("harms"), list) or not binding_semantic.get("harms"):
            rank = min(rank, ASSURANCE_RANK["independently_verified"])
    for name, value in ASSURANCE_RANK.items():
        if value == rank:
            return name
    return "exploratory"


def validate_evidence_semantics(audit_data: Any, paper_data: Any, work_items: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(audit_data, dict):
        return ["results audit must be an object"]
    if not isinstance(paper_data, dict):
        return ["paper bindings must be an object"]
    runs = work_item_runs(work_items)
    seen_run_ids: set[str] = set()
    if isinstance(work_items, dict):
        for item in work_items.get("items", []):
            if not isinstance(item, dict):
                continue
            for episode in item.get("episodes", []):
                run = episode.get("experiment_run") if isinstance(episode, dict) else None
                if not isinstance(run, dict) or not meaningful(run.get("run_id")):
                    continue
                run_id = str(run["run_id"])
                if run_id in seen_run_ids:
                    errors.append(f"duplicate experiment run_id {run_id}")
                seen_run_ids.add(run_id)
    audit_scopes = validate_scope_registry(audit_data.get("scope_registry"), "results-audit.scope_registry", errors)
    paper_scopes = validate_scope_registry(paper_data.get("scope_registry"), "paper-bindings.scope_registry", errors)
    for scope_id, scope in audit_scopes.items():
        if scope_id in paper_scopes and scope_signature(scope) != scope_signature(paper_scopes[scope_id]):
            errors.append(f"scope {scope_id} differs between results audit and paper bindings")

    rules = audit_data.get("eligibility_rules")
    if not isinstance(rules, list):
        errors.append("results-audit.eligibility_rules must be a list")
        rules = []
    rules_by_id: dict[str, dict[str, Any]] = {}
    for index, rule in enumerate(rules, 1):
        label = f"results-audit.eligibility_rules[{index}]"
        if not isinstance(rule, dict):
            errors.append(f"{label} must be an object")
            continue
        rule_id = validate_id(rule.get("rule_id"), f"{label}.rule_id", errors)
        if rule.get("frozen_before_outcome") is not True:
            errors.append(f"{label}.frozen_before_outcome must be true")
        if not meaningful(rule.get("description")):
            errors.append(f"{label}.description must be substantive")
        if rule_id in rules_by_id:
            errors.append(f"duplicate eligibility rule {rule_id}")
        rules_by_id[rule_id] = rule

    audits = audit_data.get("audits") if isinstance(audit_data.get("audits"), list) else []
    audits_by_id: dict[str, dict[str, Any]] = {}
    for index, audit in enumerate(audits, 1):
        label = f"results-audit.audits[{index}]"
        if not isinstance(audit, dict):
            errors.append(f"{label} must be an object")
            continue
        audit_id = validate_id(audit.get("audit_id"), f"{label}.audit_id", errors)
        audits_by_id[audit_id] = audit
        scope_id = validate_id(audit.get("scope_id"), f"{label}.scope_id", errors)
        if scope_id not in audit_scopes:
            errors.append(f"{label} references unknown scope_id {scope_id}")
        included = {
            str(entry.get("run_id")): entry
            for entry in audit.get("source_runs", [])
            if isinstance(entry, dict) and meaningful(entry.get("run_id"))
        }
        selection = audit.get("run_selection") if isinstance(audit.get("run_selection"), dict) else {}
        excluded = selection.get("excluded_runs") if isinstance(selection.get("excluded_runs"), list) else []
        excluded_ids: set[str] = set()
        for ex_index, exclusion in enumerate(excluded, 1):
            ex_label = f"{label}.run_selection.excluded_runs[{ex_index}]"
            if not isinstance(exclusion, dict):
                errors.append(f"{ex_label} must be an object")
                continue
            run_id = validate_id(exclusion.get("run_id"), f"{ex_label}.run_id", errors)
            excluded_ids.add(run_id)
            rule_id = validate_id(exclusion.get("eligibility_rule_id"), f"{ex_label}.eligibility_rule_id", errors)
            if rule_id not in rules_by_id:
                errors.append(f"{ex_label} references unknown eligibility rule {rule_id}")
            exclusion_class = exclusion.get("exclusion_class")
            if exclusion_class not in ALLOWED_EXCLUSION_CLASSES:
                errors.append(f"{ex_label}.exclusion_class must be a controlled pre-outcome exclusion class")
            evidence_paths = exclusion.get("evidence_paths")
            if not isinstance(evidence_paths, list) or not evidence_paths or any(not meaningful(value) for value in evidence_paths):
                errors.append(f"{ex_label}.evidence_paths must be non-empty")
            if not meaningful(exclusion.get("rationale")):
                errors.append(f"{ex_label}.rationale must be substantive")
            found = runs.get(run_id)
            if found is None:
                errors.append(f"{ex_label} references unknown work-item run {run_id}")
                continue
            _, _, run = found
            semantic = run.get("semantic_assurance") if isinstance(run.get("semantic_assurance"), dict) else {}
            if semantic.get("eligibility_rule_id") != rule_id:
                errors.append(f"{ex_label} eligibility rule disagrees with source run")
            if semantic.get("exclusion_class") != exclusion_class:
                errors.append(f"{ex_label} exclusion class disagrees with source run")
            if semantic.get("technical_validity") == "valid" or semantic.get("outcome_class") in ADVERSE_OUTCOMES | {"positive"}:
                errors.append(f"{ex_label}: technically valid scientific outcomes cannot be excluded")

        derived_caps: list[str] = []
        adverse_ids: set[str] = set()
        for run_id, source in included.items():
            found = runs.get(run_id)
            if found is None:
                errors.append(f"{label} includes unknown work-item run {run_id}")
                continue
            item, _, run = found
            semantic = run.get("semantic_assurance") if isinstance(run.get("semantic_assurance"), dict) else {}
            for field in ("claim_id", "scope_id", "eligibility_rule_id", "technical_validity", "outcome_class"):
                if source.get(field) != semantic.get(field):
                    errors.append(f"{label} source run {run_id} field {field} disagrees with work-items projection")
            if source.get("scope_id") != scope_id:
                errors.append(f"{label} source run {run_id} is not in audit scope {scope_id}")
            if semantic.get("technical_validity") != "valid":
                errors.append(f"{label} source run {run_id} is technically invalid and cannot support an audited scientific verdict")
            if semantic.get("outcome_class") not in {"positive", "negative", "null", "contradictory"}:
                errors.append(f"{label} source run {run_id} lacks a scientific outcome class")
            if source.get("eligibility_rule_id") not in rules_by_id:
                errors.append(f"{label} source run {run_id} uses unknown eligibility rule")
            cap = derived_run_assurance(item, run)
            derived_caps.append(cap)
            if semantic.get("technical_validity") == "valid" and semantic.get("outcome_class") in ADVERSE_OUTCOMES:
                adverse_ids.add(run_id)
        attained = str(audit.get("attained_assurance_class", "none"))
        if attained not in ASSURANCE_RANK:
            errors.append(f"{label}.attained_assurance_class is unrecognized")
        cap_rank = min((ASSURANCE_RANK.get(value, 0) for value in derived_caps), default=0)
        if ASSURANCE_RANK.get(attained, 0) > cap_rank:
            errors.append(f"{label}: attained assurance {attained} exceeds source-derived cap")

        dispositions = audit.get("adverse_evidence_dispositions")
        if not isinstance(dispositions, list):
            dispositions = []
        disposition_ids = {
            str(entry.get("run_id"))
            for entry in dispositions
            if isinstance(entry, dict)
            and meaningful(entry.get("run_id"))
            and meaningful(entry.get("rationale"))
            and entry.get("manuscript_consequence") in {"qualify", "limitation", "contradict", "no-net-effect"}
        }
        missing_adverse = adverse_ids - disposition_ids
        if missing_adverse:
            errors.append(f"{label} omits explicit disposition for adverse same-scope runs: {', '.join(sorted(missing_adverse))}")
        if adverse_ids and audit.get("verdict") in {
            "supports_confirmatory_claim",
            "independently_verified",
            "supports_operational_high_stakes_claim",
        }:
            limitations = audit.get("limitations")
            if not isinstance(limitations, list) or not limitations:
                errors.append(f"{label}: positive verdict with adverse evidence requires explicit limitations")

        claim_id = audit.get("claim_id")
        eligible_for_claim = {
            run_id
            for run_id, (_, _, run) in runs.items()
            if isinstance(run.get("semantic_assurance"), dict)
            and run["semantic_assurance"].get("claim_id") == claim_id
            and run["semantic_assurance"].get("eligibility_rule_id") in rules_by_id
            and run["semantic_assurance"].get("scope_id") == scope_id
        }
        omitted = eligible_for_claim - set(included) - excluded_ids
        if omitted:
            errors.append(f"{label} omits semantically eligible runs: {', '.join(sorted(omitted))}")

    claims = paper_data.get("claims") if isinstance(paper_data.get("claims"), list) else []
    for index, claim in enumerate(claims, 1):
        label = f"paper-bindings.claims[{index}]"
        if not isinstance(claim, dict):
            errors.append(f"{label} must be an object")
            continue
        scope_id = validate_id(claim.get("scope_id"), f"{label}.scope_id", errors)
        if scope_id not in paper_scopes:
            errors.append(f"{label} references unknown scope_id {scope_id}")
        linked_ids = {str(value) for value in claim.get("audit_ids", []) if meaningful(value)}
        if claim.get("evidence_mode") in {"empirical", "mixed"} and claim.get("manuscript_action") == "assert":
            for audit_id in linked_ids:
                audit = audits_by_id.get(audit_id)
                if audit is None:
                    errors.append(f"{label} references unknown audit {audit_id}")
                elif audit.get("scope_id") != scope_id:
                    errors.append(f"{label}: asserted empirical claim must use exact same structured scope as audit {audit_id}")
                else:
                    dispositions = audit.get("adverse_evidence_dispositions") if isinstance(audit.get("adverse_evidence_dispositions"), list) else []
                    requires_qualification = any(
                        isinstance(entry, dict) and entry.get("manuscript_consequence") in {"qualify", "limitation", "contradict"}
                        for entry in dispositions
                    )
                    if requires_qualification:
                        errors.append(f"{label}: adverse evidence in audit {audit_id} forbids an unqualified manuscript assertion")
        exclusions = claim.get("audit_exclusions") if isinstance(claim.get("audit_exclusions"), list) else []
        for ex_index, exclusion in enumerate(exclusions, 1):
            ex_label = f"{label}.audit_exclusions[{ex_index}]"
            if not isinstance(exclusion, dict):
                errors.append(f"{ex_label} must be an object")
                continue
            audit_id = str(exclusion.get("audit_id", ""))
            audit = audits_by_id.get(audit_id)
            if audit is None:
                errors.append(f"{ex_label} references unknown audit {audit_id}")
                continue
            audit_scope_id = str(audit.get("scope_id", ""))
            claim_scope = paper_scopes.get(scope_id)
            audit_scope = audit_scopes.get(audit_scope_id)
            if claim_scope is None or audit_scope is None:
                continue
            changed = {
                field
                for field in SCOPE_DIMENSIONS
                if claim_scope.get(field) != audit_scope.get(field)
            }
            declared_changed = set(map(str, exclusion.get("differing_dimensions", [])))
            if not changed:
                errors.append(f"{ex_label}: cannot exclude semantically identical scope audit {audit_id}")
            if declared_changed != changed:
                errors.append(f"{ex_label}.differing_dimensions must equal exact structured scope differences")
            if not meaningful(exclusion.get("rationale")):
                errors.append(f"{ex_label}.rationale must be substantive")
    return errors
