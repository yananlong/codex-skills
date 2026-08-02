#!/usr/bin/env python3
"""Initialize a recall-audited literature review pack."""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path

PROFILES = {
    "comprehensive-systematic",
    "bounded-systematic",
    "critical-evidence-map",
    "rapid-scan",
    "novelty-prior-art",
}


@dataclass(frozen=True)
class Inputs:
    topic: str
    domain: str
    profile: str
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
    domain_adapter: str
    intended_decision: str
    assumptions: tuple[str, ...]
    today: str


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    if not slug:
        raise ValueError("topic is invalid after normalization")
    return slug


def require(name: str, value: str | None) -> str:
    if value is None or not value.strip():
        raise ValueError(f"{name} is required")
    return value.strip()


def resolve(args: argparse.Namespace) -> Inputs:
    topic = require("topic", args.topic)
    domain = require("domain", args.domain)
    assumptions: list[str] = []
    profile = args.review_profile or "bounded-systematic"
    if args.review_profile is None:
        assumptions.append("review_profile defaulted to bounded-systematic; confirm the boundary before searching")
    if profile not in PROFILES:
        raise ValueError(f"review-profile must be one of {sorted(PROFILES)}")

    defaults = {
        "question": f"What does current evidence show about {topic} in {domain}?",
        "inclusion_criteria": "Include works that directly answer the review question and meet the declared domain-adapter criteria.",
        "exclusion_criteria": "Exclude off-topic, duplicate-publication, and methodologically or argumentatively non-substantive records.",
        "date_range": "Foundational horizon unrestricted; current-evidence horizon and update horizon to be declared",
        "study_types": "Adapter-appropriate empirical, theoretical, methodological, benchmark, software, review, and critical work",
        "language": "English unless the protocol declares additional languages and coverage limits",
        "population_context": "Broad context implied by the topic and domain unless explicitly narrowed",
        "outcomes": "Adapter-appropriate outcomes, propositions, mechanisms, comparisons, criticisms, and negative evidence",
        "quality_threshold": "Retain records with enough methodological, formal, or argumentative detail for evidence extraction",
        "domain_adapter": "TODO select an empirical, methodological, theoretical, benchmark, interdisciplinary, novelty, or emerging-field adapter",
        "intended_decision": "TODO state the decision this review will support",
    }

    def choose(field: str, value: str | None) -> str:
        if value is not None:
            return require(field.replace("_", "-"), value)
        assumptions.append(f"{field} defaulted to: {defaults[field]}")
        return defaults[field]

    return Inputs(
        topic=topic,
        domain=domain,
        profile=profile,
        out_dir=Path(require("out-dir", args.out_dir)).expanduser().resolve(),
        question=choose("question", args.question),
        inclusion_criteria=choose("inclusion_criteria", args.inclusion_criteria),
        exclusion_criteria=choose("exclusion_criteria", args.exclusion_criteria),
        date_range=choose("date_range", args.date_range),
        study_types=choose("study_types", args.study_types),
        language=choose("language", args.language),
        population_context=choose("population_context", args.population_context),
        outcomes=choose("outcomes", args.outcomes),
        quality_threshold=choose("quality_threshold", args.quality_threshold),
        domain_adapter=choose("domain_adapter", args.domain_adapter),
        intended_decision=choose("intended_decision", args.intended_decision),
        assumptions=tuple(assumptions),
        today=date.today().isoformat(),
    )


def protocol(i: Inputs) -> str:
    assumptions = "\n".join(f"- {value}" for value in i.assumptions) or "- No defaults were applied."
    return f"""# Protocol: {i.topic}

## Metadata

| Field | Value |
| --- | --- |
| Topic | {i.topic} |
| Domain | {i.domain} |
| Review profile | {i.profile} |
| Protocol version | v1 |
| Created date | {i.today} |
| Reviewer | TODO |

## Inputs

| Input | Value |
| --- | --- |
| research_question | {i.question} |
| intended_decision | {i.intended_decision} |
| domain_adapter | {i.domain_adapter} |
| inclusion_criteria | {i.inclusion_criteria} |
| exclusion_criteria | {i.exclusion_criteria} |
| date_range | {i.date_range} |
| study_types | {i.study_types} |
| language | {i.language} |
| population/context | {i.population_context} |
| outcomes | {i.outcomes} |
| quality_threshold | {i.quality_threshold} |

## Assumptions applied

{assumptions}

## Inclusion criteria

- TODO convert the protocol inputs into operational inclusion rules.

## Exclusion criteria

- TODO convert the protocol inputs into operational exclusion rules.

## Discovery assurance

- Visible seed set required: {'yes' if i.profile in {'comprehensive-systematic', 'bounded-systematic'} else 'proportionate to profile'}
- Withheld challenge set: TODO available / unavailable, custodian, and reason
- Search-strategy review: TODO required / not required and why
- Corpus freeze required before detailed extraction: {'yes' if i.profile in {'comprehensive-systematic', 'bounded-systematic'} else 'recommended'}

## PRISMA scope

- PRISMA accounts for record flow and does not establish retrieval completeness.
- Canonical published or accepted versions are preferred over duplicate preprints.
- The review profile and recall audit determine the maximum defensible coverage claim.

## Deviations log

- None yet.
"""


def search_log(i: Inputs) -> str:
    return f"""# Search Log: {i.topic}

## Search metadata

| Field | Value |
| --- | --- |
| Topic | {i.topic} |
| Domain | {i.domain} |
| Review profile | {i.profile} |
| Date range | {i.date_range} |
| Language | {i.language} |
| Search date | {i.today} |

## Source queries

| run_id | date | channel | source | coverage_target | query_or_seed | filters | records_returned | unique_candidates | included_yield | new_vocabulary | next_repair_action |
| --- | --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| run-001 | {i.today} | database | TODO | TODO | TODO | TODO | 0 | 0 | 0 | | |

## Seed recovery ledger

| seed_id | canonical_citation | why_seeded | recovered_by_run | recovered | miss_reason | repair_run |
| --- | --- | --- | --- | --- | --- | --- |
| seed-001 | TODO | foundation / close anchor / expert seed | | no | TODO | TODO |

## Search-channel decisions

| channel | status | rationale | rounds | unique_candidates | included_yield | last_round_yield |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| backward-citation | required | TODO | 0 | 0 | 0 | 0 |
| forward-citation | required | TODO | 0 | 0 | 0 | 0 |
| venue-census | required | TODO | 0 | 0 | 0 | 0 |
| author-lab-expansion | required | TODO | 0 | 0 | 0 | 0 |
| benchmark-dataset-tracing | required | TODO | 0 | 0 | 0 | 0 |
| prior-review-harvesting | required | TODO | 0 | 0 | 0 | 0 |
| grey-literature | required | TODO | 0 | 0 | 0 | 0 |
| zotero-cross-check | required | TODO | 0 | 0 | 0 | 0 |

## Deduplication ledger

| step_id | method | input_records | duplicates_removed | output_records | notes |
| --- | --- | ---: | ---: | ---: | --- |
| dedup-001 | exact-title-doi | 0 | 0 | 0 | |

## Zotero library sync

| sync_id | date | access_mode | library_type | library_id | collection_key | tags | query | items_retrieved | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | ---: | --- |
| zot-001 | {i.today} | api-key / oauth-key / mcp | user / group | | | | | 0 | |

## Version resolution ledger

| mapping_id | preprint_citation | preprint_id | preprint_url | resolved_published_citation | resolved_publication_url | doi | status | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| map-001 | | | | | | | resolved/unresolved | |

## Search repairs and late omissions

| event_id | publication_or_gap | severity | why_missed | repair | conclusions_changed |
| --- | --- | --- | --- | --- | --- |
| repair-001 | | | | | no |

## Coverage notes

- TODO document coverage topology, high-priority empty cells, unavailable sources, and mitigations.
"""


def recall_audit(i: Inputs) -> str:
    return f"""# Recall Audit: {i.topic}

## Declared review profile

- Profile: {i.profile}
- Intended decision: {i.intended_decision}

## Visible seed recovery

- Seeds defined: TODO
- Seeds recovered through ordinary discovery: TODO
- Recovery failures and repairs: TODO

## Withheld challenge evaluation

- Challenge set available: TODO yes / no
- Separation from query design: TODO
- Recovery result or reason unavailable: TODO

## Search-channel assurance

- Backward citation searching: TODO
- Forward citation searching: TODO
- Venue, author, benchmark, prior-review, grey-literature, and Zotero decisions: TODO
- Marginal yield by expansion round: TODO

## Search-strategy review

- Performed: TODO yes / no
- Reviewer and material separation: TODO
- Defects found and repairs: TODO

## Coverage gaps and source constraints

- TODO

## Corpus freeze

- Manifest: `{slugify(i.topic)}.corpus-manifest.json`
- Corpus version: 1
- Freeze identifier/date: TODO
- Post-freeze amendments: TODO

## Late major omissions

- TODO none, or list every material omission, why it was missed, and the repaired strategy.

## Stopping rationale

- TODO justify stopping from seed/challenge recovery, coverage, marginal yield, constraints, and residual omission risk.

## Bounded assurance verdict

- Verdict: insufficient
- Supported claim scope: TODO
- Unsupported completeness or priority claims: TODO
"""


def screening(i: Inputs) -> str:
    return f"""# Screening Log: {i.topic}

## Stage definitions

- `title_abstract`: initial relevance screen.
- `full_text`: eligibility after full-document inspection.

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

## Exclusion reasons

| stage | reason | count |
| --- | --- | ---: |
| title_abstract | off-topic | 0 |
| full_text | duplicate-publication | 0 |

## Decision ledger

| study_id | record_type | canonical_citation | publication_url | doi | venue | preprint_id | stage | decision | reason | reviewer | date | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| | published/preprint/book/report/software | | | | | | title_abstract | include/exclude | | | {i.today} | |
"""


def evidence(i: Inputs) -> str:
    return f"""# Evidence Table: {i.topic}

## Extraction matrix

| study_id | canonical_citation | publication_url | year | venue | doi | publication_status | preprint_id | work_type | context_or_formal_setting | method_or_argument | result_or_proposition | limitations | quality_or_risk | relevance_to_question | notes |
| --- | --- | --- | ---: | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| | | | 0 | | | published/preprint | | empirical/theoretical/method/benchmark/review | {i.population_context} | | | | low/moderate/high | | |

## Extraction notes

- Use one row per included work.
- Use adapter-appropriate fields; do not fabricate sample-size, intervention, or effect-size values for theoretical or conceptual work.
- Fill `publication_url` with the canonical published or accepted venue record whenever it exists.
- Keep claims traceable to the corresponding row and record negative or contradictory evidence explicitly.
"""


def report(i: Inputs, flow_name: str) -> str:
    title = "Systematic Literature Review" if i.profile in {"comprehensive-systematic", "bounded-systematic"} else "Literature Evidence Review"
    return f"""# {title}: {i.topic}

## Protocol

- Domain: {i.domain}
- Review profile: {i.profile}
- Research question: {i.question}
- Intended decision: {i.intended_decision}
- Domain adapter: {i.domain_adapter}
- Inclusion criteria: {i.inclusion_criteria}
- Exclusion criteria: {i.exclusion_criteria}
- Date range: {i.date_range}
- Study or work types: {i.study_types}
- Language: {i.language}
- Population/context: {i.population_context}
- Outcomes or conceptual targets: {i.outcomes}
- Quality threshold: {i.quality_threshold}

## Discovery Assurance

- Seed and challenge recovery: TODO
- Citation and expansion channels: TODO
- Search repairs: TODO
- Corpus freeze and amendments: TODO
- Assurance verdict: insufficient

## Search Strategy

- Sources, queries, filters, search repairs, and version-resolution policy: TODO

## Screening Decisions

- TODO

## Evidence Table

- TODO

## Synthesis

- High-confidence findings: TODO
- Mixed, negative, or contradictory findings: TODO
- Coverage-dependent conclusions: TODO
- Unresolved questions: TODO

## Adversarial Stress Test

- Claim-killing work, alternative terminology, correlated evidence, and late-omission challenge: TODO

## Limitations

- Search, source-access, screening, evidence, and inference limitations: TODO

## Confidence Assessment

- Claim-level confidence and residual omission risk: TODO

## PRISMA flow accounting

Generate and paste flow content from `{flow_name}`. PRISMA consistency does not establish retrieval completeness.
"""


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--topic", required=True)
    p.add_argument("--domain", required=True)
    p.add_argument("--review-profile", choices=sorted(PROFILES))
    p.add_argument("--out-dir", required=True)
    p.add_argument("--question")
    p.add_argument("--inclusion-criteria")
    p.add_argument("--exclusion-criteria")
    p.add_argument("--date-range")
    p.add_argument("--study-types")
    p.add_argument("--language")
    p.add_argument("--population-context")
    p.add_argument("--outcomes")
    p.add_argument("--quality-threshold")
    p.add_argument("--domain-adapter")
    p.add_argument("--intended-decision")
    p.add_argument("--force", action="store_true")
    return p


def main() -> int:
    try:
        args = parser().parse_args()
        i = resolve(args)
        slug = slugify(i.topic)
        i.out_dir.mkdir(parents=True, exist_ok=True)
        paths = {
            "protocol": i.out_dir / f"{slug}.protocol.md",
            "search": i.out_dir / f"{slug}.search-log.md",
            "recall": i.out_dir / f"{slug}.recall-audit.md",
            "manifest": i.out_dir / f"{slug}.corpus-manifest.json",
            "screening": i.out_dir / f"{slug}.screening-log.md",
            "evidence": i.out_dir / f"{slug}.evidence-table.md",
            "report": i.out_dir / f"{slug}.review.md",
            "flow": i.out_dir / f"{slug}.prisma-flow.md",
        }
        existing = [str(path) for key, path in paths.items() if key != "flow" and path.exists()]
        if existing and not args.force:
            raise ValueError("refusing to overwrite existing artifacts: " + ", ".join(existing))

        contents = {
            "protocol": protocol(i),
            "search": search_log(i),
            "recall": recall_audit(i),
            "screening": screening(i),
            "evidence": evidence(i),
            "report": report(i, paths["flow"].name),
        }
        for key, text in contents.items():
            paths[key].write_text(text, encoding="utf-8")

        manifest = {
            "schema_version": "1.0",
            "topic": i.topic,
            "review_profile": i.profile,
            "freeze_date": None,
            "corpus_version": 1,
            "records": [],
            "seed_ids": [],
            "challenge_ids": [],
            "post_freeze_amendments": [],
            "search_strategy_review": {
                "performed": False,
                "independence": "self-review",
                "notes": "",
            },
            "assurance_verdict": "insufficient",
        }
        paths["manifest"].write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        for key in ("report", "protocol", "search", "recall", "manifest", "screening", "evidence"):
            print(f"created {paths[key]}")
        print(f"next step: generate {paths['flow'].name} after screening counts are populated")
        return 0
    except Exception as exc:  # pylint: disable=broad-except
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
