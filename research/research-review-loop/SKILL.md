---
name: research-review-loop
description: Run iterative adversarial review over research plans, experiment outputs, and drafts with claim ledgers, issue tracking, evidence checks, and explicit closure criteria. Use when asked to red-team a research artifact, run recurring review rounds, maintain review state across revisions, or pressure-test whether results and prose actually support a claim.
---

# Research Review Loop

## Quick start

1. Identify the target artifact, stakes, and intended audience.
2. Initialize review state with `scripts/init_review_loop.py` unless a review pack already exists.
3. Build a claim ledger before issuing conclusions.
4. Review for internal consistency, evidence quality, and external verifiability.
5. Update `REVIEW_STATE.json`, `AUTO_REVIEW.md`, and `NARRATIVE_REPORT.md` after each round.

## Workflow

### 1) Treat review as an iterative stateful process

- Carry unresolved, resolved, and accepted issues across rounds.
- Never collapse multiple review rounds into one untracked summary.
- Require each issue to have severity, status, evidence, and a concrete fix or follow-up.

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

## References

- `references/review-checklist.md`
- `references/report-template.md`
- `references/review-state-schema.md`
- `references/tabmol-ddi-ood-adapter.md`

## Script

- `scripts/init_review_loop.py`: create deterministic state and report scaffolds for repeated review rounds.
