---
name: research-results-auditor
description: Audit ML/statistics experiment outputs for validity, confounds, statistical support, calibration, and mismatch between measured results and claimed conclusions. Use when asked to interpret results, sanity-check benchmarks, review ablations, assess robustness claims, decide whether an experiment supports a paper claim, or produce a machine-readable result-audit record for downstream paper planning.
---

# Research Results Auditor

## Quick start

1. Collect the concrete result artifact, the exact source claim, and the evaluation protocol.
2. Classify the requested assurance as exploratory, confirmatory, independently verified, or operational/high-stakes.
3. In tracked work, initialize `results-audit.json` and `results-audit.md` with `scripts/init_results_audit.py`.
4. Reconstruct the experiment binding, submitted run, verifier decision, gate result, lineage, artifact digests, and failure history before interpreting the headline metric.
5. Audit protocol integrity, metrics, baselines, uncertainty, selection, outcome accounting, provenance, confounds, and actual independence.
6. Record one bounded audit object per claim under review; do not hide conflicting runs inside a prose summary.
7. Validate with `scripts/validate_results_audit.py`; use the linked profile for orchestrated runs.
8. Hand the canonical JSON audit to `research-paper-plan` instead of asking it to infer support from figures or filenames.

## Modes

### Standalone mode

- Work from the prompt plus concrete local result files, tables, plots, logs, or reported numbers.
- Do not require a suite root or experiment harness.
- Use `source_mode=standalone`; retain exact artifact paths and bounded caveats.
- If the request is really project sequencing or cross-stage coordination, invoke `research-pipeline-planner` first.

### Orchestrated mode

- Use the canonical directory `./results-audit/`.
- Read `research-commitment.json`, `experiment-plan/claim-map.json`, the bound work item, submitted episode, verifier record, result artifacts, and relevant predecessor failures.
- Resolve run IDs and parent relations from event-backed work-item records or `harness_runtime.py experiment-lineage`; never infer lineage from filenames.
- Use `source_mode=orchestrated` and bind every source run to its exact work item, episode digest, submitted run metadata, verifier decision, and verified gate/disposition.
- Keep the audit legible to paper planning, review-loop, rebuttal, and later claim narrowing.

## Input contract

Minimum:

- a real result artifact or concrete reported result;
- the source claim being evaluated;
- enough protocol information to identify missing controls.

Prefer:

- commitment paper ID and identity version;
- claim map and run block;
- work-item and episode records;
- verifier decision and evidence;
- run logs, seeds, intervals, ablations, baselines, selection rule, all skipped/failed/null/retried cases, provenance records, and independence evidence.

## Output contract

### Canonical machine record

Write `results-audit.json` as the authority for downstream claim support. It contains:

- paper identity and audit status;
- stable audit ID and source claim ID;
- requested and attained assurance classes;
- bounded verdict and audited claim effect;
- exact source-run and verifier bindings when orchestrated;
- evidence artifact paths and digests;
- required check results with rationales and evidence paths;
- actual independence dimensions and self-review disclosure;
- limitations, predecessor-failure dispositions, and minimum corrective action.

Use the schema in `references/results-audit-schema.md` and the authority rules in `../research-pipeline-planner/references/result-audit-paper-binding-contract.md`.

### Human-readable view

Write `results-audit.md` as the explanatory view. Use one exact heading `## Audit <audit_id>` per JSON record and include the exact line:

```text
- Bounded verdict: <verdict>
```

The narrative may explain the audit but must not promote, soften, or replace the JSON verdict.

### Bounded verdicts

- `structurally_valid_only`
- `internally_consistent_only`
- `supports_exploratory_follow_up`
- `supports_confirmatory_claim`
- `independently_verified`
- `supports_operational_high_stakes_claim`
- `inconclusive`
- `does_not_support_claim`

## Hard stops

- Do not issue an unqualified pass from file presence, successful commands, schema validation, internal agreement, or polished reporting.
- Do not treat technical completion or verifier approval as a passing scientific gate.
- Do not issue a positive orchestrated verdict without at least one approved source run.
- Do not issue confirmatory-or-stronger support without an approved run whose verified gate is `pass`, verified disposition is `supports_claim`, and submitted claim effect is `strengthen`.
- Do not call results independently verified when the audit is self-review or when evaluation and advancement authority are not materially separated.
- Do not describe start/submission digest equality as executor isolation or filesystem immutability.
- Do not omit skips, nulls, retries, initial failures, resource failures, or exclusions that could affect the claim.
- Preserve outcome-informed case or metric selection as exploratory unless a separate confirmatory evaluation exists.
- Do not let a prose result summary override a negative or inconclusive machine-readable audit.

## Audit workflow

### 1) Reconstruct the intended claim and evidence route

- Freeze the source claim ID and bounded claim text.
- Identify the exact numbers, plots, tables, or artifacts intended to support it.
- Record requested assurance and the paper identity.
- For orchestrated work, resolve work item, episode, run, block, gate, lineage parent, submitted claim effect, verifier decision, verified gate, and verified disposition.

### 2) Check protocol integrity

- Verify task/metric fit, comparable baselines, split integrity, search budgets, stopping rules, and isolated ablations.
- Recover the case-selection rule and identify outcome-conditioned or oracle-conditioned selection.
- Check hidden-truth and evaluator leakage controls.
- Compare declared snapshot and binding records while stating their repository-local assurance boundary.

### 3) Check run lineage and verification semantics

- Verify that the lineage relation is permitted by the bound block.
- Require parents for technical retries, ablations, parameter variations, and sensitivity runs.
- Do not count a technical retry as independent replication.
- Compare the submitted run with the exact verification record for that episode.
- Treat a correctly executed negative experiment as valid evidence even when it weakens or falsifies the claim.

### 4) Complete the required check set

Record exactly one result for each:

- `protocol_integrity`
- `metric_validity`
- `baseline_fairness`
- `outcome_accounting`
- `inferential_support`
- `confound_control`
- `provenance`
- `snapshot_continuity`
- `independence`

Use `pass`, `fail`, `inconclusive`, or `not_assessed`, with a substantive rationale and declared evidence paths.

### 5) Determine assurance and verdict

- Attained assurance cannot exceed requested assurance.
- Positive exploratory support requires passing protocol, metric, and provenance checks.
- Positive confirmatory support additionally requires baseline fairness, outcome accounting, inferential support, and confound control; orchestrated work also requires snapshot continuity.
- Independent support requires a passing independence check, no self-review, evaluation and advancement-authority separation, and at least one additional independence dimension.
- Operational/high-stakes support requires all independence dimensions and every required check to pass.
- Keep assurance strength separate from direction of evidence: a confirmatory audit may conclude `does_not_support_claim`.

### 6) Preserve failure inheritance and write the handoff

- Classify each predecessor failure as open, resolved, or accepted with narrowing.
- State limitations and the minimum corrective action.
- Write the JSON record first, then the matching narrative section.
- Validate before handing the audit to paper planning.

## Validation

Structural validation:

```bash
python scripts/validate_results_audit.py \
  --audit results-audit.json \
  --narrative results-audit.md
```

Orchestrated linked validation:

```bash
python scripts/validate_results_audit.py \
  --audit results-audit/results-audit.json \
  --narrative results-audit/results-audit.md \
  --assurance-profile linked \
  --commitment research-commitment.json \
  --claim-map experiment-plan/claim-map.json \
  --work-items work-items.json
```

A passing validator establishes declared repository consistency, not scientific validity, authenticated execution, external immutability, or real-world independence.

## References

- `references/results-audit-template.md`
- `references/results-audit-schema.md`
- `references/metrics-and-tests-checklist.md`
- `references/tabmol-ddi-ood-adapter.md`
- `../research-pipeline-planner/references/experiment-execution-binding.md`
- `../research-pipeline-planner/references/result-audit-paper-binding-contract.md`
- `../research-pipeline-planner/references/epistemic-assurance-contract.md`

## Scripts

- `scripts/init_results_audit.py`: initialize `results-audit.json` and `results-audit.md` without overwriting existing work unless `--force` is supplied.
- `scripts/validate_results_audit.py`: validate audit structure, verdict preconditions, narrative anchors, and optional commitment/claim/run/verifier/evidence bindings.
