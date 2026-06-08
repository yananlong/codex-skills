# Paper-Context Evidence Map Template

Use this template when `research-systematic-literature-review` is invoked from `research-paper-review` to contextualize one paper's novelty, impact, related-work adequacy, or benchmark claims. When a paper-review workspace exists, place all four files under `<review_dir>/context/`; otherwise place them in one explicit paper-context output directory and preserve that path for later handoff.

This is a bounded paper-context evidence map, not a full systematic review, unless the full PRISMA workflow was actually completed.

## Scope

- Target paper:
- Domain:
- Target community / venue:
- Upstream paper-review artifacts:
- Context questions:
- Search date:
- Reviewer constraints:

## Target Paper Claims Being Contextualized

| claim_id | Claim | Claim type | Paper location | What external evidence must establish |
| --- | --- | --- | --- | --- |
| C1 | | novelty / impact / SOTA / benchmark / related-work adequacy | | |

## Search Strategy

Summarize the exact sources, queries, filters, retrieval dates, and inclusion decisions. Keep detailed rows in `literature-context-search-log.md`.

| run_id | source | query_string | filters | purpose | records_returned | retained |
| --- | --- | --- | --- | --- | ---: | ---: |
| run-001 | | | | falsify/support C1 | 0 | 0 |

## Closest Prior Work

| work_id | Citation | Venue / year | Why close | Threatened target claim | Notes |
| --- | --- | --- | --- | --- | --- |
| P1 | | | | | |

## Related-Work Coverage Assessment

- Adequately covered work:
- Missing or under-discussed work:
- Mischaracterized work:
- Preprint vs published-version issues:

## Benchmark Or Evaluation Context

- Common datasets / tasks / baselines in this area:
- Norms for uncertainty, ablations, statistical testing, or robustness:
- Target paper gaps:

## Impact / Significance Context

- External evidence supporting significance:
- External evidence weakening significance:
- Communities or use cases for which impact is plausible:
- Communities or use cases for which the impact claim is overstated:

## Claims That Need Qualification

| claim_id | Required qualification | Evidence basis | Confidence (1-5) |
| --- | --- | --- | ---: |
| C1 | | | 3 |

## Confidence and Limitations

- Coverage confidence:
- Search limitations:
- Evidence limitations:

# literature-context-search-log.md

## Search Runs

| run_id | date | source | query_string | filters | purpose | records_returned | retained | notes |
| --- | --- | --- | --- | --- | --- | ---: | ---: | --- |
| run-001 | | | | | falsify/support target paper claim | 0 | 0 | |

## Inclusion Decisions

| record_id | citation | source_run | decision | reason |
| --- | --- | --- | --- | --- |
| rec-001 | | run-001 | include / exclude / duplicate | |

## Version Resolution

| mapping_id | preprint_or_submission | canonical_record | status | notes |
| --- | --- | --- | --- | --- |
| map-001 | | | resolved / unresolved | |

# literature-context-evidence-table.md

| work_id | Citation | Publication status | Venue / year | Claim relevance | Key evidence | Risk or limitation | Target-paper implication |
| --- | --- | --- | --- | --- | --- | --- | --- |
| P1 | | published / preprint / submission | | closest prior work / benchmark norm / impact evidence | | | |

# literature-context-decision.json

```json
{
  "mode": "paper_context_evidence_map",
  "contextualization_rating": 3,
  "impact_evidence_rating": 3,
  "coverage_confidence_rating": 3,
  "closest_prior_work": [],
  "related_work_omissions": [],
  "benchmark_context_gaps": [],
  "limits_of_search": []
}
```

Decision fields:

- contextualization_rating (1-5):
- impact_evidence_rating (1-5):
- coverage_confidence_rating (1-5):
- closest_prior_work:
- related_work_omissions:
- benchmark_context_gaps:
- limits_of_search:
