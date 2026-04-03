---
name: research-rebuttal
description: Draft venue-aware academic rebuttals and author responses from reviewer comments, scores, and paper artifacts. Use when concrete reviewer comments already exist and Codex needs to analyze reviews, build a reviewer issue board, plan evidence or manuscript fixes, draft a rebuttal, respond to AC or meta-review feedback, manage multi-round author-reviewer discussion, or prepare a paste-ready response for conference or journal review systems. Prefer `research-paper-review` for initial manuscript diagnosis before reviews arrive, `research-review-loop` for internal tracked review without external reviewer comments, and `research-novelty-review` for prior-art positioning disputes.
---

# Research Rebuttal

## Quick start

1. Decide whether this stays standalone or becomes `./rebuttal/` inside an orchestrated research suite.
2. Route the venue first with `references/venue_rule_matrix.md`; if dates, limits, or policy details are decision-critical, re-check the official venue source before finalizing.
3. Initialize the rebuttal pack with `scripts/init_rebuttal_pack.py` unless usable artifacts already exist.
4. Build the review analysis and issue board before drafting prose.
5. Convert major issues into concrete evidence or manuscript tasks, then draft the correct artifact shape and verify limits with `scripts/count_limits.sh`.

## Modes

### Standalone mode

- Work from pasted reviews, PDFs, screenshots, or local notes.
- Do not require a suite root.
- Remain collaboration-friendly: if `research-paper-plan`, `research-review-loop`, experiment outputs, or manuscript diffs already exist, use them.

### Orchestrated mode

- Prefer the canonical directory `./rebuttal/`.
- Read upstream context from `research-brief.md`, `artifact-index.md`, `./paper-plan/`, `./review-loop/`, and relevant result artifacts when present.
- Keep outputs legible to later manuscript revision, camera-ready planning, or follow-up review rounds.

## Relationship to sibling skills

- `research-paper-review` should usually happen before rebuttal if the paper still needs a first-pass technical diagnosis.
- `research-review-loop` should track internal revision rounds and issue closure between rebuttal iterations.
- `research-rebuttal` starts when there are concrete reviewer comments and a venue-specific response artifact to produce.
- `research-novelty-review` is a helper when the central dispute is novelty or prior-art overlap rather than general reviewer response.

## Handling review inputs

- Pasted text: use directly, but check whether the paste is complete.
- PDF review bundles: extract all review text, scores, and confidence values before analysis.
- Screenshots: transcribe visible review content and flag truncation or unreadable regions.
- OpenReview or CMT links: treat raw platform access as unreliable; ask for pasted review text if needed.
- Paper PDF or source: read as needed to cross-reference challenged claims, tables, or sections.
- If review metadata is incomplete, proceed conservatively and label the missing fields rather than inventing them.

## Input contract

- Minimum:
  - concrete reviewer feedback or review text
  - target venue or best-known venue family
- Prefer:
  - scores and confidence values
  - paper PDF, source, or exact section references
  - existing experimental logs, tables, or manuscript diffs
  - deadline and artifact constraints

## Hard stops

- Stop if there is no concrete review text or reviewer feedback artifact.
- Stop if the venue materially changes the artifact but cannot be inferred well enough to pick a conservative route.
- Stop if the draft would require invented evidence, fabricated experiments, or unverified manuscript changes.
- In standalone mode, do not force a scaffold pack when a compact direct response is enough.

## Output contract

- Primary files:
  - `review-analysis.md`
  - `issue-board.md`
  - `task-list.md`
  - `rebuttal-working.md`
  - `rebuttal-paste-ready.md`
- Optional file:
  - `ac-note.md`
- In orchestrated mode, these live under `./rebuttal/`.
- The working draft may contain `[INTERNAL]` notes; the paste-ready draft must not.

## Workflow

### 1) Route venue and policy constraints first

- Use `references/venue_rule_matrix.md` to choose the artifact structure:
  - one-shot PDF
  - per-review response
  - threaded discussion
  - rolling revision response
  - single-feedback response
- Use `references/platforms_and_policies.md` for platform mechanics, anonymity, disclosure, link, revision, and LLM-policy checks.
- If venue information is incomplete, state the assumption and choose the most conservative valid route.
- Treat dated limits, windows, and policy details as unstable. Re-check official venue sources before final submission when those details matter.

### 2) Analyze reviews and build the issue board

- Summarize each reviewer's decision logic, score, confidence, and likely AC-facing concern in `review-analysis.md`.
- Build `issue-board.md` using `references/issue_board_guide.md`.
- Extract a score matrix first. As a default heuristic, treat reviewers as:
  - Champion: strong accept signal or clearly positive language
  - Persuadable: mixed review or borderline score
  - Entrenched: strongly negative decision logic unlikely to flip
- Spend most rebuttal budget on Persuadable reviewers and committee-facing concerns, while maintaining Champion support.
- Group shared concerns across reviewers and mark severity aggressively:
  - Major-Blocking
  - Major-Addressable
  - Minor
  - Misunderstanding
- Classify reviewer stance as Champion, Persuadable, or Entrenched using `references/writing_principles.md`.
- Use an explicit issue-board shape rather than free-form notes. For example:

```text
issue_id | reviewer | severity          | category   | strategy | status | shared_with
R1-1     | R1       | Major-Blocking    | baselines  | TBD      | open   |
R2-1     | R2       | Misunderstanding  | novelty    | TBD      | open   |
R3-1     | R3       | Major-Addressable | ablations  | TBD      | open   | R1-1
```

- If the user asked only for triage or analysis, stop after the analysis and issue board.

### 3) Choose response strategies per issue

- Use `references/response_strategies.md`.
- Prefer one or more of:
  - Accept and fix
  - Clarify misunderstanding
  - Partial agree and narrow claim
  - Respectful disagreement
  - Out of scope
  - Escalate to AC
- Strategy choice must depend on factual correctness, acceptance impact, and venue policy constraints, not rhetorical preference.
- Compound strategies are often correct:
  - clarify misunderstanding + accept a presentation fix
  - accept and fix + provide new evidence
  - partial agree + narrow the claim
- Do not promise evidence you do not have. Missing evidence becomes a task, not a rhetorical flourish.

### 4) Convert strategy into an execution plan

- Fill `task-list.md` with owner if known, required input, evidence source, whether the task blocks drafting, and whether it changes the manuscript, rebuttal, or both.
- Prefer real evidence over promises. If evidence is missing, turn the gap into an explicit task rather than bluffing.
- Pull in upstream research artifacts when available:
  - `research-paper-plan` for claim and section mappings
  - `research-review-loop` for tracked issues across rounds
  - experiment or results artifacts for numbers and provenance

### 5) Draft the correct artifact

- Draft `rebuttal-working.md` first, then strip it down into `rebuttal-paste-ready.md`.
- Match the venue family:
  - one-shot PDF venues: merge repeated concerns and lead with the few issues most likely to affect the decision
  - per-review venues: keep replies self-contained
  - threaded venues: optimize for concise follow-ups and delta replies
  - rolling venues: emphasize revision plan over argument
- Use direct answer -> evidence -> implication structure.
- Keep every response self-contained enough that the reviewer or AC can scan it without hunting through the manuscript.
- For venues with strict character budgets, allocate rough space before writing:
  - opener or global summary: 10-15%
  - per-reviewer core responses: 75-80%
  - closing or summary of changes: 5-10%
- Use the working draft as the evidence-rich version and the paste-ready draft as the platform-safe compressed artifact.
- Example of a good response shape:

```text
[R2] Missing comparison to MethodX
Direct answer: We agree this comparison is decision-relevant and have now run it.
Evidence: Table 2 below shows +2.1 points over MethodX on Dataset A.
Implication: This resolves the concern that our gains came only from benchmark selection.
```

- Avoid defensive responses such as:
  - "the reviewer failed to notice"
  - "it is obvious"
  - "we will fix this in the camera-ready" without evidence or a venue-legal commitment

### 6) Run mandatory safety gates

- Provenance gate:
  - every number, experimental result, section reference, and manuscript change must trace to a real source
- Commitment gate:
  - do not claim a manuscript change or experiment unless it already exists or is explicitly labeled as planned
- Coverage gate:
  - every Major-Blocking and Major-Addressable issue must be closed, deferred with justification, or explicitly accepted as a risk
- Verify size limits with `scripts/count_limits.sh <file> [--chars|--words|--pages] [--limit N]`.
- If `paper-review/final_issues.json` or `review-loop/REVIEW_STATE.json` exists, cross-check that the rebuttal does not quietly contradict the internal diagnosis.

### 7) Handle follow-up rounds carefully

- Update the issue board rather than rewriting the whole response from scratch.
- Reply only to new or still-open points.
- Increase technical specificity, not argumentative intensity.
- If a disagreement persists after repeated rounds, summarize the positions cleanly and let the committee adjudicate.
- In multi-round venues, treat the issue board as the source of truth and write delta replies only.

## Scripts

- `scripts/init_rebuttal_pack.py`: create deterministic rebuttal scaffolds in a standalone directory or `./rebuttal/`.
- `scripts/count_limits.sh`: measure chars, words, or rough page equivalents after stripping common markup.

## References

- `references/issue_board_guide.md`
- `references/platforms_and_policies.md`
- `references/response_strategies.md`
- `references/venue_rule_matrix.md`
- `references/writing_principles.md`
- `../research-pipeline-planner/references/review-stage-contract.md`
