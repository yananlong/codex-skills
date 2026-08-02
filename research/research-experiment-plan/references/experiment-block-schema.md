# Experiment Block Schema

Every kept experiment block should define the core fields below. Confirmatory and high-stakes blocks must also define the assurance and execution fields; exploratory blocks should include them when the work will be bound to an orchestrated harness item.

## Core fields

- `block_id`: stable ID such as `B1`
- `paper_role`: `main`, `appendix`, or `cut`
- `claim_ids`: claim IDs from `claim-map.json`
- `anti_claims_ruled_out`: anti-claims this block addresses
- `why_this_block_exists`: reviewer-relevant reason for the block
- `dataset_split_task`: exact evaluation setting
- `systems_compared`: strongest baselines, ablations, and variants only
- `fixed_factors`: factors held constant to keep the comparison fair
- `variable_factors`: the specific manipulated factor(s)
- `metrics`: decisive metrics first
- `setup_details`: backbone, resource assumptions, and key settings
- `seeds`: integer seed count
- `success_criterion`: result that would count as support
- `minimum_effect_size`: threshold or margin if applicable
- `failure_interpretation`: what a negative result would mean
- `expected_output_artifact`: table, figure, or audit artifact to produce
- `compute_budget`: planning note for expected resource use; not a repository-enforced assurance property
- `dependencies`: block IDs or prerequisites
- `priority`: `must-run`, `nice-to-have`, or `defer`
- `decision_gate_id`: gate in `decision-gates.md` that interprets this block

## Assurance fields

- `evidence_class`: `exploratory`, `confirmatory`, `independently_verified`, or `operational_high_stakes`
- `selection_rule`: how cases, samples, checkpoints, or tasks are selected; disclose outcome-informed selection
- `non_vacuity_check`: cheapest check showing that competing systems, policies, or actions can differ and that the comparator can plausibly win
- `complete_outcome_accounting`: how successes, errors, omissions, skips, nulls, retries, timeouts, and execution failures are retained
- `hidden_information_controls`: information unavailable to the evaluated system and how leakage is prevented or detected
- `independence_requirements`: required separation dimensions across context, data, implementation, evaluation, and advancement authority
- `predecessor_failures`: material prior failures this block must resolve, narrow, or carry forward

## Execution fields

`execution` binds the block to a later harness work item:

```json
{
  "mode": "command",
  "entrypoint": {"argv": ["python", "scripts/run_b1.py"], "cwd": "."},
  "declared_inputs": [
    {"path": "data/test.jsonl", "role": "evaluation-data", "snapshot": "digest-at-start"}
  ],
  "declared_evaluator_artifacts": [
    {"path": "evaluation/score.py", "snapshot": "digest-at-start"}
  ],
  "required_outputs": [
    {"path": "results/B1.json", "kind": "metrics"}
  ]
}
```

Supported modes are `command`, `notebook`, `manual`, and `external_job`. An entrypoint is required for all except `manual`. `required_outputs` must contain `expected_output_artifact` when that field is set.

Declared inputs and evaluator artifacts are snapshotted by digest when the bound work item starts. This detects later changes to those declared paths; it does not establish filesystem immutability or executor isolation.

## Lineage policy

`lineage_policy.allowed_relations` declares the scientific relations permitted for runs of this block. Supported relations are:

- `baseline`
- `replication`
- `ablation`
- `parameter_variation`
- `negative_control`
- `sensitivity`
- `alternative_hypothesis`
- `technical_retry`

Include `baseline`. Do not include `pivot`; D3-D4 changes belong to the research commitment contract rather than experiment lineage.

## Gate semantics

The gate bound by `decision_gate_id` must open after the same block. Gate success is separate from technical work-item completion. A correctly executed negative experiment can complete while recording `gate_result=fail` and a scientific disposition such as `falsifies_claim`.

Field presence does not establish that an assurance property actually holds. Structural validation and digest continuity must be followed by semantic audit before confirmatory or high-stakes promotion.

For harness binding, activation-condition syntax, episode fields, and verification commands, see `../../research-pipeline-planner/references/experiment-execution-binding.md`.
