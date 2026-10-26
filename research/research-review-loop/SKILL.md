---
name: research-review-loop
description: Run iterative adversarial review over research plans, experiment outputs, and drafts with claim ledgers, issue tracking, evidence checks, and explicit closure criteria. Use when asked to red-team a research artifact across multiple rounds, maintain issue state across revisions, or pressure-test whether revised results and prose actually support a claim. Prefer `research-paper-review` for an initial single-paper critique or OCR/extraction workflow, and prefer `research-rebuttal` when concrete external reviewer comments already exist and the task is to draft a venue response.
---

# Research Review Loop

## Quick start

1. Identify the target artifact, stakes, intended audience, and requested evidence class.
2. Initialize review state with `scripts/init_review_loop.py` unless a review pack already exists. Use `--from-paper-review <review_dir, final_issues.json, or project root>` when a first-pass paper-review bundle is available; without a target folder it writes `round-1/` (or the next free round) inside the bundle's workspace. To start the next round of an existing loop, use `--from-state <round-N/REVIEW_STATE.json>`; it writes the next integer `round-<N+1>/` in the same review home. `scripts/resolve_review_artifacts.py --root .` shows where the latest round is when you do not know.
3. Build a claim ledger and a predecessor-failure ledger before issuing conclusions.
4. Review for internal consistency, evidence quality, external verifiability, provenance, non-vacuity, complete outcome accounting, and real rather than nominal independence.
5. Preserve previous rounds and append or version new outputs instead of overwriting prior review artifacts.
6. Update the latest `REVIEW_STATE.json`, `AUTO_REVIEW.md`, and `NARRATIVE_REPORT.md` after each round only after preserving prior versions.
7. If a `research-paper-review` bundle exists, import its issue IDs, quotes, ratings, and summary path rather than re-summarizing or downgrading the first-pass critique.
8. Infer the provenance of existing review artifacts before reorganizing them: upstream Claude/OpenAIReview bundles, Codex-native paper-review bundles, and review-loop hybrids are all valid inputs.
9. If the user asks for project-level sequencing, current-state inspection, or coordination across multiple research stages, invoke `research-pipeline-planner` first instead of treating the review loop as the whole task.
10. Use `../research-pipeline-planner/references/epistemic-assurance-contract.md` whenever a round is expected to authorize evidence promotion or route advancement.

## Relationship to sibling skills

- `research-paper-review` should usually run before this skill when the artifact is a paper that has not yet received a first-pass critique.
- `research-review-loop` owns tracked iterative review: issue carry-forward, resolution checks, accepted risks, and round discipline.
- `research-results-auditor` owns detailed validity checks over concrete result artifacts; invoke it when a route decision turns on experiment outputs.
- `research-rebuttal` owns responses to external reviewer comments and venue-constrained discussion artifacts.
- `adversarial-doc-review` is broader and lighter-weight; use it for one-off document critique without a tracked research review state.

Ownership when skills chain: only the skill the user invoked spawns workers, and it sets one budget for the whole chain (quick: no workers; standard: up to 3; deep: 5 to 8). A skill reached by handoff never spawns. When the user invokes this skill, it owns the budget for the round: a first-pass `research-paper-review` it starts runs serially inside that budget, the three review passes below may each take a worker, and revision handed to `technical-writing-reviser` (prose per issue cluster) and the final `prose-flow-improver` pass count against the same budget. When the planner or another skill started this round, run every pass serially. Record the depth and the workers used in the round report.

## Input contract

- Minimum:
  - one concrete artifact under review
- Prefer:
  - an existing review pack or tracked issue state
  - upstream Claude/OpenAIReview or Codex-adapted paper-review artifacts such as `summary.md`, `final_issues.json`, `review_summary.json`, `overall_assessment.txt`, `metadata.json`, `comments/`, `context/`, and `sections/`
  - revision diffs or an explicit statement of what changed since the last round
  - experiment plans, result artifacts, decision logs, failure reviews, and provenance records
  - current and requested evidence class plus the claimed independence arrangement

## Output contract

- For future research-review-loop runs: preserve previous rounds and append/version new outputs instead of overwriting prior review artifacts.
- Preserve prior rounds. Before writing a new round, copy, archive, or write into a round-specific directory so earlier `REVIEW_STATE.json`, `AUTO_REVIEW.md`, and `NARRATIVE_REPORT.md` artifacts remain available.
- Primary tracked artifacts:
  - `REVIEW_STATE.json`
  - `AUTO_REVIEW.md`
  - `NARRATIVE_REPORT.md`
- If upstream `paper-review` artifacts exist, keep explicit references to their file paths in the round state rather than rewriting the whole first-pass critique from scratch.
- Preserve `impact_rating`, `confidence_rating`, `severity`, `quote`, `source_section`, and `related_sections` from the first-pass bundle's `final_issues.json` when importing first-pass paper-review issues. Map `impact_rating >= 4` to major-tracked issues, `impact_rating == 3` to moderate tracked issues, and `impact_rating <= 2` to minor tracked issues; if only upstream `severity` is present, preserve it as the tracked severity and leave numeric ratings null.
- If the first-pass bundle lacks a root `review_summary.json` but has `metadata.json.round_summaries` or `round-N/review_summary.json`, use the latest round summary as the numeric/currentness summary and record the exact path in `source_artifacts`.
- For any round that authorizes advancement, record the bounded verdict, current evidence class, requested evidence class, actual independence dimensions, unresolved predecessor failures, and the exact evidence supporting each closure.

## Hard stops

- Do not authorize confirmatory or high-stakes advancement solely because all required files exist, validators pass, or the artifacts agree internally.
- Do not mark a material assurance issue resolved by renaming a role, adding a field, changing a flag, replacing an artifact, or reclassifying the route without new evidence.
- Do not call a review independent when the same effective process controls context, hidden data, implementation, evaluation, and advancement authority.
- If a prior round identified hidden-truth leakage, vacuous comparisons, incomplete loss accounting, omitted failures, or self-attested controls, carry the issue forward until evidence resolves it or the claim is explicitly narrowed.
- Continue useful exploratory review when stronger assurance is unavailable, but do not silently promote the evidence class.

## Workflow

### 1) Treat review as an iterative stateful process

- Carry unresolved, resolved, and accepted issues across rounds.
- Never collapse multiple review rounds into one untracked summary.
- Never overwrite earlier round artifacts without first preserving them in a versioned or timestamped location.
- Require each issue to have severity or impact rating, confidence, status, evidence, and a concrete fix or follow-up.
- If `resolve_review_artifacts.py` finds a first-pass bundle, initialize the first tracked issue set from its `final_issues.json` instead of inventing a new initial ledger. Keep the paper-review issue title, quote, explanation, source section, and ratings traceable in the state.
- Write the next round where `resolve_review_artifacts.py --next-round` says: an integer `round-<N>/` folder in the review's home, which for a review started now is `review_results/<slug>_review/`. Existing reviews keep their home, including dated or labelled round folders, and continue there with integer folders; never move or flatten earlier rounds or root paper-review files. `init_review_loop.py --from-state` carries open, resolved, and accepted-risk entries unchanged, keeps their IDs, and sets `round` to prior + 1 (override with `--round N`).
- Record which agent, model, prompt/context, code path, data access, and authority produced each stage-critical artifact when that provenance is available.

### 2) Build the claim and failure ledgers first

- Extract definitions, assumptions, factual claims, quantitative claims, causal claims, speculative claims, control claims, and route-authorization claims.
- Keep each claim traceable to a file location, section, figure, table, result artifact, or decision log.
- Distinguish unsupported from false, and ambiguous from misleading.
- For every material predecessor failure, record:
  - original failure and evidence
  - affected claim or route
  - current status
  - new evidence, accepted-risk rationale, or improper reclassification
- Reclassification, replacement, or omission is not resolution.

### 3) Review in three passes

- Internal pass:
  - consistency
  - terminology
  - logic
  - methodology
  - claim-to-evidence alignment
- Assurance pass:
  - evidence class and selection history
  - complete decision or loss contract
  - non-vacuity and discriminating cases
  - hidden-information controls
  - successes, errors, omissions, skips, nulls, retries, timeouts, and initial failures
  - property-versus-label checks for locks, isolation, replay, role independence, and validators
  - actual independence across context, data, implementation, evaluation, and advancement authority
- External pass:
  - time-sensitive facts
  - citations
  - benchmark claims
  - standards and rules
- If external verification is unavailable, mark items as unverified and say what evidence would resolve them.

### 4) Force closure discipline

- Do not mark a major issue resolved without new evidence, a revised artifact, or an explicit accepted risk.
- Treat “future work” as a resolution only when the claim has been narrowed accordingly.
- Do not resolve an imported paper-review issue by paraphrase alone; cite the revision diff, new analysis, narrowed claim, or accepted-risk rationale that changes its status.
- Do not resolve an assurance issue because a self-attested field now says the desired property holds; inspect the mechanism and evidence.
- An accepted risk must identify the unresolved failure, justify acceptance, narrow the affected claim or route, and remain visible in later rounds.
- Prefer fewer high-signal issues over long undifferentiated lists.

### 5) Authorize advancement conservatively

- Separate structural validity, internal consistency, exploratory usefulness, confirmatory support, and independent verification.
- Require `research-results-auditor` when advancement depends on concrete experimental outputs that have not received a validity audit.
- State the strongest remaining objection before the route decision.
- Use `proceed`, `revise`, `narrow evidence class`, or `stop`; never use an unqualified “passed” when the bounded meaning matters.
- If the runtime cannot provide material independence, record self-review and limit the verdict accordingly.

### 6) Keep the report actionable

- Use `references/report-template.md` for each round.
- Separate major issues from minor issues and open questions.
- When wording is the real problem, hand the affected passage to `technical-writing-reviser` (with the issue's `route_effect` as critique intake) rather than rewriting it inside the review; a rewrite this skill makes itself follows the drafting contract (`writing/technical-writing-drafter/references/drafting-contract.md`) and records the `prose_tells.py` line.
- Record what changed since the prior round and why each formerly-open issue is now resolved, deferred, accepted, narrowed, or still open.
- List the minimum evidence needed to reach the next stronger evidence class.

## Stage gate

This skill owns its stage gate. Standalone, it is the proceed, revise, or stop test for the request. In an orchestrated project the planner applies it, together with the paper-identity and evidence-promotion gates in `research-pipeline-planner/SKILL.md`, before work enters or leaves this stage.

- Proceed when the artifact is important enough to benefit from iterative review.
- Revise when the artifact is too incomplete to support adversarial feedback.
- Stop when there is no concrete artifact to review.
- Carry material predecessor failures forward until new evidence resolves them; reclassification or omission does not close an issue.
- Every round must classify identity drift as D0-D4. D3-D4 findings become pivot requests rather than ordinary issue closure.

## References

- `references/review-checklist.md`
- `references/report-template.md`
- `references/review-state-schema.md`
- `references/domain-adapters.md`: optional checks for LLM evaluation, Bayesian measurement, recomputation audits, theory, conceptual work, and the TabMol DDI/OOD agenda, with the rule for choosing one
- `../research-pipeline-planner/references/review-stage-contract.md`
- `../research-pipeline-planner/references/epistemic-assurance-contract.md`

## Scripts

- `scripts/validate_review_state.py`: check a `REVIEW_STATE.json` against the canonical issue schema. The default mode reads every known layout and reports legacy names as warnings; `--strict` requires the canonical schema, which every state `init_review_loop.py` writes passes.
- `scripts/resolve_review_artifacts.py` and `scripts/review_schema.py`: shared copies from `research-paper-review` (see its `references/review-schema.md`).
- `scripts/init_review_loop.py`: create deterministic state and report scaffolds for repeated review rounds. `--from-paper-review` seeds open issues from `research-paper-review` output in any known layout (read through `review_schema.py`, so every alias in the conversion table is accepted and unmapped fields are kept under `extra`), keeping incoming issue `id`s (it mints `PR<n>` only when absent); it exits non-zero and lists issue IDs when title, quote, evidence, or severity (or a 1-5 impact) resolves empty. `--from-state <REVIEW_STATE.json>` continues a loop into the next integer round folder of the same review home; `--round N` sets the round explicitly.