---
name: research-novelty-review
description: Run a stringent, adversarial novelty review over a concrete research idea, method, protocol, artifact, or claimed finding. Use when asked to assess novelty, position a paper or project, build a prior-art matrix, decide whether something is incremental, or pressure-test whether the right move is to proceed, reframe, or abandon. Prefer `research-paper-review` for first-pass technical critique of a single paper artifact and `research-rebuttal` when the task is to answer concrete reviewer comments rather than establish novelty positioning from scratch.
---

# Research Novelty Review

## Quick start

1. Start skeptical: treat the contribution as incremental until the evidence says otherwise.
2. Decompose the claim into searchable units before looking at any literature.
3. Search strongest overlaps first, not flattering long-tail analogies.
4. Write down novelty-killing objections explicitly before giving any green light.
5. End with a 1-5 novelty decision rating, not a coarse ternary label, plus the narrowest defensible positioning.

## Modes

### Standalone mode

- Work from the user prompt plus any local notes, citations, or existing review artifacts.
- Do not require a suite root.
- Remain collaboration-friendly: if literature review or review-loop artifacts already exist, consume them; if broader retrieval or a second adversarial pass would materially help, recommend or invoke that workflow rather than staying artificially isolated.

### Orchestrated mode

- Prefer the canonical directory `./novelty-review/`.
- Read upstream context from `research-brief.md`, `artifact-index.md`, `./literature-review/`, and `./zotero/` when present.
- Keep outputs legible to downstream experiment planning and paper planning.

## Input contract

- Minimum: a concrete method, protocol, artifact, finding, or contribution claim.
- Prefer:
  - target venue or community
  - closest known prior work
  - scope of novelty under consideration
  - existing literature or review artifacts
  - existing Zotero library artifacts

## Hard stops

- Stop if the proposed contribution is too vague to search.
- Stop if browsing or a usable corpus is unavailable.
- Stop if the claim bundles so many moving parts that a fair novelty comparison is impossible.
- In standalone mode, do not force suite initialization when a direct adversarial review will do.

## Output contract

- Primary files:
  - `novelty-report.md`
  - `prior-art-matrix.md`
  - `search-log.md`
  - `novelty-decision.json`
- In orchestrated mode, these live under `./novelty-review/`.
- In standalone mode, any target directory is valid.
- `novelty-decision.json` should capture the final 1-5 novelty rating, confidence rating, and the exact narrow positioning that survives the review.

## Workflow

### 1) Decompose the claim before searching

- Write the contribution in one sentence.
- Split novelty into:
  - framing
  - method
  - evaluation protocol
  - artifact or dataset
  - empirical finding
- Reject blended claims that hide which part is allegedly new.

### 2) Search with a kill-shot mindset

- Use `references/adversarial-query-patterns.md` and `references/search-log-template.md`.
- If the user maintains a relevant Zotero library or collection, invoke `research-zotero` first or consume `./zotero/zotero-items.json` as a curated seed corpus.
- Search the strongest plausible overlaps first.
- Prioritize recent literature and venue-appropriate sources before padding with weaker analogies.
- Log exact queries, filters, and what each search was trying to falsify.

### 3) Build the prior-art matrix

- Use `references/prior-art-matrix-template.md`.
- Record closest overlaps, not just vaguely related work.
- Score how much each prior work threatens the novelty claim on a 1-5 scale.
- Prefer concrete overlap dimensions over narrative hand-waving.

### 4) Write the objections first

- Use `references/reviewer-objection-rubric.md` and `references/overlap-scoring-rubric.md`.
- State the strongest objections a skeptical reviewer would raise.
- Flag renaming, recombination, routine scaling, and standard-bundle effects aggressively.
- If the novelty is weak but the usefulness is real, say so clearly.
- Keep the ratings explicit:
  - overlap threat rating: 1-5
  - surviving novelty strength: 1-5
  - confidence in the decision: 1-5

### 5) Decide and position narrowly

- Use `references/decision-scale.md`.
- End with:
  - `novelty_decision_rating` on a 1-5 scale
  - `decision_confidence_rating` on a 1-5 scale
- Offer the narrowest defensible positioning that survives the objections.
- Use this interpretation:
  - `1`: abandon; the core claim is effectively killed by overlap
  - `2`: major reframe required before proceeding
  - `3`: narrow proceed only; some novelty survives but only under a sharply reduced claim
  - `4`: proceed with careful positioning; novelty looks real but vulnerable
  - `5`: strong novelty position; closest overlaps do not materially undercut the core claim
- If deeper retrieval would materially improve confidence, collaborate with `research-systematic-literature-review`.
- If a second adversarial pass would help and delegation is explicitly available and permitted, an independent review pass is allowed. Do not assume that permission.

## References

- `references/novelty-checklist.md`
- `references/prior-art-matrix-template.md`
- `references/search-log-template.md`
- `references/adversarial-query-patterns.md`
- `references/decision-scale.md`
- `references/overlap-scoring-rubric.md`
- `references/reviewer-objection-rubric.md`
- `references/tabmol-ddi-ood-adapter.md`

## Script

- `scripts/init_novelty_pack.py`: create `novelty-report.md`, `prior-art-matrix.md`, `search-log.md`, and `novelty-decision.json` in a standalone directory or the suite's `novelty-review/` directory.
