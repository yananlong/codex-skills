# Literature Discovery and Recall Assurance Contract

Use this contract before expensive extraction and synthesis. PRISMA accounting establishes transparent record flow, not adequate retrieval recall.

## Review profiles

- `comprehensive-systematic`: high-recall discovery with explicit assurance and a strong stopping rationale.
- `bounded-systematic`: systematic within declared sources, dates, venues, languages, publication types, or corpora.
- `critical-evidence-map`: structured, adversarial contextualization without a completeness claim.
- `rapid-scan`: time-bounded orientation where omissions are expected.
- `novelty-prior-art`: claim-killing search for closest and materially overlapping work.

Never label a review comprehensive merely because protocol, PRISMA, and evidence-table files exist.

## Required assurance for systematic profiles

1. Define a visible quasi-gold seed set of known relevant publications.
2. When feasible, define a withheld challenge set that query designers cannot use for search construction.
3. Record whether backward citation searching, forward citation searching, venue census, author/lab expansion, benchmark/dataset tracing, prior-review harvesting, grey-literature search, and Zotero cross-check are required, performed, unavailable, or not applicable.
4. Test seed recovery through ordinary discovery rather than manual insertion alone.
5. Repair searches when a known relevant publication is missed, recording the missed terminology or source blind spot and the repair run.
6. Record unique included yield by search channel and marginal yield by expansion round.
7. Reconsider the original strategy when citation searching or late challenge work yields material additions.
8. Freeze the candidate corpus before detailed extraction, enumerate it, and record post-freeze amendments.
9. State a stopping rationale based on recovery, coverage, marginal yield, source constraints, and residual omission risk.
10. Obtain a materially separate search-strategy review for comprehensive claims, high-stakes novelty, commitment, or expensive execution decisions when feasible; otherwise disclose self-review and narrow the assurance verdict.

## Recall-audit artifact

The canonical file is `<topic>.recall-audit.md` and includes:

- declared review profile and intended decision;
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

For an adequate verdict, every section must be completed without template placeholders.

## Corpus manifest

The canonical file is `<topic>.corpus-manifest.json`. Schema `1.1` extends the existing authority with coverage questions; do not create a separate question-frontier file.

```json
{
  "schema_version": "1.1",
  "topic": "",
  "review_profile": "bounded-systematic",
  "freeze_date": "YYYY-MM-DD",
  "corpus_version": 1,
  "records": [
    {
      "record_id": "P001",
      "canonical_citation": "",
      "publication_url": "https://...",
      "publication_status": "published"
    }
  ],
  "seed_ids": ["seed-001"],
  "challenge_ids": [],
  "coverage_questions": [
    {
      "question_id": "CQ-001",
      "question": "",
      "perspective": "closest-method overlap",
      "decision_role": "novelty positioning",
      "priority": "high",
      "status": "answered",
      "critical_for_novelty": true,
      "search_run_ids": ["run-001"],
      "record_ids": ["P001"],
      "answer_summary": "",
      "residual_gap": "",
      "closure_reason": "",
      "blocked_mitigation": "",
      "scope_consequence": "",
      "protocol_boundary": "",
      "created_after_freeze": false,
      "amendment_id": null
    }
  ],
  "post_freeze_amendments": [],
  "search_strategy_review": {
    "performed": false,
    "independence": "self-review",
    "notes": "Reason performed or not performed"
  },
  "assurance_verdict": "insufficient"
}
```

Coverage-question statuses are `open`, `searching`, `answered`, `contradicted`, `saturated`, `blocked`, and `out-of-scope`. Closed evidential states require linked records and substantive closure text. `blocked` requires a residual gap, mitigation, and supported-scope consequence. `out-of-scope` requires the exact protocol boundary. Search rows and questions reference each other in both directions; corpus records and questions are reciprocal through record `question_ids` and question `record_ids`; post-freeze questions and amendments are also reciprocal.

Every record needs a unique `record_id`, canonical citation, canonical HTTP(S) publication URL, publication status, and reciprocal `question_ids`. Post-freeze amendments identify their kind (`record` or `coverage-question`), stable amendment ID, target ID, reason, and effect on conclusions.

Allowed verdicts:

- `insufficient`
- `adequate-for-bounded-claims`
- `adequate-for-comprehensive-claim`

An adequate verdict requires a freeze date, non-empty candidate corpus, included evidence, completed recall audit, substantive search-strategy-review notes, recovered visible seeds, and at least one coverage question for coverage-gated profiles. Bounded assurance cannot retain an open or searching high-priority novelty-critical question. A disclosed blocked question may remain only with mitigation and an explicit supported-scope consequence. Comprehensive assurance cannot retain an open, searching, or blocked high-priority novelty-critical question and additionally requires the comprehensive profile, performed backward and forward citation searching, and a performed search-strategy review. Rapid scans remain proportionate and are not promoted to systematic assurance by polished artifacts.

## Hard failures

Fail validation when a systematic profile:

- omits a substantive seed-recovery record;
- leaves a seed unrecovered while asserting an adequate verdict;
- omits or leaves unfinished a required citation-search decision;
- omits a completed stopping rationale;
- omits reciprocal coverage-question/search/record links or required closure evidence;
- adds a material post-freeze coverage question without a reciprocal amendment;
- lacks a corpus manifest or freeze date for an adequate verdict;
- asserts comprehensive coverage while required citation searches or search-strategy review remain incomplete;
- manually adds a major omitted publication without documenting the search failure and repair;
- has evidence-row counts inconsistent with PRISMA `studies_included`;
- omits canonical publication URLs for included works;
- treats PRISMA counts, file presence, canonical URLs, or validator success as evidence of actual recall.

A passing validator establishes recorded structural and process consistency only. It does not prove that all important publications were found or that screening and search review were materially independent.
