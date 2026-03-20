---
name: research-results-auditor
description: Audit ML/statistics experiment outputs for validity, confounds, statistical support, calibration, and mismatch between measured results and claimed conclusions. Use when asked to interpret results, sanity-check benchmarks, review ablations, assess robustness claims, or decide whether an experiment actually supports a paper or project claim.
---

# Research Results Auditor

## Quick start

1. Collect the result artifact, the claim it is supposed to support, and the evaluation protocol.
2. Audit metrics, baselines, controls, uncertainty, and confounds before interpreting the headline result.
3. Separate what the data shows from what the author wants it to imply.
4. Produce an audit using `references/results-audit-template.md`.

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
