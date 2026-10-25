#!/usr/bin/env python3
"""Turn a claim ledger into an editable paragraph-level outline, or check an edited outline.

The outline is the first thing the author sees and approves. It is one line per paragraph:
the paragraph's job or topic sentence in plain words, the ledger entries it carries in square
brackets, and the exhibit or source it draws on. No prose is written until the outline is
approved, so the author's edits cost a line each instead of a rewrite.

Build mode:
    outline_from_ledger.py --ledger claim-ledger.json --out outline.md
        [--sections method,results,limitations,related_work,introduction,abstract]
        [--piece "manuscript" | "report" | "response"]

Sections come from the paper plan when the ledger has bindings that name them (the plan's own
titles or numbers, in the plan's order), else from --sections, else from the --piece default.

Check mode (after the author edits the outline):
    outline_from_ledger.py --ledger claim-ledger.json --check outline.md

Check mode exits 1 when a ready or careful ledger claim is missing from the outline, when the
outline cites an ID the ledger does not have, or when a blocked claim appears outside a marker
line. Those are the three ways an outline and a ledger drift apart before drafting starts.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

DEFAULT_ORDER = {
    "manuscript": ["method", "results", "limitations", "related_work", "introduction", "conclusion", "abstract"],
    "report": ["setup", "results", "limitations", "recommendation", "summary"],
    "response": ["response"],
}

SECTION_JOBS = {
    "method": "what was done, bounded to the protocol the plan records",
    "setup": "what was measured, on what, with which metric",
    "results": "what was measured and what it shows, one paragraph per audited claim or exhibit",
    "limitations": "what the work covers and what it does not, each stated once",
    "related_work": "one sentence per read source, grouped by the dimension of difference",
    "introduction": "the question, why it matters, and the contributions as the results state them",
    "conclusion": "what follows from the results, not a restatement",
    "abstract": "one sentence per primary ready claim, numbers as the results give them",
    "recommendation": "what the evidence section supports, no more",
    "summary": "the report in five sentences for a reader who stops there",
    "response": "one response per issue in the board's order: what was raised, what was done, where it appears",
}

# Ledger section labels that map onto outline sections.
SECTION_ALIASES = {
    "results": {"results", "result", "experiments", "evaluation", "findings"},
    "method": {"method", "methods", "approach", "setup", "experimental setup", "protocol"},
    "limitations": {"limitations", "limitation", "discussion"},
    "related_work": {"related_work", "related work", "background", "prior work"},
    "introduction": {"introduction", "intro", "contributions"},
    "abstract": {"abstract"},
    "conclusion": {"conclusion", "conclusions"},
    "response": {"response", "rebuttal"},
}

ID_RE = re.compile(r"\[([^\[\]\n]+?)\]")
# Bracketed text that is not a ledger ID is reported only when it looks like one (an upper-case
# prefix with a digit, or a bare number), so "[see Table 2]" in an author's line is left alone.
ID_LIKE_RE = re.compile(r"^(?:[A-Z][\w&.' -]*\d[\w&.' -]*|\d+)$")
MARKER_RE = re.compile(r"\[(?:EVIDENCE|CITATION) NEEDED")


def load_ledger(path: Path) -> list[dict]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"error: {path}: {exc}")
    claims = data.get("claims") if isinstance(data, dict) else data
    if not isinstance(claims, list):
        raise SystemExit(f"error: {path}: no claims list")
    return [c for c in claims if isinstance(c, dict)]


def canonical_section(label: str) -> str:
    low = label.strip().lower()
    for canonical, aliases in SECTION_ALIASES.items():
        if low in aliases:
            return canonical
    return low.replace(" ", "_")


def sections_from_ledger(claims: list[dict]) -> list[str]:
    """Use the sections the ledger itself names, when its claim source is a paper plan.

    Paper-plan bindings label sections with the manuscript's own titles ("Structural
    Redundancy") or numbers ("4", "s2"), not the generic archetypes. The outline follows the
    plan: labels in order of first appearance, numeric labels sorted numerically and shown as
    "Section N". Returns an empty list when no bindings name a section.
    """
    labels: list[str] = []
    for claim in claims:
        if claim.get("source", {}).get("kind") != "paper_plan.bindings" or claim.get("status") == "excluded":
            continue
        for label in claim.get("sections", []):
            if isinstance(label, str) and label.strip():
                canonical = canonical_section(label)
                if canonical not in labels:
                    labels.append(canonical)
    numeric = sorted((l for l in labels if re.fullmatch(r"s?\d+", l)), key=lambda l: int(l.lstrip("s")))
    named = [l for l in labels if not re.fullmatch(r"s?\d+", l)]
    return numeric + named


def heading(section: str) -> str:
    if re.fullmatch(r"s?\d+", section):
        return f"Section {section.lstrip('s')}"
    return section.replace("_", " ").title()


def assign(claims: list[dict], sections: list[str]) -> dict[str, list[dict]]:
    """Place each drafting-eligible claim in every section it names; unplaced claims go to a holding list."""
    placed: dict[str, list[dict]] = {s: [] for s in sections}
    placed["unassigned"] = []
    for claim in claims:
        if claim.get("status") == "excluded":
            continue
        targets = [canonical_section(s) for s in claim.get("sections", []) if isinstance(s, str)]
        hits = [t for t in targets if t in placed]
        if not hits:
            placed["unassigned"].append(claim)
            continue
        for target in dict.fromkeys(hits):
            placed[target].append(claim)
    return placed


def paragraph_line(claim: dict) -> str:
    status = claim.get("status", "")
    text = (claim.get("text") or "(no claim text in the source)").strip()
    cid = claim.get("id", "?")
    evidence = ", ".join(claim.get("evidence", [])[:2]) or "no exhibit named"
    if status == "blocked":
        gap = "; ".join(claim.get("missing_evidence", [])) or "evidence"
        return f"- [EVIDENCE NEEDED: {gap}] where [{cid}] would go: {text}"
    if status == "careful":
        limitation = "; ".join(claim.get("limitations", [])) or "state the limitation in this paragraph"
        return f"- {text} [{cid}] (careful: {limitation}) <- {evidence}"
    if status == "proposed":
        return f"- {text} [{cid}] (proposed: awaiting the author's confirmation) <- {evidence}"
    return f"- {text} [{cid}] <- {evidence}"


def render(claims: list[dict], sections: list[str], piece: str, plan_order: bool = False) -> str:
    placed = assign(claims, sections)
    lines = [f"# Outline: {piece}", ""]
    lines.append("One line per paragraph: its topic sentence or job, the ledger entries it carries in brackets, "
                 "and the exhibit it draws on after the arrow. Edit lines, reorder, delete, or add; keep the IDs.")
    if plan_order:
        lines.append("Sections follow the paper plan's own labels and order. Drafting still runs evidence-bearing "
                     "sections first; mark the order to draft in if it differs from the order shown.")
    else:
        lines.append("Framing sections are listed last because they are written last.")
    lines.append("")
    for order, section in enumerate(sections, start=1):
        lines.append(f"## {order}. {heading(section)}")
        lines.append("")
        lines.append(f"Job: {SECTION_JOBS.get(section, 'as the brief states')}. Budget: <words>.")
        lines.append("")
        entries = placed.get(section, [])
        if entries:
            lines.extend(paragraph_line(c) for c in entries)
        else:
            lines.append("- (no ledger entry is planned for this section; add paragraphs here or delete the section)")
        lines.append("")
    if placed["unassigned"]:
        lines.append("## Unplaced ledger entries")
        lines.append("")
        lines.append("These entries name no section the outline has. Move each line into a section or delete it.")
        lines.append("")
        lines.extend(paragraph_line(c) for c in placed["unassigned"])
        lines.append("")
    lines.append("## Questions for the author")
    lines.append("")
    lines.append("- (the drafter lists at most three, each with the default it will take if unanswered)")
    lines.append("")
    return "\n".join(lines)


def check(outline_text: str, claims: list[dict]) -> list[str]:
    by_id = {c.get("id"): c for c in claims}
    problems: list[str] = []
    seen: set[str] = set()
    for line_no, line in enumerate(outline_text.splitlines(), start=1):
        is_marker = bool(MARKER_RE.search(line))
        for match in ID_RE.finditer(line):
            cid = match.group(1)
            if cid.startswith(("EVIDENCE NEEDED", "CITATION NEEDED")):
                continue
            if cid not in by_id:
                if ID_LIKE_RE.match(cid):
                    problems.append(f"line {line_no}: [{cid}] is not in the ledger")
                continue
            seen.add(cid)
            status = by_id[cid].get("status")
            if status == "blocked" and not is_marker:
                problems.append(f"line {line_no}: blocked claim [{cid}] appears without an evidence marker")
            if status == "excluded":
                problems.append(f"line {line_no}: excluded claim [{cid}] appears in the outline")
    for cid, claim in by_id.items():
        if claim.get("status") in {"ready", "careful"} and cid not in seen:
            problems.append(f"ledger claim [{cid}] ({claim.get('status')}) has no paragraph in the outline")
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=None, help="write the outline here (build mode)")
    parser.add_argument("--check", type=Path, default=None, help="check this edited outline against the ledger")
    parser.add_argument("--sections", default=None, help="comma-separated section order; overrides --piece")
    parser.add_argument("--piece", choices=sorted(DEFAULT_ORDER), default="manuscript")
    args = parser.parse_args(argv)

    claims = load_ledger(args.ledger)
    if args.check:
        try:
            text = args.check.read_text(encoding="utf-8")
        except OSError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        problems = check(text, claims)
        if problems:
            print(f"outline check: {len(problems)} problems")
            for problem in problems:
                print(f"  {problem}")
            return 1
        print("outline check: every ready and careful claim has a paragraph, no unknown IDs, blocked claims are markers")
        return 0

    plan_order = False
    if args.sections:
        sections = [canonical_section(s) for s in args.sections.split(",")]
    else:
        sections = sections_from_ledger(claims)
        plan_order = bool(sections)
        if not sections:
            sections = DEFAULT_ORDER[args.piece]
    outline = render(claims, sections, args.piece, plan_order)
    if args.out:
        args.out.write_text(outline, encoding="utf-8")
        placed = assign(claims, sections)
        print(
            f"outline: {len(sections)} sections, "
            f"{sum(len(v) for k, v in placed.items() if k != 'unassigned')} paragraph lines, "
            f"{len(placed['unassigned'])} unplaced entries"
        )
    else:
        print(outline)
    return 0


if __name__ == "__main__":
    sys.exit(main())
