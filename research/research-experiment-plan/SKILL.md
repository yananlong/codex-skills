---
name: research-experiment-plan
description: Convert a concrete research claim into a tracked, decisive experiment plan that works either as a standalone planning artifact or as the experiment stage inside a coordinated research workflow. Use when asked to design experiments, define baselines or ablations, decide run order, separate must-run from nice-to-have evidence, or turn a claim plus evaluation goal into a validation plan.
---

# Research Experiment Plan

## Quick start

1. Freeze the claim, decision rule, and anti-claims before listing runs.
2. Decide whether this is a standalone plan or the experiment stage inside an orchestrated suite.
3. Initialize `experiment-plan.md` and `experiment-tracker.md` only when tracked artifacts will help.
4. Build the minimum decisive experiment blocks, not a benchmark wishlist.
5. Separate must-run from nice-to-have runs and put stop/go gates on the run order.

## Modes

### Standalone mode

- Work from the user prompt plus any local notes or result files already present.
- Do not require a suite root.
- Collaboration is still allowed: if novelty review, results audit, or review-loop artifacts exist, use them; if one of those skills would materially improve the plan, recommend or invoke it.

### Orchestrated mode

- Prefer the canonical directory `./experiment-plan/`.
- Read upstream artifacts from `research-brief.md`, `artifact-index.md`, `./novelty-review/`, and `./literature-review/` when present.
- Keep the experiment outputs easy for downstream paper planning and review to consume.

## Input contract

- Minimum:
  - a concrete claim or hypothesis
  - an evaluation goal or target decision
- Prefer:
  - baselines under consideration
  - constraints on data, compute, or deadlines
  - known reviewer objections
  - existing novelty or literature artifacts

## Hard stops

- Stop if the claim is still too vague to falsify.
- Stop if the evaluation target is undefined.
- Stop if the proposed experiment block mixes too many interventions to interpret cleanly.
- In standalone mode, do not force extra structure when a compact direct answer is sufficient.

## Output contract

- Primary files:
  - `experiment-plan.md`
  - `experiment-tracker.md`
- In orchestrated mode, these live under `./experiment-plan/`.
- In standalone mode, any target directory is valid.

## Workflow

### 1) Freeze the claim map

- Use `references/claim-evidence-map-template.md`.
- Write:
  - primary claim
  - optional supporting claim
  - anti-claims to rule out
  - minimum convincing evidence
- If the claim map is unstable, revise it before planning runs.

### 2) Build decisive experiment blocks

- Use `references/experiment-plan-template.md`.
- Group runs into named blocks with a single purpose each.
- Every block must answer a reviewer-relevant question, not just produce another number.
- Label each block:
  - must-run
  - nice-to-have
  - defer

### 3) Tighten controls and ablations

- Use `references/control-and-ablation-checklist.md`.
- Require a fair comparison protocol and the minimum ablations needed to isolate the claimed factor.
- Flag hidden changes such as altered data, training time, search budget, or model capacity.

### 4) Build the run order

- Use `references/run-order-template.md`.
- Put must-run blocks first.
- Add stop/go gates so later runs depend on what earlier runs actually show.
- Track expected outputs in `experiment-tracker.md`.

### 5) Record risks and collaboration hooks

- Use `references/risk-confound-checklist.md`.
- If novelty is still uncertain, pull in `research-novelty-review`.
- If existing results already exist, pull in `research-results-auditor`.
- If the plan will later feed a draft or response to reviewers, keep outputs legible to `research-paper-plan` and `research-review-loop`.

## References

- `references/experiment-plan-template.md`
- `references/claim-evidence-map-template.md`
- `references/run-order-template.md`
- `references/control-and-ablation-checklist.md`
- `references/risk-confound-checklist.md`
- `references/tabmol-ddi-ood-adapter.md`

## Script

- `scripts/init_experiment_pack.py`: create `experiment-plan.md` and `experiment-tracker.md` in a standalone directory or the suite's `experiment-plan/` directory.
