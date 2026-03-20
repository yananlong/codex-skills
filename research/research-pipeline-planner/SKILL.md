---
name: research-pipeline-planner
description: Plan open-ended ML/statistics research as a staged, artifact-backed workflow with explicit deliverables, success criteria, decision logs, and checkpoints. Use when asked to scope a research direction, break a project into stages, create a research brief/task board, or coordinate low-supervision research work across experiments, reviews, and drafts.
---

# Research Pipeline Planner

## Quick start

1. Confirm the research goal, intended audience, stakes, constraints, and available resources.
2. Initialize the planning pack with `scripts/init_research_pack.py` unless a project pack already exists.
3. Fill `research-brief.md`, `task-board.md`, `decision-log.md`, and `artifact-index.md` before proposing execution.
4. Break the work into stages with entry criteria, exit criteria, and required artifacts.
5. Record unresolved decisions and explicit checkpoints before any substantial execution.

## Workflow

### 1) Frame the problem

- State the main claim or question in falsifiable terms.
- Record audience, success criteria, budget, deadline, and non-goals.
- Distinguish core uncertainties from execution tasks.

### 2) Initialize and fill the artifact pack

- Use `references/research-brief-template.md`, `references/task-board-template.md`, and `references/decision-log-template.md`.
- Refuse to leave key fields implicit; log assumptions when inputs are missing.
- Keep the artifact index current so later agents can find the canonical outputs.

### 3) Plan by stages, not by vague todo lists

- Define a small number of stages such as framing, evidence gathering, experiment planning, execution, review, and manuscripting.
- For each stage, specify:
  - objective
  - required inputs
  - concrete outputs
  - blocking dependencies
  - exit criteria
- Prefer the minimum stage sequence that resolves the main uncertainty.

### 4) Make checkpoints explicit

- Add a checkpoint whenever the next step could waste substantial compute, time, or paper space.
- At each checkpoint, decide whether to proceed, revise scope, or stop.
- Record the decision and rationale in the decision log.

### 5) Support low-supervision research

- Make every important artifact legible to a later agent with no hidden context.
- Require a stable file path for each canonical artifact.
- Prefer deterministic templates and checklists over free-form planning prose.

## References

- `references/research-brief-template.md`
- `references/task-board-template.md`
- `references/decision-log-template.md`
- `references/tabmol-ddi-ood-adapter.md`

## Script

- `scripts/init_research_pack.py`: create a deterministic planning pack in a target directory.
