---
name: research-experiment-plan
description: Convert a research claim into the minimum experiment matrix needed to test it with clear hypotheses, controls, ablations, required artifacts, and stop conditions. Use when asked to design experiments, define ablations, plan validation work, or reduce an open-ended research agenda to a decisive execution plan.
---

# Research Experiment Plan

## Quick start

1. Write the claim or hypothesis in falsifiable terms.
2. Decide what evidence would confirm, weaken, or refute it.
3. Build the minimum experiment matrix that answers that question.
4. Specify controls, ablations, artifacts, and stop conditions before execution.

## Workflow

### 1) Define the claim-to-evidence contract

- State the primary hypothesis and the alternative explanations.
- Identify the dependent variables, evaluation protocol, and decision rule.
- Reject plans that cannot say what outcome would change the conclusion.

### 2) Plan the minimum decisive matrix

- Include only experiments that resolve an uncertainty or block a later decision.
- Prefer a compact matrix with named purposes over a large grid of loosely motivated runs.
- Explicitly label:
  - must-run
  - nice-to-have
  - defer

### 3) Specify controls and ablations

- Require a baseline, a fair comparison protocol, and the minimal ablation set needed to isolate the claimed factor.
- Flag hidden interventions such as changed data, changed training time, or changed model capacity.

### 4) Define outputs and stop conditions

- Name the expected artifacts for each experiment.
- State when to stop because the claim is already supported, already weakened, or not worth more compute.
- Record known risks that could invalidate interpretation.

## References

- `references/experiment-plan-template.md`
- `references/control-and-ablation-checklist.md`
- `references/tabmol-ddi-ood-adapter.md`
