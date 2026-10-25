#!/usr/bin/env python3
"""Inventory the supporting artifacts a draft can be written from.

Walks a project directory, classifies the files the research suite and ordinary
research projects produce (claim sources, result audits, data tables, figures,
literature reviews, novelty packs, review critiques, rebuttal boards, manuscript
source, notes), and writes an intake record that names what the draft can lean
on and what is missing. The record is the first input to ``build_claim_ledger.py``
and to the writing brief.

Usage:
    inventory_artifacts.py <root> [--out-json writing-intake.json] [--out-md writing-intake.md]
                           [--max-files 50000]

Exit status is 0 whenever the walk completes; gaps are reported, not failed,
because a draft can still be written around a visible gap.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

SKIP_DIRS = {".git", ".hg", ".svn", "node_modules", "__pycache__", ".venv", "venv", ".mypy_cache", ".pytest_cache", "build", "dist", ".idea", ".vscode"}

# (regex on the file name, kind, role). First match wins; order matters.
RULES: list[tuple[str, str, str]] = [
    (r"^claim-evidence-bindings\.json$", "paper_plan.bindings", "claims"),
    (r"^claims-evidence-matrix\.md$", "paper_plan.matrix", "claims"),
    (r"^paper-plan\.md$", "paper_plan.plan", "structure"),
    (r"^figure-plan\.md$", "paper_plan.figure_plan", "structure"),
    (r"^citation-plan\.md$", "paper_plan.citation_plan", "literature"),
    (r"^results-audit\.json$", "results_audit.json", "evidence"),
    (r"^results-audit\.md$", "results_audit.narrative", "evidence"),
    (r"^claim-map\.json$", "experiment_plan.claim_map", "claims"),
    (r"^run-blocks\.json$", "experiment_plan.run_blocks", "method"),
    (r"^experiment-plan\.md$", "experiment_plan.narrative", "method"),
    (r"^results\.tsv$", "iteration_loop.ledger", "data"),
    (r"^program\.md$", "iteration_loop.program", "method"),
    (r"^experiments\.md$", "iteration_loop.notebook", "method"),
    (r".*evidence-table\.md$", "literature.evidence_table", "literature"),
    (r".*\.review\.md$", "literature.review", "literature"),
    (r".*corpus-manifest\.json$", "literature.corpus_manifest", "literature"),
    (r"^literature-context.*\.(md|json)$", "literature.context", "literature"),
    (r"^citation-audit\.md$", "literature.citation_audit", "literature"),
    (r"^bib-inventory\.json$", "literature.bib_inventory", "literature"),
    (r"^novelty-report\.md$", "novelty.report", "literature"),
    (r"^novelty-decision\.json$", "novelty.decision", "literature"),
    (r"^prior-art-matrix\.md$", "novelty.prior_art", "literature"),
    (r"^novelty-context\.md$", "novelty.context", "literature"),
    (r"^issue-board\.md$", "rebuttal.issue_board", "critique"),
    (r"^task-list\.md$", "rebuttal.task_list", "critique"),
    (r"^rebuttal-(working|paste-ready)\.md$", "rebuttal.draft", "source"),
    (r"^REVIEW_STATE\.json$", "review_loop.state", "critique"),
    (r"^final_issues\.json$", "paper_review.issues", "critique"),
    (r"^research-brief\.md$", "planning.brief", "structure"),
    (r"^artifact-index\.md$", "planning.artifact_index", "structure"),
    (r"^research-commitment\.json$", "planning.commitment", "structure"),
    (r"^idea-brief\.md$", "discovery.idea_brief", "structure"),
    (r".*\.(tex|ltx)$", "manuscript.latex", "source"),
    (r".*\.bib$", "manuscript.bibliography", "literature"),
    (r".*\.(csv|tsv|parquet|jsonl)$", "data.table", "data"),
    (r".*\.(png|pdf|svg|jpg|jpeg|eps)$", "figure", "figure"),
    (r".*\.(ipynb)$", "data.notebook", "data"),
    (r"^(README|readme)\.md$", "notes.readme", "notes"),
    (r".*\.(md|txt|rst)$", "notes.text", "notes"),
    (r".*\.json$", "data.json", "data"),
]

COMPILED = [(re.compile(pattern), kind, role) for pattern, kind, role in RULES]

DATA_DIR_HINTS = ("results", "data", "metrics", "outputs", "runs", "eval", "evals", "tables")
FIGURE_DIR_HINTS = ("figures", "figs", "plots")


@dataclass
class Artifact:
    path: str
    kind: str
    role: str
    bytes: int
    count: int = 1


COLLAPSE_ROLES = {"data", "figure", "notes"}
COLLAPSE_THRESHOLD = 20
COLLAPSE_DEPTH = 2


def classify(rel_path: Path) -> tuple[str, str] | None:
    name = rel_path.name
    parts = {part.lower() for part in rel_path.parts[:-1]}
    for pattern, kind, role in COMPILED:
        if pattern.match(name):
            if kind == "data.json" and not parts.intersection(DATA_DIR_HINTS):
                # A bare .json outside a results-like folder is configuration, not evidence.
                return None
            if kind == "figure" and name.lower().endswith(".pdf") and not parts.intersection(FIGURE_DIR_HINTS):
                # A PDF outside a figures folder is a paper or a reference, not an exhibit.
                return ("document.pdf", "literature")
            return (kind, role)
    return None


def collapse(found: list[Artifact]) -> list[Artifact]:
    """Fold a directory holding many data files or figures into one entry with a count.

    A results folder with thousands of run files is one source for the number checker, not
    thousands of rows in the intake table, and a docs tree with hundreds of notes is one place
    to look for the author's intent.
    """
    groups: dict[tuple[str, str], list[Artifact]] = {}
    kept: list[Artifact] = []
    for artifact in found:
        if artifact.role in COLLAPSE_ROLES:
            # Group by the subtree two levels deep, so results/runs/<hundreds of dirs> folds into
            # one entry instead of one entry per small directory.
            parent = Path(artifact.path).parent
            key_dir = Path(*parent.parts[:COLLAPSE_DEPTH]) if len(parent.parts) > COLLAPSE_DEPTH else parent
            groups.setdefault((str(key_dir), artifact.kind), []).append(artifact)
        else:
            kept.append(artifact)
    for (directory, kind), members in groups.items():
        if len(members) > COLLAPSE_THRESHOLD:
            kept.append(
                Artifact(
                    path=(directory if directory != "." else "") + "/",
                    kind=kind,
                    role=members[0].role,
                    bytes=sum(m.bytes for m in members),
                    count=len(members),
                )
            )
        else:
            kept.extend(members)
    return sorted(kept, key=lambda a: a.path)


def walk(root: Path, max_files: int) -> tuple[list[Artifact], bool]:
    """Walk the tree, pruning skipped directories before descending; max_files bounds visited files."""
    found: list[Artifact] = []
    truncated = False
    visited = 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        for name in sorted(filenames):
            visited += 1
            if visited > max_files:
                truncated = True
                break
            path = Path(dirpath) / name
            if not path.is_file():
                continue
            rel = path.relative_to(root)
            hit = classify(rel)
            if hit is None:
                continue
            kind, role = hit
            found.append(Artifact(path=rel.as_posix(), kind=kind, role=role, bytes=path.stat().st_size))
        if truncated:
            break
    return collapse(sorted(found, key=lambda a: a.path)), truncated


def summarize(artifacts: list[Artifact]) -> dict:
    roles: dict[str, list[str]] = {}
    kinds: dict[str, list[str]] = {}
    for artifact in artifacts:
        roles.setdefault(artifact.role, []).append(artifact.path)
        kinds.setdefault(artifact.kind, []).append(artifact.path)

    claim_sources = [k for k in ("paper_plan.bindings", "experiment_plan.claim_map", "results_audit.json") if k in kinds]
    pack_dirs = sorted({str(Path(p).parent) for k in ("paper_plan.bindings", "experiment_plan.claim_map") for p in kinds.get(k, [])})
    gaps: list[str] = []
    if len(pack_dirs) > 1:
        gaps.append(
            f"{len(pack_dirs)} claim packs under distinct directories ({', '.join(pack_dirs[:4])}{', ...' if len(pack_dirs) > 4 else ''}): "
            "choose the pack for the piece being drafted and pass it to build_claim_ledger.py directly instead of --intake"
        )
    if not claim_sources:
        gaps.append(
            "no claim source (claim-evidence-bindings.json, claim-map.json, or results-audit.json): "
            "the claim ledger must be proposed from the data and confirmed by the author before framing sections are drafted"
        )
    if "results_audit.json" not in kinds and "data" in roles:
        gaps.append("data tables without a results audit: numbers may be drafted only from the tables and must pass check_draft_numbers.py")
    if "data" not in roles and "results_audit.json" not in kinds:
        gaps.append("no data or audit: result sentences are limited to [EVIDENCE NEEDED] markers")
    if "literature" not in roles:
        gaps.append("no literature artifact (evidence table, bib, novelty pack, citation plan): related-work sentences carry [CITATION NEEDED] markers")
    if "critique" not in roles:
        gaps.append("no critique artifact: nothing to respond to, so this is a manuscript or report draft rather than a rebuttal")
    if "manuscript.latex" in kinds:
        gaps.append("LaTeX source present: the draft is written in LaTeX and register-and-format.md applies")

    return {
        "counts_by_role": {role: len(paths) for role, paths in sorted(roles.items())},
        "kinds_present": sorted(kinds),
        "claim_sources": claim_sources,
        "claim_pack_dirs": pack_dirs,
        "gaps": gaps,
    }


def render_markdown(root: Path, artifacts: list[Artifact], summary: dict, truncated: bool) -> str:
    lines = [f"# Writing intake for `{root.name}`", ""]
    lines.append("## What the draft can lean on")
    lines.append("")
    if not artifacts:
        lines.append("No recognised artifacts. The draft starts from the author's notes only.")
    else:
        lines.append("| Role | Kind | Path |")
        lines.append("| --- | --- | --- |")
        for artifact in sorted(artifacts, key=lambda a: (a.role, a.kind, a.path)):
            suffix = f" ({artifact.count} files)" if artifact.count > 1 else ""
            lines.append(f"| {artifact.role} | {artifact.kind} | `{artifact.path}`{suffix} |")
    lines.append("")
    lines.append("## Claim sources")
    lines.append("")
    if summary["claim_sources"]:
        for kind in summary["claim_sources"]:
            lines.append(f"- `{kind}`")
    else:
        lines.append("- none")
    lines.append("")
    lines.append("## Gaps the draft must show rather than hide")
    lines.append("")
    for gap in summary["gaps"]:
        lines.append(f"- {gap}")
    if truncated:
        lines.append("- the walk stopped at the file limit; rerun with a higher --max-files or a narrower root")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("root", type=Path)
    parser.add_argument("--out-json", type=Path, default=None)
    parser.add_argument("--out-md", type=Path, default=None)
    parser.add_argument("--max-files", type=int, default=50000)
    args = parser.parse_args(argv)

    root = args.root.resolve()
    if not root.is_dir():
        print(f"error: {root} is not a directory", file=sys.stderr)
        return 2

    artifacts, truncated = walk(root, args.max_files)
    summary = summarize(artifacts)
    record = {
        "schema_version": "1.0",
        "root": str(root),
        "artifacts": [asdict(a) for a in artifacts],
        "summary": summary,
        "truncated": truncated,
    }
    if args.out_json:
        args.out_json.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    markdown = render_markdown(root, artifacts, summary, truncated)
    if args.out_md:
        args.out_md.write_text(markdown, encoding="utf-8")
    if not args.out_json and not args.out_md:
        print(markdown)
    else:
        print(
            f"intake: {len(artifacts)} artifacts, roles {summary['counts_by_role']}, "
            f"claim sources {summary['claim_sources'] or 'none'}, {len(summary['gaps'])} gaps"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
