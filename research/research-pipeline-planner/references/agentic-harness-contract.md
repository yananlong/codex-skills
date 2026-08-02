# Agentic Research Harness Contract

Use this contract for orchestrated research work spanning stages, sessions, tools, or agents. Keep one-off standalone tasks lightweight. The repository runtime is a local control plane for state, work selection, transition recording, recovery, and trace validation; it is not an authenticated executor, an external append-only ledger, or an isolation boundary.

## Assurance boundary

The runtime can establish these repository-local properties:

- events are schema-checked, sequentially identified, hash-chained, and preflighted before append;
- state and work-item projections can be reconstructed from accepted events;
- one work item is active by default;
- objectives, acceptance checks, expected artifacts, and declared write scopes remain frozen in the event history;
- submitted episode files and declared artifacts are digest-anchored until verification;
- checkpoint identifiers are path-safe, checkpoint files are no-overwrite through the runtime, and checkpoint contents are digest-anchored;
- declared attempt and tool-call usage is checked against configured budgets;
- same-role verification must be explicitly marked as self-review;
- experiment work may be bound to a frozen claim map, run block, commitment identity, and decision gate;
- declared experiment input and evaluator paths can be digest-compared at start and submission;
- gate-conditioned dependencies can prevent a downstream experiment from becoming ready after a disallowed predecessor result;
- experiment lineage can be reconstructed from submitted episode records.

The runtime cannot by itself establish:

- authenticated human, agent, or role identity;
- undisclosed filesystem, network, secret, data, context, or tool activity;
- process, container, or network isolation;
- externally anchored immutability or non-repudiation;
- semantic validity, scientific validity, or material independence;
- that undeclared inputs, evaluator state, or execution context remained unchanged.

An external executor must supply and record evidence for those stronger properties. Never infer them from actor labels, environment flags, self-reported usage, local hashes, start/submission digest equality, or successful structural validation.

## Control-plane artifacts

| Artifact | Authority | Purpose |
| --- | --- | --- |
| `harness-events.jsonl` | canonical local history | runtime-appended, hash-chained transition and observation records; locally mutable outside the runtime |
| `HARNESS_STATE.json` | projection | current scheduler state; rebuildable from events |
| `work-items.json` | projection | bounded work definitions and lifecycle state; rebuildable from events |
| `episodes/` | submitted evidence | one digest-anchored worker episode package per attempt |
| `checkpoints/` | recovery aid | no-overwrite, digest-anchored local snapshots |
| `research-brief.md` | canonical intent | project frame, success conditions, constraints, and harness policy |
| `artifact-index.md` | canonical map | paths and authority status for project artifacts |
| `task-board.md` | human-readable view | optional summary; never scheduling authority |
| `decision-log.md` | human-readable rationale | consequential decisions mirrored by events |

Do not hand-edit projections. Use `scripts/harness_runtime.py`; if projections drift, run `replay` and inspect the event history. When external immutability matters, mirror or anchor the event chain in an independently controlled append-only system.

## State machine

The runtime supports:

`queued -> ready -> running -> awaiting_verification -> completed`

Alternative transitions include:

- `awaiting_verification -> ready` after `revise`, subject to the attempt budget;
- `running -> ready` after a retryable failure with attempts remaining;
- an incomplete item to `blocked` after a non-retryable failure, exhausted budget, or verifier block.

Events are applied to a copied reconstructed state before the canonical log is appended. A rejected transition must not alter the event log. Aggregate run status is derived from work-item state and pause state rather than trusted as an independent source of truth.

Only one item is active by default. Increase concurrency only when an external executor supplies isolation and conflict handling or the write scopes are demonstrably disjoint.

For ordinary work, completed dependencies make a queued item ready. An experiment item with `activation_conditions` additionally requires the predecessor's latest verified gate result to be allowed. Technical predecessor completion therefore does not substitute for scientific gate success.

## Work-item contract

Freeze one bounded item before work starts. Each item carries:

- stable `work_item_id`, stage, and declared `owner_skill`;
- exact objective;
- declared input/context manifest;
- expected output artifacts;
- verifier-readable acceptance checks with stable IDs;
- dependencies;
- attempt and declared usage budgets;
- declared permission policy and write scope;
- predecessor failures;
- evidence class;
- `enforcement_scope`, which defaults to `repository_validation_only`.

An experiment-bound work item may additionally carry:

- an `experiment_binding` with claim-map, run-block, and commitment paths plus digests;
- one block ID, decision gate, paper ID, and identity version;
- the block's declared inputs, evaluator artifacts, required outputs, claim IDs, and allowed lineage relations;
- `activation_conditions` connecting predecessor work-item gates to allowed results.

The binding is created from the existing experiment-plan artifacts. It is not a second execution-plan authority. See `experiment-execution-binding.md`.

Context manifests, permission policies, actor labels, write scopes, and usage records are declarations unless an external executor supplies enforcement traces. The repository runtime validates the declared episode against them but cannot detect omitted activity.

## Worker session protocol

For every orchestrated worker session:

1. Read the current state, assigned item, and only the context needed for the objective.
2. Confirm that the item is `running`, dependencies are complete, and the declared owner label matches.
3. Reproduce or inspect relevant starting behaviour before changing artifacts.
4. Work toward the frozen acceptance checks without broadening the objective.
5. Record material observations, failures, and scope changes.
6. Checkpoint before risky, expensive, destructive, or interruption-sensitive operations.
7. Leave outputs in the declared write scope and do not weaken tests, gates, or acceptance checks to obtain a pass.
8. Write one episode JSON file under `episodes/` and request `approve`, `revise`, or `block`.

For experiment-bound work, also preserve the frozen block and commitment identity, use a stable run ID, record lineage, retain negative results, and distinguish the gate result from technical completion.

A worker may later perform self-review only when the same-role condition is explicitly disclosed with `--self-review`. This is not independent verification.

## Episode contract

Required episode fields are:

```json
{
  "schema_version": "1.0",
  "episode_id": "EP-WI-001-A1",
  "work_item_id": "WI-001",
  "attempt": 1,
  "owner_skill": "research-idea-discovery",
  "objective": "Frozen objective copied exactly",
  "artifacts": ["ideation/selected-idea.md"],
  "verification": [
    {"check_id": "AC1", "result": "pass", "evidence": "specific evidence"}
  ],
  "failures": [],
  "tool_calls": [],
  "observed_usage": {"max_tool_calls": 0},
  "outcome": "completed",
  "transition_request": "approve",
  "summary": "What changed and what remains."
}
```

Rules:

- outcomes are `completed`, `partial`, or `failed`;
- transition requests are `approve`, `revise`, or `block`;
- `completed` and `approve` must occur together;
- a failed episode must record at least one failure object with substantive `category` and `reason` fields;
- completed episodes must include all expected artifacts and evidence-bearing passes for every acceptance check;
- declared usage budgets apply to all outcomes;
- the episode file must be a direct child of `episodes/`, its filename must match `episode_id`, and the runtime records its digest plus the digests of declared artifacts;
- approval rechecks those digests.

An experiment-bound episode also requires `experiment_run`, including:

- stable `run_id` and matching block ID;
- lineage relation, parent run, or explicit parent rationale;
- matching gate ID and result;
- scientific disposition;
- scoped claim effects;
- substantive interpretation.

Technical outcome, transition request, gate result, and scientific disposition are independent dimensions. A completed experiment may weaken or falsify the claim and still be approved as correctly executed work.

Digest continuity detects post-submission mutation of declared files. Start/submission equality for declared experiment inputs and evaluators records continuity at those control points; it does not prove that undeclared files were untouched or that a digest was externally anchored. Later legitimate plan or evaluator revisions do not retroactively rewrite an earlier submitted run because the event log retains the matched start/submission digest records.

## Verification protocol

Before approving:

1. Re-read the frozen item and acceptance checks.
2. Inspect the submitted episode and artifacts rather than trusting its summary.
3. Confirm that the episode is completed and explicitly requests approval.
4. Re-run deterministic checks where feasible.
5. Confirm that failures, skips, nulls, retries, timeouts, and deviations remain visible.
6. Treat budget, context, permission, and write-scope compliance as trace-bounded unless executor evidence exists.
7. Apply the epistemic-assurance contract when a transition promotes evidence.
8. Record concrete evidence for `approve`, `revise`, or `block`.
9. Disclose self-review; claim independence only when context, data, implementation, evaluation, and advancement authority are materially separated.

For experiment approval, the verifier must record the same gate result and scientific disposition submitted by the worker after inspecting the evidence. Approval does not convert `fail` or `inconclusive` into `pass`. Gate-conditioned downstream work becomes ready only from an allowed verified result.

The runtime validates actor labels and disclosure flags, not real-world identity or organizational independence. Replay re-enforces the same-role disclosure rule, verifier evidence, episode binding, and experiment gate/disposition consistency so command-time authorization cannot disappear from the event projection.

## Checkpoint, pause, and recovery

- Checkpoint IDs must be safe basenames and cannot overwrite an existing runtime-created checkpoint.
- The runtime records a digest of the checkpoint file and a digest of its logical snapshot.
- Paused runs reject state-changing commands other than `resume`; observations remain recordable.
- Keep side effects around interruption points idempotent or explicitly recorded.
- Use `replay` to rebuild projections after interrupted projection writes or manual drift.
- Never infer completion from the absence of work or a polished artifact.

## Failure and escalation

Classify failures as specification ambiguity, missing context, tool/connector failure, permission boundary, execution/resource failure, verification failure, scientific failure, or harness defect. Retry only when the next attempt changes a documented condition or the failure is plausibly transient. Respect attempt budgets and preserve failed attempts.

For experiment work, use `technical_retry` only for a run that repairs execution while preserving the block. Do not mislabel a technical retry as replication, independent confirmation, or a paper pivot.

Pause and seek judgment when an action is irreversible, the objective or acceptance contract is materially ambiguous, credentials or sensitive data would enter worker context, evidence promotion requires normative judgment, or the harness cannot enforce a declared boundary.

## Runtime commands

Typical lifecycle:

```bash
python scripts/harness_runtime.py --root <suite> add \
  --work-item-id WI-001 \
  --stage ideation \
  --owner-skill research-idea-discovery \
  --objective "Generate and select one grounded research idea" \
  --acceptance-check "The selected claim is falsifiable" \
  --context research-brief.md \
  --expected-artifact ideation/selected-idea.md \
  --write-scope ideation/

python scripts/harness_runtime.py --root <suite> start WI-001 \
  --actor research-idea-discovery \
  --idempotency-key WI-001-attempt-1

python scripts/harness_runtime.py --root <suite> submit WI-001 \
  --episode <suite>/episodes/EP-WI-001-A1.json \
  --actor research-idea-discovery \
  --idempotency-key WI-001-submit-A1

python scripts/harness_runtime.py --root <suite> verify WI-001 \
  --decision approve \
  --evidence "Acceptance checks re-run; see verification log." \
  --actor research-pipeline-planner
```

For experiment binding and activation examples, use `experiment-execution-binding.md`. Use `experiment-lineage` to derive the run graph without adding another canonical artifact.

Use stable explicit idempotency keys when a caller may retry after an uncertain response. Use `record`, `checkpoint`, `fail`, `pause`, `resume`, `replay`, and `status` for observation, recovery, and control.

## Compatibility and bounded verdict

Legacy directory packs and unbound work items remain structurally valid under their existing profiles. New experiment-specific fields are required only when `experiment_binding` is present. Earlier draft harness event logs may require replay or migration when the schema gains derived fields.

A passing harness validation means the declared repository artifacts, event chain, projections, dependencies, recorded digests, experiment bindings, gate records, lineage references, and event-to-episode projections are internally consistent. Every submitted episode is revalidated against the historical work-item state that preceded its event. It does not establish external immutability, authenticated execution, isolation, semantic validity, scientific validity, or independent verification.
