# Review Stage Contract

Use this contract to keep `paper-review`, `review-loop`, and `rebuttal` interoperable.

## Canonical ownership

- `research-paper-review`: initial ingestion, OCR, first-pass critique, and viz output for a single paper
- `research-review-loop`: tracked iterative review across revisions
- `research-rebuttal`: venue-constrained response to external reviewer comments

If more than one of these appears applicable, route by the artifact that already exists:

- no review artifacts yet -> `research-paper-review`
- existing internal issue ledger or revision rounds -> `research-review-loop`
- concrete external reviewer comments and venue response task -> `research-rebuttal`

## Paper-review handoff bundle

In orchestrated mode, record the active review directory in `artifact-index.md`.

Required files:

- `<review_dir>/summary.md`
- `<review_dir>/final_issues.json`
- `<review_dir>/overall_assessment.txt`

Required support files:

- `<review_dir>/metadata.json`
- `<review_dir>/full_text.md`
- `<review_dir>/sections/index.json`

Optional but preferred:

- `<review_dir>/comments/all_comments.json`
- `./review_results/<slug>_skill.json`

## Review-loop consumption rules

- Initialize the first tracked issue set from `paper-review/final_issues.json` when available.
- Preserve source paths back to the original paper-review artifacts.
- Do not silently rewrite issue titles or severities unless new evidence justifies the change.
- Record what changed between rounds and whether each inherited issue is now resolved, still open, or accepted as a risk.

## Rebuttal consumption rules

- External reviewer comments are primary. Paper-review artifacts are supporting internal evidence, not substitutes for reviewer text.
- Use `summary.md` and `final_issues.json` to cross-check reviewer concerns, locate evidence quickly, and detect contradictions.
- If `review-loop/REVIEW_STATE.json` exists, use it to avoid re-opening already-resolved internal issues without cause.
- Keep a clear distinction between:
  - internal diagnosis
  - reviewer complaint
  - response strategy
  - evidence source

## Provenance rule

Any downstream skill consuming upstream review artifacts must preserve the exact file paths in its own state or working notes. Do not rely on memory when a concrete artifact already exists.
