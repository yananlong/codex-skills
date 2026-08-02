#!/usr/bin/env python3
"""Validate machine-readable result audits and optional orchestrated source bindings."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "1.0"
STATUS_VALUES = {"draft", "complete", "superseded"}
ASSURANCE_CLASSES = {
    "none",
    "exploratory",
    "confirmatory",
    "independently_verified",
    "operational_high_stakes",
}
ASSURANCE_RANK = {
    name: rank
    for rank, name in enumerate(
        ("none", "exploratory", "confirmatory", "independently_verified", "operational_high_stakes")
    )
}
VERDICTS = {
    "structurally_valid_only",
    "internally_consistent_only",
    "supports_exploratory_follow_up",
    "supports_confirmatory_claim",
    "independently_verified",
    "supports_operational_high_stakes_claim",
    "inconclusive",
    "does_not_support_claim",
}
CLAIM_EFFECTS = {"strengthen", "weaken", "kill", "unchanged", "inconclusive"}
SOURCE_MODES = {"standalone", "orchestrated"}
GATE_RESULTS = {"pass", "fail", "inconclusive", "not_applicable"}
SCIENTIFIC_DISPOSITIONS = {
    "supports_claim",
    "weakens_claim",
    "falsifies_claim",
    "inconclusive",
    "diagnostic_only",
}
LINEAGE_RELATIONS = {
    "baseline",
    "replication",
    "ablation",
    "parameter_variation",
    "negative_control",
    "sensitivity",
    "alternative_hypothesis",
    "technical_retry",
}
CHECK_STATUSES = {"pass", "fail", "inconclusive", "not_assessed"}
REQUIRED_CHECKS = {
    "protocol_integrity",
    "metric_validity",
    "baseline_fairness",
    "outcome_accounting",
    "inferential_support",
    "confound_control",
    "provenance",
    "snapshot_continuity",
    "independence",
}
INDEPENDENCE_DIMENSIONS = {
    "context",
    "data",
    "implementation",
    "evaluation",
    "advancement_authority",
}
FAILURE_STATUSES = {"open", "resolved", "accepted_with_narrowing"}
IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,191}$")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
POSITIVE_VERDICTS = {
    "supports_exploratory_follow_up",
    "supports_confirmatory_claim",
    "independently_verified",
    "supports_operational_high_stakes_claim",
}


def meaningful(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def read_json(path: Path, label: str, errors: list[str]) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(f"missing {label}: {path}")
    except json.JSONDecodeError as exc:
        errors.append(f"invalid JSON in {label}: {exc}")
    return None


def read_text(path: Path, label: str, errors: list[str]) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        errors.append(f"missing {label}: {path}")
        return ""


def require_string(record: dict[str, Any], field: str, label: str, errors: list[str]) -> str:
    value = record.get(field)
    if not meaningful(value):
        errors.append(f"{label}.{field} must be substantive")
        return ""
    return str(value)


def validate_identifier(value: Any, label: str, errors: list[str]) -> str:
    if not meaningful(value) or not IDENTIFIER_RE.fullmatch(str(value)):
        errors.append(f"{label} must use letters, numbers, dot, underscore, colon, or hyphen")
        return ""
    return str(value)


def validate_checks(audit: dict[str, Any], label: str, complete: bool, errors: list[str]) -> dict[str, str]:
    entries = audit.get("check_results")
    if not isinstance(entries, list):
        errors.append(f"{label}.check_results must be a list")
        return {}
    checks: dict[str, str] = {}
    for index, entry in enumerate(entries, start=1):
        item_label = f"{label}.check_results[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{item_label} must be an object")
            continue
        check_id = entry.get("check_id")
        if check_id not in REQUIRED_CHECKS:
            errors.append(f"{item_label}.check_id must be one of {sorted(REQUIRED_CHECKS)}")
            continue
        if check_id in checks:
            errors.append(f"{label}.check_results contains duplicate check_id {check_id}")
        status = entry.get("status")
        if status not in CHECK_STATUSES:
            errors.append(f"{item_label}.status must be one of {sorted(CHECK_STATUSES)}")
            continue
        checks[str(check_id)] = str(status)
        if complete and not meaningful(entry.get("rationale")):
            errors.append(f"{item_label}.rationale must be substantive for a complete audit")
        evidence_paths = entry.get("evidence_paths", [])
        if not isinstance(evidence_paths, list) or any(not meaningful(path) for path in evidence_paths):
            errors.append(f"{item_label}.evidence_paths must be a list of substantive paths")
    if complete:
        missing = sorted(REQUIRED_CHECKS - set(checks))
        if missing:
            errors.append(f"{label}.check_results missing required checks: {', '.join(missing)}")
    return checks


def validate_independence(
    audit: dict[str, Any], label: str, complete: bool, attained: str, checks: dict[str, str], errors: list[str]
) -> None:
    independence = audit.get("independence")
    if not isinstance(independence, dict):
        errors.append(f"{label}.independence must be an object")
        return
    self_review = independence.get("self_review")
    if not isinstance(self_review, bool):
        errors.append(f"{label}.independence.self_review must be boolean")
    dimensions = independence.get("dimensions")
    if not isinstance(dimensions, list):
        errors.append(f"{label}.independence.dimensions must be a list")
        dimensions = []
    elif len(dimensions) != len(set(map(str, dimensions))):
        errors.append(f"{label}.independence.dimensions contains duplicates")
    unknown = sorted({str(value) for value in dimensions} - INDEPENDENCE_DIMENSIONS)
    if unknown:
        errors.append(f"{label}.independence.dimensions contains unsupported values: {', '.join(unknown)}")
    rank = ASSURANCE_RANK.get(attained, -1)
    if rank >= ASSURANCE_RANK["independently_verified"]:
        if self_review is not False:
            errors.append(f"{label}: independently verified assurance cannot be self-review")
        required = {"evaluation", "advancement_authority"}
        if not required.issubset(set(dimensions)) or len(set(dimensions)) < 3:
            errors.append(
                f"{label}: independently verified assurance requires evaluation, advancement_authority, and at least one additional independence dimension"
            )
        if not meaningful(independence.get("evidence")):
            errors.append(f"{label}.independence.evidence must be substantive")
        if checks.get("independence") != "pass":
            errors.append(f"{label}: independently verified assurance requires independence check status pass")
    if attained == "operational_high_stakes" and set(dimensions) != INDEPENDENCE_DIMENSIONS:
        errors.append(f"{label}: operational_high_stakes assurance requires all independence dimensions")
    if complete and self_review is True and attained in {"independently_verified", "operational_high_stakes"}:
        errors.append(f"{label}: self-review cannot attain {attained}")


def validate_source_runs(
    audit: dict[str, Any], label: str, complete: bool, source_mode: str, errors: list[str]
) -> list[dict[str, Any]]:
    runs = audit.get("source_runs")
    if not isinstance(runs, list):
        errors.append(f"{label}.source_runs must be a list")
        return []
    if complete and source_mode == "orchestrated" and not runs:
        errors.append(f"{label}: complete orchestrated audit requires at least one source run")
    seen: set[str] = set()
    normalized: list[dict[str, Any]] = []
    for index, run in enumerate(runs, start=1):
        run_label = f"{label}.source_runs[{index}]"
        if not isinstance(run, dict):
            errors.append(f"{run_label} must be an object")
            continue
        for field in ("work_item_id", "episode_id", "episode_digest", "run_id", "block_id", "gate_id"):
            require_string(run, field, run_label, errors)
        run_id = run.get("run_id")
        if meaningful(run_id):
            if run_id in seen:
                errors.append(f"{label}.source_runs contains duplicate run_id {run_id}")
            seen.add(str(run_id))
        digest = run.get("episode_digest")
        if meaningful(digest) and not DIGEST_RE.fullmatch(str(digest)):
            errors.append(f"{run_label}.episode_digest must be a lowercase SHA-256 hex digest")
        if run.get("gate_result") not in GATE_RESULTS:
            errors.append(f"{run_label}.gate_result must be one of {sorted(GATE_RESULTS)}")
        if run.get("scientific_disposition") not in SCIENTIFIC_DISPOSITIONS:
            errors.append(
                f"{run_label}.scientific_disposition must be one of {sorted(SCIENTIFIC_DISPOSITIONS)}"
            )
        if run.get("lineage_relation") not in LINEAGE_RELATIONS:
            errors.append(f"{run_label}.lineage_relation must be one of {sorted(LINEAGE_RELATIONS)}")
        parent = run.get("parent_run_id")
        if parent is not None and not meaningful(parent):
            errors.append(f"{run_label}.parent_run_id must be JSON null or a substantive string")
        if run.get("submitted_claim_effect") not in CLAIM_EFFECTS:
            errors.append(f"{run_label}.submitted_claim_effect must be one of {sorted(CLAIM_EFFECTS)}")
        decision = run.get("verification_decision")
        if decision not in {"approve", "revise", "block"}:
            errors.append(f"{run_label}.verification_decision must be approve, revise, or block")
        verified_gate = run.get("verified_gate_result")
        verified_disposition = run.get("verified_scientific_disposition")
        if decision == "approve":
            if verified_gate not in GATE_RESULTS:
                errors.append(f"{run_label}.verified_gate_result must be a gate result for approved work")
            if verified_disposition not in SCIENTIFIC_DISPOSITIONS:
                errors.append(
                    f"{run_label}.verified_scientific_disposition must be a scientific disposition for approved work"
                )
        else:
            if verified_gate is not None and verified_gate not in GATE_RESULTS:
                errors.append(f"{run_label}.verified_gate_result must be null or a valid gate result")
            if verified_disposition is not None and verified_disposition not in SCIENTIFIC_DISPOSITIONS:
                errors.append(
                    f"{run_label}.verified_scientific_disposition must be null or a valid scientific disposition"
                )
        if not isinstance(run.get("verification_self_review"), bool):
            errors.append(f"{run_label}.verification_self_review must be boolean")
        normalized.append(run)
    return normalized


def validate_evidence_artifacts(
    audit: dict[str, Any], label: str, complete: bool, errors: list[str]
) -> list[dict[str, Any]]:
    artifacts = audit.get("evidence_artifacts")
    if not isinstance(artifacts, list):
        errors.append(f"{label}.evidence_artifacts must be a list")
        return []
    if complete and not artifacts:
        errors.append(f"{label}: complete audit requires at least one evidence artifact")
    seen: set[str] = set()
    normalized: list[dict[str, Any]] = []
    for index, artifact in enumerate(artifacts, start=1):
        item_label = f"{label}.evidence_artifacts[{index}]"
        if not isinstance(artifact, dict):
            errors.append(f"{item_label} must be an object")
            continue
        path = require_string(artifact, "path", item_label, errors)
        require_string(artifact, "kind", item_label, errors)
        source = artifact.get("source")
        if source not in {"experiment", "audit"}:
            errors.append(f"{item_label}.source must be experiment or audit")
        if path:
            if path in seen:
                errors.append(f"{label}.evidence_artifacts contains duplicate path {path}")
            seen.add(path)
        digest = artifact.get("digest")
        if source == "experiment":
            if not meaningful(digest) or not DIGEST_RE.fullmatch(str(digest)):
                errors.append(f"{item_label}.digest must be a lowercase SHA-256 hex digest for experiment evidence")
        elif digest is not None and digest != "" and not DIGEST_RE.fullmatch(str(digest)):
            errors.append(f"{item_label}.digest must be empty or a lowercase SHA-256 hex digest")
        normalized.append(artifact)
    return normalized


def validate_failure_dispositions(audit: dict[str, Any], label: str, errors: list[str]) -> None:
    failures = audit.get("predecessor_failures")
    if not isinstance(failures, list):
        errors.append(f"{label}.predecessor_failures must be a list")
        return
    seen: set[str] = set()
    for index, failure in enumerate(failures, start=1):
        item_label = f"{label}.predecessor_failures[{index}]"
        if not isinstance(failure, dict):
            errors.append(f"{item_label} must be an object")
            continue
        failure_id = require_string(failure, "failure_id", item_label, errors)
        if failure_id in seen:
            errors.append(f"{label}.predecessor_failures contains duplicate failure_id {failure_id}")
        seen.add(failure_id)
        if failure.get("status") not in FAILURE_STATUSES:
            errors.append(f"{item_label}.status must be one of {sorted(FAILURE_STATUSES)}")
        require_string(failure, "rationale", item_label, errors)


def validate_verdict_semantics(
    audit: dict[str, Any],
    label: str,
    source_mode: str,
    runs: list[dict[str, Any]],
    checks: dict[str, str],
    errors: list[str],
) -> None:
    verdict = audit.get("verdict")
    attained = audit.get("attained_assurance_class")
    effect = audit.get("audited_claim_effect")
    if verdict not in VERDICTS:
        errors.append(f"{label}.verdict must be one of {sorted(VERDICTS)}")
        return
    if attained not in ASSURANCE_CLASSES:
        errors.append(f"{label}.attained_assurance_class must be one of {sorted(ASSURANCE_CLASSES)}")
        return
    if effect not in CLAIM_EFFECTS:
        errors.append(f"{label}.audited_claim_effect must be one of {sorted(CLAIM_EFFECTS)}")
        return
    minimum = {
        "supports_exploratory_follow_up": "exploratory",
        "supports_confirmatory_claim": "confirmatory",
        "independently_verified": "independently_verified",
        "supports_operational_high_stakes_claim": "operational_high_stakes",
    }.get(str(verdict))
    if minimum and ASSURANCE_RANK[attained] < ASSURANCE_RANK[minimum]:
        errors.append(f"{label}: verdict {verdict} requires attained assurance class at least {minimum}")
    if verdict in POSITIVE_VERDICTS and effect != "strengthen":
        errors.append(f"{label}: positive support verdict requires audited_claim_effect=strengthen")
    if verdict == "inconclusive" and effect not in {"inconclusive", "unchanged"}:
        errors.append(f"{label}: inconclusive verdict requires inconclusive or unchanged claim effect")
    if verdict == "does_not_support_claim" and effect == "strengthen":
        errors.append(f"{label}: does_not_support_claim cannot strengthen the claim")

    exploratory_required = {"protocol_integrity", "metric_validity", "provenance"}
    confirmatory_required = exploratory_required | {
        "baseline_fairness",
        "outcome_accounting",
        "inferential_support",
        "confound_control",
    }
    if verdict in POSITIVE_VERDICTS:
        required = exploratory_required
        if verdict != "supports_exploratory_follow_up":
            required = confirmatory_required
        if source_mode == "orchestrated" and verdict != "supports_exploratory_follow_up":
            required = required | {"snapshot_continuity"}
        missing = sorted(check for check in required if checks.get(check) != "pass")
        if missing:
            errors.append(f"{label}: verdict {verdict} requires pass checks: {', '.join(missing)}")
    if verdict in {"independently_verified", "supports_operational_high_stakes_claim"}:
        if checks.get("independence") != "pass":
            errors.append(f"{label}: verdict {verdict} requires independence check pass")
    if source_mode == "orchestrated" and verdict in POSITIVE_VERDICTS:
        approved = [run for run in runs if run.get("verification_decision") == "approve"]
        if not approved:
            errors.append(f"{label}: positive orchestrated verdict requires an approved source run")
        if verdict != "supports_exploratory_follow_up" and not any(
            run.get("verified_gate_result") == "pass"
            and run.get("verified_scientific_disposition") == "supports_claim"
            and run.get("submitted_claim_effect") == "strengthen"
            for run in approved
        ):
            errors.append(
                f"{label}: confirmatory-or-stronger support requires an approved run with verified pass gate, "
                "supports_claim disposition, and strengthen submitted effect"
            )


def validate_audits(data: dict[str, Any], complete: bool, narrative: str, errors: list[str]) -> list[dict[str, Any]]:
    audits = data.get("audits")
    if not isinstance(audits, list):
        errors.append("results-audit.json.audits must be a list")
        return []
    if complete and not audits:
        errors.append("complete result-audit pack requires at least one audit record")
    seen: set[str] = set()
    normalized: list[dict[str, Any]] = []
    for index, audit in enumerate(audits, start=1):
        label = f"results-audit.json.audits[{index}]"
        if not isinstance(audit, dict):
            errors.append(f"{label} must be an object")
            continue
        audit_id = validate_identifier(audit.get("audit_id"), f"{label}.audit_id", errors)
        if audit_id in seen:
            errors.append(f"duplicate audit_id: {audit_id}")
        seen.add(audit_id)
        claim_id = validate_identifier(audit.get("claim_id"), f"{label}.claim_id", errors)
        source_mode = audit.get("source_mode")
        if source_mode not in SOURCE_MODES:
            errors.append(f"{label}.source_mode must be one of {sorted(SOURCE_MODES)}")
            source_mode = "standalone"
        requested = audit.get("requested_assurance_class")
        attained = audit.get("attained_assurance_class")
        if requested not in ASSURANCE_CLASSES - {"none"}:
            errors.append(
                f"{label}.requested_assurance_class must be one of {sorted(ASSURANCE_CLASSES - {'none'})}"
            )
        if attained not in ASSURANCE_CLASSES:
            errors.append(f"{label}.attained_assurance_class must be one of {sorted(ASSURANCE_CLASSES)}")
        elif requested in ASSURANCE_CLASSES and ASSURANCE_RANK[attained] > ASSURANCE_RANK[requested]:
            errors.append(f"{label}: attained assurance class cannot exceed requested assurance class")
        if complete:
            require_string(audit, "claim_text", label, errors)
            require_string(audit, "minimum_corrective_action", label, errors)
            require_string(audit, "narrative_anchor", label, errors)
        runs = validate_source_runs(audit, label, complete, str(source_mode), errors)
        artifacts = validate_evidence_artifacts(audit, label, complete, errors)
        checks = validate_checks(audit, label, complete, errors)
        validate_independence(audit, label, complete, str(attained), checks, errors)
        validate_failure_dispositions(audit, label, errors)
        limitations = audit.get("limitations")
        if not isinstance(limitations, list) or any(not meaningful(value) for value in limitations):
            errors.append(f"{label}.limitations must be a list of substantive strings")
        validate_verdict_semantics(audit, label, str(source_mode), runs, checks, errors)
        if complete and audit_id:
            heading = f"## Audit {audit_id}"
            if heading not in narrative:
                errors.append(f"results-audit.md missing exact heading {heading!r}")
            verdict = audit.get("verdict")
            if meaningful(verdict) and f"Bounded verdict: {verdict}" not in narrative:
                errors.append(
                    f"results-audit.md must record exact bounded verdict for {audit_id}: {verdict}"
                )
        if claim_id and not runs and source_mode == "orchestrated" and complete:
            errors.append(f"{label}: orchestrated audit {audit_id} has no run binding")
        if artifacts:
            known_paths = {entry.get("path") for entry in artifacts if isinstance(entry, dict)}
            for check in audit.get("check_results", []):
                if not isinstance(check, dict):
                    continue
                unknown = [path for path in check.get("evidence_paths", []) if path not in known_paths]
                if unknown:
                    errors.append(
                        f"{label}.{check.get('check_id')}: evidence_paths reference unknown audit artifacts: {', '.join(unknown)}"
                    )
        normalized.append(audit)
    return normalized


def find_run(work_items: dict[str, Any], run_id: str) -> tuple[dict[str, Any], dict[str, Any]] | None:
    found: tuple[dict[str, Any], dict[str, Any]] | None = None
    for item in work_items.get("items", []):
        if not isinstance(item, dict):
            continue
        for episode in item.get("episodes", []):
            if not isinstance(episode, dict):
                continue
            run = episode.get("experiment_run")
            if isinstance(run, dict) and run.get("run_id") == run_id:
                if found is not None:
                    raise ValueError(f"duplicate run_id in work-items projection: {run_id}")
                found = (item, episode)
    return found


def validate_linked(
    data: dict[str, Any],
    audits: list[dict[str, Any]],
    commitment: Any,
    claim_map: Any,
    work_items: Any,
    errors: list[str],
) -> None:
    if not isinstance(commitment, dict):
        errors.append("linked profile requires commitment JSON object")
        return
    if data.get("paper_id") != commitment.get("paper_id"):
        errors.append("results-audit paper_id does not match commitment")
    if data.get("identity_version") != commitment.get("identity_version"):
        errors.append("results-audit identity_version does not match commitment")
    if not isinstance(claim_map, list):
        errors.append("linked profile requires claim-map JSON array")
        claim_ids: set[str] = set()
    else:
        claim_ids = {
            str(entry.get("claim_id"))
            for entry in claim_map
            if isinstance(entry, dict) and meaningful(entry.get("claim_id"))
        }
    if not isinstance(work_items, dict) or not isinstance(work_items.get("items"), list):
        errors.append("linked profile requires work-items JSON object with items")
        return

    for audit in audits:
        audit_id = audit.get("audit_id", "<unknown>")
        claim_id = audit.get("claim_id")
        if claim_id not in claim_ids:
            errors.append(f"audit {audit_id} references unknown claim_id {claim_id}")
        matched_artifacts: dict[str, str] = {}
        for source in audit.get("source_runs", []):
            if not isinstance(source, dict) or not meaningful(source.get("run_id")):
                continue
            try:
                found = find_run(work_items, str(source["run_id"]))
            except ValueError as exc:
                errors.append(str(exc))
                continue
            if found is None:
                errors.append(f"audit {audit_id} references unknown run_id {source.get('run_id')}")
                continue
            item, episode = found
            run = episode.get("experiment_run", {})
            binding = item.get("experiment_binding", {})
            verifications = [
                verification
                for verification in item.get("verifications", [])
                if isinstance(verification, dict)
                and verification.get("episode_id") == episode.get("episode_id")
            ]
            if len(verifications) != 1:
                errors.append(
                    f"audit {audit_id} source run {source.get('run_id')} must resolve exactly one verification record"
                )
                verification: dict[str, Any] = {}
            else:
                verification = verifications[0]
            gate_results = verification.get("gate_results")
            verified_gate = (
                gate_results.get(run.get("gate_id")) if isinstance(gate_results, dict) else None
            )
            expected = {
                "work_item_id": item.get("work_item_id"),
                "episode_id": episode.get("episode_id"),
                "episode_digest": episode.get("episode_digest"),
                "run_id": run.get("run_id"),
                "block_id": run.get("block_id"),
                "gate_id": run.get("gate_id"),
                "gate_result": run.get("gate_result"),
                "scientific_disposition": run.get("scientific_disposition"),
                "lineage_relation": run.get("relation"),
                "parent_run_id": run.get("parent_run_id"),
                "verification_decision": verification.get("decision"),
                "verified_gate_result": verified_gate,
                "verified_scientific_disposition": verification.get("scientific_disposition"),
                "verification_self_review": verification.get("self_review"),
            }
            effects = [
                effect.get("effect")
                for effect in run.get("claim_effects", [])
                if isinstance(effect, dict) and effect.get("claim_id") == claim_id
            ]
            if len(effects) != 1:
                errors.append(
                    f"audit {audit_id} source run {source.get('run_id')} must have exactly one submitted claim effect for {claim_id}"
                )
            else:
                expected["submitted_claim_effect"] = effects[0]
            for field, value in expected.items():
                if source.get(field) != value:
                    errors.append(
                        f"audit {audit_id} source run {source.get('run_id')} field {field} disagrees with work-items projection"
                    )
            if binding.get("paper_id") != data.get("paper_id") or binding.get("identity_version") != data.get("identity_version"):
                errors.append(f"audit {audit_id} source run belongs to a different paper identity")
            if claim_id not in binding.get("claim_ids", []):
                errors.append(f"audit {audit_id} claim_id is outside the source run binding")
            for path, digest in episode.get("artifact_digests", {}).items():
                if isinstance(path, str) and isinstance(digest, str):
                    matched_artifacts[path] = digest
        for artifact in audit.get("evidence_artifacts", []):
            if not isinstance(artifact, dict) or artifact.get("source") != "experiment":
                continue
            path = artifact.get("path")
            if path not in matched_artifacts:
                errors.append(f"audit {audit_id} experiment evidence path is absent from source episodes: {path}")
            elif artifact.get("digest") != matched_artifacts[path]:
                errors.append(f"audit {audit_id} experiment evidence digest mismatch for {path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit", required=True, type=Path)
    parser.add_argument("--narrative", required=True, type=Path)
    parser.add_argument("--assurance-profile", choices=("structural", "linked"), default="structural")
    parser.add_argument("--commitment", type=Path)
    parser.add_argument("--claim-map", type=Path)
    parser.add_argument("--work-items", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    errors: list[str] = []
    data = read_json(args.audit, "results-audit JSON", errors)
    narrative = read_text(args.narrative, "results-audit narrative", errors)
    if not isinstance(data, dict):
        if data is not None:
            errors.append("results-audit JSON must be an object")
        audits: list[dict[str, Any]] = []
    else:
        if data.get("schema_version") != SCHEMA_VERSION:
            errors.append(f"results-audit.schema_version must equal {SCHEMA_VERSION}")
        status = data.get("status")
        if status not in STATUS_VALUES:
            errors.append(f"results-audit.status must be one of {sorted(STATUS_VALUES)}")
        if not isinstance(data.get("identity_version"), int) or data.get("identity_version", 0) < 1:
            errors.append("results-audit.identity_version must be a positive integer")
        complete = status == "complete"
        if complete and not meaningful(data.get("paper_id")):
            errors.append("complete results-audit requires substantive paper_id")
        audits = validate_audits(data, complete, narrative, errors)
        if args.assurance_profile == "linked":
            if status != "complete":
                errors.append("linked assurance profile requires results-audit.status=complete")
            if not all((args.commitment, args.claim_map, args.work_items)):
                errors.append("linked profile requires --commitment, --claim-map, and --work-items")
            else:
                commitment = read_json(args.commitment, "commitment", errors)
                claim_map = read_json(args.claim_map, "claim-map", errors)
                work_items = read_json(args.work_items, "work-items", errors)
                validate_linked(data, audits, commitment, claim_map, work_items, errors)
    if errors:
        print("Validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    if args.assurance_profile == "linked":
        print(
            "Validation passed: machine-readable result audits, narrative anchors, claim IDs, source runs, "
            "episode digests, submitted run metadata, and experiment evidence digests are internally linked. "
            "This establishes repository-local consistency only; it does not establish executor isolation, "
            "external immutability, scientific validity, or independent verification beyond the recorded evidence."
        )
    else:
        print(
            "Validation passed: the result-audit pack is structurally consistent. This does not establish "
            "semantic validity, source-run authenticity, scientific support, or independent verification."
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
