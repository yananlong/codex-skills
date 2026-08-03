#!/usr/bin/env python3
"""Coverage-question validation shared by literature and novelty assurance."""
from __future__ import annotations

from typing import Any

QUESTION_PRIORITIES = {"high", "medium", "low"}
QUESTION_STATUSES = {
    "open",
    "searching",
    "answered",
    "contradicted",
    "saturated",
    "blocked",
    "out-of-scope",
}
CLOSED_STATUSES = {"answered", "contradicted", "saturated", "out-of-scope"}
UNRESOLVED_STATUSES = {"open", "searching", "blocked"}
SYSTEMATIC = {"comprehensive-systematic", "bounded-systematic"}
COVERAGE_GATED_PROFILES = SYSTEMATIC | {"critical-evidence-map", "novelty-prior-art"}


def meaningful(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip()) and "todo" not in value.lower()


def split_ids(value: Any) -> set[str]:
    if not isinstance(value, str) or not value.strip():
        return set()
    normalized = value.replace(";", ",")
    return {part.strip() for part in normalized.split(",") if part.strip()}


def unresolved_high_priority_novelty_questions(manifest: Any) -> set[str]:
    if not isinstance(manifest, dict):
        return set()
    unresolved: set[str] = set()
    for question in manifest.get("coverage_questions", []):
        if not isinstance(question, dict):
            continue
        if (
            question.get("priority") == "high"
            and question.get("critical_for_novelty") is True
            and question.get("status") in UNRESOLVED_STATUSES
            and meaningful(question.get("question_id"))
        ):
            unresolved.add(str(question["question_id"]))
    return unresolved


def validate_coverage_questions(
    manifest: Any,
    query_rows: list[dict[str, str]],
    profile: str | None,
    verdict: str | None,
    record_ids: set[str],
    errors: list[str],
) -> set[str]:
    """Validate canonical questions and reciprocal search/record/amendment links."""
    if not isinstance(manifest, dict):
        return set()
    schema_version = manifest.get("schema_version")
    questions = manifest.get("coverage_questions")
    if schema_version == "1.0":
        if verdict and verdict != "insufficient":
            errors.append("adequate assurance requires corpus manifest schema_version 1.1 with coverage_questions")
        return set()
    if schema_version != "1.1":
        return set()
    if not isinstance(questions, list):
        errors.append("corpus manifest coverage_questions must be a list")
        return set()

    record_question_ids: dict[str, set[str]] = {}
    for index, record in enumerate(manifest.get("records", []), 1):
        if not isinstance(record, dict) or not meaningful(record.get("record_id")):
            continue
        record_id = str(record["record_id"])
        raw_question_ids = record.get("question_ids")
        if not isinstance(raw_question_ids, list) or any(not meaningful(value) for value in raw_question_ids):
            errors.append(f"corpus manifest records[{index}].question_ids must be a list of substantive question IDs")
            record_question_ids[record_id] = set()
            continue
        linked = set(map(str, raw_question_ids))
        if len(raw_question_ids) != len(linked):
            errors.append(f"corpus manifest records[{index}].question_ids contains duplicates")
        if verdict and verdict != "insufficient" and not linked:
            errors.append(f"corpus manifest record {record_id} must reference at least one coverage question")
        record_question_ids[record_id] = linked

    run_question_ids: dict[str, set[str]] = {}
    for index, row in enumerate(query_rows, 1):
        run_id = row.get("run_id", "").strip()
        if not meaningful(run_id):
            continue
        if run_id in run_question_ids:
            errors.append(f"duplicate source query run_id: {run_id}")
        run_question_ids[run_id] = split_ids(row.get("question_ids", ""))
        if schema_version == "1.1" and not run_question_ids[run_id]:
            errors.append(f"source query row {index}.question_ids must reference at least one coverage question")

    amendments = manifest.get("post_freeze_amendments")
    amendment_index: dict[str, dict[str, Any]] = {}
    if isinstance(amendments, list):
        for amendment in amendments:
            if not isinstance(amendment, dict) or not meaningful(amendment.get("amendment_id")):
                continue
            amendment_id = str(amendment["amendment_id"])
            if amendment_id in amendment_index:
                errors.append(f"duplicate post-freeze amendment_id: {amendment_id}")
            amendment_index[amendment_id] = amendment

    question_index: dict[str, dict[str, Any]] = {}
    for index, question in enumerate(questions, 1):
        label = f"coverage_questions[{index}]"
        if not isinstance(question, dict):
            errors.append(f"{label} must be an object")
            continue
        question_id = question.get("question_id")
        if not meaningful(question_id):
            errors.append(f"{label}.question_id must be substantive")
            continue
        question_id = str(question_id)
        if question_id in question_index:
            errors.append(f"duplicate coverage question_id: {question_id}")
            continue
        question_index[question_id] = question
        for field in ("question", "perspective", "decision_role"):
            if not meaningful(question.get(field)):
                errors.append(f"{label}.{field} must be substantive")
        if question.get("priority") not in QUESTION_PRIORITIES:
            errors.append(f"{label}.priority must be one of {sorted(QUESTION_PRIORITIES)}")
        status = question.get("status")
        if status not in QUESTION_STATUSES:
            errors.append(f"{label}.status must be one of {sorted(QUESTION_STATUSES)}")
        if not isinstance(question.get("critical_for_novelty"), bool):
            errors.append(f"{label}.critical_for_novelty must be boolean")

        search_run_ids = question.get("search_run_ids")
        if not isinstance(search_run_ids, list) or any(not meaningful(value) for value in search_run_ids):
            errors.append(f"{label}.search_run_ids must be a list of substantive run IDs")
            search_run_ids = []
        elif len(search_run_ids) != len(set(map(str, search_run_ids))):
            errors.append(f"{label}.search_run_ids contains duplicates")
        for run_id in map(str, search_run_ids):
            if run_id not in run_question_ids:
                errors.append(f"{label} references unknown search run {run_id}")
            elif question_id not in run_question_ids[run_id]:
                errors.append(f"search run {run_id} does not reciprocally reference coverage question {question_id}")

        linked_records = question.get("record_ids")
        if not isinstance(linked_records, list) or any(not meaningful(value) for value in linked_records):
            errors.append(f"{label}.record_ids must be a list of substantive record IDs")
            linked_records = []
        elif len(linked_records) != len(set(map(str, linked_records))):
            errors.append(f"{label}.record_ids contains duplicates")
        unknown_records = set(map(str, linked_records)) - record_ids
        if unknown_records:
            errors.append(f"{label} references unknown corpus records: {', '.join(sorted(unknown_records))}")
        for record_id in set(map(str, linked_records)) - unknown_records:
            if question_id not in record_question_ids.get(record_id, set()):
                errors.append(f"corpus record {record_id} does not reciprocally reference coverage question {question_id}")

        if status in {"answered", "contradicted", "saturated"}:
            if not linked_records:
                errors.append(f"{label}: status {status} requires record_ids")
            for field in ("answer_summary", "closure_reason"):
                if not meaningful(question.get(field)):
                    errors.append(f"{label}.{field} must be substantive for status {status}")
        if status == "blocked":
            for field in ("residual_gap", "closure_reason", "blocked_mitigation", "scope_consequence"):
                if not meaningful(question.get(field)):
                    errors.append(f"{label}.{field} must be substantive for status blocked")
        if status == "out-of-scope":
            for field in ("closure_reason", "protocol_boundary"):
                if not meaningful(question.get(field)):
                    errors.append(f"{label}.{field} must be substantive for status out-of-scope")

        created_after_freeze = question.get("created_after_freeze")
        if not isinstance(created_after_freeze, bool):
            errors.append(f"{label}.created_after_freeze must be boolean")
        if created_after_freeze is True:
            if not manifest.get("freeze_date"):
                errors.append(f"{label}: created_after_freeze requires manifest.freeze_date")
            amendment_id = question.get("amendment_id")
            if not meaningful(amendment_id):
                errors.append(f"{label}: created_after_freeze requires amendment_id")
            else:
                amendment = amendment_index.get(str(amendment_id))
                if amendment is None:
                    errors.append(f"{label} references unknown amendment_id {amendment_id}")
                elif amendment.get("question_id") != question_id:
                    errors.append(f"amendment {amendment_id} does not reciprocally reference {question_id}")
        elif question.get("amendment_id") not in (None, ""):
            errors.append(f"{label}.amendment_id must be null when created_after_freeze is false")

    known_question_ids = set(question_index)
    for record_id, linked_questions in record_question_ids.items():
        unknown = linked_questions - known_question_ids
        if unknown:
            errors.append(f"corpus record {record_id} references unknown coverage questions: {', '.join(sorted(unknown))}")
        for question_id in linked_questions & known_question_ids:
            declared_records = set(map(str, question_index[question_id].get("record_ids", [])))
            if record_id not in declared_records:
                errors.append(f"coverage question {question_id} does not reciprocally reference corpus record {record_id}")

    for amendment_id, amendment in amendment_index.items():
        if amendment.get("kind", "record") != "coverage-question":
            continue
        question_id = amendment.get("question_id")
        if not meaningful(question_id) or str(question_id) not in question_index:
            errors.append(f"post-freeze amendment {amendment_id} references unknown coverage question {question_id}")
            continue
        question = question_index[str(question_id)]
        if question.get("created_after_freeze") is not True or question.get("amendment_id") != amendment_id:
            errors.append(f"coverage question {question_id} does not reciprocally reference amendment {amendment_id}")

    for run_id, linked_questions in run_question_ids.items():
        unknown = linked_questions - known_question_ids
        if unknown:
            errors.append(f"search run {run_id} references unknown coverage questions: {', '.join(sorted(unknown))}")
        for question_id in linked_questions & known_question_ids:
            declared_runs = set(map(str, question_index[question_id].get("search_run_ids", [])))
            if run_id not in declared_runs:
                errors.append(f"coverage question {question_id} does not reciprocally reference search run {run_id}")

    if profile in COVERAGE_GATED_PROFILES and verdict and verdict != "insufficient" and not question_index:
        errors.append("adequate assurance requires at least one coverage question")

    unresolved = unresolved_high_priority_novelty_questions(manifest)
    if profile == "comprehensive-systematic" and verdict == "adequate-for-comprehensive-claim" and unresolved:
        errors.append(
            "comprehensive assurance cannot retain unresolved high-priority novelty-critical questions: "
            + ", ".join(sorted(unresolved))
        )
    if profile != "rapid-scan" and verdict == "adequate-for-bounded-claims":
        active = sorted(
            question_id
            for question_id, question in question_index.items()
            if question.get("priority") == "high"
            and question.get("critical_for_novelty") is True
            and question.get("status") in {"open", "searching"}
        )
        if active:
            errors.append(
                "bounded assurance cannot retain open or searching high-priority novelty-critical questions: "
                + ", ".join(active)
            )
    return unresolved
