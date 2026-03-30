---
name: research-pipeline-planner
description: Coordinate research as either a standalone staged planning pass or an orchestrated multi-skill workflow with shared artifacts, stage gates, and optional collaboration with literature review, novelty review, experiment planning, result auditing, review, paper planning, and venue-response drafting. Use when asked to scope a research direction, inspect existing research artifacts, choose the next research stage, create a research brief or task board, or coordinate a reusable research workflow.
---

# Research Pipeline Planner

## Quick start

1. Inspect the current project state before asking broad reset questions.
2. Decide whether this should stay standalone or use an orchestrated suite pack.
3. Initialize `research-brief.md`, `task-board.md`, `decision-log.md`, and `artifact-index.md` only when shared stage artifacts will help.
4. Choose the next blocking stage, then either do that work locally or hand it off to the most relevant sibling skill.
5. Insert checkpoints before any step that could waste major time, compute, or paper space.

## Modes

### Standalone mode

- Work from the user prompt plus any local files already present.
- Do not require a suite root or prior pipeline setup.
- Remain composable: if sibling-skill outputs already exist, consume them; if another skill would materially improve the answer, recommend or invoke that workflow rather than pretending isolation.

### Orchestrated mode

- Use the canonical suite layout in `references/suite-contract.md`.
- Keep `artifact-index.md` current and respect the stage gates in `references/stage-gates.md`.
- Coordinate handoffs, but do not monopolize execution. Any stage skill may still be invoked directly.

## Input contract

- Minimum: topic or problem, current state, and desired outcome.
- Prefer: intended audience, success criteria, constraints, deadlines, budget, and existing artifacts.
- If files already imply the current stage, infer it from the artifacts instead of asking generic setup questions.

## Hard stops

- Stop if the goal is too vague to choose a next stage.
- Stop if critical constraints are missing and the next step could waste substantial work.
- In standalone mode, do not force suite initialization when a direct answer would be better.
- In orchestrated mode, do not advance past a stage gate with unresolved blockers.

## Workflow

### 1) Inspect existing state first

- Look for problem statements, literature notes, novelty assessments, experiment plans, result artifacts, review notes, and draft outlines.
- Distinguish:
  - no structured artifacts yet
  - partial standalone artifacts
  - an existing suite pack
- Summarize what already exists before proposing new structure.

### 2) Choose the operating mode deliberately

- Stay standalone when the user wants a direct answer, a one-off plan, or a single stage.
- Initialize the suite when multiple stages need to coordinate through stable file paths.
- Do not treat standalone as single-skill only. Collaboration with sibling skills remains valid in either mode.

### 3) Build the minimum useful planning state

- Use `references/research-brief-template.md`, `references/task-board-template.md`, and `references/decision-log-template.md`.
- Keep the brief explicit about:
  - main question
  - working thesis
  - current stage
  - next blocking decision
  - constraints
- Keep `artifact-index.md` as the source of truth for where stage outputs live.

### 4) Choose the next stage, not the whole future

- Prefer the next blocking stage over speculative long todo lists.
- Use the canonical handoff map:
  - evidence gathering or systematic search -> `research-systematic-literature-review`
  - adversarial novelty pressure test -> `research-novelty-review`
  - decisive validation plan -> `research-experiment-plan`
  - result sanity check -> `research-results-auditor`
  - iterative red-team pass -> `research-review-loop`
  - manuscript structuring -> `research-paper-plan`
  - venue-aware author response or rebuttal -> `research-rebuttal`
- If a sibling skill would improve the answer materially, say so explicitly and collaborate instead of staying artificially local.

### 5) Make checkpoints explicit

- Add a checkpoint whenever the next step could burn major compute, time, or paper space.
- Record whether the decision is:
  - proceed
  - revise scope
  - stop
- Log the rationale in `decision-log.md`.

### 6) Allow collaboration without forcing delegation

- Multi-skill collaboration is valid in both modes.
- If independent review or parallel work would help and the runtime plus caller explicitly allow delegation, bounded subagent passes are allowed.
- If delegation is unavailable, keep collaboration within the current agent and the locally available artifacts.

## References

- `references/research-brief-template.md`
- `references/task-board-template.md`
- `references/decision-log-template.md`
- `references/suite-contract.md`
- `references/stage-gates.md`
- `references/tabmol-ddi-ood-adapter.md`

## Scripts

- `scripts/init_research_pack.py`: create a deterministic suite pack with root planning files and recommended stage directories.
- `scripts/validate_research_pack.py`: validate the orchestrated suite layout and the canonical artifact index.
