---
name: research-rebuttal
description: Draft venue-aware academic rebuttals and author responses from reviewer comments, scores, and paper artifacts. Use when asked to analyze reviews, build a reviewer issue board, plan evidence or manuscript fixes, draft a rebuttal, respond to AC or meta-review feedback, manage multi-round author-reviewer discussion, or prepare a paste-ready response for conference or journal review systems.
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
- Group shared concerns across reviewers and mark severity aggressively:
  - Major-Blocking
  - Major-Addressable
  - Minor
  - Misunderstanding
- Classify reviewer stance as Champion, Persuadable, or Entrenched using `references/writing_principles.md`.
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

### 6) Run mandatory safety gates

- Provenance gate:
  - every number, experimental result, section reference, and manuscript change must trace to a real source
- Commitment gate:
  - do not claim a manuscript change or experiment unless it already exists or is explicitly labeled as planned
- Coverage gate:
  - every Major-Blocking and Major-Addressable issue must be closed, deferred with justification, or explicitly accepted as a risk
- Verify size limits with `scripts/count_limits.sh <file> [--chars|--words|--pages] [--limit N]`.

### 7) Handle follow-up rounds carefully

- Update the issue board rather than rewriting the whole response from scratch.
- Reply only to new or still-open points.
- Increase technical specificity, not argumentative intensity.
- If a disagreement persists after repeated rounds, summarize the positions cleanly and let the committee adjudicate.

## Scripts

- `scripts/init_rebuttal_pack.py`: create deterministic rebuttal scaffolds in a standalone directory or `./rebuttal/`.
- `scripts/count_limits.sh`: measure chars, words, or rough page equivalents after stripping common markup.

## References

- `references/issue_board_guide.md`
- `references/platforms_and_policies.md`
- `references/response_strategies.md`
- `references/venue_rule_matrix.md`
- `references/writing_principles.md`
