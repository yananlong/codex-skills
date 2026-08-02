#!/usr/bin/env python3
"""Validate paper claim-evidence bindings and their human-readable plan views."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "1.0"
STATUS_VALUES = {"draft", "complete"}
CLAIM_TYPES = {"primary", "supporting", "limitation", "context"}
EVIDENCE_MODES = {"empirical", "theoretical", "citation", "mixed", "limitation"}
SUPPORT_STATUSES = {"supported", "partial", "blocked", "contradicted", "withdrawn"}
MANUSCRIPT_ACTIONS = {"assert", "qualify", "limitation", "omit"}
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
POSITIVE_VERDICTS = {
    "supports_exploratory_follow_up",
    "supports_confirmatory_claim",
    "independently_verified",
    "supports_operational_high_stakes_claim",
}
NEGATIVE_VERDICTS = {"does_not_support_claim"}
IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,191}$")
REQUIRED_PLAN_HEADINGS = {
    "# Paper Plan",
    "## Header",
    "## Structure",
    "## Section Notes",
    "## Evidence Boundary",
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


def validate_identifier(value: Any, label: str, errors: list[str]) -> str:
    if not meaningful(value) or not IDENTIFIER_RE.fullmatch(str(value)):
        errors.append(f"{label} must use letters, numbers, dot, underscore, colon, or hyphen")
        return ""
    return str(value)


def substantive_string_list(value: Any, label: str, errors: list[str], *, nonempty: bool = False) -> list[str]:
    if not isinstance(value, list):
        errors.append(f"{label} must be a list")
        return []
    normalized: list[str] = []
    for index, item in enumerate(value, start=1):
        if not meaningful(item):
            errors.append(f"{label}[{index}] must be substantive")
            continue
        normalized.append(str(item))
    if len(normalized) != len(set(normalized)):
        errors.append(f"{label} contains duplicates")
    if nonempty and not normalized:
        errors.append(f"{label} must be non-empty")
    return normalized


def parse_table(markdown: str, heading: str, errors: list[str]) -> tuple[list[str], list[dict[str, str]]]:
    lines = markdown.splitlines()
    try:
        start = next(index for index, line in enumerate(lines) if line.strip() == heading)
    except StopIteration:
        errors.append(f"missing heading {heading!r}")
        return [], []
    table_start = None
    for index in range(start + 1, len(lines)):
        stripped = lines[index].strip()
        if stripped.startswith("#"):
            break
        if stripped.startswith("|") and stripped.endswith("|"):
            table_start = index
            break
    if table_start is None or table_start + 1 >= len(lines):
        errors.append(f"{heading} has no Markdown table")
        return [], []
    headers = [cell.strip() for cell in lines[table_start].strip().strip("|").split("|")]
    separator = lines[table_start + 1].strip()
    if not separator.startswith("|") or "---" not in separator:
        errors.append(f"{heading} table lacks a separator row")
        return headers, []
    rows: list[dict[str, str]] = []
    for line in lines[table_start + 2 :]:
        stripped = line.strip()
        if not stripped:
            if rows:
                break
            continue
        if stripped.startswith("#"):
            break
        if not (stripped.startswith("|") and stripped.endswith("|")):
            if rows:
                break
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if len(cells) != len(headers):
            errors.append(f"{heading} table row has {len(cells)} cells; expected {len(headers)}")
            continue
        if any(cells):
            rows.append(dict(zip(headers, cells)))
    return headers, rows


def split_ids(value: str) -> set[str]:
    if not value.strip():
        return set()
    return {part.strip() for part in re.split(r"[,;]", value) if part.strip()}


def validate_claims(data: dict[str, Any], complete: bool, errors: list[str]) -> list[dict[str, Any]]:
    claims = data.get("claims")
    if not isinstance(claims, list):
        errors.append("claim-evidence-bindings.json.claims must be a list")
        return []
    if complete and not claims:
        errors.append("complete paper plan requires at least one claim binding")
    seen: set[str] = set()
    normalized: list[dict[str, Any]] = []
    for index, claim in enumerate(claims, start=1):
        label = f"claim-evidence-bindings.json.claims[{index}]"
        if not isinstance(claim, dict):
            errors.append(f"{label} must be an object")
            continue
        claim_id = validate_identifier(claim.get("paper_claim_id"), f"{label}.paper_claim_id", errors)
        if claim_id in seen:
            errors.append(f"duplicate paper_claim_id: {claim_id}")
        seen.add(claim_id)
        claim_type = claim.get("claim_type")
        evidence_mode = claim.get("evidence_mode")
        support = claim.get("support_status")
        action = claim.get("manuscript_action")
        required = claim.get("required_assurance_class")
        if claim_type not in CLAIM_TYPES:
            errors.append(f"{label}.claim_type must be one of {sorted(CLAIM_TYPES)}")
        if evidence_mode not in EVIDENCE_MODES:
            errors.append(f"{label}.evidence_mode must be one of {sorted(EVIDENCE_MODES)}")
        if support not in SUPPORT_STATUSES:
            errors.append(f"{label}.support_status must be one of {sorted(SUPPORT_STATUSES)}")
        if action not in MANUSCRIPT_ACTIONS:
            errors.append(f"{label}.manuscript_action must be one of {sorted(MANUSCRIPT_ACTIONS)}")
        if required not in ASSURANCE_CLASSES:
            errors.append(f"{label}.required_assurance_class must be one of {sorted(ASSURANCE_CLASSES)}")
        if complete:
            for field in ("claim", "scope", "rationale"):
                if not meaningful(claim.get(field)):
                    errors.append(f"{label}.{field} must be substantive")
        source_claim_ids = substantive_string_list(
            claim.get("source_claim_ids"), f"{label}.source_claim_ids", errors
        )
        audit_ids = substantive_string_list(claim.get("audit_ids"), f"{label}.audit_ids", errors)
        evidence_artifacts = substantive_string_list(
            claim.get("evidence_artifacts"), f"{label}.evidence_artifacts", errors
        )
        planned_sections = substantive_string_list(
            claim.get("planned_sections"), f"{label}.planned_sections", errors
        )
        exhibit_ids = substantive_string_list(claim.get("exhibit_ids"), f"{label}.exhibit_ids", errors)
        citation_ids = substantive_string_list(
            claim.get("citation_need_ids"), f"{label}.citation_need_ids", errors
        )
        limitations = substantive_string_list(claim.get("limitations"), f"{label}.limitations", errors)
        missing = substantive_string_list(
            claim.get("missing_evidence"), f"{label}.missing_evidence", errors
        )
        if action == "qualify" and not limitations:
            errors.append(f"{label}: manuscript_action=qualify requires explicit limitations")
        if complete and support != "withdrawn" and not planned_sections:
            errors.append(f"{label}.planned_sections must be non-empty for an active claim")
        if support == "supported" and action == "omit":
            errors.append(f"{label}: supported claim cannot use manuscript_action=omit")
        if support == "partial":
            if action not in {"qualify", "limitation"}:
                errors.append(f"{label}: partial claim must be qualified or presented as a limitation")
            if not limitations or not missing:
                errors.append(f"{label}: partial claim requires limitations and missing_evidence")
        if support in {"blocked", "contradicted", "withdrawn"} and action not in {"omit", "limitation"}:
            errors.append(f"{label}: {support} claim cannot be asserted or merely qualified")
        if support == "blocked" and not missing:
            errors.append(f"{label}: blocked claim requires missing_evidence")
        if support == "contradicted" and not limitations:
            errors.append(f"{label}: contradicted claim requires limitations")
        if evidence_mode in {"empirical", "mixed"} and required == "none" and support in {"supported", "partial"}:
            errors.append(f"{label}: empirical or mixed active claim requires a non-none assurance class")
        if complete and evidence_mode in {"empirical", "mixed"} and support in {"supported", "partial", "contradicted"}:
            if not source_claim_ids:
                errors.append(f"{label}: empirical or mixed claim requires source_claim_ids")
            if not audit_ids:
                errors.append(f"{label}: empirical or mixed claim requires audit_ids")
        if complete and evidence_mode == "theoretical" and support == "supported" and not evidence_artifacts:
            errors.append(f"{label}: supported theoretical claim requires evidence_artifacts")
        if complete and evidence_mode == "citation" and support == "supported" and not citation_ids:
            errors.append(f"{label}: supported citation claim requires citation_need_ids")
        if claim_type == "limitation" and action not in {"limitation", "omit"}:
            errors.append(f"{label}: limitation claim must use manuscript_action=limitation or omit")
        normalized.append(claim)
    return normalized


def validate_markdown_views(
    claims: list[dict[str, Any]], matrix: str, figure: str, citation: str, complete: bool, errors: list[str]
) -> None:
    matrix_headers, matrix_rows = parse_table(matrix, "# Claims-Evidence Matrix", errors)
    required_matrix_headers = {
        "Paper claim ID",
        "Claim",
        "Type",
        "Evidence mode",
        "Support status",
        "Manuscript action",
        "Required assurance",
        "Source claim IDs",
        "Audit IDs",
        "Planned sections",
        "Exhibit IDs",
        "Citation need IDs",
        "Limitation",
    }
    if set(matrix_headers) != required_matrix_headers:
        errors.append("claims-evidence-matrix.md table headers do not match the binding contract")
    matrix_by_id: dict[str, dict[str, str]] = {}
    for row in matrix_rows:
        claim_id = row.get("Paper claim ID", "")
        if claim_id in matrix_by_id:
            errors.append(f"claims-evidence-matrix.md contains duplicate paper claim ID {claim_id}")
        matrix_by_id[claim_id] = row

    figure_headers, figure_rows = parse_table(figure, "# Figure Plan", errors)
    if set(figure_headers) != {"Exhibit ID", "Purpose", "Paper claim IDs", "Priority", "Status", "Notes"}:
        errors.append("figure-plan.md table headers do not match the binding contract")
    exhibit_map = {row.get("Exhibit ID", ""): split_ids(row.get("Paper claim IDs", "")) for row in figure_rows}
    if len(exhibit_map) != len(figure_rows):
        errors.append("figure-plan.md contains duplicate exhibit IDs")

    citation_headers, citation_rows = parse_table(citation, "# Citation Plan", errors)
    if set(citation_headers) != {"Citation need ID", "Paper claim IDs", "Citation need", "Source status", "Notes"}:
        errors.append("citation-plan.md table headers do not match the binding contract")
    citation_map = {
        row.get("Citation need ID", ""): split_ids(row.get("Paper claim IDs", ""))
        for row in citation_rows
    }
    if len(citation_map) != len(citation_rows):
        errors.append("citation-plan.md contains duplicate citation need IDs")

    known_claim_ids = {str(claim.get("paper_claim_id")) for claim in claims}
    if complete:
        extra_matrix_ids = set(matrix_by_id) - known_claim_ids
        if extra_matrix_ids:
            errors.append(
                "claims-evidence-matrix.md contains noncanonical claim rows: "
                + ", ".join(sorted(extra_matrix_ids))
            )
    for exhibit_id, linked in exhibit_map.items():
        unknown = linked - known_claim_ids
        if unknown:
            errors.append(f"figure-plan.md exhibit {exhibit_id} references unknown claims: {', '.join(sorted(unknown))}")
    for citation_id, linked in citation_map.items():
        unknown = linked - known_claim_ids
        if unknown:
            errors.append(
                f"citation-plan.md citation need {citation_id} references unknown claims: {', '.join(sorted(unknown))}"
            )

    for claim in claims:
        claim_id = str(claim.get("paper_claim_id"))
        if complete:
            row = matrix_by_id.get(claim_id)
            if row is None:
                errors.append(f"claims-evidence-matrix.md missing row for {claim_id}")
            else:
                expected = {
                    "Claim": str(claim.get("claim", "")),
                    "Type": str(claim.get("claim_type", "")),
                    "Evidence mode": str(claim.get("evidence_mode", "")),
                    "Support status": str(claim.get("support_status", "")),
                    "Manuscript action": str(claim.get("manuscript_action", "")),
                    "Required assurance": str(claim.get("required_assurance_class", "")),
                }
                for field, value in expected.items():
                    if row.get(field) != value:
                        errors.append(f"claims-evidence-matrix.md {claim_id} field {field} disagrees with JSON")
                list_fields = {
                    "Source claim IDs": set(map(str, claim.get("source_claim_ids", []))),
                    "Audit IDs": set(map(str, claim.get("audit_ids", []))),
                    "Planned sections": set(map(str, claim.get("planned_sections", []))),
                    "Exhibit IDs": set(map(str, claim.get("exhibit_ids", []))),
                    "Citation need IDs": set(map(str, claim.get("citation_need_ids", []))),
                }
                for field, values in list_fields.items():
                    if split_ids(row.get(field, "")) != values:
                        errors.append(f"claims-evidence-matrix.md {claim_id} field {field} disagrees with JSON")
                if claim.get("limitations") and not row.get("Limitation", "").strip():
                    errors.append(f"claims-evidence-matrix.md {claim_id} omits the JSON limitation")
        for exhibit_id in claim.get("exhibit_ids", []):
            if exhibit_id not in exhibit_map:
                errors.append(f"claim {claim_id} references unknown exhibit ID {exhibit_id}")
            elif claim_id not in exhibit_map[exhibit_id]:
                errors.append(f"figure-plan.md exhibit {exhibit_id} does not reciprocally reference {claim_id}")
        for citation_id in claim.get("citation_need_ids", []):
            if citation_id not in citation_map:
                errors.append(f"claim {claim_id} references unknown citation need ID {citation_id}")
            elif claim_id not in citation_map[citation_id]:
                errors.append(f"citation-plan.md citation need {citation_id} does not reciprocally reference {claim_id}")


def validate_linked(
    data: dict[str, Any],
    claims: list[dict[str, Any]],
    commitment: Any,
    claim_map: Any,
    results_audit: Any,
    errors: list[str],
) -> None:
    if not isinstance(commitment, dict):
        errors.append("linked profile requires commitment JSON object")
        return
    if data.get("paper_id") != commitment.get("paper_id"):
        errors.append("paper binding paper_id does not match commitment")
    if data.get("identity_version") != commitment.get("identity_version"):
        errors.append("paper binding identity_version does not match commitment")
    if not isinstance(claim_map, list):
        errors.append("linked profile requires claim-map JSON array")
        source_claim_ids: set[str] = set()
    else:
        source_claim_ids = {
            str(entry.get("claim_id"))
            for entry in claim_map
            if isinstance(entry, dict) and meaningful(entry.get("claim_id"))
        }
    if not isinstance(results_audit, dict):
        errors.append("linked profile requires results-audit JSON object")
        return
    if results_audit.get("status") != "complete":
        errors.append("linked paper plan requires results-audit.status=complete")
    if results_audit.get("paper_id") != data.get("paper_id"):
        errors.append("results-audit paper_id does not match paper binding")
    if results_audit.get("identity_version") != data.get("identity_version"):
        errors.append("results-audit identity_version does not match paper binding")
    audit_index: dict[str, dict[str, Any]] = {}
    for audit in results_audit.get("audits", []):
        if not isinstance(audit, dict) or not meaningful(audit.get("audit_id")):
            continue
        audit_id = str(audit["audit_id"])
        if audit_id in audit_index:
            errors.append(f"results-audit contains duplicate audit_id {audit_id}")
        audit_index[audit_id] = audit

    for claim in claims:
        claim_id = claim.get("paper_claim_id", "<unknown>")
        unknown_sources = set(map(str, claim.get("source_claim_ids", []))) - source_claim_ids
        if unknown_sources:
            errors.append(f"paper claim {claim_id} references unknown source claims: {', '.join(sorted(unknown_sources))}")
        linked: list[dict[str, Any]] = []
        for audit_id in claim.get("audit_ids", []):
            audit = audit_index.get(str(audit_id))
            if audit is None:
                errors.append(f"paper claim {claim_id} references unknown audit_id {audit_id}")
                continue
            linked.append(audit)
            if audit.get("claim_id") not in claim.get("source_claim_ids", []):
                errors.append(
                    f"paper claim {claim_id} audit {audit_id} targets claim {audit.get('claim_id')} outside source_claim_ids"
                )
        mode = claim.get("evidence_mode")
        support = claim.get("support_status")
        action = claim.get("manuscript_action")
        required = claim.get("required_assurance_class")
        positive = [
            audit
            for audit in linked
            if audit.get("verdict") in POSITIVE_VERDICTS
            and audit.get("audited_claim_effect") == "strengthen"
        ]
        adequate = [
            audit
            for audit in positive
            if audit.get("attained_assurance_class") in ASSURANCE_RANK
            and required in ASSURANCE_RANK
            and ASSURANCE_RANK[audit["attained_assurance_class"]] >= ASSURANCE_RANK[required]
        ]
        negative = [
            audit
            for audit in linked
            if audit.get("verdict") in NEGATIVE_VERDICTS
            or audit.get("audited_claim_effect") in {"weaken", "kill"}
        ]
        inconclusive = [
            audit
            for audit in linked
            if audit.get("verdict") == "inconclusive"
            or audit.get("audited_claim_effect") in {"inconclusive", "unchanged"}
        ]
        if mode in {"empirical", "mixed"}:
            if support == "supported" and not adequate:
                errors.append(
                    f"paper claim {claim_id} lacks a positive audit at required assurance class {required}"
                )
            if support == "partial" and not positive and not inconclusive:
                errors.append(f"paper claim {claim_id} partial status lacks positive or inconclusive audit evidence")
            if support == "contradicted" and not negative:
                errors.append(f"paper claim {claim_id} contradicted status lacks negative audit evidence")
            if support == "contradicted" and adequate:
                errors.append(
                    f"paper claim {claim_id} cannot be marked contradicted while adequate positive audit evidence remains"
                )
            if action == "assert" and negative:
                errors.append(f"paper claim {claim_id} cannot be asserted while linked negative audits remain")
            if action == "assert" and not adequate:
                errors.append(f"paper claim {claim_id} cannot be asserted without adequate positive audit evidence")
            audited_paths = {
                artifact.get("path")
                for audit in linked
                for artifact in audit.get("evidence_artifacts", [])
                if isinstance(artifact, dict) and meaningful(artifact.get("path"))
            }
            missing_paths = set(map(str, claim.get("evidence_artifacts", []))) - audited_paths
            if missing_paths:
                errors.append(
                    f"paper claim {claim_id} evidence_artifacts are absent from linked audits: {', '.join(sorted(missing_paths))}"
                )
        if support == "blocked" and adequate:
            errors.append(f"paper claim {claim_id} is marked blocked despite adequate positive audit evidence")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--matrix", required=True, type=Path)
    parser.add_argument("--bindings", required=True, type=Path)
    parser.add_argument("--figure-plan", required=True, type=Path)
    parser.add_argument("--citation-plan", required=True, type=Path)
    parser.add_argument("--assurance-profile", choices=("structural", "linked"), default="structural")
    parser.add_argument("--commitment", type=Path)
    parser.add_argument("--claim-map", type=Path)
    parser.add_argument("--results-audit", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    errors: list[str] = []
    plan = read_text(args.plan, "paper plan", errors)
    matrix = read_text(args.matrix, "claims-evidence matrix", errors)
    figure = read_text(args.figure_plan, "figure plan", errors)
    citation = read_text(args.citation_plan, "citation plan", errors)
    data = read_json(args.bindings, "claim-evidence bindings", errors)
    for heading in REQUIRED_PLAN_HEADINGS:
        if heading not in plan:
            errors.append(f"paper-plan.md missing heading {heading!r}")
    if not isinstance(data, dict):
        if data is not None:
            errors.append("claim-evidence-bindings JSON must be an object")
        claims: list[dict[str, Any]] = []
    else:
        if data.get("schema_version") != SCHEMA_VERSION:
            errors.append(f"claim-evidence-bindings.schema_version must equal {SCHEMA_VERSION}")
        status = data.get("status")
        if status not in STATUS_VALUES:
            errors.append(f"claim-evidence-bindings.status must be one of {sorted(STATUS_VALUES)}")
        if not isinstance(data.get("identity_version"), int) or data.get("identity_version", 0) < 1:
            errors.append("claim-evidence-bindings.identity_version must be a positive integer")
        complete = status == "complete"
        if complete and not meaningful(data.get("paper_id")):
            errors.append("complete claim-evidence bindings require substantive paper_id")
        claims = validate_claims(data, complete, errors)
        validate_markdown_views(claims, matrix, figure, citation, complete, errors)
        if args.assurance_profile == "linked":
            if status != "complete":
                errors.append("linked assurance profile requires claim-evidence-bindings.status=complete")
            if not all((args.commitment, args.claim_map, args.results_audit)):
                errors.append("linked profile requires --commitment, --claim-map, and --results-audit")
            else:
                commitment = read_json(args.commitment, "commitment", errors)
                claim_map = read_json(args.claim_map, "claim-map", errors)
                results_audit = read_json(args.results_audit, "results-audit", errors)
                validate_linked(data, claims, commitment, claim_map, results_audit, errors)
    if errors:
        print("Validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    if args.assurance_profile == "linked":
        print(
            "Validation passed: paper claims, manuscript actions, source claim IDs, result-audit verdicts, "
            "assurance thresholds, evidence artifacts, exhibits, citations, and Markdown views are internally linked. "
            "This does not establish that the underlying evidence is scientifically valid or independently verified "
            "beyond the recorded audit properties."
        )
    else:
        print(
            "Validation passed: the paper-planning pack and claim-evidence bindings are structurally consistent. "
            "This does not establish evidential sufficiency, citation correctness, or manuscript validity."
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
