---
name: research-results-auditor
description: Audit ML/statistics experiment outputs for validity, confounds, statistical support, calibration, and mismatch between measured results and claimed conclusions. Use when asked to interpret results, sanity-check benchmarks, review ablations, assess robustness claims, or decide whether an experiment actually supports a paper or project claim.
---

# Research Results Auditor

## Quick start

1. Collect the result artifact, the claim it is supposed to support, and the evaluation protocol.
2. Audit metrics, baselines, controls, uncertainty, and confounds before interpreting the headline result.
3. Separate what the data shows from what the author wants it to imply.
4. Decide whether this is standalone or the results-audit stage inside an orchestrated suite.
5. Produce an audit using `references/results-audit-template.md`.

## Modes

### Standalone mode

- Work from the user prompt plus any local result files, tables, plots, logs, or paper claims.
- Do not require a suite root.
- If the user asks for project-level sequencing, current-state inspection, or coordination across multiple research stages, invoke `research-pipeline-planner` first instead of treating the audit as an isolated task.

### Orchestrated mode

- Prefer the canonical directory `./results-audit/`.
- Read upstream context from `research-brief.md`, `artifact-index.md`, `./experiment-plan/`, `./paper-review/`, and result artifacts when present.
- Keep the audit legible to downstream paper planning, review-loop, and rebuttal work.

## Input contract

- Minimum:
  - a real result artifact or concrete reported numbers
  - the claim those results are supposed to support
  - the evaluation protocol or enough context to identify missing protocol details
- Prefer:
  - experiment plan, run logs, random seeds, confidence intervals, ablations, baseline details, and known reviewer objections

## Output contract

- Primary file: `results-audit.md`
- In orchestrated mode, write the audit under `./results-audit/`.
- In standalone mode, any target directory is valid.

## Audit workflow

### 1) Reconstruct the intended claim

- Write the target claim in one sentence.
- Identify the exact numbers, plots, or tables meant to support it.
- Flag any missing result artifact needed for verification.

### 2) Check protocol integrity

- Verify that metrics match the task.
- Check whether baselines, splits, and data filters are comparable.
- Confirm that ablations isolate the claimed factor rather than multiple changes at once.

### 3) Check inferential quality

- Look for class imbalance, calibration problems, threshold sensitivity, unstable aggregates, and cherry-picked best runs.
- Require statistical tests or uncertainty intervals when claims compare conditions.
- Treat non-significant or noisy deltas as weak evidence, not wins.

### 4) Check confounds and claim drift

- Ask what else could explain the result.
- Compare the measured quantity with the stated conclusion.
- Flag any jump from benchmark score to real-world robustness, safety, or causality without additional support.

## References

- `references/results-audit-template.md`
- `references/metrics-and-tests-checklist.md`
- `references/tabmol-ddi-ood-adapter.md`
