# Review Stage Contract

Use this contract to keep `paper-review`, literature context, novelty review, review-loop, and rebuttal interoperable.

## Canonical ownership

- `research-paper-review`: initial ingestion, OCR, first-pass critique, and viz output for a single paper
- `research-systematic-literature-review`: independent external literature review and evidence mapping for related-work, benchmark, impact, and SOTA claims; full PRISMA review only when explicitly needed
- `research-novelty-review`: adversarial prior-art and contribution-positioning assessment
- `research-review-loop`: tracked iterative review across revisions
- `research-rebuttal`: venue-constrained response to external reviewer comments

If more than one of these appears applicable, route by the artifact that already exists:

- no review artifacts yet -> `research-paper-review`
- paper-review summary exists and external novelty/context is needed -> `research-systematic-literature-review` paper-context mode in `<review_dir>/context/`, then `research-novelty-review`
- existing internal issue ledger or revision rounds -> `research-review-loop`
- concrete external reviewer comments and venue response task -> `research-rebuttal`

## Paper-review handoff bundle

In orchestrated mode, record the active review directory in `artifact-index.md`.

Required files:

- `<review_dir>/summary.md`
- `<review_dir>/final_issues.json`
- `<review_dir>/review_summary.json`
- `<review_dir>/overall_assessment.txt`

Required support files:

- `<review_dir>/metadata.json`
- `<review_dir>/full_text.md`
- `<review_dir>/sections/index.json`

Optional but preferred:

- `<review_dir>/context/context-plan.md`
- `<review_dir>/context/literature-context.md`
- `<review_dir>/context/literature-context-search-log.md`
- `<review_dir>/context/literature-context-evidence-table.md`
- `<review_dir>/context/literature-context-decision.json`
- `<review_dir>/context/novelty-context.md`
- `<review_dir>/comments/all_comments.json`
- `./review_results/<slug>_skill.json`

## Literature-context handoff

Use this when `research-paper-review` needs external grounding for novelty, impact, benchmark, related-work, SOTA, or significance claims.

The SLR skill remains independently runnable. If it runs without a paper-review workspace, keep its artifact directory intact and record that path for later consumption. If a paper-review workspace exists, use `<review_dir>/context/` as the exchange directory.

Preferred inputs:

- `<review_dir>/summary.md`
- `<review_dir>/context/context-plan.md`
- cited closest prior work from the target paper
- domain and target community

Preferred outputs:

- `<review_dir>/context/literature-context.md`
- `<review_dir>/context/literature-context-search-log.md`
- `<review_dir>/context/literature-context-evidence-table.md`
- `<review_dir>/context/literature-context-decision.json`

Minimum decision fields:

- `contextualization_rating`
- `impact_evidence_rating`
- `coverage_confidence_rating`
- `closest_prior_work`
- `related_work_omissions`
- `benchmark_context_gaps`
- `limits_of_search`

Paper-review maps `impact_evidence_rating` to `review_summary.json.impact_context_rating`, preserves `contextualization_rating` and `coverage_confidence_rating`, and converts omissions/gaps into raw review comments only when they affect the target paper.

Do not label a bounded paper-context evidence map as a full systematic review unless the PRISMA workflow was completed.

## Novelty-context handoff

Use this after a paper summary exists, preferably after the literature-context handoff.

Preferred inputs:

- `<review_dir>/summary.md`
- `<review_dir>/context/literature-context.md`
- `literature-context-decision.json`
- `prior-art` or Zotero artifacts when present

Preferred outputs:

- `novelty-report.md`
- `prior-art-matrix.md`
- `search-log.md`
- `novelty-decision.json`
- optional `<review_dir>/context/novelty-context.md` summary

Minimum decision fields:

- `novelty_decision_rating`
- `impact_positioning_rating`
- `decision_confidence_rating`
- `narrowest_defensible_positioning`
- `claims_to_qualify`
- `missing_prior_work`
- `review_findings_to_add`

Paper-review should convert `review_findings_to_add` into raw comment JSON before consolidation.

## Review-loop consumption rules

- Initialize the first tracked issue set from `paper-review/final_issues.json` when available.
- Use `paper-review/review_summary.json` as the numeric first-pass summary for round initialization and routing.
- Preserve source paths back to the original paper-review artifacts.
- Do not silently rewrite issue titles or impact/confidence ratings unless new evidence justifies the change.
- Record what changed between rounds and whether each inherited issue is now resolved, still open, or accepted as a risk.

## Rebuttal consumption rules

- External reviewer comments are primary. Paper-review artifacts are supporting internal evidence, not substitutes for reviewer text.
- Use `summary.md`, `final_issues.json`, and `review_summary.json` to cross-check reviewer concerns, locate evidence quickly, and detect contradictions.
- If `review-loop/REVIEW_STATE.json` exists, use it to avoid re-opening already-resolved internal issues without cause.
- Keep a clear distinction between:
  - internal diagnosis
  - reviewer complaint
  - response strategy
  - evidence source

## Provenance rule

Any downstream skill consuming upstream review artifacts must preserve the exact file paths in its own state or working notes. Do not rely on memory when a concrete artifact already exists.
