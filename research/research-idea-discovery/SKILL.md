---
name: research-idea-discovery
description: Generate, filter, rank, and hand off grounded research ideas from a broad research direction, problem area, literature landscape, Zotero corpus, paper limitation, or user notes. Use when asked to brainstorm publishable research ideas, find a direction, turn a broad area into candidate claims, choose what to work on, evaluate idea quality before novelty review, or create an ideation stage inside a coordinated research workflow. Prefer research-novelty-review when the user already has one concrete idea to pressure-test, research-experiment-plan when the claim is already frozen, and research-pipeline-planner when the main request is multi-stage project sequencing rather than ideation itself.
---

# Research Idea Discovery

## Quick Start

1. Clarify the ideation target, constraints, and desired contribution type.
2. Inspect existing literature notes, Zotero exports, review artifacts, paper limitations, and failed ideas before searching or brainstorming.
3. Build a compact landscape map: active subareas, closest work, open gaps, and negative constraints.
4. Generate a diverse idea bank, then filter before ranking. Do not present raw brainstorming as a recommendation.
5. Score ideas on clarity, novelty signal, feasibility, testability, and significance.
6. Select at most 1-3 ideas for downstream validation and write the handoff artifacts.
7. Route the selected idea to `research-novelty-review` before experiment planning unless novelty has already been pressure-tested.

## Modes

### Standalone mode

- Use when the user wants ideation for a topic, paper, problem area, or notes without a full suite pack.
- Create an `ideation/` directory only when the task is substantial enough to preserve artifacts; otherwise return a compact ranked list in chat.
- If web search is unavailable, use the provided corpus and clearly mark novelty signals as unverified.

### Orchestrated mode

- Prefer canonical directory `./ideation/`.
- Read upstream context from `research-brief.md`, `artifact-index.md`, `./zotero/`, `./literature-review/`, and existing `./ideation/` artifacts when present.
- Write all required outputs under `./ideation/` and update `artifact-index.md` when the runtime task includes file maintenance.
- Handoff selected ideas to `research-novelty-review`; hand off a frozen claim plus evaluation goal to `research-experiment-plan` only after novelty risk is acceptable.

## Input Contract

- Minimum: broad research direction, problem area, paper limitation, or project notes.
- Prefer: target venue/audience, domain, available data, compute budget, timeline, non-goals, prior failed ideas, known closest work, and desired contribution type.
- Use `research-zotero` or existing `./zotero/` artifacts when the user wants to seed ideas from a curated library.
- Use `research-systematic-literature-review` first when the landscape is too unfamiliar or evidence coverage is the blocking task.

## Output Contract

For tracked ideation, produce these files:

- `landscape-map.md`: compact map of the area, closest work, gaps, constraints, and search/source limits.
- `idea-bank.md`: all generated ideas, grouped by theme, including rejected but informative options.
- `idea-scores.json`: machine-readable scored idea records; use `references/idea-score-schema.md`.
- `selected-idea.md`: the recommended idea or shortlist with hypothesis, contribution, minimum validation, risks, and next step.
- `rejected-ideas.md`: eliminated ideas and the reason each was removed.
- `ideation-decision.json`: final decision and next-skill handoff; use `references/ideation-decision-schema.md`.

In orchestrated mode these live under `./ideation/`. Validate tracked artifacts with `scripts/validate_ideation_pack.py`.

## Hard Stops

- Stop if the topic is so vague that ideas would be generic slogans.
- Stop before recommending an idea if every candidate lacks a testable hypothesis.
- Stop before experiment planning if the selected idea has not had at least a quick novelty check.
- Do not invent prior art, data access, benchmark feasibility, or pilot results.
- Do not treat "apply X to Y" as a publishable idea unless the application exposes a surprising mechanism, diagnostic, dataset, or empirical finding.

## Workflow

### 1) Frame the ideation target

- Convert the prompt into a bounded ideation brief:
  - domain and subarea
  - problem or limitation
  - intended contribution type
  - available resources
  - time and compute constraints
  - non-goals and banned directions
- If the user provided a paper, summarize the paper's core contribution, limitations, and improvement surfaces before generating ideas.
- If the user provided project notes, extract failed attempts and avoid regenerating them.

### 2) Build the landscape map

- Inspect local artifacts first: `papers/`, `literature/`, `zotero/`, `literature-review/`, `paper-review/`, notes, and prior ideation outputs.
- Search or request search/corpus access when the task requires current prior-art awareness.
- Keep the map focused on ideation, not a full systematic review:
  - subareas and dominant approaches
  - closest work and common assumptions
  - explicit limitations and future-work claims
  - reusable datasets, benchmarks, and codebases
  - open questions with plausible validation paths
- Write `landscape-map.md` with enough citations or source notes that downstream novelty review can replay the reasoning.

### 3) Generate candidates deliberately

- Generate 8-15 candidates unless constraints require fewer.
- Use multiple lenses rather than one generic brainstorming pass:
  - limitation inversion: turn repeated limitations into concrete tests
  - assumption testing: identify an assumption nobody has isolated
  - transfer with mechanism: move a method across domains only if it tests a new mechanism
  - benchmark or dataset gap: propose an artifact when the field lacks a decisive measurement
  - negative-result value: prefer questions where either outcome teaches something
- Record every candidate in `idea-bank.md` with hypothesis, minimum validation, closest known work, and likely failure mode.

### 4) Filter before scoring

- Remove ideas that are already done, impossible under constraints, not testable, too incremental, or not interesting if they fail.
- Keep rejected ideas in `rejected-ideas.md`; this prevents repeated regeneration and gives future users a banlist.
- If fewer than three candidates survive, revise the scope or return to the landscape map instead of forcing weak ideas into the shortlist.

### 5) Score and rank

- Use `references/scoring-rubric.md`.
- Score each surviving idea from 1-5 on:
  - clarity
  - novelty signal
  - feasibility
  - testability
  - significance
- Record risk level, estimated effort, blocking questions, and decision status in `idea-scores.json`.
- Favor ideas with clear falsification paths over ideas that only sound ambitious.

### 6) Select and hand off

- Select at most 1-3 ideas.
- Write `selected-idea.md` so a downstream agent can work without reconstructing context:
  - title and one-sentence claim
  - hypothesis and mechanism
  - closest work and differentiation
  - minimum viable validation
  - expected positive and negative outcomes
  - risks, constraints, and unresolved questions
  - recommended next skill
- Write `ideation-decision.json` with one of:
  - `proceed_to_novelty_review`
  - `revise_scope`
  - `generate_more`
  - `stop`
- Default next skill is `research-novelty-review` for selected ideas. Use `research-experiment-plan` only when novelty has already been checked and the claim/evaluation goal are frozen.

## Collaboration

- Invoke `research-systematic-literature-review` when broad evidence coverage, citation integrity, or SOTA mapping is the blocker.
- Invoke `research-novelty-review` for the selected idea before treating novelty as established.
- Invoke `research-experiment-plan` after the selected idea has a frozen claim and validation target.
- Invoke `research-pipeline-planner` when ideation is one stage in a larger roadmap with shared artifacts.

## Resources

- `references/landscape-map-template.md`
- `references/idea-bank-template.md`
- `references/selected-idea-template.md`
- `references/rejected-ideas-template.md`
- `references/scoring-rubric.md`
- `references/idea-score-schema.md`
- `references/ideation-decision-schema.md`
- `scripts/init_ideation_pack.py`: create the tracked ideation file set.
- `scripts/validate_ideation_pack.py`: validate required headings plus `idea-scores.json` and `ideation-decision.json`.
