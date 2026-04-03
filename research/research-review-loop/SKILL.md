---
name: research-review-loop
description: Run iterative adversarial review over research plans, experiment outputs, and drafts with claim ledgers, issue tracking, evidence checks, and explicit closure criteria. Use when asked to red-team a research artifact across multiple rounds, maintain issue state across revisions, or pressure-test whether revised results and prose actually support a claim. Prefer `research-paper-review` for an initial single-paper critique or OCR/extraction workflow, and prefer `research-rebuttal` when concrete external reviewer comments already exist and the task is to draft a venue response.
---

# Research Review Loop

## Quick start

1. Identify the target artifact, stakes, and intended audience.
2. Initialize review state with `scripts/init_review_loop.py` unless a review pack already exists.
3. Build a claim ledger before issuing conclusions.
4. Review for internal consistency, evidence quality, and external verifiability.
5. Update `REVIEW_STATE.json`, `AUTO_REVIEW.md`, and `NARRATIVE_REPORT.md` after each round.

## Relationship to sibling skills

- `research-paper-review` should usually run before this skill when the artifact is a paper that has not yet received a first-pass critique.
- `research-review-loop` owns tracked iterative review: issue carry-forward, resolution checks, accepted risks, and round discipline.
- `research-rebuttal` owns responses to external reviewer comments and venue-constrained discussion artifacts.
- `adversarial-doc-review` is broader and lighter-weight; use it for one-off document critique without a tracked research review state.

## Input contract

- Minimum:
  - one concrete artifact under review
- Prefer:
  - an existing review pack or tracked issue state
  - upstream `paper-review` artifacts such as `summary.md`, `final_issues.json`, and `overall_assessment.txt`
  - revision diffs or an explicit statement of what changed since the last round

## Output contract

- Primary tracked artifacts:
  - `REVIEW_STATE.json`
  - `AUTO_REVIEW.md`
  - `NARRATIVE_REPORT.md`
- If upstream `paper-review` artifacts exist, keep explicit references to their file paths in the round state rather than rewriting the whole first-pass critique from scratch.

## Workflow

### 1) Treat review as an iterative stateful process

- Carry unresolved, resolved, and accepted issues across rounds.
- Never collapse multiple review rounds into one untracked summary.
- Require each issue to have severity, status, evidence, and a concrete fix or follow-up.
- If `paper-review/final_issues.json` exists, initialize the first tracked issue set from that file instead of inventing a new initial ledger.

### 2) Build the claim ledger first

- Extract definitions, assumptions, factual claims, quantitative claims, causal claims, and speculative claims.
- Keep each claim traceable to a file location, section, figure, or table.
- Distinguish unsupported from false, and ambiguous from misleading.

### 3) Review in two passes

- Internal pass:
  - consistency
  - terminology
  - logic
  - methodology
  - claim-to-evidence alignment
- External pass:
  - time-sensitive facts
  - citations
  - benchmark claims
  - standards and rules
- If external verification is unavailable, mark items as unverified and say what evidence would resolve them.

### 4) Force closure discipline

- Do not mark a major issue resolved without new evidence, a revised artifact, or an explicit accepted risk.
- Treat “future work” as a resolution only when the claim has been narrowed accordingly.
- Prefer fewer high-signal issues over long undifferentiated lists.

### 5) Keep the report actionable

- Use `references/report-template.md` for each round.
- Separate major issues from minor issues and open questions.
- Include targeted rewrites when wording is the real problem.
- Record what changed since the prior round and why each formerly-open issue is now resolved, deferred, or still open.

## References

- `references/review-checklist.md`
- `references/report-template.md`
- `references/review-state-schema.md`
- `references/tabmol-ddi-ood-adapter.md`
- `../research-pipeline-planner/references/review-stage-contract.md`

## Script

- `scripts/init_review_loop.py`: create deterministic state and report scaffolds for repeated review rounds.
