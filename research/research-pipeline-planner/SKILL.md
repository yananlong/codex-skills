---
name: research-pipeline-planner
description: Coordinate research as a staged, evidence-gated workflow with durable state, paper-level commitment, explicit work items, verifier-backed transitions, checkpoints, replay, observability, and controlled pivots. Use when asked to scope a research direction, inspect existing research artifacts, choose what to do next, create a research roadmap, coordinate literature, ideation, novelty, experiments, auditing, review, paper planning, or prevent a project from drifting between paper identities.
---

# Research Pipeline Planner

## Quick start

1. Inspect the current project, harness state, and `research-commitment.json` before asking broad reset questions.
2. Use this skill for project-level sequencing or work spanning two or more research stages.
3. Initialize orchestrated mode with `scripts/init_research_pack.py`; use `scripts/harness_runtime.py` as the only writer for work-item and run state.
4. Keep one active paper identity and one active work item by default.
5. Freeze the paper identity with `references/research-commitment-contract.md` before moving from exploration into a paper-bearing route.
6. Freeze each work item with explicit inputs, outputs, acceptance checks, permissions, budgets, dependencies, predecessor failures, evidence class, and relation to the commitment contract.
7. Authorize transitions only after verifier inspection, applying `references/stage-gates.md`, `references/epistemic-assurance-contract.md`, and the commitment contract.
8. Treat D3-D4 changes as pivot requests, not ordinary revisions.

## Modes

### Standalone mode

- Use for one-off sequencing or a single-stage task without durable state.
- Do not claim replay, independent verification, durable commitment enforcement, or verifier-backed completion.

### Orchestrated mode

- Follow `references/agentic-harness-contract.md` and `references/suite-contract.md`.
- Treat `harness-events.jsonl` as canonical machine history; `HARNESS_STATE.json` and `work-items.json` are replayable projections.
- Treat `research-commitment.json` as canonical paper-level intent.
- Use `scripts/harness_runtime.py`; do not hand-edit dynamic machine state.
- Keep one active work item unless write scopes and isolation are demonstrably disjoint.
- Treat stage skills as bounded workers. The planner owns scheduling, transition authority, and D3-D4 pivot authorization.

## Input contract

- Minimum: topic or problem, current state, and desired outcome.
- Prefer: intended audience, success criteria, constraints, deadline, budget, existing artifacts, requested evidence class, known predecessor failures, approval boundaries, and tool/data permissions.
- For an existing suite, inspect `research-commitment.json`, `HARNESS_STATE.json`, `work-items.json`, the event-log tail, active episode, checkpoints, and artifact index before proposing work.

## Hard stops

- Stop if the objective is too vague to define a verifier-readable work item.
- Stop if a committed project lacks a valid commitment contract.
- Do not advance from prose, file presence, worker self-report, validator success, or polished artifacts alone.
- Do not let a worker change its frozen objective, acceptance checks, selection rule, metric, gate, or paper identity after starting.
- Do not authorize conceptual reconsideration before the declared next mandatory evidence artifact, unless a recorded pivot trigger or kill condition has fired.
- Do not enact D3-D4 changes without an explicit pivot request and planner authorization.
- Do not retry an unchanged failed action without a changed hypothesis or transient-failure basis.
- Do not call same-process verification independent.
- Do not promote exploratory or outcome-informed evidence because artifacts are complete or internally consistent.

## Workflow

### 1) Inspect and reconstruct state

- Distinguish unstructured work, legacy suite, harness-backed suite, and standalone stage artifacts.
- In harness mode, replay and inspect state with `harness_runtime.py`.
- Identify the active paper identity, active work item, blocked items, attempts, checkpoint, unresolved predecessor failures, and unverified episodes.
- Classify any observed identity change as D0-D4.

### 2) Establish or validate paper identity

- During exploration, allow multiple candidates but preserve selection history and rejected ideas.
- Before commitment, populate `research-commitment.json` with the main question, central object, contribution class, minimum publishable claim, primary evidence obligation, next mandatory evidence artifact, permitted refinements, pivot triggers, kill conditions, and successor policy.
- Move to `committed` only when these fields are concrete and the literature assurance is proportionate to the novelty or priority claims being relied upon.
- After commitment, default new alternatives to the successor policy.

### 3) Freeze one bounded work item

Use `harness_runtime.py add` and include:

- stable work-item ID;
- stage and owner skill;
- exact objective;
- minimal context manifest;
- expected artifacts;
- acceptance checks with stable IDs;
- dependencies;
- attempt and tool-call budgets;
- permission policy and write scope;
- predecessor failures;
- evidence class;
- commitment paper ID, identity version, and whether the work produces the next mandatory evidence artifact.

Prefer one next blocking decision over a speculative queue.

### 4) Run and supervise the worker

- Require the worker to preserve the frozen objective and commitment identity.
- Record material observations, failures, selection changes, and any apparent D3-D4 drift.
- Checkpoint before expensive runs, destructive edits, external writes, approval boundaries, and context transitions.
- Keep secrets outside worker context.

### 5) Submit and verify an episode

- Require a structured episode package matching `references/agentic-harness-contract.md`.
- Inspect actual artifacts and rerun deterministic checks where feasible.
- Confirm acceptance checks, failure accounting, permission compliance, selection history, evidence class, and identity consistency.
- Invoke `research-results-auditor` when experimental outputs determine advancement.
- Record `approve`, `revise`, `block`, `pivot-request`, or `park-successor` with concrete evidence.

### 6) Apply transition gates

- Use `references/stage-gates.md` for stage-specific decisions.
- D0-D2 changes may proceed when documented.
- D3 requires a pivot request covering fatal defect, switching cost, discarded evidence, new literature and validation burden, and successor-project feasibility.
- D4 closes or parks the current lineage and initializes a new paper ID.
- A worker cannot approve its own transition; self-review must be disclosed.

### 7) Recover, retry, stop, or split

- Classify failures as specification, missing context, tool, permission, execution, verification, scientific, evidential, identity-drift, or harness defects.
- Retry only changed-condition or plausibly transient failures within budget.
- Preserve failed attempts and negative evidence.
- Prefer `submit`, `split`, `park`, or `kill` over indefinite conceptual expansion once the mandatory evidence route is exhausted.

### 8) Maintain the suite

Track task success, verifier reversals, false completion, retries, blocked work, tool usage, permission violations, identity-drift events, pivot requests, late literature omissions, recovery after interruption, context volume, and cross-task transfer.

Every suite change must state its predicted effect, affected tasks, risk, rollback path, and evaluation result. Maintain regression cases for clean transition, missing artifact, retry, interruption/resume, malformed episode, blocked evidence promotion, predecessor-failure carry-forward, unapproved D3-D4 drift, and literature recall failure.

## References

- `references/research-commitment-contract.md`
- `references/research-commitment.schema.json`
- `references/agentic-harness-contract.md`
- `references/epistemic-assurance-contract.md`
- `references/suite-contract.md`
- `references/stage-gates.md`
- `references/review-stage-contract.md`
- `references/research-brief-template.md`
- `references/task-board-template.md`
- `references/decision-log-template.md`

## Scripts

- `scripts/init_research_pack.py`: initialize a harness-backed suite and paper-commitment artifact.
- `scripts/harness_runtime.py`: single-writer event-sourced runtime for work items, episodes, verification, checkpoints, retries, replay, and status.
- `scripts/validate_research_pack.py`: validate suite layout, commitment contract, event-chain integrity, replayed projections, and evidence references.
