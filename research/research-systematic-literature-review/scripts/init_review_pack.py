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
    date_range: str
    language: str
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
    profile = require("review-profile", args.review_profile)
    if profile not in PROFILES:
        raise ValueError(f"review-profile must be one of {sorted(PROFILES)}")
    today = date.today().isoformat()
    question = args.question.strip() if args.question else f"What does current evidence show about {topic} in {domain}?"
    date_range = args.date_range.strip() if args.date_range else "Foundational horizon unrestricted; current-evidence horizon and update horizon to be declared"
    language = args.language.strip() if args.language else "English unless the protocol declares additional languages"
    return Inputs(topic, domain, profile, Path(args.out_dir).expanduser().resolve(), question, date_range, language, today)


def protocol(i: Inputs) -> str:
    return f"""# Protocol: {i.topic}

## Metadata

| Field | Value |
| --- | --- |
| Topic | {i.topic} |
| Domain | {i.domain} |
| Review profile | {i.profile} |
| Created date | {i.today} |
| Reviewer | TODO |

## Inputs

| Input | Value |
| --- | --- |
| research_question | {i.question} |
| date_range | {i.date_range} |
| language | {i.language} |
| intended_decision | TODO |
| domain_adapter | TODO |

## Assumptions applied

- TODO

## Inclusion criteria

- TODO

## Exclusion criteria

- TODO

## Discovery assurance

- Visible seed set required: {'yes' if 'systematic' in i.profile else 'proportionate to profile'}
- Withheld challenge set: TODO available / unavailable and why
- Search-strategy review: TODO required / not required and why
- Corpus freeze required before detailed extraction: {'yes' if 'systematic' in i.profile else 'recommended'}

## PRISMA scope

- PRISMA accounts for record flow and does not establish retrieval completeness.
- Canonical publication versions are preferred over duplicate preprints.

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
| seed-001 | TODO | foundation / close anchor / expert seed | | no | | |

## Search-channel decisions

| channel | status | rationale | rounds | unique_candidates | included_yield | last_round_yield |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| backward-citation | required/performed/unavailable/not-applicable | TODO | 0 | 0 | 0 | 0 |
| forward-citation | required/performed/unavailable/not-applicable | TODO | 0 | 0 | 0 | 0 |
| venue-census | required/performed/unavailable/not-applicable | TODO | 0 | 0 | 0 | 0 |
| author-lab-expansion | required/performed/unavailable/not-applicable | TODO | 0 | 0 | 0 | 0 |
| benchmark-dataset-tracing | required/performed/unavailable/not-applicable | TODO | 0 | 0 | 0 | 0 |
| prior-review-harvesting | required/performed/unavailable/not-applicable | TODO | 0 | 0 | 0 | 0 |
| grey-literature | required/performed/unavailable/not-applicable | TODO | 0 | 0 | 0 | 0 |
| zotero-cross-check | required/performed/unavailable/not-applicable | TODO | 0 | 0 | 0 | 0 |

## Deduplication ledger

| step_id | method | input_records | duplicates_removed | output_records | notes |
| --- | --- | ---: | ---: | ---: | --- |
| dedup-001 | exact-title-doi | 0 | 0 | 0 | |

## Version resolution ledger

| mapping_id | preprint_citation | preprint_url | resolved_published_citation | resolved_publication_url | doi | status | notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| map-001 | | | | | | resolved/unresolved | |

## Search repairs and late omissions

| event_id | publication_or_gap | severity | why_missed | repair | conclusions_changed |
| --- | --- | --- | --- | --- | --- |
| repair-001 | | | | | no |

## Coverage notes

- TODO: coverage topology, empty high-priority cells, unavailable sources, and mitigations.
"""


def recall_audit(i: Inputs) -> str:
    return f"""# Recall Audit: {i.topic}

## Declared review profile

- Profile: {i.profile}
- Intended decision: TODO

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

- TODO none or list each omission, why it was missed, and the repaired strategy.

## Stopping rationale

- TODO: justify stopping from seed/challenge recovery, coverage, marginal yield, constraints, and residual omission risk.

## Bounded assurance verdict

- Verdict: insufficient
- Supported claim scope: TODO
- Unsupported completeness or priority claims: TODO
"""


def screening(i: Inputs) -> str:
    return f"""# Screening Log: {i.topic}

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

## Decision ledger

| study_id | record_type | canonical_citation | publication_url | stage | decision | reason | reviewer | date | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| | published/preprint/book/report/software | | | title_abstract | include/exclude | | | {i.today} | |
"""


def evidence(i: Inputs) -> str:
    return f"""# Evidence Table: {i.topic}

## Extraction matrix

| study_id | canonical_citation | publication_url | publication_status | work_type | context_or_formal_setting | method_or_argument | result_or_proposition | limitations | quality_or_risk | relevance_to_question | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| | | | published/preprint | empirical/theoretical/method/benchmark/review | | | | | low/moderate/high | | |
"""


def report(i: Inputs, flow_name: str) -> str:
    return f"""# Systematic Literature Review: {i.topic}

## Protocol

- Domain: {i.domain}
- Review profile: {i.profile}
- Research question: {i.question}

## Discovery Assurance

- Seed and challenge recovery: TODO
- Citation and expansion channels: TODO
- Corpus freeze and amendments: TODO
- Assurance verdict: insufficient

## Search Strategy

- Sources, queries, search repairs, and version-resolution policy: TODO

## Screening Decisions

- TODO

## Evidence Table

- TODO

## Synthesis

- High-confidence findings: TODO
- Mixed, negative, or contradictory findings: TODO
- Coverage-dependent conclusions: TODO

## Adversarial Stress Test

- Claim-killing work, alternative terminology, and late-omission challenge: TODO

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
    p.add_argument("--review-profile", required=True, choices=sorted(PROFILES))
    p.add_argument("--out-dir", required=True)
    p.add_argument("--question")
    p.add_argument("--date-range")
    p.add_argument("--language")
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
        existing = [str(p) for k, p in paths.items() if k != "flow" and p.exists()]
        if existing and not args.force:
            raise ValueError("refusing to overwrite existing artifacts: " + ", ".join(existing))
        contents = {
            "protocol": protocol(i), "search": search_log(i), "recall": recall_audit(i),
            "screening": screening(i), "evidence": evidence(i), "report": report(i, paths["flow"].name),
        }
        for key, text in contents.items():
            paths[key].write_text(text, encoding="utf-8")
        manifest = {
            "schema_version": "1.0", "topic": i.topic, "review_profile": i.profile,
            "freeze_date": None, "corpus_version": 1, "records": [], "seed_ids": [],
            "challenge_ids": [], "post_freeze_amendments": [],
            "search_strategy_review": {"performed": False, "independence": "self-review", "notes": ""},
            "assurance_verdict": "insufficient",
        }
        paths["manifest"].write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        for key in ("report", "protocol", "search", "recall", "manifest", "screening", "evidence"):
            print(f"created {paths[key]}")
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
