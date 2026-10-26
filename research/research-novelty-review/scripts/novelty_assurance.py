#!/usr/bin/env python3
"""Bind a novelty decision to its literature evidence, and migrate pre-1.1 decisions.

Subcommands:
  link     Bind the decision to a seven-file literature pack (--pack-dir, mode linked)
           or to a four-file paper context (--context, mode context). Records paths and
           SHA-256 digests and updates the report's assurance lines. Ratings are untouched.
  migrate  Bring a pre-1.1 decision to schema 1.1. Sets mode unlinked, caps the novelty
           rating at 3 (and at one point above the prior-art row count when the matrix is
           given), records the original rating, and never raises a rating.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "1.1"
STRUCTURAL_CAP = 3
SKILL_ROOT = Path(__file__).resolve().parents[1]
SLR_SCRIPTS = SKILL_ROOT.parent / "research-systematic-literature-review" / "scripts"

PACK_SUFFIXES = {
    "protocol": ".protocol.md",
    "search_log": ".search-log.md",
    "recall_audit": ".recall-audit.md",
    "corpus_manifest": ".corpus-manifest.json",
    "screening_log": ".screening-log.md",
    "evidence": ".evidence-table.md",
    "report": ".review.md",
}
CONTEXT_FILES = (
    "literature-context.md",
    "literature-context-search-log.md",
    "literature-context-evidence-table.md",
    "literature-context-decision.json",
)
CONTEXT_VERDICT = "paper-context-validated"
PLACEHOLDER_CELLS = {"", "todo", "tbd", "-", "n/a", "1-5"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative_to_decision(decision_path: Path, target: Path) -> str:
    return Path(os.path.relpath(target.resolve(), decision_path.resolve().parent)).as_posix()


def empty_assurance() -> dict[str, Any]:
    keys = tuple(PACK_SUFFIXES)
    return {
        "mode": "unlinked",
        "paths": {key: "" for key in keys},
        "file_sha256": {key: "" for key in keys},
        "corpus_manifest_sha256": "",
        "corpus_version": None,
        "review_profile": "",
        "assurance_verdict": "",
        "unresolved_high_priority_novelty_question_ids": [],
    }


def prior_art_rows(markdown: str) -> list[str]:
    """Return the Work cells of filled prior-art matrix rows (placeholder rows are skipped)."""
    works: list[str] = []
    header: list[str] | None = None
    for line in markdown.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if header is None:
            header = cells
            continue
        if all(set(cell) <= {"-", ":"} for cell in cells):
            continue
        work = cells[0] if cells else ""
        if work.lower() not in PLACEHOLDER_CELLS and "todo" not in work.lower():
            works.append(work)
    return works


def set_report_line(report: str, label: str, value: str) -> str:
    pattern = re.compile(rf"(?mi)^-[ \t]*{re.escape(label)}:[^\n]*$")
    line = f"- {label}: {value}".rstrip()
    if pattern.search(report):
        return pattern.sub(lambda _match: line, report, count=1)
    marker = "\n## Paper-Review Handoff"
    if marker in report:
        head, tail = report.split(marker, 1)
        return head.rstrip("\n") + "\n" + line + "\n" + marker + tail
    return report.rstrip("\n") + "\n" + line + "\n"


def update_report(report_path: Path | None, assurance: dict[str, Any], rating: int | None = None) -> None:
    if report_path is None or not report_path.is_file():
        return
    report = report_path.read_text(encoding="utf-8")
    if rating is not None:
        report = set_report_line(report, "Novelty decision rating (1-5)", str(rating))
    report = set_report_line(report, "Literature assurance mode", str(assurance.get("mode", "")))
    report = set_report_line(report, "Literature assurance verdict", str(assurance.get("assurance_verdict", "")))
    unresolved = assurance.get("unresolved_high_priority_novelty_question_ids") or []
    report = set_report_line(report, "Unresolved high-priority novelty-critical questions", ", ".join(unresolved))
    report_path.write_text(report, encoding="utf-8")


def find_pack_files(pack_dir: Path) -> dict[str, Path]:
    found: dict[str, Path] = {}
    for key, suffix in PACK_SUFFIXES.items():
        matches = sorted(pack_dir.glob(f"*{suffix}"))
        if len(matches) != 1:
            raise SystemExit(
                f"expected exactly one *{suffix} in {pack_dir}, found {len(matches)}; "
                "a seven-file pack holds one topic"
            )
        found[key] = matches[0]
    return found


def unresolved_ids(manifest: dict[str, Any]) -> list[str]:
    if str(SLR_SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SLR_SCRIPTS))
    try:
        from review_pack_coverage import unresolved_high_priority_novelty_questions
    except ImportError as exc:
        raise SystemExit(
            "linking a seven-file pack requires research-systematic-literature-review installed alongside "
            f"research-novelty-review (expected {SLR_SCRIPTS / 'review_pack_coverage.py'})"
        ) from exc
    return sorted(unresolved_high_priority_novelty_questions(manifest))


def link_pack(decision_path: Path, decision: dict[str, Any], pack_dir: Path) -> dict[str, Any]:
    files = find_pack_files(pack_dir)
    manifest = json.loads(files["corpus_manifest"].read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise SystemExit(f"corpus manifest must be a JSON object: {files['corpus_manifest']}")
    digests = {key: sha256(path) for key, path in files.items()}
    assurance = {
        "mode": "linked",
        "paths": {key: relative_to_decision(decision_path, path) for key, path in files.items()},
        "file_sha256": digests,
        "corpus_manifest_sha256": digests["corpus_manifest"],
        "corpus_version": manifest.get("corpus_version"),
        "review_profile": manifest.get("review_profile", ""),
        "assurance_verdict": manifest.get("assurance_verdict", ""),
        "unresolved_high_priority_novelty_question_ids": unresolved_ids(manifest),
    }
    decision["literature_assurance"] = assurance
    return assurance


def link_context(decision_path: Path, decision: dict[str, Any], context_dir: Path) -> dict[str, Any]:
    missing = [name for name in CONTEXT_FILES if not (context_dir / name).is_file()]
    if missing:
        raise SystemExit("paper context is missing: " + ", ".join(missing))
    assurance = {
        "mode": "context",
        "context_dir": relative_to_decision(decision_path, context_dir),
        "context_sha256": {name: sha256(context_dir / name) for name in CONTEXT_FILES},
        "assurance_verdict": CONTEXT_VERDICT,
        "unresolved_high_priority_novelty_question_ids": [],
    }
    decision["literature_assurance"] = assurance
    return assurance


def load_decision(path: Path) -> dict[str, Any]:
    try:
        decision = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SystemExit(f"missing novelty decision: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(decision, dict):
        raise SystemExit("novelty decision must be a JSON object")
    return decision


def write_decision(path: Path, decision: dict[str, Any]) -> None:
    path.write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def default_report(decision_path: Path, given: Path | None) -> Path | None:
    if given is not None:
        return given
    sibling = decision_path.parent / "novelty-report.md"
    return sibling if sibling.is_file() else None


def command_link(args: argparse.Namespace) -> int:
    decision_path = args.decision.resolve()
    decision = load_decision(decision_path)
    if args.pack_dir is not None:
        assurance = link_pack(decision_path, decision, args.pack_dir.resolve())
        hint = "validate with --assurance-profile linked"
    else:
        assurance = link_context(decision_path, decision, args.context.resolve())
        hint = "validate with the default structural profile; the context is revalidated each time"
    write_decision(decision_path, decision)
    update_report(default_report(decision_path, args.report), assurance)
    print(f"bound {decision_path.name} in mode {assurance['mode']}; {hint}")
    return 0


def migrate_decision(
    decision: dict[str, Any], prior_art: str | None, today: str
) -> tuple[dict[str, Any], int | None]:
    migrated = copy.deepcopy(decision)
    previous_version = decision.get("schema_version")
    if previous_version == SCHEMA_VERSION:
        raise SystemExit("decision is already schema 1.1; nothing to migrate")
    migrated["schema_version"] = SCHEMA_VERSION
    if migrated.get("status") not in {"draft", "complete"}:
        filled = all(
            isinstance(migrated.get(field), str) and migrated[field].strip()
            for field in ("narrowest_defensible_positioning", "what_would_change_the_decision")
        )
        migrated["status"] = "complete" if filled else "draft"
    for field in ("top_kill_shot_objections", "literature_context_used", "claims_to_qualify", "missing_prior_work", "review_findings_to_add"):
        migrated.setdefault(field, [])
    migrated.setdefault("paper_review_summary_used", "")
    assurance = migrated.get("literature_assurance")
    if not isinstance(assurance, dict) or assurance.get("mode") not in {"unlinked", "linked", "context"}:
        migrated["literature_assurance"] = empty_assurance()

    original = decision.get("novelty_decision_rating")
    new_rating = original if isinstance(original, int) and not isinstance(original, bool) else None
    note_parts: list[str] = []
    if new_rating is not None and migrated["literature_assurance"].get("mode") == "unlinked":
        ceiling = STRUCTURAL_CAP
        if prior_art is not None:
            ceiling = min(ceiling, len(prior_art_rows(prior_art)) + 1)
        if new_rating > ceiling:
            note_parts.append(
                f"novelty_decision_rating lowered from {new_rating} to {ceiling}: structural mode caps it at "
                f"{STRUCTURAL_CAP} and needs one prior-art row per point above 1; bind literature with "
                "novelty_assurance.py link to restore a higher rating"
            )
            new_rating = ceiling
    migrated["novelty_decision_rating"] = new_rating
    migrated["migration"] = {
        "from_schema_version": previous_version,
        "migrated_on": today,
        "original_novelty_decision_rating": original,
        "note": "; ".join(note_parts) or "schema fields added; ratings unchanged",
    }
    return migrated, new_rating


def command_migrate(args: argparse.Namespace) -> int:
    decision_path = args.decision.resolve()
    decision = load_decision(decision_path)
    prior_art = args.prior_art_matrix.read_text(encoding="utf-8") if args.prior_art_matrix else None
    migrated, rating = migrate_decision(decision, prior_art, date.today().isoformat())
    if args.dry_run:
        print(json.dumps(migrated, indent=2, sort_keys=True))
        return 0
    write_decision(decision_path, migrated)
    update_report(default_report(decision_path, args.report), migrated["literature_assurance"], rating)
    print(f"migrated {decision_path.name} to schema {SCHEMA_VERSION}: {migrated['migration']['note']}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    link = sub.add_parser("link", help="Bind the decision to a literature pack or a paper context")
    link.add_argument("--decision", type=Path, required=True)
    target = link.add_mutually_exclusive_group(required=True)
    target.add_argument("--pack-dir", type=Path, help="Seven-file literature pack directory (mode linked)")
    target.add_argument("--context", type=Path, help="Four-file paper-context directory (mode context)")
    link.add_argument("--report", type=Path, help="Novelty report to update; defaults to the sibling novelty-report.md")
    link.set_defaults(func=command_link)
    migrate = sub.add_parser("migrate", help="Bring a pre-1.1 decision to schema 1.1")
    migrate.add_argument("--decision", type=Path, required=True)
    migrate.add_argument("--prior-art-matrix", type=Path, help="Also cap the rating at one point above the filled prior-art rows")
    migrate.add_argument("--report", type=Path, help="Novelty report to update; defaults to the sibling novelty-report.md")
    migrate.add_argument("--dry-run", action="store_true", help="Print the migrated decision without writing")
    migrate.set_defaults(func=command_migrate)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
