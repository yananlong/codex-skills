---
name: research-pipeline-planner
description: Coordinate research as either a standalone staged planning pass or an orchestrated multi-skill workflow with shared artifacts, stage gates, and optional collaboration with Zotero library sync, literature review, idea discovery, novelty review, experiment planning, paper review, result auditing, review, paper planning, and venue-response drafting. Use when asked to scope a research direction, inspect existing research artifacts, choose the next research stage, create a research brief or task board, coordinate a reusable research workflow, build a research roadmap or agenda, organize a research repo, turn notes into a phase plan, define milestones, decide what to do next, or coordinate literature plus ideation plus experiments plus paper work.
---

# Research Pipeline Planner

## Quick start

1. Inspect the current project state before asking broad reset questions.
2. Use this skill as the default first pass when the user asks for project-level sequencing, current-state inspection, or a task that spans two or more research stages.
3. Decide whether this should stay standalone or use an orchestrated suite pack.
4. Classify any proposed evidence promotion as exploratory, confirmatory, independently verified, or operational/high-stakes; use `references/epistemic-assurance-contract.md` before authorizing a stronger class.
5. Initialize `research-brief.md`, `task-board.md`, `decision-log.md`, and `artifact-index.md` only when shared stage artifacts will help.
6. Choose the next blocking stage, then either do that work locally or hand it off to the most relevant sibling skill.
7. Insert checkpoints before any step that could waste major time, compute, paper space, or evidential credibility.

## Routing triggers

Prefer this skill before a sibling stage skill when the user asks for a research roadmap, research agenda, project plan, phase plan, milestones, what to do next, repo organization, notes-to-plan conversion, or coordination across literature review, idea discovery, novelty review, experiments, results audit, paper planning, review, and rebuttal.

Do not force this skill for a clear one-stage request. Route direct ideation, paper reviews, novelty checks, experiment plans, result audits, paper outlines, Zotero syncs, or rebuttals to the relevant sibling skill unless the user also asks for project-level sequencing or persistent cross-stage coordination.

## Modes

### Standalone mode

- Work from the user prompt plus any local files already present.
- Do not require a suite root or prior pipeline setup.
- Default to lightweight triage and next-stage recommendation; do not create files unless persistent shared state would materially help.
- Remain composable: if sibling-skill outputs already exist, consume them; if another skill would materially improve the answer, recommend or invoke that workflow rather than pretending isolation.

### Orchestrated mode

- Use the canonical suite layout in `references/suite-contract.md`.
- Keep `artifact-index.md` current and respect the stage gates in `references/stage-gates.md`.
- Coordinate handoffs, but do not monopolize execution. Any stage skill may still be invoked directly.
- Keep the evidence class and promotion record visible across handoffs; changing stage or role labels must not silently upgrade the evidence.

## Input contract

- Minimum: topic or problem, current state, and desired outcome.
- Prefer: intended audience, success criteria, constraints, deadlines, budget, existing artifacts, requested evidence class, and known predecessor failures.
- If files already imply the current stage, infer it from the artifacts instead of asking generic setup questions.

## Hard stops

- Stop if the goal is too vague to choose a next stage.
- Stop if critical constraints are missing and the next step could waste substantial work.
- In standalone mode, do not force suite initialization when a direct answer would be better.
- In orchestrated mode, do not advance past a stage gate with unresolved blockers.
- Do not promote exploratory or outcome-informed evidence as confirmatory merely because the artifact is polished, internally consistent, or structurally valid.
- Stop confirmatory or high-stakes promotion when the decision contract is incomplete, material failure states are omitted, hidden truth is available to the evaluated process, independence is only a role label, or a material predecessor failure has no evidence-backed disposition. Continue only at a weaker evidence class when useful.

## Workflow

### 1) Inspect existing state first

- Look for problem statements, literature notes, ideation artifacts, novelty assessments, experiment plans, paper-review artifacts, result artifacts, review notes, draft outlines, decision logs, and failure reviews.
- Distinguish:
  - no structured artifacts yet
  - partial standalone artifacts
  - an existing suite pack
- Summarize what already exists before proposing new structure.
- Identify material predecessor failures and whether they were resolved by new evidence, accepted with claim narrowing, merely reclassified, or omitted.

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
  - current and requested evidence class
  - material predecessor failures
- Keep `artifact-index.md` as the source of truth for where stage outputs live.

### 4) Choose the next stage, not the whole future

- Prefer the next blocking stage over speculative long todo lists.
- Use the canonical handoff map:
  - curated Zotero library sync or citation export -> `research-zotero`
  - evidence gathering or systematic search -> `research-systematic-literature-review`
  - broad direction to grounded candidate ideas -> `research-idea-discovery`
  - adversarial novelty pressure test -> `research-novelty-review`
  - decisive validation plan -> `research-experiment-plan`
  - deep single-paper review -> `research-paper-review`
  - paper-review novelty, impact, or literature contextualization -> `research-paper-review` plus `research-systematic-literature-review` paper-context mode and `research-novelty-review`
  - result sanity check -> `research-results-auditor`
  - iterative red-team pass -> `research-review-loop`
  - manuscript structuring -> `research-paper-plan`
  - venue-aware author response or rebuttal -> `research-rebuttal`
- If a sibling skill would improve the answer materially, say so explicitly and collaborate instead of staying artificially local.

### 5) Make checkpoints explicit

- Add a checkpoint whenever the next step could burn major compute, time, paper space, or evidential credibility.
- Record whether the decision is:
  - proceed
  - revise scope
  - narrow evidence class
  - stop
- For evidence promotion, record the claim or property, provenance, complete decision or loss contract, selection rule, non-vacuity check, predecessor failures, actual independence dimensions, unresolved limitations, and route decision.
- Log the rationale in `decision-log.md`.

### 6) Allow collaboration without forcing delegation

- Multi-skill collaboration is valid in both modes.
- If independent review or parallel work would help and the runtime plus caller explicitly allow delegation, bounded subagent passes are allowed.
- If delegation is unavailable, keep collaboration within the current agent and the locally available artifacts, disclose self-review, and avoid calling the result independent.

## References

- `references/research-brief-template.md`
- `references/task-board-template.md`
- `references/decision-log-template.md`
- `references/suite-contract.md`
- `references/review-stage-contract.md`
- `references/stage-gates.md`
- `references/epistemic-assurance-contract.md`
- `references/tabmol-ddi-ood-adapter.md`

## Scripts

- `scripts/init_research_pack.py`: create a deterministic suite pack with root planning files and recommended stage directories.
- `scripts/validate_research_pack.py`: validate the orchestrated suite layout and the canonical artifact index.