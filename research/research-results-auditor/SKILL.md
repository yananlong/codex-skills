---
name: research-results-auditor
description: Audit ML/statistics experiment outputs for validity, confounds, statistical support, calibration, and mismatch between measured results and claimed conclusions. Use when asked to interpret results, sanity-check benchmarks, review ablations, assess robustness claims, or decide whether an experiment actually supports a paper or project claim.
---

# Research Results Auditor

## Quick start

1. Collect the result artifact, the claim it is supposed to support, and the evaluation protocol.
2. Classify the claimed evidence as exploratory, confirmatory, independently verified, or operational/high-stakes.
3. Audit metrics, baselines, controls, uncertainty, provenance, selection, complete outcome accounting, and confounds before interpreting the headline result.
4. Separate what the data shows from what the author wants it to imply.
5. Test whether assurance labels correspond to real properties rather than file fields, role names, or self-attested controls.
6. Decide whether this is standalone or the results-audit stage inside an orchestrated suite.
7. Produce an audit using `references/results-audit-template.md` and the precise verdict language in `../research-pipeline-planner/references/epistemic-assurance-contract.md`.

## Modes

### Standalone mode

- Work from the user prompt plus any local result files, tables, plots, logs, or paper claims.
- Do not require a suite root.
- If the user asks for project-level sequencing, current-state inspection, or coordination across multiple research stages, invoke `research-pipeline-planner` first instead of treating the audit as an isolated task.

### Orchestrated mode

- Prefer the canonical directory `./results-audit/`.
- Read upstream context from `research-brief.md`, `artifact-index.md`, `./experiment-plan/`, `./paper-review/`, failure reviews, decision logs, and result artifacts when present.
- Keep the audit legible to downstream paper planning, review-loop, and rebuttal work.
- Carry material predecessor failures forward until new evidence resolves them; do not reset the ledger because a new result pack exists.

## Input contract

- Minimum:
  - a real result artifact or concrete reported numbers
  - the claim those results are supposed to support
  - the evaluation protocol or enough context to identify missing protocol details
- Prefer:
  - experiment plan, run logs, random seeds, confidence intervals, ablations, baseline details, known reviewer objections, case-selection rule, all skipped/failed/null/retried cases, source code for oracle and runner, provenance records, and the claimed independence arrangement

## Output contract

- Primary file: `results-audit.md`
- In orchestrated mode, write the audit under `./results-audit/`.
- In standalone mode, any target directory is valid.
- End with one of these bounded conclusions:
  - `structurally valid only`
  - `internally consistent only`
  - `supports exploratory follow-up`
  - `supports the confirmatory claim`
  - `independently verified`
  - `inconclusive`
  - `does not support the claim`
- State the actual independence dimensions and unresolved predecessor failures beside the verdict.

## Hard stops

- Do not issue an unqualified pass from file presence, successful commands, schema validation, internal agreement, or polished reporting alone.
- Do not treat a self-hash as an external lock, an environment flag as isolation, a copied digest as replay, or a role label as independence.
- Do not call results independently verified unless a materially separate evaluator or reproduction pass exists and its independence dimensions are stated.
- If skips, nulls, retries, initial failures, resource failures, or exclusions that could affect the claim are missing, the verdict cannot exceed `inconclusive` until accounting is repaired.
- If cases or metrics were selected after inspecting the relevant outcomes, preserve the result as exploratory unless a separate confirmatory evaluation exists.
- If the loss or outcome contract cannot penalize a decision-relevant mistake, do not accept a confirmatory gate based on that contract.

## Audit workflow

### 1) Reconstruct the intended claim and route

- Write the target claim in one sentence.
- Identify the exact numbers, plots, tables, artifacts, or control assertions meant to support it.
- Record the current and requested evidence class.
- Flag any missing result artifact, provenance record, failure ledger, or decision rule needed for verification.

### 2) Check protocol integrity

- Verify that metrics match the task.
- Check whether baselines, splits, data filters, search budgets, and stopping rules are comparable.
- Confirm that ablations isolate the claimed factor rather than multiple changes at once.
- Recover the case-selection rule and identify outcome-conditioned or oracle-conditioned selection.
- Check whether hidden truth, labels, or adjudication state were available to the evaluated system.

### 3) Check assurance properties

- Compare each assurance label with the actual property claimed.
- Inspect whether runner, oracle, comparator, and sensitivity checks share hard-coded policy, code paths, data, or hidden truth that could create correlated failure.
- Distinguish exact regeneration from copying or reusing a recorded digest.
- Distinguish external anchoring from self-referential integrity checks.
- State independence across context, data, implementation, evaluation, and advancement authority. If the same agent or team performed multiple roles, call it self-review.

### 4) Check non-vacuity and complete outcome accounting

- Verify that at least one plausible case makes competing systems, policies, or actions differ.
- Verify that the comparator can win under a plausible condition rather than being disabled by construction.
- Confirm that every decision-relevant error, including failure to act, appears in the loss or outcome contract.
- Account for successes, wrong actions, missed actions, skips, nulls, retries, timeouts, initial execution failures, and resource failures.
- Treat missing or silently reduced set-valued outcomes as a protocol defect, not a harmless formatting choice.

### 5) Check inferential quality

- Look for class imbalance, calibration problems, threshold sensitivity, unstable aggregates, multiple testing, and cherry-picked best runs.
- Require statistical tests or uncertainty intervals when claims compare conditions.
- Treat non-significant or noisy deltas as weak evidence, not wins.
- Check whether uncertainty analysis matches the actual sampling and selection process.

### 6) Check confounds, claim drift, and failure inheritance

- Ask what else could explain the result.
- Compare the measured quantity with the stated conclusion.
- Flag any jump from benchmark score to real-world robustness, safety, security, or causality without additional support.
- Carry each material predecessor failure forward and classify it as resolved by evidence, accepted with claim narrowing, still open, or improperly reclassified/omitted.
- Treat replacement of the route, artifact, or label as a new claim unless the original failure is actually resolved.

### 7) Write the verdict precisely

- Separate structural validity, internal consistency, exploratory usefulness, confirmatory support, and independent verification.
- Explain the strongest evidence against the preferred interpretation before giving the final verdict.
- List the minimum corrective action needed to reach the next stronger evidence class.
- Never shorten a bounded verdict into an unqualified “passed,” “validated,” or “verified.”

## References

- `references/results-audit-template.md`
- `references/metrics-and-tests-checklist.md`
- `references/tabmol-ddi-ood-adapter.md`
- `../research-pipeline-planner/references/epistemic-assurance-contract.md`