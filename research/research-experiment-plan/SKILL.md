---
name: research-experiment-plan
description: Convert a concrete research claim into a tracked, decisive experiment plan that works either as a standalone planning artifact or as the experiment stage inside a coordinated research workflow. Use when asked to design experiments, define baselines or ablations, decide run order, separate must-run from nice-to-have evidence, or turn a claim plus evaluation goal into a validation plan.
---

# Research Experiment Plan

## Quick start

1. Freeze the claim, decision rule, and anti-claims before listing runs.
2. Decide whether this is a standalone plan or the experiment stage inside an orchestrated suite.
3. Initialize the full experiment pack with `scripts/init_experiment_pack.py` whenever the plan needs tracked execution.
4. Build the minimum decisive experiment blocks, not a benchmark wishlist.
5. Separate must-run from nice-to-have runs, attach explicit decision gates, and emit bridge-ready outputs for later execution.

## Constants

- `MAX_PRIMARY_CLAIMS = 2` unless multiple inseparable claims are truly required.
- `MAX_CORE_BLOCKS = 5` unless the evaluation setting forces more.
- `MAX_BASELINE_FAMILIES = 3` unless the field norm demands additional families.
- `DEFAULT_SEEDS = 3` when stochastic variance matters and budget allows.

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
  - `claim-map.json`
  - `run-blocks.json`
  - `decision-gates.md`
  - `execution-bridge.md`
- In orchestrated mode, these live under `./experiment-plan/`.
- In standalone mode, any target directory is valid.
- `claim-map.json` is the machine-readable source of truth for claims, anti-claims, and evidence thresholds.
- `run-blocks.json` is the machine-readable source of truth for experiment blocks, dependencies, and pass/fail criteria.
- `decision-gates.md` records the checkpoints that can halt or narrow the plan before expensive runs.
- `execution-bridge.md` translates the plan into implementation-ready instructions without forcing another skill to reverse-engineer the planning intent.

## Workflow

### 0) Load the proposal context before inventing runs

- Read the strongest available upstream artifacts first:
  - `research-brief.md`
  - `novelty-review/novelty-report.md`
  - `literature-review/*.review.md`
  - `review-loop/REVIEW_STATE.json`
  - existing result tables or audit notes
- Extract:
  - problem anchor
  - dominant contribution
  - optional supporting contribution
  - reviewer-relevant failure modes
  - data, compute, and deadline constraints
- If these are missing, derive the same fields explicitly from the user prompt before planning any block.

### 1) Freeze the claim map

- Use `references/claim-evidence-map-template.md`.
- Write:
  - primary claim
  - optional supporting claim
  - anti-claims to rule out
  - minimum convincing evidence
- cap the number of primary/supporting claims aggressively
- define what result would force reframing or abandonment
- If the claim map is unstable, revise it before planning runs.
- Record the claim map in both `experiment-plan.md` and `claim-map.json`.

### 2) Build the experimental storyline before the detailed blocks

- Start from a compact default storyline and delete any block that does not defend the paper:
  - main anchor result
  - novelty isolation
  - simplicity or elegance check
  - frontier-necessity check when a frontier-model-era component is central
  - failure analysis or qualitative diagnosis
- Mark each storyline block as:
  - main paper
  - appendix
  - cut
- A stronger modern baseline is preferable to many weak baselines.
- If the project is intentionally non-frontier, say so explicitly and skip the frontier-necessity block rather than forcing one.

### 3) Build decisive experiment blocks

- Use `references/experiment-plan-template.md`.
- Use `references/experiment-block-schema.md`.
- Group runs into named blocks with a single purpose each.
- Every block must answer a reviewer-relevant question, not just produce another number.
- Label each block:
  - must-run
  - nice-to-have
  - defer
- For every kept block, specify:
  - claim tested
  - anti-claim ruled out
  - why this block exists
  - dataset / split / task
  - compared systems
  - decisive metrics
  - setup details
  - success criterion
  - failure interpretation
  - expected paper artifact
  - compute budget
  - dependencies
- Write the block objects to `run-blocks.json` rather than leaving the critical structure only in prose.

### 4) Tighten controls and ablations

- Use `references/control-and-ablation-checklist.md`.
- Require a fair comparison protocol and the minimum ablations needed to isolate the claimed factor.
- Flag hidden changes such as altered data, training time, search budget, or model capacity.
- A simplicity check should usually compare the final method against an overbuilt or tempting extra-component variant.
- A frontier-necessity check should compare the chosen modern component against the strongest simpler plausible alternative.

### 5) Build the run order and decision gates

- Use `references/run-order-template.md`.
- Use `references/decision-gates-template.md`.
- Put must-run blocks first.
- Add stop/go gates so later runs depend on what earlier runs actually show.
- Every must-run block needs:
  - a gate that opens it
  - a condition that advances the plan
  - a condition that forces revision
  - a condition that stops the plan
- Track expected outputs and lifecycle state in `experiment-tracker.md`.
- Use tracker statuses:
  - `planned`
  - `ready`
  - `blocked`
  - `running`
  - `analyzed`
  - `decisive`
  - `inconclusive`
  - `dropped`

### 6) Emit the execution bridge

- Use `references/execution-bridge-template.md`.
- For each must-run block, record:
  - exact upstream claim IDs
  - required inputs and datasets
  - expected command or implementation entrypoint if known
  - output artifacts the auditor or paper planner should look for
  - blockers that must be resolved before someone starts coding or submitting jobs
- Keep `execution-bridge.md` concise and implementation-facing. It exists so later stages do not have to reconstruct planning intent from a narrative plan.

### 7) Record risks and collaboration hooks

- Use `references/risk-confound-checklist.md`.
- If novelty is still uncertain, pull in `research-novelty-review`.
- If existing results already exist, pull in `research-results-auditor`.
- If the plan will later feed a draft or response to reviewers, keep outputs legible to `research-paper-plan` and `research-review-loop`.
- Validate tracked packs with `scripts/validate_experiment_pack.py` before treating them as stable stage artifacts.

## References

- `references/experiment-plan-template.md`
- `references/claim-evidence-map-template.md`
- `references/experiment-block-schema.md`
- `references/run-order-template.md`
- `references/decision-gates-template.md`
- `references/execution-bridge-template.md`
- `references/control-and-ablation-checklist.md`
- `references/risk-confound-checklist.md`
- `references/tabmol-ddi-ood-adapter.md`

## Scripts

- `scripts/init_experiment_pack.py`: create the full experiment-planning pack in a standalone directory or the suite's `experiment-plan/` directory.
- `scripts/validate_experiment_pack.py`: validate required headings, JSON structure, gate references, and tracker states for tracked experiment packs.
