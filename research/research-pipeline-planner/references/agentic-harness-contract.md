# Agentic Research Harness Contract

Use this contract for orchestrated research work that spans stages, sessions, tools, or agents. Keep one-off standalone tasks lightweight. The harness is a control plane around stage skills: it owns state, work selection, transition authority, recovery, and observability; stage skills remain specialized workers.

## Design basis

The contract follows current harness-engineering practice:

- keep repository-local, versioned knowledge as the system of record and use a short map for progressive disclosure;
- externalize state so runs can resume after context loss, interruption, or sandbox replacement;
- make incremental progress on one bounded work item at a time and leave a clean handoff artifact;
- use an append-only event log plus snapshots for replay and recovery;
- permit completion only through verifier-backed state transitions;
- separate harness state and credentials from model-generated execution environments;
- trace actions, failures, decisions, and interventions across the full trajectory rather than scoring only the final output;
- turn harness changes into falsifiable, reversible changes with predicted effects and later evaluation;
- run recurring entropy audits so stale instructions, duplicated artifacts, and bad patterns do not accumulate.

## Control-plane artifacts

| Artifact | Authority | Purpose |
| --- | --- | --- |
| `harness-events.jsonl` | canonical | append-only, hash-chained transition and observation log |
| `HARNESS_STATE.json` | projection | current scheduler state; rebuildable from the event log |
| `work-items.json` | projection | work definitions and lifecycle state; rebuildable from the event log |
| `episodes/` | canonical evidence | one worker episode package per submitted attempt |
| `checkpoints/` | recovery aid | resumable snapshots tied to checkpoint events |
| `research-brief.md` | canonical intent | project frame, success conditions, constraints, and harness policy |
| `artifact-index.md` | canonical map | paths and authority status for project artifacts |
| `task-board.md` | human-readable view | optional summary; never the scheduling source of truth |
| `decision-log.md` | human-readable rationale | consequential decisions mirrored by machine events |

Do not hand-edit `HARNESS_STATE.json` or dynamic fields in `work-items.json`. Use `scripts/harness_runtime.py`; if projections drift, run `replay` and inspect the event that caused the divergence.

## Single-writer state machine

The harness runtime is the single writer for machine state. Work-item states are:

`queued -> ready -> running -> awaiting_verification -> completed`

Alternative transitions:

- `awaiting_verification -> ready` after `revise`, subject to the attempt budget;
- `running -> ready` after a retryable failure with attempts remaining;
- `running` or `awaiting_verification -> blocked` after a non-retryable failure, exhausted budget, or verifier block;
- any not-yet-completed item may be explicitly cancelled by a future runtime extension, but cancellation must remain in the event log.

Only one work item is active by default. Increase concurrency only when work items have disjoint write scopes or the executor provides isolation and conflict handling.

## Work-item contract

The planner must freeze one bounded work item before a worker starts. Each item carries:

- stable `work_item_id`;
- stage and `owner_skill`;
- exact objective;
- input artifacts and a minimal `context_manifest`;
- expected output artifacts;
- verifier-readable acceptance checks with stable IDs;
- dependencies;
- attempt and usage budgets;
- declared permission policy and write scope;
- predecessor failures;
- evidence class.

Use the context manifest as an allowlist for progressive disclosure. Do not dump the full project history into every worker context. Add a source only when it is needed to execute or verify the current objective.

Permission fields are declarations, not proof of enforcement. The external executor must enforce sandboxing, filesystem boundaries, network policy, secrets handling, and human approval. Keep credentials out of worker context and model-generated compute environments.

## Worker session protocol

For every orchestrated worker session:

1. Read `HARNESS_STATE.json`, the assigned work item in `work-items.json`, and only the context-manifest artifacts needed for the task.
2. Confirm that the item is `running`, the objective is unchanged, dependencies are complete, and the owner skill matches.
3. Reproduce or verify the starting state before changing artifacts when the task depends on existing behavior.
4. Work incrementally toward the acceptance checks. Do not broaden the objective without a new work item.
5. Record material observations, decisions, tool failures, and scope changes with `harness_runtime.py record`.
6. Create a checkpoint before risky, expensive, or context-boundary operations.
7. Leave outputs in the declared write scope and do not silently modify tests, gates, or acceptance checks to obtain a pass.
8. Write one episode JSON file for the attempt and submit it. The worker requests a transition but cannot approve its own work.

## Episode package

Each submitted attempt must use this shape:

```json
{
  "schema_version": "1.0",
  "episode_id": "EP-WI-001-A1",
  "work_item_id": "WI-001",
  "attempt": 1,
  "owner_skill": "research-idea-discovery",
  "objective": "Frozen objective copied exactly from the work item",
  "inputs_used": ["research-brief.md"],
  "actions": ["high-signal action summary"],
  "tool_calls": [
    {
      "tool": "web search",
      "purpose": "verify current primary literature",
      "result": "success",
      "evidence": "search log path or citation"
    }
  ],
  "artifacts": ["ideation/selected-idea.md"],
  "verification": [
    {
      "check_id": "AC1",
      "result": "pass",
      "evidence": "specific artifact location or test output"
    }
  ],
  "failures": [],
  "assumptions": [],
  "observed_usage": {
    "max_tool_calls": 7
  },
  "outcome": "completed",
  "transition_request": "approve",
  "summary": "What changed, what remains, and why the requested transition is justified."
}
```

Allowed outcomes are `completed`, `partial`, and `failed`. Allowed transition requests are `approve`, `revise`, and `block`.

A completed episode must list at least one artifact and provide passing, evidence-bearing verification for every acceptance check. Structural episode validation does not establish scientific validity; it establishes traceability and completeness of the submitted evidence package.

## Verifier protocol

The verifier must be distinct from the worker role, even when the same underlying agent performs both sequentially. Disclose self-review and do not call it independent unless context, data, implementation, evaluation, and advancement authority are materially separated.

Before approving:

1. Re-read the frozen work item and acceptance checks.
2. Inspect the submitted artifacts and evidence rather than trusting the worker summary.
3. Re-run deterministic checks when feasible.
4. Confirm that failures, skipped cases, nulls, retries, and deviations are preserved.
5. Confirm budget and permission-policy compliance from the available trace.
6. Apply the epistemic-assurance contract when the transition promotes evidence.
7. Record `approve`, `revise`, or `block` with concrete verifier evidence.

The worker cannot mutate its own acceptance checks after starting. A changed objective, selection rule, metric, or gate requires a new or revised work item and an event explaining the change.

## Checkpoint and recovery protocol

- Create checkpoints at context-window boundaries, before expensive runs, before destructive edits, and before requesting human input.
- Keep side effects before a resumable interruption idempotent or explicitly recorded so replay does not duplicate them.
- Treat `harness-events.jsonl` as authoritative. Run `replay` to rebuild state after interrupted writes or manual projection drift.
- On restart, read the latest state, event tail, active work item, checkpoint, and episode before taking action.
- Never infer completion from the absence of work or a polished final artifact.

## Failure and escalation protocol

Classify failures at least as:

- specification or acceptance ambiguity;
- missing context or inaccessible source;
- tool or connector failure;
- permission or approval boundary;
- execution or resource failure;
- verification failure;
- scientific or evidential failure;
- harness defect.

Retry only when the failure is plausibly transient or the next attempt changes a documented condition. Repeating the same action without a changed hypothesis is not recovery. Respect attempt budgets; after exhaustion, block the item or create an explicit escalation item.

Pause and request human judgment when:

- the next action is irreversible or consequential and approval was not pre-authorized;
- the objective or acceptance contract is materially ambiguous;
- required credentials or sensitive data would enter worker context;
- evidence classes or route decisions depend on normative judgment not encoded in the work item;
- the harness cannot enforce a declared boundary.

## Observability and harness evolution

Capture three layers:

- **component observability**: every editable prompt, policy, schema, script, and tool configuration has a file-level representation and version history;
- **experience observability**: episode packages distill the trajectory while preserving links to detailed evidence;
- **decision observability**: every harness change states a predicted effect, affected tasks, risk, rollback path, and later measured outcome.

Evaluate the system as `model + harness + environment`, not the model alone. Track at minimum:

- task and acceptance-check success;
- verifier reversals and false completions;
- retries, blocked items, and failure attribution;
- tool calls, elapsed time, and cost or token proxies when available;
- permission-boundary and information-flow violations;
- recovery success after interruption;
- context volume and stale-context rate;
- cross-model and cross-task transfer of harness changes.

Do not optimize the harness against a single visible benchmark without a held-out evaluation set and change log. Every harness edit should be reversible and evaluated against predicted outcomes.

## Entropy audit

Run periodic maintenance work items to:

- find stale or contradictory instructions;
- detect duplicated schemas, templates, and sources of truth;
- identify dead work items, orphan artifacts, and unresolved predecessor failures;
- compact large context manifests into indexed references;
- promote repeated review feedback into executable checks;
- remove obsolete workarounds after the underlying defect is fixed;
- verify that docs describe actual runtime behavior.

Entropy cleanup is ordinary harness work and must use the same work-item, episode, and verifier protocol.

## Runtime commands

Typical lifecycle:

```bash
python scripts/harness_runtime.py --root <suite> add \
  --work-item-id WI-001 \
  --stage ideation \
  --owner-skill research-idea-discovery \
  --objective "Generate and select one grounded research idea" \
  --acceptance-check "The selected claim is falsifiable" \
  --acceptance-check "Selection history and negative evidence are preserved" \
  --context research-brief.md \
  --expected-artifact ideation/selected-idea.md \
  --write-scope ideation/

python scripts/harness_runtime.py --root <suite> start WI-001 \
  --actor research-idea-discovery

python scripts/harness_runtime.py --root <suite> submit WI-001 \
  --episode <suite>/episodes/EP-WI-001-A1.json \
  --actor research-idea-discovery

python scripts/harness_runtime.py --root <suite> verify WI-001 \
  --decision approve \
  --evidence "Acceptance checks re-run; see verification log." \
  --actor research-pipeline-planner
```

Use `record`, `checkpoint`, `fail`, `pause`, `resume`, `replay`, and `status` for observations, recovery, and control.

## Compatibility

Legacy suite packs remain valid under `validate_research_pack.py --profile legacy` or automatic legacy detection. New orchestrated packs initialize the harness by default. Do not claim that a legacy pack has durable execution, replayable transitions, or verifier-backed completion merely because its directory layout validates.
