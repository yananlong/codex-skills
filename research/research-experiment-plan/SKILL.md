---
name: research-experiment-plan
description: Convert a concrete research claim into a tracked, decisive experiment plan that works either as a standalone planning artifact or as the experiment stage inside a coordinated research workflow. Use when asked to design experiments, define baselines or ablations, decide run order, separate must-run from nice-to-have evidence, or turn a claim plus evaluation goal into a validation plan.
---

# Research Experiment Plan

## Quick start

1. Freeze the claim, decision rule, and anti-claims before listing runs.
2. Classify the intended evidence as exploratory, confirmatory, independently verified, or operational/high-stakes; use `../research-pipeline-planner/references/epistemic-assurance-contract.md` when promoting beyond exploratory status.
3. Decide whether this is a standalone plan or the experiment stage inside an orchestrated suite.
4. Initialize the full experiment pack with `scripts/init_experiment_pack.py` whenever the plan needs tracked execution.
5. Build the minimum decisive experiment blocks, not a benchmark wishlist or a paper-defence script.
6. Run a cheap non-vacuity preflight before expensive or confirmatory execution.
7. Separate must-run from nice-to-have runs, attach explicit decision gates, and emit bridge-ready outputs for later execution.
8. For orchestrated execution, declare inputs, evaluator artifacts, required outputs, allowed lineage relations, and gate-conditioned downstream activation using `../research-pipeline-planner/references/experiment-execution-binding.md`.

## Constants

- `MAX_PRIMARY_CLAIMS = 2` unless multiple inseparable claims are truly required.
- `MAX_CORE_BLOCKS = 5` unless the evaluation setting forces more.
- `MAX_BASELINE_FAMILIES = 3` unless the field norm demands additional families.
- `DEFAULT_SEEDS = 3` when stochastic variance matters and budget allows.

## Modes

### Standalone mode

- Work from the user prompt plus any local notes or result files already present.
- Do not require a suite root.
- If the user asks for project-level sequencing, current-state inspection, or coordination across multiple research stages, invoke `research-pipeline-planner` first instead of treating experiment planning as the whole task.
- If the user asks what idea to pursue, or the claim is still only a broad research direction, invoke `research-idea-discovery` before experiment planning.
- Collaboration is still allowed: if novelty review, results audit, or review-loop artifacts exist, use them; if one of those skills would materially improve the plan, recommend or invoke it.

### Orchestrated mode

- Prefer the canonical directory `./experiment-plan/`.
- Read upstream artifacts from `research-brief.md`, `artifact-index.md`, `./ideation/`, `./novelty-review/`, and `./literature-review/` when present.
- Keep the experiment outputs easy for downstream paper planning and review to consume.
- Carry forward selection history, evidence class, negative evidence, and material predecessor failures rather than resetting them at the experiment stage.
- Treat `claim-map.json` and `run-blocks.json` as frozen inputs when creating an experiment-bound harness work item.
- Keep technical episode completion, scientific disposition, and decision-gate result distinct. A correctly executed negative experiment may complete while failing its scientific gate.

## Input contract

- Minimum:
  - a concrete claim or hypothesis
  - an evaluation goal or target decision
- Prefer:
  - baselines under consideration
  - constraints on data, compute, or deadlines
  - known reviewer objections
  - existing novelty or literature artifacts
  - current and requested evidence class
  - case-selection history
  - material predecessor failures and prior negative results

## Hard stops

- Stop if the claim is still too vague to falsify.
- If no concrete claim exists yet, route to `research-idea-discovery` instead of inventing one inside the experiment plan.
- Stop if the evaluation target is undefined.
- Stop if the proposed experiment block mixes too many interventions to interpret cleanly.
- In standalone mode, do not force extra structure when a compact direct answer is sufficient.
- Do not design a confirmatory route around cases selected because they already yield the desired answer; preserve them as exploratory and define a separate selection rule.
- Stop confirmatory promotion when the decision or loss contract omits a decision-relevant error, omission, skip, null, retry, or failure state.
- Stop confirmatory promotion when the evaluated system can read hidden truth, the oracle and runner share undisclosed hard-coded policy, or the claimed independence is only a role label.
- Do not treat structural validation, internal agreement, self-hashes, copied digests, environment flags, or field presence as proof that the claimed assurance property holds.
- Do not treat a technically completed run as a passing scientific gate.
- Do not use experiment lineage to encode a D3-D4 paper pivot; route that through the research commitment contract.
- A failed non-vacuity preflight normally forces revision or a weaker evidence class; it does not prohibit exploratory work.

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
- `claim-map.json` is the machine-readable source of truth for claims, anti-claims, evidence class, decision rules, loss contracts, falsification tests, and predecessor failures.
- `run-blocks.json` is the machine-readable source of truth for experiment blocks, dependencies, decision-gate links, pass/fail criteria, selection rules, non-vacuity checks, outcome accounting, hidden-information controls, execution declarations, and allowed lineage relations.
- `decision-gates.md` records the checkpoints that can halt, narrow, reclassify, or authorize later blocks after a result is interpreted.
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
  - current evidence class and outcome-informed selection history
  - material predecessor failures and unresolved negative evidence
- If these are missing, derive the same fields explicitly from the user prompt before planning any block.

### 1) Freeze the claim map

- Use `references/claim-evidence-map-template.md`.
- Write:
  - primary claim
  - optional supporting claim
  - anti-claims to rule out
  - minimum convincing evidence
  - current and requested evidence class
  - complete decision rule and loss or outcome contract
  - falsification test
  - material predecessor failures and their disposition
- Cap the number of primary/supporting claims aggressively.
- Define what result would force reframing, reclassification, or abandonment.
- If the claim map is unstable, revise it before planning runs.
- Record the claim map in both `experiment-plan.md` and `claim-map.json`.

### 2) Build the experimental storyline before the detailed blocks

- Start from a compact default storyline and delete any block that does not test a decision-relevant claim:
  - main anchor result
  - novelty isolation
  - simplicity or elegance check
  - frontier-necessity check when a frontier-model-era component is central
  - failure analysis or qualitative diagnosis
- Do not optimize only for a favorable paper story. A block exists to discriminate among claims, actions, or explanations, including outcomes that weaken the project.
- Mark each storyline block as:
  - main paper
  - appendix
  - cut
- A stronger modern baseline is preferable to many weak baselines.
- If the project is intentionally non-frontier, say so explicitly and skip the frontier-necessity block rather than forcing one.

### 3) Run the non-vacuity preflight

Before expensive or confirmatory runs, check that:

- at least one plausible case makes competing systems, policies, or actions differ;
- every decision-relevant error, including failure to act, is penalized by the loss or outcome contract;
- the comparator can win under a plausible condition rather than being disabled by construction;
- case selection was not conditioned on the oracle answer or desired outcome;
- skipped, failed, null, and retried cases remain visible in the accounting.

Record the result in `decision-gates.md` and in each affected block's `non_vacuity_check`. If the preflight fails, revise the plan or keep the evidence exploratory.

### 4) Build decisive experiment blocks

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
  - compute budget as a planning note, not a repository-enforced assurance property
  - dependencies
  - decision gate ID
  - case-selection rule
  - non-vacuity check
  - complete outcome accounting
  - hidden-information controls
  - actual independence requirements
  - execution mode and entrypoint when known
  - declared input snapshot paths
  - declared evaluator snapshot paths
  - required output paths
  - allowed lineage relations
- Write the block objects to `run-blocks.json` rather than leaving the critical structure only in prose.

### 5) Tighten controls and ablations

- Use `references/control-and-ablation-checklist.md`.
- Require a fair comparison protocol and the minimum ablations needed to isolate the claimed factor.
- Flag hidden changes such as altered data, training time, search budget, or model capacity.
- A simplicity check should usually compare the final method against an overbuilt or tempting extra-component variant.
- A frontier-necessity check should compare the chosen modern component against the strongest simpler plausible alternative.
- Treat agreement among implementations that share policy, code, data, or hidden truth as correlated evidence until diversity is demonstrated.
- State whether review is self-review or materially independent across context, data, implementation, evaluation, and advancement authority.

### 6) Build the run order and decision gates

- Use `references/run-order-template.md`.
- Use `references/decision-gates-template.md`.
- Put must-run blocks first.
- Add stop/go gates so later runs depend on what earlier runs actually show.
- Every must-run block needs:
  - a gate bound to that block;
  - a condition that advances the plan;
  - a condition that forces revision or weaker evidence classification;
  - a condition that stops the plan.
- A dependent block that requires a scientific outcome must declare a gate-conditioned activation rule in the harness, not only a structural dependency.
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
- Carry material predecessor failures forward until new evidence resolves them; reclassification, replacement, or omission is not resolution.

### 7) Emit the execution bridge

- Use `references/execution-bridge-template.md`.
- For each must-run block, record:
  - exact upstream claim IDs
  - decision gate ID
  - required inputs and datasets
  - declared input and evaluator snapshot paths
  - expected command or implementation entrypoint if known
  - required output artifacts the auditor or paper planner should look for
  - intended lineage relation and parent-run requirement
  - blockers that must be resolved before someone starts coding or submitting jobs
  - evidence class and whether outcome inspection would trigger reclassification
  - hidden information unavailable to the evaluated system
  - all failure, skip, null, and retry states that must be retained
  - idempotency and restart requirements
  - any downstream activation rule governed by the gate
- Keep `execution-bridge.md` concise and implementation-facing. It exists so later stages do not have to reconstruct planning intent from a narrative plan.

### 8) Record risks and collaboration hooks

- Use `references/risk-confound-checklist.md`.
- If novelty is still uncertain, pull in `research-novelty-review`.
- If existing results already exist, pull in `research-results-auditor`.
- If the plan will later feed a draft or response to reviewers, keep outputs legible to `research-paper-plan` and `research-review-loop`.
- Validate tracked packs with `scripts/validate_experiment_pack.py` before treating them as stable stage artifacts.
- The default validator profile remains structural for backward compatibility. For confirmatory or high-stakes promotion, run it with `--assurance-profile confirmatory`; even that checks field presence, links, and internal consistency, not whether the declared controls actually held.

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
- `../research-pipeline-planner/references/experiment-execution-binding.md`
- `../research-pipeline-planner/references/epistemic-assurance-contract.md`

## Scripts

- `scripts/init_experiment_pack.py`: create the full experiment-planning pack in a standalone directory or the suite's `experiment-plan/` directory, including execution and lineage scaffolds.
- `scripts/validate_experiment_pack.py`: validate required headings, JSON structure, reciprocal claim/block links, gate bindings, execution declarations, lineage policy, tracker states, and confirmatory assurance fields without claiming executor isolation or scientific validity.
