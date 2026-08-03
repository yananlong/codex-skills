from __future__ import annotations

from typing import Any

from .common import ACTIVE_WORK_STATUSES, D2_FIELDS, D3_FIELDS, DRIFT_RANK, IGNORED_DIFF_FIELDS, canonical_digest, meaningful, validate_id


def exact_diff(before: dict[str, Any], after: dict[str, Any]) -> dict[str, list[Any]]:
    fields = (set(before) | set(after)) - IGNORED_DIFF_FIELDS
    return {
        field: [before.get(field), after.get(field)]
        for field in sorted(fields)
        if before.get(field) != after.get(field)
    }


def computed_drift_floor(before: dict[str, Any], after: dict[str, Any], changes: dict[str, list[Any]]) -> str:
    if before.get("paper_id") != after.get("paper_id"):
        return "D4"
    if D3_FIELDS.intersection(changes):
        return "D3"
    if D2_FIELDS.intersection(changes):
        return "D2"
    if changes:
        return "D1"
    return "D0"


def validate_commitment_transitions(history: Any, ledger: Any, work_items: Any | None = None) -> list[str]:
    errors: list[str] = []
    if not isinstance(history, dict) or history.get("schema_version") != "1.0":
        return ["commitment history must be a schema_version 1.0 object"]
    if not isinstance(ledger, dict) or ledger.get("schema_version") != "1.0":
        return ["commitment transition ledger must be a schema_version 1.0 object"]
    snapshots_raw = history.get("snapshots")
    transitions = ledger.get("transitions")
    if not isinstance(snapshots_raw, list) or len(snapshots_raw) < 2:
        return ["commitment history requires at least two snapshots"]
    if not isinstance(transitions, list):
        return ["commitment transition ledger transitions must be a list"]

    snapshots: dict[str, dict[str, Any]] = {}
    ordered_ids: list[str] = []
    for index, entry in enumerate(snapshots_raw, 1):
        label = f"history.snapshots[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{label} must be an object")
            continue
        snapshot_id = validate_id(entry.get("snapshot_id"), f"{label}.snapshot_id", errors)
        commitment = entry.get("commitment")
        if not isinstance(commitment, dict):
            errors.append(f"{label}.commitment must be an object")
            continue
        if snapshot_id in snapshots:
            errors.append(f"duplicate snapshot_id {snapshot_id}")
        snapshots[snapshot_id] = commitment
        ordered_ids.append(snapshot_id)

    expected_pairs = list(zip(ordered_ids, ordered_ids[1:]))
    seen_transition_ids: set[str] = set()
    seen_pairs: set[tuple[str, str]] = set()
    used_authorizations: set[str] = set()
    for index, transition in enumerate(transitions, 1):
        label = f"ledger.transitions[{index}]"
        if not isinstance(transition, dict):
            errors.append(f"{label} must be an object")
            continue
        transition_id = validate_id(transition.get("transition_id"), f"{label}.transition_id", errors)
        if transition_id in seen_transition_ids:
            errors.append(f"duplicate transition_id {transition_id}")
        seen_transition_ids.add(transition_id)
        before_id = validate_id(transition.get("from_snapshot_id"), f"{label}.from_snapshot_id", errors)
        after_id = validate_id(transition.get("to_snapshot_id"), f"{label}.to_snapshot_id", errors)
        pair = (before_id, after_id)
        if pair in seen_pairs:
            errors.append(f"duplicate commitment transition {before_id}->{after_id}")
        seen_pairs.add(pair)
        before = snapshots.get(before_id)
        after = snapshots.get(after_id)
        if before is None or after is None:
            errors.append(f"{label} references unknown snapshot")
            continue

        before_digest = canonical_digest(before)
        after_digest = canonical_digest(after)
        if transition.get("before_digest") != before_digest:
            errors.append(f"{label}.before_digest does not match canonical before snapshot")
        if transition.get("after_digest") != after_digest:
            errors.append(f"{label}.after_digest does not match canonical after snapshot")
        changes = exact_diff(before, after)
        if transition.get("computed_field_changes") != changes:
            errors.append(f"{label}.computed_field_changes is not the exact deterministic field diff")
        floor = computed_drift_floor(before, after, changes)
        if transition.get("computed_change_class") != floor:
            errors.append(f"{label}.computed_change_class must equal deterministic floor {floor}")
        declared = transition.get("declared_change_class")
        if declared not in DRIFT_RANK:
            errors.append(f"{label}.declared_change_class must be D0-D4")
            declared = "D0"
        if DRIFT_RANK[declared] < DRIFT_RANK[floor]:
            errors.append(f"{label}: declared {declared} is weaker than computed drift floor {floor}")
        if after.get("last_change_class") != declared:
            errors.append(f"{label}: after commitment last_change_class must equal declared class")

        before_version = before.get("identity_version")
        after_version = after.get("identity_version")
        if not isinstance(before_version, int) or not isinstance(after_version, int):
            errors.append(f"{label}: identity versions must be integers")
        elif declared in {"D0", "D1", "D2"} and after_version != before_version:
            errors.append(f"{label}: D0-D2 transition must preserve identity_version")
        elif declared == "D3" and (before.get("paper_id") != after.get("paper_id") or after_version != before_version + 1):
            errors.append(f"{label}: D3 must keep paper_id and increment identity_version by one")
        elif declared == "D4" and (before.get("paper_id") == after.get("paper_id") or after_version != 1):
            errors.append(f"{label}: D4 must create a new paper_id at identity_version 1")

        if declared in {"D3", "D4"}:
            if not meaningful(transition.get("trigger_id")):
                errors.append(f"{label}.trigger_id must identify the fired pivot trigger or kill condition")
            for field in ("switching_cost", "successor_project_assessment"):
                if not meaningful(transition.get(field)):
                    errors.append(f"{label}.{field} must be substantive")
            if not isinstance(transition.get("discarded_evidence"), list):
                errors.append(f"{label}.discarded_evidence must be a list")
            authorization = transition.get("authorization")
            if not isinstance(authorization, dict):
                errors.append(f"{label}.authorization must be an object")
            else:
                auth_id = validate_id(authorization.get("authorization_id"), f"{label}.authorization.authorization_id", errors)
                if auth_id in used_authorizations:
                    errors.append(f"authorization {auth_id} is reused")
                used_authorizations.add(auth_id)
                expected_decision = "authorize-D3" if declared == "D3" else "close-and-create-D4"
                if authorization.get("decision") != expected_decision:
                    errors.append(f"{label}.authorization.decision must be {expected_decision}")
                if authorization.get("before_digest") != before_digest or authorization.get("after_digest") != after_digest:
                    errors.append(f"{label}.authorization must bind the exact before and after digests")
                if not meaningful(authorization.get("rationale")):
                    errors.append(f"{label}.authorization.rationale must be substantive")
                if not isinstance(authorization.get("self_review"), bool):
                    errors.append(f"{label}.authorization.self_review must be boolean")
            if declared == "D4":
                closure = transition.get("old_lineage_closure")
                if not isinstance(closure, dict):
                    errors.append(f"{label}.old_lineage_closure is required for D4")
                else:
                    if closure.get("paper_id") != before.get("paper_id") or closure.get("status") != "closed":
                        errors.append(f"{label}.old_lineage_closure must close the previous paper identity")
                    if not meaningful(closure.get("closure_rationale")):
                        errors.append(f"{label}.old_lineage_closure.closure_rationale must be substantive")
                    closure_digest = closure.get("closure_digest")
                    closure_payload = {key: value for key, value in closure.items() if key != "closure_digest"}
                    if closure_digest != canonical_digest(closure_payload):
                        errors.append(f"{label}.old_lineage_closure.closure_digest is invalid")

    missing_pairs = set(expected_pairs) - seen_pairs
    extra_pairs = seen_pairs - set(expected_pairs)
    if missing_pairs:
        errors.append("transition ledger omits adjacent history transitions: " + ", ".join(f"{a}->{b}" for a, b in sorted(missing_pairs)))
    if extra_pairs:
        errors.append("transition ledger contains non-adjacent transitions: " + ", ".join(f"{a}->{b}" for a, b in sorted(extra_pairs)))
    if work_items is not None and ordered_ids:
        latest = snapshots.get(ordered_ids[-1], {})
        current_identity = (latest.get("paper_id"), latest.get("identity_version"))
        if isinstance(work_items, dict):
            for item in work_items.get("items", []):
                if not isinstance(item, dict) or item.get("status") not in ACTIVE_WORK_STATUSES:
                    continue
                item_identity = (item.get("paper_id"), item.get("identity_version"))
                binding = item.get("experiment_binding")
                if isinstance(binding, dict):
                    item_identity = (binding.get("paper_id"), binding.get("identity_version"))
                if item_identity != current_identity:
                    errors.append(f"active work item {item.get('work_item_id', '<unknown>')} is bound to stale paper identity {item_identity}")
    return errors
