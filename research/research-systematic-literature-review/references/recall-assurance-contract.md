# Literature Discovery and Recall Assurance Contract

Use this contract before expensive extraction and synthesis. PRISMA accounting establishes transparent record flow, not adequate retrieval recall.

## Review profiles

- `comprehensive-systematic`: high-recall discovery with explicit assurance and a strong stopping rationale.
- `bounded-systematic`: systematic within declared sources, dates, venues, languages, or corpora.
- `critical-evidence-map`: structured, adversarial contextualization without a completeness claim.
- `rapid-scan`: time-bounded orientation where omissions are expected.
- `novelty-prior-art`: claim-killing search for closest and materially overlapping work.

Never label a review comprehensive merely because protocol, PRISMA, and evidence-table files exist.

## Required assurance for comprehensive and bounded systematic profiles

1. Define a visible quasi-gold seed set of known relevant publications.
2. When feasible, define a withheld challenge set that query designers cannot use for search construction.
3. Record whether backward citation searching, forward citation searching, venue census, author/lab expansion, benchmark/dataset tracing, prior-review harvesting, grey-literature search, and Zotero cross-check are required, performed, unavailable, or not applicable.
4. Test seed recovery through ordinary discovery rather than manual insertion alone.
5. Repair searches when a known relevant publication is missed, recording the missed terminology or source blind spot.
6. Record unique included yield by search channel and marginal yield by expansion round.
7. Reconsider the original strategy when citation searching or late challenge work yields multiple material additions.
8. Freeze the candidate corpus before detailed extraction, hash or enumerate it, and record post-freeze amendments.
9. State a stopping rationale based on recovery, coverage, marginal yield, source constraints, and residual omission risk.
10. Obtain a materially separate search-strategy review for high-stakes novelty, commitment, or expensive execution decisions when feasible; otherwise disclose self-review.

## Recall audit artifact

The canonical file is `<topic>.recall-audit.md` and must include:

- declared review profile;
- visible seed set and recovery result;
- withheld challenge result or reason unavailable;
- search-channel decisions and yields;
- citation-search rounds and marginal yield;
- coverage gaps and source constraints;
- search-strategy review and independence statement;
- corpus-freeze identifier;
- late major omissions and search repairs;
- stopping rationale;
- bounded assurance verdict.

## Corpus manifest

The canonical file is `<topic>.corpus-manifest.json` and contains:

```json
{
  "schema_version": "1.0",
  "topic": "",
  "review_profile": "bounded-systematic",
  "freeze_date": "YYYY-MM-DD",
  "corpus_version": 1,
  "records": [],
  "seed_ids": [],
  "challenge_ids": [],
  "post_freeze_amendments": [],
  "search_strategy_review": {
    "performed": false,
    "independence": "self-review",
    "notes": ""
  },
  "assurance_verdict": "insufficient"
}
```

Allowed `assurance_verdict` values are `insufficient`, `adequate-for-bounded-claims`, and `adequate-for-comprehensive-claim`.

## Hard failures

Fail validation when a systematic profile:

- omits a seed-recovery report;
- omits a citation-search decision;
- omits a stopping rationale;
- lacks a corpus manifest;
- asserts comprehensive coverage while seed recovery is incomplete or major coverage gaps remain unexplained;
- manually adds a major omitted publication without documenting the search failure and repair;
- treats PRISMA counts, file presence, or canonical URLs as evidence of recall.
