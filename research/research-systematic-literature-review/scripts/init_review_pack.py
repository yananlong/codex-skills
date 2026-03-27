#!/usr/bin/env python3
"""Initialize a Markdown review pack for systematic literature review workflows."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Dict, List


@dataclass(frozen=True)
class ReviewInputs:
    topic: str
    domain: str
    out_dir: Path
    question: str
    inclusion_criteria: str
    exclusion_criteria: str
    date_range: str
    study_types: str
    language: str
    population_context: str
    outcomes: str
    quality_threshold: str
    assumptions: List[str]
    today: str


def _normalize_topic_to_slug(topic: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", topic.lower()).strip("-")
    if not slug:
        raise ValueError("Topic is invalid after normalization; provide alphanumeric text.")
    return slug


def _non_empty(name: str, value: str | None) -> str:
    if value is None:
        raise ValueError(f"Missing required value: {name}")
    trimmed = value.strip()
    if not trimmed:
        raise ValueError(f"{name} cannot be empty.")
    return trimmed


def _defaults(topic: str, domain: str) -> Dict[str, str]:
    today = date.today()
    default_start = date(today.year - 10, 1, 1)
    return {
        "question": f"What does current evidence show about {topic} in {domain}?",
        "inclusion_criteria": (
            "Include peer-reviewed primary studies (published) directly relevant to topic and domain. "
            "Use high-quality preprints only when no published version exists or when recency is essential, "
            "and label them as preprints."
        ),
        "exclusion_criteria": (
            "Exclude off-topic sources, narrative-only commentary without methods, and "
            "studies with insufficient methodological detail."
        ),
        "date_range": f"{default_start.isoformat()} to {today.isoformat()}",
        "study_types": (
            "Experimental, observational, benchmarking, and systematic-review studies where relevant"
        ),
        "language": "English",
        "population_context": (
            "Broad population/context implied by topic and domain unless explicitly narrowed"
        ),
        "outcomes": (
            "Efficacy/performance, robustness, safety, and transferability outcomes where applicable"
        ),
        "quality_threshold": (
            "Retain studies with at least moderate methodological quality and transparent reporting"
        ),
        "today": today.isoformat(),
    }


def _resolve_inputs(args: argparse.Namespace) -> ReviewInputs:
    topic = _non_empty("topic", args.topic)
    domain = _non_empty("domain", args.domain)
    out_dir = Path(_non_empty("out-dir", args.out_dir)).expanduser().resolve()
    d = _defaults(topic=topic, domain=domain)

    assumptions: List[str] = []

    def choose(field_name: str, cli_value: str | None) -> str:
        if cli_value is not None:
            return _non_empty(field_name, cli_value)
        assumptions.append(f"{field_name} defaulted to: {d[field_name]}")
        return d[field_name]

    return ReviewInputs(
        topic=topic,
        domain=domain,
        out_dir=out_dir,
        question=choose("question", args.question),
        inclusion_criteria=choose("inclusion_criteria", args.inclusion_criteria),
        exclusion_criteria=choose("exclusion_criteria", args.exclusion_criteria),
        date_range=choose("date_range", args.date_range),
        study_types=choose("study_types", args.study_types),
        language=choose("language", args.language),
        population_context=choose("population_context", args.population_context),
        outcomes=choose("outcomes", args.outcomes),
        quality_threshold=choose("quality_threshold", args.quality_threshold),
        assumptions=assumptions,
        today=d["today"],
    )


def _protocol_md(inputs: ReviewInputs) -> str:
    assumption_lines = "\n".join(f"- {line}" for line in inputs.assumptions) or "- No defaults were applied."
    return f"""# Protocol: {inputs.topic}

## Metadata

| Field | Value |
| --- | --- |
| Topic | {inputs.topic} |
| Domain | {inputs.domain} |
| Protocol version | v1 |
| Created date | {inputs.today} |
| Reviewer | TODO |

## Inputs

| Input | Value |
| --- | --- |
| research_question | {inputs.question} |
| inclusion_criteria | {inputs.inclusion_criteria} |
| exclusion_criteria | {inputs.exclusion_criteria} |
| date_range | {inputs.date_range} |
| study_types | {inputs.study_types} |
| language | {inputs.language} |
| population/context | {inputs.population_context} |
| outcomes | {inputs.outcomes} |
| quality_threshold | {inputs.quality_threshold} |

## Assumptions applied

{assumption_lines}

## Inclusion criteria

- TODO

## Exclusion criteria

- TODO

## PRISMA scope

- Records identified from all eligible sources.
- Deduplication performed before title/abstract screening.
- Full-text eligibility decisions recorded with explicit reasons.

## Deviations log

- None yet.
"""


def _search_log_md(inputs: ReviewInputs) -> str:
    return f"""# Search Log: {inputs.topic}

## Search metadata

| Field | Value |
| --- | --- |
| Topic | {inputs.topic} |
| Domain | {inputs.domain} |
| Date range | {inputs.date_range} |
| Language | {inputs.language} |
| Search date | {inputs.today} |

## Source queries

| run_id | date | source | query_string | filters | records_returned | notes |
| --- | --- | --- | --- | --- | ---: | --- |
| run-001 | {inputs.today} | TODO | TODO | TODO | 0 | |

## Deduplication ledger

| step_id | method | input_records | duplicates_removed | output_records | notes |
| --- | --- | ---: | ---: | ---: | --- |
| dedup-001 | exact-title-doi | 0 | 0 | 0 | |

## Version resolution ledger (preprint → published)

Use this ledger to resolve preprints (e.g., arXiv/bioRxiv/SSRN) to their peer-reviewed published versions when available.

| mapping_id | preprint_citation | preprint_id | resolved_published_citation | doi | status | notes |
| --- | --- | --- | --- | --- | --- | --- |
| map-001 | | | | | resolved/unresolved | |

## Coverage notes

- TODO: Document coverage limitations, source outages, or inaccessible corpora.
"""


def _screening_log_md(inputs: ReviewInputs) -> str:
    return f"""# Screening Log: {inputs.topic}

## Stage definitions

- title_abstract: initial relevance screen.
- full_text: eligibility after full document review.

## PRISMA Counts

| Metric | Count |
| --- | ---: |
| records_identified | 0 |
| duplicates_removed | 0 |
| records_screened | 0 |
| records_excluded | 0 |
| reports_sought_for_retrieval | 0 |
| reports_not_retrieved | 0 |
| reports_assessed_for_eligibility | 0 |
| reports_excluded | 0 |
| studies_included | 0 |

## Exclusion reasons (title/abstract)

| reason | count |
| --- | ---: |
| off-topic | 0 |
| wrong-study-type | 0 |
| insufficient-detail | 0 |

## Exclusion reasons (full-text)

| reason | count |
| --- | ---: |
| wrong-endpoint | 0 |
| unresolved-method-issues | 0 |
| duplicate-publication | 0 |

## Decision ledger

| study_id | record_type | canonical_citation | doi | venue | preprint_id | stage | decision | reason | reviewer | date | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| | published/preprint | | | | | title_abstract | include/exclude | | | {inputs.today} | |
"""


def _evidence_md(inputs: ReviewInputs) -> str:
    return f"""# Evidence Table: {inputs.topic}

## Extraction matrix

| study_id | canonical_citation | year | venue | doi | publication_status | preprint_id | population_or_context | study_design | sample_size | intervention_or_exposure | comparator | outcomes | key_result | effect_size | risk_of_bias | notes |
| --- | --- | ---: | --- | --- | --- | --- | --- | --- | ---: | --- | --- | --- | --- | --- | --- | --- |
| | | 0 | | | published/preprint | | {inputs.population_context} | | 0 | | | {inputs.outcomes} | | | low/moderate/high | |

## Extraction notes

- Use one row per included study.
- Keep outcome naming consistent across rows.
- Keep claims traceable to the corresponding study row.
"""


def _report_md(inputs: ReviewInputs, flow_relative_path: str) -> str:
    return f"""# Systematic Literature Review: {inputs.topic}

## Protocol

- Domain: {inputs.domain}
- Research question: {inputs.question}
- Inclusion criteria: {inputs.inclusion_criteria}
- Exclusion criteria: {inputs.exclusion_criteria}
- Date range: {inputs.date_range}
- Study types: {inputs.study_types}
- Language: {inputs.language}
- Population/context: {inputs.population_context}
- Outcomes: {inputs.outcomes}
- Quality threshold: {inputs.quality_threshold}

## Search Strategy

- Sources searched: TODO
- Query logic: TODO
- Deduplication approach: TODO
- Publication status policy: prefer peer-reviewed published versions; treat preprints as supplemental unless no published version exists.

## Screening Decisions

- Title/abstract stage summary: TODO
- Full-text stage summary: TODO
- Exclusion reasons summary: TODO

## Evidence Table

- Included-study profile: TODO
- Risk-of-bias profile: TODO

## Synthesis

- High-confidence findings: TODO
- Mixed or contradictory findings: TODO
- Open questions: TODO

## Adversarial Stress Test

- Vulnerable claims and caveats: TODO
- Potential overreach and framing risks: TODO

## Limitations

- Search limitations: TODO
- Data/method limitations: TODO
- Inference limitations: TODO

## Confidence Assessment

- Claim-level confidence: TODO
- Confidence rationale: TODO

## PRISMA flow accounting

Generate and paste flow content from `{flow_relative_path}` produced by `scripts/prisma_flow_md.py`.
"""


def _build_paths(out_dir: Path, topic_slug: str) -> Dict[str, Path]:
    return {
        "protocol": out_dir / f"{topic_slug}.protocol.md",
        "search": out_dir / f"{topic_slug}.search-log.md",
        "screening": out_dir / f"{topic_slug}.screening-log.md",
        "evidence": out_dir / f"{topic_slug}.evidence-table.md",
        "report": out_dir / f"{topic_slug}.review.md",
        "flow": out_dir / f"{topic_slug}.prisma-flow.md",
    }


def _ensure_writable(paths: Dict[str, Path], force: bool) -> None:
    existing = [str(path) for name, path in paths.items() if name != "flow" and path.exists()]
    if existing and not force:
        joined = "\n  - ".join(existing)
        raise ValueError(
            "Refusing to overwrite existing review artifacts. Use --force to overwrite:\n"
            f"  - {joined}"
        )


def _write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create a deterministic Markdown review pack for systematic literature review workflows.",
    )
    parser.add_argument("--topic", required=True, help="Review topic title.")
    parser.add_argument("--domain", required=True, help="Domain label (required gate).")
    parser.add_argument("--out-dir", required=True, help="Output directory for review artifacts.")
    parser.add_argument("--question", help="Research question.")
    parser.add_argument("--inclusion-criteria", help="Inclusion criteria text.")
    parser.add_argument("--exclusion-criteria", help="Exclusion criteria text.")
    parser.add_argument("--date-range", help="Date range text (e.g., 2016-01-01 to 2026-02-23).")
    parser.add_argument("--study-types", help="Allowed study types.")
    parser.add_argument("--language", help="Language scope.")
    parser.add_argument("--population-context", help="Population/context scope.")
    parser.add_argument("--outcomes", help="Outcome scope.")
    parser.add_argument("--quality-threshold", help="Minimum study quality threshold.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing artifacts if present.")
    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    try:
        inputs = _resolve_inputs(args)
        topic_slug = _normalize_topic_to_slug(inputs.topic)
        paths = _build_paths(inputs.out_dir, topic_slug)
        _ensure_writable(paths, force=args.force)

        flow_relative_path = paths["flow"].name
        _write_file(paths["protocol"], _protocol_md(inputs))
        _write_file(paths["search"], _search_log_md(inputs))
        _write_file(paths["screening"], _screening_log_md(inputs))
        _write_file(paths["evidence"], _evidence_md(inputs))
        _write_file(paths["report"], _report_md(inputs, flow_relative_path=flow_relative_path))

        print("Created review artifact pack:")
        print(f"  - {paths['report']}")
        print(f"  - {paths['protocol']}")
        print(f"  - {paths['search']}")
        print(f"  - {paths['screening']}")
        print(f"  - {paths['evidence']}")
        print(f"Next step: run prisma_flow_md.py to produce {paths['flow'].name}")
        return 0
    except Exception as exc:  # pylint: disable=broad-except
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
