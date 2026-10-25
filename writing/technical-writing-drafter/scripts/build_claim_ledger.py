#!/usr/bin/env python3
"""Build the claim ledger a draft may assert from, out of the project's artifacts.

The ledger is the drafting contract's claim list, derived from machine-readable
sources instead of written from memory. Each entry records where the claim comes
from, what supports it, and whether the draft may assert it (``ready``), must
qualify it (``careful``), or may only mark it as missing (``blocked``).

Sources, any subset:
    --bindings claim-evidence-bindings.json      (research-paper-plan; authoritative when present)
    --results-audit results-audit.json           (research-results-auditor)
    --claim-map claim-map.json                   (research-experiment-plan)
    --evidence-table <topic>.evidence-table.md   (research-systematic-literature-review)
    --issue-board issue-board.md                 (research-rebuttal)
    --intake writing-intake.json                 (from inventory_artifacts.py; picks the above up by kind)

Usage:
    build_claim_ledger.py [sources] [--out-json claim-ledger.json] [--out-md claim-ledger.md]

Exit status 0 when a ledger was written (a malformed source is skipped with a warning and
listed under ``skipped_sources``), 1 when no source yielded a claim, 2 when the intake record
itself is unreadable.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SUPPORT_BY_MODE = {
    "empirical": "measured",
    "theoretical": "formal",
    "citation": "cited",
    "mixed": "measured",
    "limitation": "argued",
}

STATUS_BY_SUPPORT_STATUS = {
    "supported": "ready",
    "partial": "careful",
    "blocked": "blocked",
    "contradicted": "blocked",
    "withdrawn": "excluded",
}

STATUS_BY_CLAIM_EFFECT = {
    "strengthen": "ready",
    "unchanged": "ready",
    "weaken": "careful",
    "kill": "blocked",
    "inconclusive": "blocked",
}

STATUS_ORDER = {"ready": 0, "careful": 1, "blocked": 2, "excluded": 3}


class SourceError(Exception):
    pass


def load_json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SourceError(f"{path}: {exc}") from exc


def as_list(value: object, path: Path, key: str) -> list:
    if isinstance(value, list):
        return value
    if isinstance(value, dict) and isinstance(value.get(key), list):
        return value[key]
    raise SourceError(f"{path}: expected a list or an object with a '{key}' list")


def text_of(record: dict, *keys: str) -> str:
    for key in keys:
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def entry(
    *,
    claim_id: str,
    text: str,
    support: str,
    status: str,
    source_kind: str,
    source_path: str,
    locator: str,
    sections: list[str] | None = None,
    evidence: list[str] | None = None,
    limitations: list[str] | None = None,
    missing: list[str] | None = None,
    notes: str = "",
) -> dict:
    return {
        "id": claim_id,
        "text": text,
        "support": support,
        "status": status,
        "source": {"kind": source_kind, "path": source_path, "locator": locator},
        "sections": sections or [],
        "evidence": evidence or [],
        "limitations": limitations or [],
        "missing_evidence": missing or [],
        "notes": notes,
    }


def from_bindings(path: Path) -> list[dict]:
    data = load_json(path)
    claims = as_list(data, path, "claims")
    out: list[dict] = []
    for index, claim in enumerate(claims):
        if not isinstance(claim, dict):
            raise SourceError(f"{path}: claims[{index}] is not an object")
        claim_id = text_of(claim, "paper_claim_id") or f"PC-{index + 1}"
        support_status = text_of(claim, "support_status")
        status = STATUS_BY_SUPPORT_STATUS.get(support_status, "blocked")
        action = text_of(claim, "manuscript_action")
        if action == "omit":
            status = "excluded"
        elif action == "limitation" and status == "ready":
            status = "careful"
        mode = text_of(claim, "evidence_mode")
        support = SUPPORT_BY_MODE.get(mode, "missing")
        if status in {"blocked", "excluded"}:
            support = "missing" if support_status != "contradicted" else "contradicted"
        notes = []
        if action:
            notes.append(f"manuscript_action={action}")
        if text_of(claim, "scope"):
            notes.append(f"scope: {text_of(claim, 'scope')}")
        out.append(
            entry(
                claim_id=claim_id,
                text=text_of(claim, "claim", "claim_text", "statement"),
                support=support,
                status=status,
                source_kind="paper_plan.bindings",
                source_path=path.as_posix(),
                locator=f"claims[{index}]",
                sections=[str(s) for s in claim.get("planned_sections", []) if isinstance(s, str)],
                evidence=[str(e) for e in claim.get("evidence_artifacts", []) if isinstance(e, str)],
                limitations=[str(l) for l in claim.get("limitations", []) if isinstance(l, str)],
                missing=[str(m) for m in claim.get("missing_evidence", []) if isinstance(m, str)],
                notes="; ".join(notes),
            )
        )
    return out


def from_results_audit(path: Path) -> list[dict]:
    data = load_json(path)
    audits = as_list(data, path, "audits")
    out: list[dict] = []
    for index, audit in enumerate(audits):
        if not isinstance(audit, dict):
            raise SourceError(f"{path}: audits[{index}] is not an object")
        effect = text_of(audit, "audited_claim_effect")
        status = STATUS_BY_CLAIM_EFFECT.get(effect, "blocked")
        evidence = []
        for item in audit.get("evidence_artifacts", []) or []:
            if isinstance(item, dict) and isinstance(item.get("path"), str):
                evidence.append(item["path"])
            elif isinstance(item, str):
                evidence.append(item)
        notes = []
        if text_of(audit, "verdict"):
            notes.append(f"verdict: {text_of(audit, 'verdict')}")
        if text_of(audit, "scope"):
            notes.append(f"scope: {text_of(audit, 'scope')}")
        if text_of(audit, "attained_assurance_class"):
            notes.append(f"assurance: {text_of(audit, 'attained_assurance_class')}")
        anchor = text_of(audit, "narrative_anchor")
        out.append(
            entry(
                claim_id=text_of(audit, "claim_id") or text_of(audit, "audit_id") or f"AUD-{index + 1}",
                text=text_of(audit, "claim_text", "claim", "statement"),
                support="measured" if status != "blocked" else "missing",
                status=status,
                source_kind="results_audit",
                source_path=path.as_posix(),
                locator=f"audits[{index}]" + (f" ({text_of(audit, 'audit_id')})" if text_of(audit, "audit_id") else ""),
                sections=["results"] + (["limitations"] if status == "careful" else []),
                evidence=evidence,
                limitations=[str(l) for l in audit.get("limitations", []) or [] if isinstance(l, str)],
                notes="; ".join(notes + ([f"anchor: {anchor}"] if anchor else [])),
            )
        )
    return out


def from_claim_map(path: Path) -> list[dict]:
    data = load_json(path)
    claims = as_list(data, path, "claims")
    out: list[dict] = []
    for index, claim in enumerate(claims):
        if not isinstance(claim, dict):
            raise SourceError(f"{path}: claims[{index}] is not an object")
        out.append(
            entry(
                claim_id=text_of(claim, "claim_id") or f"C{index + 1}",
                text=text_of(claim, "claim", "claim_text", "statement"),
                support="planned",
                status="blocked",
                source_kind="experiment_plan.claim_map",
                source_path=path.as_posix(),
                locator=f"claims[{index}]",
                sections=["method"],
                missing=["a results audit or data table that tests this claim"],
                notes="; ".join(
                    part
                    for part in (
                        f"evidence_class: {text_of(claim, 'evidence_class')}" if text_of(claim, "evidence_class") else "",
                        f"falsifier: {text_of(claim, 'falsifier')}" if text_of(claim, "falsifier") else "",
                        f"anti-claim: {text_of(claim, 'anti_claim')}" if text_of(claim, "anti_claim") else "",
                        f"anti-claims: {len(claim['anti_claims'])}" if isinstance(claim.get("anti_claims"), list) and claim["anti_claims"] else "",
                    )
                    if part
                ),
            )
        )
    return out


def parse_pipe_table(text: str) -> list[dict[str, str]]:
    """Parse the first Markdown pipe table in ``text`` into row dicts."""
    rows: list[dict[str, str]] = []
    header: list[str] | None = None
    for raw in text.splitlines():
        line = raw.strip()
        if not line.startswith("|"):
            if header is not None and rows:
                break
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if header is None:
            # "Issue ID", "issue_id" and "Issue id" are the same column.
            header = [re.sub(r"[^a-z0-9]+", "_", c.strip("`* ").lower()).strip("_") for c in cells]
            continue
        if all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
            continue
        if len(cells) < len(header):
            cells += [""] * (len(header) - len(cells))
        rows.append(dict(zip(header, cells[: len(header)])))
    return rows


EVIDENCE_ALIASES = {
    "id": ("study_id", "id", "work", "source", "citation", "canonical_citation"),
    "citation": ("canonical_citation", "citation", "work", "source", "title"),
    "result": (
        "key_result", "extracted_finding", "method_or_finding", "relevant_claim", "key_finding", "finding",
        "relevance_to_this_project", "target_and_method", "evaluator_change_signal", "relation_to_paper", "coverage",
    ),
    "quote": ("quote", "verbatim_quote"),
    "fetch_status": ("fetch_status", "access_level"),
    "rung": ("rung",),
}


def pick(row: dict[str, str], field: str) -> str | None:
    """Return the first aliased column present in the row (None when the table lacks it)."""
    for name in EVIDENCE_ALIASES[field]:
        if name in row:
            return row[name].strip()
    return None


def from_evidence_table(path: Path) -> list[dict]:
    """Evidence tables vary across review generations; read the columns that exist.

    The canonical template has ``study_id``, ``fetch_status``, ``rung`` and ``quote``. Older or
    free-form tables (``Work | Status | ...``, ``ID | Citation | ...``) have none of these, so
    their rows cannot be ``ready``: they become ``careful`` with a note to confirm the source,
    rather than ``blocked``, which is reserved for a row the table itself marks as not read or
    without a quote.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise SourceError(f"{path}: {exc}") from exc
    rows = parse_pipe_table(text)
    if not rows:
        raise SourceError(f"{path}: no pipe table")
    header = list(rows[0])
    id_col = next((c for c in EVIDENCE_ALIASES["id"] if c in header), header[0])
    has_quote_col = any(c in header for c in EVIDENCE_ALIASES["quote"])
    has_fetch_col = any(c in header for c in EVIDENCE_ALIASES["fetch_status"])
    out: list[dict] = []
    for index, row in enumerate(rows):
        study = (row.get(id_col) or "").strip() or f"S{index + 1}"
        study_id = re.sub(r"\s+", " ", re.sub(r"[\[\]\(\)*`]", "", study))[:60]
        fetch = (pick(row, "fetch_status") or "").lower()
        rung = pick(row, "rung") or ""
        quote = pick(row, "quote") or ""
        result = pick(row, "result") or ""
        citation = pick(row, "citation") or ""
        missing: list[str] = []
        if has_fetch_col and fetch not in {"read", "full", "full-text", "full text"}:
            status = "blocked"
            missing.append(f"source not read (fetch_status={fetch or 'unset'})")
        elif has_quote_col and not quote:
            status = "blocked"
            missing.append("no verbatim quote anchors this result")
        elif not has_quote_col or not has_fetch_col:
            status = "careful"
            missing.append("table predates the fetch_status/quote columns: confirm the source before asserting")
        elif rung in {"3", "4"}:
            status = "careful"
        else:
            status = "ready"
        out.append(
            entry(
                claim_id=f"LIT-{study_id}",
                text=result or f"[CITATION NEEDED: what {study_id} shows]",
                support="cited" if status != "blocked" else "missing",
                status=status,
                source_kind="literature.evidence_table",
                source_path=path.as_posix(),
                locator=f"row {index + 1} ({study_id})",
                sections=["related_work"],
                evidence=[citation] if citation else [],
                missing=missing,
                notes="; ".join(
                    part for part in (f"rung {rung}" if rung else "", f"quote: {quote[:120]}" if quote else "") if part
                ),
            )
        )
    return out


def from_issue_board(path: Path) -> list[dict]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise SourceError(f"{path}: {exc}") from exc
    rows = parse_pipe_table(text)
    if not rows or "issue_id" not in rows[0]:
        raise SourceError(f"{path}: no pipe table with an issue_id column")
    out: list[dict] = []
    for index, row in enumerate(rows):
        issue = row.get("issue_id", "") or f"EXT-{index + 1}"
        strategy = row.get("strategy", "").strip()
        state = row.get("status", "").strip().lower()
        if not strategy:
            status = "blocked"
            missing = ["no response strategy decided on the issue board"]
        elif state in {"open", "undecided", "todo", ""}:
            status = "careful"
            missing = []
        else:
            status = "ready"
            missing = []
        summary = row.get("summary", "") or row.get("issue", "") or row.get("concern", "")
        out.append(
            entry(
                claim_id=f"RESP-{issue}",
                text=summary or f"response to {issue}",
                support="argued",
                status=status,
                source_kind="rebuttal.issue_board",
                source_path=path.as_posix(),
                locator=f"row {index + 1} ({issue})",
                sections=["response"],
                missing=missing,
                notes="; ".join(
                    part
                    for part in (
                        f"reviewer {row.get('reviewer', '')}" if row.get("reviewer") else "",
                        f"strategy: {strategy}" if strategy else "",
                        f"severity: {row.get('severity', '')}" if row.get("severity") else "",
                    )
                    if part
                ),
            )
        )
    return out


def sources_from_intake(path: Path) -> dict[str, list[Path]]:
    data = load_json(path)
    if not isinstance(data, dict) or not isinstance(data.get("artifacts"), list):
        raise SourceError(f"{path}: not an intake record")
    root = Path(data.get("root", path.parent))
    picked: dict[str, list[Path]] = {}
    wanted = {
        "paper_plan.bindings": "bindings",
        "results_audit.json": "results_audit",
        "experiment_plan.claim_map": "claim_map",
        "literature.evidence_table": "evidence_table",
        "rebuttal.issue_board": "issue_board",
    }
    for artifact in data["artifacts"]:
        kind = artifact.get("kind") if isinstance(artifact, dict) else None
        if kind in wanted:
            picked.setdefault(wanted[kind], []).append(root / artifact["path"])
    return picked


def render_markdown(ledger: list[dict]) -> str:
    lines = ["# Claim ledger", ""]
    lines.append("The draft may assert `ready` claims, must qualify `careful` claims with their limitations, "
                 "and may only mark `blocked` claims with `[EVIDENCE NEEDED]` or `[CITATION NEEDED]`. "
                 "`excluded` claims do not appear.")
    lines.append("")
    lines.append("| Status | ID | Claim | Support | Sections | Source | Limitations / missing |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- |")
    for item in ledger:
        tail = "; ".join(item["limitations"] + item["missing_evidence"])
        lines.append(
            f"| {item['status']} | {item['id']} | {item['text'] or '(no text in source)'} | {item['support']} | "
            f"{', '.join(item['sections'])} | `{item['source']['path']}` {item['source']['locator']} | {tail} |"
        )
    lines.append("")
    counts: dict[str, int] = {}
    for item in ledger:
        counts[item["status"]] = counts.get(item["status"], 0) + 1
    lines.append("Counts: " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items(), key=lambda kv: STATUS_ORDER.get(kv[0], 9))))
    lines.append("")
    return "\n".join(lines)


def build(sources: dict[str, list[Path]], skipped: list[str] | None = None) -> list[dict]:
    skipped = skipped if skipped is not None else []
    builders = {
        "bindings": from_bindings,
        "results_audit": from_results_audit,
        "claim_map": from_claim_map,
        "evidence_table": from_evidence_table,
        "issue_board": from_issue_board,
    }
    ledger: list[dict] = []
    for key in ("bindings", "results_audit", "claim_map", "evidence_table", "issue_board"):
        for path in sources.get(key, []):
            try:
                ledger.extend(builders[key](path))
            except SourceError as exc:
                # One unreadable source must not cost the ledger the others; the skip is visible.
                skipped.append(str(exc))
                print(f"warning: skipped {exc}", file=sys.stderr)

    # When bindings exist they are authoritative: an audit or claim-map entry whose ID a
    # binding already references (via its own ID or notes) stays, but is marked as a source
    # the binding draws on rather than a second claim to assert.
    bound_ids = {item["id"] for item in ledger if item["source"]["kind"] == "paper_plan.bindings"}
    if bound_ids:
        for item in ledger:
            if item["source"]["kind"] in {"results_audit", "experiment_plan.claim_map"} and item["id"] in bound_ids:
                item["notes"] = (item["notes"] + "; " if item["notes"] else "") + "also bound in the paper plan; assert through the binding"
    ledger.sort(key=lambda item: (STATUS_ORDER.get(item["status"], 9), item["source"]["kind"], item["id"]))
    return ledger


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--bindings", type=Path, action="append", default=[])
    parser.add_argument("--results-audit", type=Path, action="append", default=[])
    parser.add_argument("--claim-map", type=Path, action="append", default=[])
    parser.add_argument("--evidence-table", type=Path, action="append", default=[])
    parser.add_argument("--issue-board", type=Path, action="append", default=[])
    parser.add_argument("--intake", type=Path, default=None)
    parser.add_argument("--out-json", type=Path, default=None)
    parser.add_argument("--out-md", type=Path, default=None)
    args = parser.parse_args(argv)

    sources: dict[str, list[Path]] = {
        "bindings": list(args.bindings),
        "results_audit": list(args.results_audit),
        "claim_map": list(args.claim_map),
        "evidence_table": list(args.evidence_table),
        "issue_board": list(args.issue_board),
    }
    try:
        if args.intake:
            for key, paths in sources_from_intake(args.intake).items():
                sources[key].extend(p for p in paths if p not in sources[key])
        skipped: list[str] = []
        ledger = build(sources, skipped)
    except SourceError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if not ledger:
        print("error: no source yielded a claim; write the ledger by hand from the author's notes and mark every entry's support", file=sys.stderr)
        return 1

    record = {"schema_version": "1.0", "claims": ledger, "skipped_sources": skipped}
    if args.out_json:
        args.out_json.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    markdown = render_markdown(ledger)
    if args.out_md:
        args.out_md.write_text(markdown, encoding="utf-8")
    if not args.out_json and not args.out_md:
        print(markdown)
    else:
        counts: dict[str, int] = {}
        for item in ledger:
            counts[item["status"]] = counts.get(item["status"], 0) + 1
        print("ledger: " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items(), key=lambda kv: STATUS_ORDER.get(kv[0], 9))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
