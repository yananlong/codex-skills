# Paper Review Integration

Use this reference when `research-novelty-review` is invoked from `research-paper-review`.

## Inputs

Prefer these artifacts:

- `<review_dir>/summary.md`
- `<review_dir>/full_text.md` only for locating exact paper claims
- `<review_dir>/context/literature-context.md`
- `<review_dir>/context/literature-context-search-log.md`
- `<review_dir>/context/literature-context-evidence-table.md`
- `<review_dir>/context/literature-context-decision.json`
- `./literature-review/` seven-file pack only when linked literature assurance is used
- `./zotero/` artifacts when available

## Decision Separation

Keep these judgments separate:

- `novelty_decision_rating`: whether the contribution is new relative to closest prior work
- `impact_positioning_rating`: whether the paper's significance/importance framing is supported by literature context
- `decision_confidence_rating`: how stable the decision is under search coverage

A paper can score low on novelty and high on impact, or high on novelty and low on demonstrated significance.

## Handoff To Paper Review

Create paper-review-ready findings for each decision-relevant issue.

| Field | Requirement |
| --- | --- |
| title | concise issue title |
| quote | exact target-paper quote when available, otherwise section/table location |
| explanation | connect the paper claim to the closest prior-art evidence |
| comment_type | `claim_accuracy`, `missing_information`, `presentation`, or `methodology` |
| impact_rating | 1-5 |
| confidence_rating | 1-5 |
| source_section | target-paper location |
| related_sections | prior-art or literature-context artifacts used |

## Common Finding Patterns

- Overstated novelty: `claim_accuracy`
- Missing closest prior work: `missing_information`
- Routine recombination framed as a new method: `claim_accuracy`
- Useful but not novel contribution: usually `presentation`, unless the central claim depends on novelty
- Impact claim unsupported by adoption, benchmark, or task context: `claim_accuracy`
- Evaluation protocol not aligned with field norms: `methodology`

## Minimum Integrated Output

When returning to `research-paper-review`, provide:

- final novelty rating
- final impact-positioning rating
- confidence rating
- narrowest defensible positioning
- strongest supportable positioning
- top 3 closest overlaps
- specific claims to qualify
- paper-review-ready findings to add before consolidation

Write `<review_dir>/context/novelty-context.md` as a projection of `novelty-report.md`. The novelty validator reads `novelty-report.md`, so keep the two in sync.
