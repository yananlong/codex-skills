#!/usr/bin/env python3
"""Create and validate paper-context evidence-map artifacts."""

from __future__ import annotations

import argparse
import json
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
    upstream_lines = [
        f"- summary.md: {summary_path or 'TODO'}",
        f"- context-plan.md: {context_plan_path or 'TODO'}",
    ]
    upstream_artifacts = "\n".join(upstream_lines)
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

Summarize the exact sources, queries, filters, retrieval dates, and inclusion decisions. Keep detailed rows in `literature-context-search-log.md`.

| run_id | source | query_string | filters | purpose | records_returned | retained |
| --- | --- | --- | --- | --- | ---: | ---: |
| run-001 | TODO | TODO | TODO | falsify/support C1 | 0 | 0 |

## Closest Prior Work

| work_id | Citation | Venue / year | Why close | Threatened target claim | Notes |
| --- | --- | --- | --- | --- | --- |
| P1 | TODO | TODO | TODO | C1 | TODO |

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
| C1 | TODO | TODO | 3 |

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
| run-001 | {today} | TODO | TODO | TODO | falsify/support target paper claim | 0 | 0 | TODO |

## Inclusion Decisions

| record_id | citation | source_run | decision | reason |
| --- | --- | --- | --- | --- |
| rec-001 | TODO | run-001 | include / exclude / duplicate | TODO |

## Version Resolution

| mapping_id | preprint_or_submission | canonical_record | status | notes |
| --- | --- | --- | --- | --- |
| map-001 | TODO | TODO | resolved / unresolved | TODO |
"""


def _evidence_table_md(args: argparse.Namespace) -> str:
    target_paper = args.target_paper or "TODO"
    return f"""# Literature Context Evidence Table: {target_paper}

| work_id | Citation | Publication status | Venue / year | Claim relevance | Key evidence | Risk or limitation | Target-paper implication |
| --- | --- | --- | --- | --- | --- | --- | --- |
| P1 | TODO | published / preprint / submission | TODO | closest prior work / benchmark norm / impact evidence | TODO | TODO | TODO |
"""


def _decision_json(args: argparse.Namespace, out_dir: Path, summary_path: str, context_plan_path: str) -> str:
    payload: dict[str, Any] = {
        "mode": "paper_context_evidence_map",
        "target_paper": args.target_paper,
        "domain": args.domain,
        "target_community": args.target_community,
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
    (out_dir / "literature-context.md").write_text(
        _context_md(args, summary_path=summary_path, context_plan_path=context_plan_path),
        encoding="utf-8",
    )
    (out_dir / "literature-context-search-log.md").write_text(
        _search_log_md(args),
        encoding="utf-8",
    )
    (out_dir / "literature-context-evidence-table.md").write_text(
        _evidence_table_md(args),
        encoding="utf-8",
    )
    (out_dir / "literature-context-decision.json").write_text(
        _decision_json(args, out_dir=out_dir, summary_path=summary_path, context_plan_path=context_plan_path),
        encoding="utf-8",
    )

    print(f"Initialized paper-context evidence map: {out_dir}")
    for path in paths:
        print(f"- {path}")
    return 0


def _is_rating(value: Any) -> bool:
    return isinstance(value, int) and 1 <= value <= 5


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


def validate_artifacts(args: argparse.Namespace) -> int:
    out_dir = _resolve_out_dir(args)
    errors: list[str] = []

    for name in REQUIRED_FILES:
        if not (out_dir / name).exists():
            errors.append(f"Missing required paper-context artifact: {out_dir / name}")

    context_path = out_dir / "literature-context.md"
    if context_path.exists():
        context_md = context_path.read_text(encoding="utf-8")
        for heading in REQUIRED_CONTEXT_HEADINGS:
            if heading not in context_md:
                errors.append(f"literature-context.md missing heading: {heading}")
        if "bounded paper-context evidence map, not a full systematic review" not in context_md:
            errors.append("literature-context.md must state that bounded paper-context mode is not a full systematic review")

    decision_path = out_dir / "literature-context-decision.json"
    if decision_path.exists():
        decision = _load_json(decision_path, errors)
        for field in REQUIRED_DECISION_FIELDS:
            if field not in decision:
                errors.append(f"literature-context-decision.json missing field: {field}")
        for field in [
            "contextualization_rating",
            "impact_evidence_rating",
            "coverage_confidence_rating",
        ]:
            if field in decision and not _is_rating(decision[field]):
                errors.append(f"literature-context-decision.json field {field} must be an integer from 1 to 5")

    if errors:
        print("Paper-context validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"Paper-context validation passed: {out_dir}")
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
    init_parser.add_argument(
        "--context-question",
        action="append",
        help="Targeted context question; repeat for 3-8 questions when known",
    )
    init_parser.add_argument("--force", action="store_true", help="Overwrite existing paper-context files")
    init_parser.set_defaults(func=init_artifacts)

    validate_parser = subparsers.add_parser("validate", help="Validate completed paper-context artifacts")
    add_common(validate_parser)
    validate_parser.set_defaults(func=validate_artifacts)

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
