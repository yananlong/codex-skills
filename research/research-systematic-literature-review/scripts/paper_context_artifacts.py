#!/usr/bin/env python3
"""Create and validate paper-context evidence-map artifacts."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Any

REQUIRED_FILES = [
    "literature-context.md",
    "literature-context-search-log.md",
    "literature-context-evidence-table.md",
    "literature-context-decision.json",
]

REQUIRED_DECISION_FIELDS = [
    "contextualization_rating",
    "impact_evidence_rating",
    "coverage_confidence_rating",
    "closest_prior_work",
    "related_work_omissions",
    "benchmark_context_gaps",
    "limits_of_search",
]

REQUIRED_CONTEXT_HEADINGS = [
    "## Scope",
    "## Target Paper Claims Being Contextualized",
    "## Search Strategy",
    "## Closest Prior Work",
    "## Related-Work Coverage Assessment",
    "## Benchmark Or Evaluation Context",
    "## Impact / Significance Context",
    "## Claims That Need Qualification",
    "## Confidence and Limitations",
]

LIST_DECISION_FIELDS = [
    "closest_prior_work",
    "related_work_omissions",
    "benchmark_context_gaps",
    "limits_of_search",
]
RATING_DECISION_FIELDS = ["contextualization_rating", "impact_evidence_rating", "coverage_confidence_rating"]
DECISION_MODE = "paper_context_evidence_map"
TODO_PATTERN = re.compile(r"\bTODO\b")

REQUIRED_EVIDENCE_HEADERS = ["Citation", "Publication URL", "Publication status"]
REQUIRED_VERSION_HEADERS = ["canonical_publication_url"]


def _resolve_out_dir(args: argparse.Namespace) -> Path:
    if args.out_dir:
        return Path(args.out_dir).expanduser().resolve()
    if args.review_dir:
        return Path(args.review_dir).expanduser().resolve() / "context"
    raise ValueError("Provide --review-dir or --out-dir.")


def _read_optional(path: str | None) -> str:
    if not path:
        return ""
    candidate = Path(path).expanduser().resolve()
    if not candidate.exists():
        raise ValueError(f"Artifact not found: {candidate}")
    return str(candidate)


def _refuse_overwrite(paths: list[Path], force: bool) -> None:
    existing = [str(path) for path in paths if path.exists()]
    if existing and not force:
        raise ValueError("Refusing to overwrite existing artifacts: " + ", ".join(existing))


def _context_md(args: argparse.Namespace, summary_path: str, context_plan_path: str) -> str:
    target_paper = args.target_paper or "TODO"
    domain = args.domain or "TODO"
    target_community = args.target_community or "TODO"
    context_questions = args.context_question or ["TODO"]
    question_lines = "\n".join(f"- {question}" for question in context_questions)
    upstream_artifacts = "\n".join([
        f"- summary.md: {summary_path or 'TODO'}",
        f"- context-plan.md: {context_plan_path or 'TODO'}",
    ])
    today = date.today().isoformat()
    return f"""# Paper-Context Evidence Map: {target_paper}

This is a bounded paper-context evidence map, not a full systematic review, unless the full PRISMA workflow was actually completed.

## Scope

- Target paper: {target_paper}
- Domain: {domain}
- Target community / venue: {target_community}
- Upstream paper-review artifacts:
{upstream_artifacts}
- Context questions:
{question_lines}
- Search date: {today}
- Reviewer constraints: TODO

## Target Paper Claims Being Contextualized

| claim_id | Claim | Claim type | Paper location | What external evidence must establish |
| --- | --- | --- | --- | --- |
| C1 | TODO | novelty / impact / SOTA / benchmark / related-work adequacy | TODO | TODO |

## Search Strategy

Summarize exact sources, queries, filters, retrieval dates, and inclusion decisions. Keep detailed rows in `literature-context-search-log.md`.

| run_id | source | query_string | filters | purpose | records_returned | retained |
| --- | --- | --- | --- | --- | ---: | ---: |
| run-001 | TODO | TODO | TODO | evaluate C1 | 0 | 0 |

## Closest Prior Work

| work_id | Citation | Publication URL | Venue / year | Publication status | Why close | Threatened target claim | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| P1 | TODO | TODO | TODO | published / preprint / submission | TODO | C1 | TODO |

## Related-Work Coverage Assessment

- Adequately covered work: TODO
- Missing or under-discussed work: TODO
- Mischaracterized work: TODO
- Preprint vs published-version issues: TODO

## Benchmark Or Evaluation Context

- Common datasets / tasks / baselines in this area: TODO
- Norms for uncertainty, ablations, statistical testing, or robustness: TODO
- Target paper gaps: TODO

## Impact / Significance Context

- External evidence supporting significance: TODO
- External evidence weakening significance: TODO
- Communities or use cases for which impact is plausible: TODO
- Communities or use cases for which the impact claim is overstated: TODO

## Claims That Need Qualification

| claim_id | Required qualification | Evidence basis | Confidence (1-5) |
| --- | --- | --- | ---: |
| C1 | TODO | TODO | TODO |

## Confidence and Limitations

- Coverage confidence: TODO
- Search limitations: TODO
- Evidence limitations: TODO
"""


def _search_log_md(args: argparse.Namespace) -> str:
    target_paper = args.target_paper or "TODO"
    today = date.today().isoformat()
    return f"""# Literature Context Search Log: {target_paper}

## Search Runs

| run_id | date | source | query_string | filters | purpose | records_returned | retained | notes |
| --- | --- | --- | --- | --- | --- | ---: | ---: | --- |
| run-001 | {today} | TODO | TODO | TODO | evaluate target paper claim | 0 | 0 | TODO |

## Inclusion Decisions

| record_id | citation | publication_url | source_run | decision | reason |
| --- | --- | --- | --- | --- | --- |
| rec-001 | TODO | TODO | run-001 | include / exclude / duplicate | TODO |

## Version Resolution

| mapping_id | preprint_or_submission | preprint_url | canonical_record | canonical_publication_url | status | notes |
| --- | --- | --- | --- | --- | --- | --- |
| map-001 | TODO | TODO | TODO | TODO | resolved / unresolved | TODO |
"""


def _evidence_table_md(args: argparse.Namespace) -> str:
    target_paper = args.target_paper or "TODO"
    return f"""# Literature Context Evidence Table: {target_paper}

| work_id | Citation | Publication URL | Publication status | Venue / year | Claim relevance | Key evidence | Risk or limitation | Target-paper implication |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P1 | TODO | TODO | published / preprint / submission | TODO | closest prior work / benchmark norm / impact evidence | TODO | TODO | TODO |
"""


def _decision_json(args: argparse.Namespace, out_dir: Path, summary_path: str, context_plan_path: str) -> str:
    payload: dict[str, Any] = {
        "mode": DECISION_MODE,
        "target_paper": args.target_paper,
        "domain": args.domain,
        "target_community": args.target_community,
        # Ratings start unset so an untouched scaffold never carries a rating.
        "contextualization_rating": None,
        "impact_evidence_rating": None,
        "coverage_confidence_rating": None,
        "closest_prior_work": [],
        "related_work_omissions": [],
        "benchmark_context_gaps": [],
        "limits_of_search": [],
        "paper_review_handoff": {
            "summary_md": summary_path or None,
            "context_plan_md": context_plan_path or None,
            "context_dir": str(out_dir),
        },
        "created_date": date.today().isoformat(),
    }
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def init_artifacts(args: argparse.Namespace) -> int:
    out_dir = _resolve_out_dir(args)
    summary_path = _read_optional(args.summary)
    context_plan_path = _read_optional(args.context_plan)
    paths = [out_dir / name for name in REQUIRED_FILES]
    _refuse_overwrite(paths, force=args.force)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "literature-context.md").write_text(_context_md(args, summary_path, context_plan_path), encoding="utf-8")
    (out_dir / "literature-context-search-log.md").write_text(_search_log_md(args), encoding="utf-8")
    (out_dir / "literature-context-evidence-table.md").write_text(_evidence_table_md(args), encoding="utf-8")
    (out_dir / "literature-context-decision.json").write_text(_decision_json(args, out_dir, summary_path, context_plan_path), encoding="utf-8")
    print(f"Initialized paper-context evidence map: {out_dir}")
    for path in paths:
        print(f"- {path}")
    return 0


def _is_rating(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and 1 <= value <= 5


def _todo_lines(text: str) -> list[int]:
    return [number for number, line in enumerate(text.splitlines(), 1) if TODO_PATTERN.search(line)]


def _json_todo_paths(value: Any, path: str = "$") -> list[str]:
    if isinstance(value, str):
        return [path] if TODO_PATTERN.search(value) else []
    if isinstance(value, list):
        return [found for index, item in enumerate(value) for found in _json_todo_paths(item, f"{path}[{index}]")]
    if isinstance(value, dict):
        return [found for key, item in value.items() for found in _json_todo_paths(item, f"{path}.{key}")]
    return []


def _check_todos(name: str, text: str, errors: list[str]) -> None:
    lines = _todo_lines(text)
    if lines:
        shown = ", ".join(str(number) for number in lines[:10]) + (", ..." if len(lines) > 10 else "")
        errors.append(f"{name} still has {len(lines)} TODO placeholder line(s) (lines {shown}); fill them or pass --draft")


def _load_json(path: Path, errors: list[str]) -> dict[str, Any]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"{path.name}: invalid JSON: {exc}")
        return {}
    if not isinstance(raw, dict):
        errors.append(f"{path.name}: expected a JSON object")
        return {}
    return raw


def _first_table_header(markdown: str) -> list[str]:
    for line in markdown.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if cells and not all(set(cell) <= {"-", ":"} for cell in cells):
            return cells
    return []


def _section_table_header(markdown: str, section_heading: str) -> list[str]:
    idx = markdown.find(section_heading)
    if idx < 0:
        return []
    return _first_table_header(markdown[idx:].split("\n## ", 1)[0])


def collect_errors(out_dir: Path, draft: bool = False) -> list[str]:
    """Return every validation error for the four paper-context files in out_dir."""
    errors: list[str] = []
    for name in REQUIRED_FILES:
        if not (out_dir / name).exists():
            errors.append(f"Missing required paper-context artifact: {out_dir / name}")
    context_path = out_dir / "literature-context.md"
    if context_path.exists():
        context_md = context_path.read_text(encoding="utf-8")
        if not draft:
            _check_todos("literature-context.md", context_md, errors)
        for heading in REQUIRED_CONTEXT_HEADINGS:
            if heading not in context_md:
                errors.append(f"literature-context.md missing heading: {heading}")
        if "bounded paper-context evidence map, not a full systematic review" not in context_md:
            errors.append("literature-context.md must state that bounded paper-context mode is not a full systematic review")
        closest_header = _section_table_header(context_md, "## Closest Prior Work")
        for required in REQUIRED_EVIDENCE_HEADERS:
            if required not in closest_header:
                errors.append(f"literature-context.md Closest Prior Work table missing column: {required}")
    search_log_path = out_dir / "literature-context-search-log.md"
    if search_log_path.exists():
        search_log_md = search_log_path.read_text(encoding="utf-8")
        if not draft:
            _check_todos("literature-context-search-log.md", search_log_md, errors)
        version_header = _section_table_header(search_log_md, "## Version Resolution")
        for required in REQUIRED_VERSION_HEADERS:
            if required not in version_header:
                errors.append(f"literature-context-search-log.md Version Resolution table missing column: {required}")
    evidence_path = out_dir / "literature-context-evidence-table.md"
    if evidence_path.exists():
        evidence_md = evidence_path.read_text(encoding="utf-8")
        if not draft:
            _check_todos("literature-context-evidence-table.md", evidence_md, errors)
        evidence_header = _first_table_header(evidence_md)
        for required in REQUIRED_EVIDENCE_HEADERS:
            if required not in evidence_header:
                errors.append(f"literature-context-evidence-table.md missing column: {required}")
    decision_path = out_dir / "literature-context-decision.json"
    if decision_path.exists():
        decision = _load_json(decision_path, errors)
        for field in REQUIRED_DECISION_FIELDS:
            if field not in decision:
                errors.append(f"literature-context-decision.json missing field: {field}")
        if decision and decision.get("mode") != DECISION_MODE:
            errors.append(f"literature-context-decision.json field mode must equal {DECISION_MODE}")
        for field in RATING_DECISION_FIELDS:
            if field not in decision:
                continue
            if decision[field] is None and draft:
                continue
            if decision[field] is None:
                errors.append(f"literature-context-decision.json field {field} is unset (null); rate it 1-5 or pass --draft")
            elif not _is_rating(decision[field]):
                errors.append(f"literature-context-decision.json field {field} must be an integer from 1 to 5")
        for field in LIST_DECISION_FIELDS:
            if field in decision and not isinstance(decision[field], list):
                errors.append(f"literature-context-decision.json field {field} must be a list")
        if not draft:
            for found in _json_todo_paths(decision):
                errors.append(f"literature-context-decision.json value {found} still contains TODO; fill it or pass --draft")
    return errors


def validate_artifacts(args: argparse.Namespace) -> int:
    out_dir = _resolve_out_dir(args)
    errors = collect_errors(out_dir, draft=bool(getattr(args, "draft", False)))
    if errors:
        print("Paper-context validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"Paper-context validation passed: {out_dir}")
    return 0



INIT_REVIEW_PACK = Path(__file__).resolve().parent / "init_review_pack.py"
PLACEHOLDER_CELLS = {"", "todo", "tbd", "-", "n/a"}


def _real_cell(value: str) -> bool:
    normalized = value.strip().lower()
    return normalized not in PLACEHOLDER_CELLS and "todo" not in normalized


def _table_rows(markdown: str, section_heading: str | None = None) -> tuple[list[str], list[dict[str, str]]]:
    body = markdown
    if section_heading is not None:
        idx = markdown.find(section_heading)
        if idx < 0:
            return [], []
        body = markdown[idx:].split("\n## ", 1)[0]
    lines = [line.strip() for line in body.splitlines() if line.strip().startswith("|")]
    if len(lines) < 2:
        return [], []
    header = [cell.strip() for cell in lines[0].strip("|").split("|")]
    rows: list[dict[str, str]] = []
    for line in lines[1:]:
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if all(set(cell) <= {"-", ":"} for cell in cells):
            continue
        cells += [""] * (len(header) - len(cells))
        rows.append(dict(zip(header, cells[: len(header)])))
    return header, rows


def _insert_note(markdown: str, note: str) -> str:
    lines = markdown.splitlines(keepends=True)
    for index, line in enumerate(lines):
        if line.startswith("# "):
            return "".join(lines[: index + 1]) + "\n> " + note + "\n" + "".join(lines[index + 1 :])
    return "> " + note + "\n\n" + markdown


def promote_artifacts(args: argparse.Namespace) -> int:
    """Turn a four-file paper context into a seven-file pack skeleton without inventing content."""
    src = _resolve_out_dir(args)
    missing = [name for name in REQUIRED_FILES if not (src / name).is_file()]
    if missing:
        raise ValueError("cannot promote; missing paper-context files: " + ", ".join(missing))
    errors: list[str] = []
    decision = _load_json(src / "literature-context-decision.json", errors)
    if errors:
        raise ValueError("; ".join(errors))
    topic = args.topic or decision.get("target_paper")
    domain = args.domain or decision.get("domain")
    if not isinstance(topic, str) or not _real_cell(topic):
        raise ValueError("the paper context has no target_paper; pass --topic")
    if not isinstance(domain, str) or not _real_cell(domain):
        raise ValueError("the paper context has no domain; pass --domain")
    pack_dir = Path(args.pack_dir).expanduser().resolve()
    command = [
        sys.executable, str(INIT_REVIEW_PACK),
        "--topic", topic, "--domain", domain,
        "--review-profile", args.review_profile,
        "--out-dir", str(pack_dir),
    ]
    if args.force:
        command.append("--force")
    completed = subprocess.run(command, text=True, capture_output=True)
    if completed.returncode != 0:
        raise ValueError("init_review_pack.py failed: " + (completed.stderr or completed.stdout).strip())

    sys.path.insert(0, str(INIT_REVIEW_PACK.parent))
    from init_review_pack import slugify  # noqa: E402

    stem = pack_dir / slugify(topic)
    today = date.today().isoformat()
    note = (
        f"Promoted on {today} from the paper-context evidence map in {src}. Rows carried over are "
        "copied as written; every TODO is a placeholder, and linked validation fails until each one "
        "is filled from a real search."
    )
    for suffix in (".protocol.md", ".search-log.md", ".recall-audit.md", ".screening-log.md", ".evidence-table.md", ".review.md"):
        path = Path(f"{stem}{suffix}")
        path.write_text(_insert_note(path.read_text(encoding="utf-8"), note), encoding="utf-8")

    carried_evidence = 0
    _, context_rows = _table_rows((src / "literature-context-evidence-table.md").read_text(encoding="utf-8"))
    matrix_rows = []
    for row in context_rows:
        if not _real_cell(row.get("Citation", "")):
            continue
        cells = [
            row.get("work_id", ""), row.get("Citation", ""), row.get("Publication URL", ""), "",
            row.get("Venue / year", ""), "", row.get("Publication status", ""), "", "TODO", "TODO",
            "TODO", row.get("Key evidence", ""), row.get("Risk or limitation", ""), "TODO",
            row.get("Claim relevance", ""), "carried from paper context",
        ]
        matrix_rows.append("| " + " | ".join(cell.replace("|", "/") for cell in cells) + " |")
    if matrix_rows:
        evidence_path = Path(f"{stem}.evidence-table.md")
        evidence_md = evidence_path.read_text(encoding="utf-8")
        lines = evidence_md.splitlines()
        start = next(i for i, line in enumerate(lines) if line.startswith("| study_id"))
        # Header and separator stay; the template's empty row is replaced by the carried rows.
        lines[start + 2 : start + 3] = matrix_rows
        evidence_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        carried_evidence = len(matrix_rows)

    search_md = (src / "literature-context-search-log.md").read_text(encoding="utf-8")
    run_header, run_rows = _table_rows(search_md, "## Search Runs")
    real_runs = [row for row in run_rows if _real_cell(row.get("query_string", ""))]
    if real_runs:
        table = ["| " + " | ".join(run_header) + " |", "| " + " | ".join("---" for _ in run_header) + " |"]
        table += ["| " + " | ".join(row.get(cell, "") for cell in run_header) + " |" for row in real_runs]
        block = (
            "## Carried over from the paper-context search log\n\n"
            "These runs were made for the bounded paper context. Record each one again in the Source "
            "queries table with its channel, coverage target, and question IDs once they are checked.\n\n"
            + "\n".join(table) + "\n\n"
        )
        log_path = Path(f"{stem}.search-log.md")
        log_md = log_path.read_text(encoding="utf-8")
        log_path.write_text(log_md.replace("## Coverage notes", block + "## Coverage notes", 1), encoding="utf-8")

    manifest_path = Path(f"{stem}.corpus-manifest.json")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["promoted_from"] = {"paper_context_dir": str(src), "promoted_on": today}
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(f"Promoted paper context {src} to a seven-file pack skeleton in {pack_dir}")
    print(f"- carried evidence rows: {carried_evidence}")
    print(f"- carried search runs: {len(real_runs)}")
    print("Linked validation fails until every TODO placeholder is filled; run validate_review_pack.py to list them.")
    return 0

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    def add_common(subparser: argparse.ArgumentParser) -> None:
        group = subparser.add_mutually_exclusive_group(required=True)
        group.add_argument("--review-dir", help="Paper-review workspace; uses <review_dir>/context")
        group.add_argument("--out-dir", help="Directory that should contain the four paper-context artifacts")

    init_parser = subparsers.add_parser("init", help="Create the paper-context artifact scaffold")
    add_common(init_parser)
    init_parser.add_argument("--target-paper", help="Target paper title or identifier")
    init_parser.add_argument("--domain", help="Domain inferred or supplied for the evidence map")
    init_parser.add_argument("--target-community", help="Target venue or research community")
    init_parser.add_argument("--summary", help="Path to upstream paper-review summary.md")
    init_parser.add_argument("--context-plan", help="Path to upstream context-plan.md")
    init_parser.add_argument("--context-question", action="append", help="Targeted context question; repeat for 3-8 questions when known")
    init_parser.add_argument("--force", action="store_true", help="Overwrite existing paper-context files")
    init_parser.set_defaults(func=init_artifacts)
    validate_parser = subparsers.add_parser("validate", help="Validate completed paper-context artifacts")
    add_common(validate_parser)
    validate_parser.add_argument(
        "--draft",
        action="store_true",
        help="Allow TODO placeholders and unset (null) ratings in an in-progress bundle",
    )
    validate_parser.set_defaults(func=validate_artifacts)
    promote_parser = subparsers.add_parser(
        "promote",
        help="Turn a four-file paper context into a seven-file literature pack skeleton for linked novelty validation",
    )
    add_common(promote_parser)
    promote_parser.add_argument("--pack-dir", required=True, help="Directory for the seven-file literature pack")
    promote_parser.add_argument("--topic", help="Pack topic; defaults to the context's target_paper")
    promote_parser.add_argument("--domain", help="Pack domain; defaults to the context's domain")
    promote_parser.add_argument("--review-profile", default="novelty-prior-art", help="Review profile for the new pack")
    promote_parser.add_argument("--force", action="store_true", help="Overwrite an existing pack with the same topic")
    promote_parser.set_defaults(func=promote_artifacts)
    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()
    try:
        return args.func(args)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
