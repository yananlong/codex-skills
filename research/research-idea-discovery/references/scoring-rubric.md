# Ideation Scoring Rubric

Use 1-5 scores. A high total score is not enough; an idea with novelty signal below 3, testability below 3, missing source basis, or missing kill criteria should not proceed without revision.

## Clarity

- 1: Vague topic or slogan.
- 3: Concrete direction but hypothesis still needs sharpening.
- 5: One-sentence claim, mechanism, and validation target are explicit.

## Novelty Signal

- 1: Appears already done or indistinguishable from closest work.
- 3: Plausibly differentiated, but needs targeted novelty review.
- 5: Clear differentiator with known closest work and concrete novelty questions.

## Feasibility

- 1: Requires unavailable data, tools, or compute.
- 3: Feasible with notable engineering or data risk.
- 5: Feasible with known resources and bounded implementation.

## Testability

- 1: No decisive experiment or analysis.
- 3: Testable, but metrics or controls need refinement.
- 5: Has a cheap minimum viable validation with interpretable success and failure outcomes.

## Significance

- 1: Would not matter even if true.
- 3: Useful for a niche audience or as a supporting result.
- 5: Could change a method choice, benchmark interpretation, theory, dataset practice, or application workflow.

## Decision Heuristic

- Select: average score >= 4.0, novelty signal >= 3, testability >= 3, explicit source basis, explicit kill criteria, and no unresolved feasibility blocker.
- Shortlist: average score >= 3.4 with one resolvable blocker.
- Reject: average score < 3.4, novelty signal < 3, testability < 3, or any fatal feasibility/significance issue.
