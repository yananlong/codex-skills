from __future__ import annotations

import math
from typing import Any

from .common import DEFAULT_CRITICAL_PERSPECTIVES, REQUIRED_PERSPECTIVES, REQUIRED_SEED_CLASSES, canonical_digest, meaningful, parse_markdown_table, split_ids

def validate_literature_semantics(
    manifest: Any,
    novelty: Any,
    prior_art: str,
    novelty_search: str,
    challenge: Any,
) -> list[str]:
    errors: list[str] = []
    if not isinstance(manifest, dict):
        return ["literature manifest must be an object"]
    if not isinstance(novelty, dict):
        return ["novelty decision must be an object"]
    semantic = manifest.get("semantic_assurance")
    if not isinstance(semantic, dict) or semantic.get("schema_version") != "1.0":
        return ["manifest.semantic_assurance must be a schema_version 1.0 object"]
    profile = manifest.get("review_profile")
    rating = novelty.get("novelty_decision_rating")
    if not isinstance(rating, int) or rating not in range(1, 6):
        errors.append("novelty_decision_rating must be an integer from 1 to 5")
        rating = 1

    records = manifest.get("records") if isinstance(manifest.get("records"), list) else []
    record_ids = {
        str(record.get("record_id"))
        for record in records
        if isinstance(record, dict) and meaningful(record.get("record_id"))
    }
    seed_ids = {str(value) for value in manifest.get("seed_ids", []) if meaningful(value)}
    questions = manifest.get("coverage_questions") if isinstance(manifest.get("coverage_questions"), list) else []
    questions_by_id = {
        str(question.get("question_id")): question
        for question in questions
        if isinstance(question, dict) and meaningful(question.get("question_id"))
    }

    basis = semantic.get("coverage_basis")
    if not isinstance(basis, list):
        errors.append("semantic_assurance.coverage_basis must be a list")
        basis = []
    basis_by_perspective: dict[str, dict[str, Any]] = {}
    for index, entry in enumerate(basis, 1):
        label = f"semantic_assurance.coverage_basis[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{label} must be an object")
            continue
        perspective = str(entry.get("perspective", ""))
        if perspective in basis_by_perspective:
            errors.append(f"duplicate coverage perspective {perspective}")
        basis_by_perspective[perspective] = entry
        applicability = entry.get("applicability")
        if applicability not in {"required", "not-applicable"}:
            errors.append(f"{label}.applicability must be required or not-applicable")
        question_ids = entry.get("question_ids")
        if applicability == "required":
            if not isinstance(question_ids, list) or not question_ids:
                errors.append(f"{label}.question_ids must be non-empty for a required perspective")
            else:
                unknown = sorted({str(value) for value in question_ids} - set(questions_by_id))
                if unknown:
                    errors.append(f"{label} references unknown coverage questions: {', '.join(unknown)}")
        elif not meaningful(entry.get("rationale")):
            errors.append(f"{label}.rationale must justify not-applicable")
    if profile in {"bounded-systematic", "comprehensive-systematic"} or rating >= 4:
        missing = sorted(REQUIRED_PERSPECTIVES - set(basis_by_perspective))
        if missing:
            errors.append("coverage basis omits required perspectives: " + ", ".join(missing))

    narrow_exception = semantic.get("narrow_topic_exception")
    exception_valid = False
    if isinstance(narrow_exception, dict):
        review = narrow_exception.get("independent_review")
        exception_valid = (
            meaningful(narrow_exception.get("rationale"))
            and meaningful(narrow_exception.get("scope_limit"))
            and isinstance(review, dict)
            and review.get("self_review") is False
            and {"context", "evaluation", "advancement_authority"}.issubset(set(map(str, review.get("dimensions", []))))
        )
        if not exception_valid:
            errors.append("narrow_topic_exception requires substantive limits and materially independent review")
    for perspective in DEFAULT_CRITICAL_PERSPECTIVES:
        entry = basis_by_perspective.get(perspective)
        if entry and entry.get("applicability") == "not-applicable" and not exception_valid:
            errors.append(f"critical coverage perspective {perspective} cannot be not-applicable without a narrow-topic exception")

    seed_entries = semantic.get("seed_classifications")
    if not isinstance(seed_entries, list):
        errors.append("semantic_assurance.seed_classifications must be a list")
        seed_entries = []
    observed_classes: set[str] = set()
    classified_seed_ids: set[str] = set()
    for index, entry in enumerate(seed_entries, 1):
        label = f"semantic_assurance.seed_classifications[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{label} must be an object")
            continue
        record_id = str(entry.get("record_id", ""))
        classes = entry.get("classes")
        if record_id not in record_ids or record_id not in seed_ids:
            errors.append(f"{label}.record_id must be a declared corpus seed")
        classified_seed_ids.add(record_id)
        if not isinstance(classes, list) or not classes:
            errors.append(f"{label}.classes must be non-empty")
        else:
            observed_classes.update(str(value) for value in classes)
    if rating >= 4 and not exception_valid:
        missing_classes = sorted(REQUIRED_SEED_CLASSES - observed_classes)
        if missing_classes:
            errors.append("strong novelty requires seed classes: " + ", ".join(missing_classes))
        if len(seed_ids) < 3 or len(record_ids) < 3:
            errors.append("strong novelty requires at least three declared seeds and three corpus records unless a narrow-topic exception is recorded")
    unclassified = seed_ids - classified_seed_ids
    if unclassified:
        errors.append("declared seeds lack semantic classification: " + ", ".join(sorted(unclassified)))

    criticality_decisions = semantic.get("criticality_decisions")
    if not isinstance(criticality_decisions, list):
        errors.append("semantic_assurance.criticality_decisions must be a list")
        criticality_decisions = []
    decision_ids: set[str] = set()
    authorization_ids: set[str] = set()
    for index, entry in enumerate(criticality_decisions, 1):
        label = f"semantic_assurance.criticality_decisions[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{label} must be an object")
            continue
        question_id = str(entry.get("question_id", ""))
        if question_id not in questions_by_id:
            errors.append(f"{label} references unknown question {question_id}")
        if entry.get("decision") not in {"downgrade-priority", "not-novelty-critical", "out-of-scope"}:
            errors.append(f"{label}.decision must be a controlled downgrade decision")
        if not meaningful(entry.get("rationale")) or not meaningful(entry.get("authorization_id")):
            errors.append(f"{label} requires rationale and authorization_id")
        else:
            authorization_id = str(entry["authorization_id"])
            if authorization_id in authorization_ids:
                errors.append(f"criticality authorization {authorization_id} is reused")
            authorization_ids.add(authorization_id)
            decision_ids.add(question_id)
    for perspective in DEFAULT_CRITICAL_PERSPECTIVES:
        entry = basis_by_perspective.get(perspective)
        if not entry:
            continue
        for question_id in entry.get("question_ids", []):
            question = questions_by_id.get(str(question_id), {})
            if question.get("priority") != "high" or question.get("critical_for_novelty") is not True:
                if str(question_id) not in decision_ids:
                    errors.append(f"coverage question {question_id} downgrades default novelty criticality without a recorded decision")

    saturation_entries = semantic.get("saturation_evidence")
    if not isinstance(saturation_entries, list):
        errors.append("semantic_assurance.saturation_evidence must be a list")
        saturation_entries = []
    saturation_by_question = {
        str(entry.get("question_id")): entry
        for entry in saturation_entries
        if isinstance(entry, dict) and meaningful(entry.get("question_id"))
    }
    for question_id, question in questions_by_id.items():
        if question.get("status") != "saturated":
            continue
        evidence = saturation_by_question.get(question_id)
        if not evidence:
            errors.append(f"saturated question {question_id} lacks saturation evidence")
            continue
        mode = evidence.get("mode")
        if mode == "rounds":
            rounds = evidence.get("rounds")
            if not isinstance(rounds, list) or len(rounds) < 2:
                errors.append(f"saturated question {question_id} requires at least two search rounds")
            else:
                yields = [entry.get("included_yield") for entry in rounds if isinstance(entry, dict)]
                if len(yields) != len(rounds) or any(not isinstance(value, int) or value < 0 for value in yields):
                    errors.append(f"saturated question {question_id} rounds require non-negative included_yield values")
                elif any(b > a for a, b in zip(yields, yields[1:])):
                    errors.append(f"saturated question {question_id} must show non-increasing marginal yield")
                ordered_run_ids = [str(entry.get("run_id")) for entry in rounds if isinstance(entry, dict)]
                run_ids = set(ordered_run_ids)
                if len(run_ids) != len(ordered_run_ids):
                    errors.append(f"saturated question {question_id} requires distinct search rounds")
                if len(yields) >= 2 and not any(b < a for a, b in zip(yields, yields[1:])):
                    errors.append(f"saturated question {question_id} must show at least one strict marginal-yield decline")
                declared_runs = {str(value) for value in question.get("search_run_ids", [])}
                if not run_ids.issubset(declared_runs):
                    errors.append(f"saturated question {question_id} saturation runs must be reciprocal search_run_ids")
        elif mode == "hard-source-boundary":
            if not meaningful(evidence.get("boundary")) or not meaningful(evidence.get("disproportionality_rationale")):
                errors.append(f"saturated question {question_id} hard boundary requires boundary and rationale")
        else:
            errors.append(f"saturated question {question_id} saturation mode must be rounds or hard-source-boundary")

    if not isinstance(challenge, dict) or challenge.get("schema_version") != "1.0":
        errors.append("challenge evaluation must be a schema_version 1.0 object")
    else:
        declared_challenge = semantic.get("challenge_evaluation")
        if not isinstance(declared_challenge, dict):
            errors.append("semantic_assurance.challenge_evaluation must be an object")
        else:
            challenge_digest = canonical_digest(challenge)
            if declared_challenge.get("challenge_digest") != challenge_digest:
                errors.append("semantic_assurance.challenge_evaluation.challenge_digest mismatch")
            mode = challenge.get("mode")
            if mode not in {"withheld", "independent-review", "unavailable"}:
                errors.append("challenge mode must be withheld, independent-review, or unavailable")
            if declared_challenge.get("mode") != mode:
                errors.append("semantic_assurance.challenge_evaluation.mode must match the challenge file")
            records_challenge = challenge.get("challenge_records")
            if not isinstance(records_challenge, list):
                errors.append("challenge_records must be a list")
                records_challenge = []
            challenge_ids = {
                str(entry.get("record_id"))
                for entry in records_challenge
                if isinstance(entry, dict) and meaningful(entry.get("record_id"))
            }
            if mode == "withheld":
                if challenge.get("frozen_before_search") is not True or not meaningful(challenge.get("custodian")):
                    errors.append("withheld challenge evaluation requires pre-search freeze and a substantive custodian")
                if challenge.get("challenge_set_digest") != canonical_digest(records_challenge):
                    errors.append("withheld challenge_set_digest does not bind the exact challenge records")
                overlap = challenge_ids & seed_ids
                if overlap:
                    errors.append("withheld challenge records cannot also be visible seeds: " + ", ".join(sorted(overlap)))
            recovered = {str(value) for value in challenge.get("recovered_record_ids", []) if meaningful(value)}
            missed = {str(value) for value in challenge.get("initially_missed_record_ids", []) if meaningful(value)}
            if not recovered.issubset(challenge_ids) or not missed.issubset(challenge_ids):
                errors.append("challenge recovered/missed IDs must belong to challenge_records")
            if not recovered.issubset(record_ids):
                errors.append("recovered challenge records must be present in the frozen corpus")
            recall = 1.0 if not challenge_ids else len(recovered) / len(challenge_ids)
            weights = {
                str(entry.get("record_id")): float(entry.get("importance", 1.0))
                for entry in records_challenge
                if isinstance(entry, dict) and meaningful(entry.get("record_id"))
            }
            total_weight = sum(weights.values())
            weighted = 1.0 if not total_weight else sum(weights.get(record_id, 0.0) for record_id in recovered) / total_weight
            if not math.isclose(float(challenge.get("critical_paper_recall", -1)), recall, rel_tol=0, abs_tol=1e-12):
                errors.append("challenge critical_paper_recall does not match recovered challenge records")
            if not math.isclose(float(challenge.get("importance_weighted_recall", -1)), weighted, rel_tol=0, abs_tol=1e-12):
                errors.append("challenge importance_weighted_recall does not match declared weights")
            if missed:
                repairs = challenge.get("search_repairs")
                if not isinstance(repairs, list) or not repairs:
                    errors.append("missed challenge records require search repair records")
                else:
                    repaired_ids: set[str] = set()
                    for repair in repairs:
                        if not isinstance(repair, dict) or not meaningful(repair.get("repair_id")):
                            errors.append("each challenge search repair requires a stable repair_id")
                            continue
                        repaired_ids.update(map(str, repair.get("recovered_record_ids", [])))
                    if not missed.issubset(repaired_ids):
                        errors.append("challenge search repairs must account for every initially missed record")
            if rating >= 4:
                if mode == "unavailable":
                    errors.append("rating 4-5 requires a withheld challenge set or materially independent search review")
                if mode == "withheld" and not challenge_ids:
                    errors.append("rating 4-5 withheld challenge evaluation requires at least one critical challenge record")
                if mode == "withheld" and recovered != challenge_ids:
                    errors.append("rating 4-5 requires all critical withheld challenge records to be recovered after repair")
                if mode == "independent-review":
                    review = challenge.get("independence")
                    if not isinstance(review, dict) or review.get("self_review") is not False:
                        errors.append("independent search review cannot be self-review")
                    else:
                        dimensions = set(map(str, review.get("dimensions", [])))
                        if not {"context", "evaluation", "advancement_authority"}.issubset(dimensions):
                            errors.append("independent search review requires context, evaluation, and advancement_authority separation")
                    if not meaningful(challenge.get("review_artifact")) or not isinstance(challenge.get("findings"), list) or not challenge.get("findings"):
                        errors.append("independent search review requires a review artifact and substantive findings")

    prior_headers, prior_rows = parse_markdown_table(prior_art, {"# Prior-Art Matrix", "## Prior-Art Matrix"})
    required_prior_headers = {
        "Record ID",
        "Work",
        "Overlap",
        "Threat",
        "Surviving distinction",
        "Coverage question IDs",
    }
    if not required_prior_headers.issubset(set(prior_headers)):
        errors.append("prior-art matrix lacks substantive nearest-work columns")
    if not prior_rows:
        errors.append("prior-art matrix requires at least one substantive row")
    high_threat = False
    represented_critical: set[str] = set()
    for row in prior_rows:
        record_id = row.get("Record ID", "")
        if record_id not in record_ids:
            errors.append(f"prior-art row references unknown corpus record {record_id}")
        if not all(meaningful(row.get(field)) for field in required_prior_headers):
            errors.append(f"prior-art row {record_id or '<unknown>'} contains empty substantive fields")
        if row.get("Threat", "").strip().lower() in {"high", "critical", "kill-shot"}:
            high_threat = True
        row_questions = split_ids(row.get("Coverage question IDs", ""))
        unknown_row_questions = row_questions - set(questions_by_id)
        if unknown_row_questions:
            errors.append("prior-art row references unknown coverage questions: " + ", ".join(sorted(unknown_row_questions)))
        represented_critical.update(row_questions)
    critical_question_ids = {
        question_id
        for question_id, question in questions_by_id.items()
        if question.get("priority") == "high" and question.get("critical_for_novelty") is True
    }
    if rating >= 4 and not high_threat:
        errors.append("rating 4-5 requires at least one high, critical, or kill-shot nearest-work comparison")
    if rating >= 4 and not critical_question_ids.issubset(represented_critical):
        errors.append("prior-art matrix omits high-priority novelty-critical coverage questions")

    search_headers, search_rows = parse_markdown_table(
        novelty_search, {"# Novelty Search Log", "## Novelty Search Evidence"}
    )
    required_search_headers = {
        "Run ID",
        "Round",
        "Query or delegation",
        "Source",
        "Corpus record IDs",
        "Coverage question IDs",
    }
    if not required_search_headers.issubset(set(search_headers)) or not search_rows:
        errors.append("novelty search log requires substantive query or reciprocal delegation rows")
    search_run_ids: set[str] = set()
    search_sources: set[str] = set()
    search_rounds: set[int] = set()
    for row in search_rows:
        if not all(meaningful(row.get(field)) for field in required_search_headers):
            errors.append("novelty search row contains empty substantive fields")
        search_run_ids.add(row.get("Run ID", "").strip())
        search_sources.add(row.get("Source", "").strip().lower())
        try:
            search_rounds.add(int(row.get("Round", "")))
        except (TypeError, ValueError):
            errors.append("novelty search row Round must be an integer")
        unknown_records = split_ids(row.get("Corpus record IDs", "")) - record_ids
        unknown_questions = split_ids(row.get("Coverage question IDs", "")) - set(questions_by_id)
        if unknown_records:
            errors.append("novelty search row references unknown corpus records: " + ", ".join(sorted(unknown_records)))
        if unknown_questions:
            errors.append("novelty search row references unknown coverage questions: " + ", ".join(sorted(unknown_questions)))
    declared_question_runs = {str(run_id) for question in questions_by_id.values() for run_id in question.get("search_run_ids", [])}
    if not search_run_ids.issubset(declared_question_runs):
        errors.append("novelty search rows must delegate to reciprocal literature search_run_ids")
    if rating >= 4 and not exception_valid:
        if len(search_run_ids) < 3 or len(search_rounds) < 2 or len(search_sources) < 2:
            errors.append("rating 4-5 requires at least three search runs across two rounds and two sources unless a narrow-topic exception is recorded")

    if rating >= 4:
        objections = novelty.get("top_kill_shot_objections")
        if not isinstance(objections, list) or not objections or any(not meaningful(value) for value in objections):
            errors.append("rating 4-5 requires at least one substantive kill-shot objection")
        if not meaningful(novelty.get("what_would_change_the_decision")):
            errors.append("rating 4-5 requires a substantive statement of what would lower or change the decision")
        missing_prior = novelty.get("missing_prior_work")
        if isinstance(missing_prior, list) and missing_prior:
            errors.append("rating 4-5 cannot retain unresolved material missing-prior-work entries")
    return errors
