# Experiment Execution Binding

Use this contract only for experiment work items in an orchestrated research suite. It binds a frozen experiment-plan block to a harness episode without turning the repository harness into an executor or isolation boundary.

## Authorities

- `research-commitment.json` owns paper identity and D3-D4 decisions.
- `experiment-plan/claim-map.json` owns experiment-facing claim IDs.
- `experiment-plan/run-blocks.json` owns experiment blocks, execution declarations, lineage policy, and decision-gate binding.
- `harness-events.jsonl` owns runtime history.
- The work item's `experiment_binding` freezes paths and digests for one block.
- The submitted episode's `experiment_run` records one scientific run and its interpretation.

Do not duplicate these authorities in a separate execution-contract artifact.

## Work-item binding

An experiment-bound work item records:

```json
{
  "experiment_binding": {
    "claim_map_path": "experiment-plan/claim-map.json",
    "claim_map_digest": "sha256...",
    "run_blocks_path": "experiment-plan/run-blocks.json",
    "run_blocks_digest": "sha256...",
    "block_id": "B1",
    "decision_gate_id": "G1",
    "commitment_path": "research-commitment.json",
    "commitment_digest": "sha256...",
    "paper_id": "paper-id",
    "identity_version": 1,
    "execution": {},
    "claim_ids": ["C1"],
    "allowed_lineage_relations": ["baseline", "ablation"]
  },
  "activation_conditions": []
}
```

The runtime rechecks the bound digests before start and submission. Digest continuity is a repository-local consistency check. It does not establish external immutability, prevent undisclosed reads or writes, or prove executor isolation.

## Execution declaration

A run block may declare:

```json
{
  "decision_gate_id": "G1",
  "execution": {
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
  },
  "lineage_policy": {
    "allowed_relations": ["baseline", "technical_retry", "ablation"]
  }
}
```

Supported execution modes are `command`, `notebook`, `manual`, and `external_job`. The harness records the declaration but does not run the command.

Declared inputs and evaluator artifacts must be outside the work item's declared write scope. Required outputs must be frozen expected artifacts inside that scope. At start, the runtime records digests for declared inputs and evaluators. Submission fails when those declared snapshots no longer match.

Use the phrases `declared snapshot` and `digest continuity`; do not call these files immutable.

## Experiment episode

An experiment-bound episode includes:

```json
{
  "experiment_run": {
    "run_id": "RUN-B1-001",
    "block_id": "B1",
    "relation": "baseline",
    "parent_run_id": null,
    "gate_id": "G1",
    "gate_result": "fail",
    "scientific_disposition": "falsifies_claim",
    "claim_effects": [
      {"claim_id": "C1", "effect": "kill", "scope": "held-out Count8 setting"}
    ],
    "interpretation": "The run completed correctly but failed the predeclared criterion."
  }
}
```

Allowed gate results are `pass`, `fail`, `inconclusive`, and `not_applicable`.

Allowed scientific dispositions are:

- `supports_claim`
- `weakens_claim`
- `falsifies_claim`
- `inconclusive`
- `diagnostic_only`

Technical completion, verification approval, and scientific disposition are independent dimensions. A correctly executed experiment that falsifies a claim may be approved as a completed work item.

## Lineage

Allowed relations are:

- `baseline`
- `replication`
- `ablation`
- `parameter_variation`
- `negative_control`
- `sensitivity`
- `alternative_hypothesis`
- `technical_retry`

`baseline` has no parent. `technical_retry`, `ablation`, `parameter_variation`, and `sensitivity` require a parent run. Other non-baseline runs without a parent require a substantive `parent_rationale`. Parent runs must belong to the same paper identity; technical retries must use the same block.

`pivot` is deliberately not a lineage relation. D3-D4 changes remain governed by the research commitment contract.

Use `harness_runtime.py experiment-lineage` to derive a lineage view from episodes. The view is not another canonical artifact.

## Gate-conditioned scheduling

Ordinary dependencies express structural order. Activation conditions express scientific permission to continue.

```json
{
  "activation_conditions": [
    {
      "predecessor_work_item_id": "WI-B1",
      "gate_id": "G1",
      "allowed_results": ["pass"]
    }
  ]
}
```

The predecessor must also be listed as a dependency. A queued item becomes ready only when all dependencies are completed and every activation condition matches the predecessor's verified gate result.

A completed predecessor with a failed or inconclusive gate does not unlock a pass-conditioned downstream item. This prevents technical completion from being substituted for scientific success.

## Verification

For an approved experiment episode, the verifier records exactly the submitted gate result and scientific disposition:

```bash
python scripts/harness_runtime.py --root <suite> verify WI-B1 \
  --decision approve \
  --gate-result G1=fail \
  --scientific-disposition falsifies_claim \
  --evidence "Run and result artifact inspected." \
  --actor research-pipeline-planner
```

Approval establishes that the declared work item was completed and inspected. It does not convert a failed gate into a passing one or establish scientific validity beyond the declared evidence class.
