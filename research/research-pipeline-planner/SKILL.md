---
name: research-pipeline-planner
description: Coordinate research as either a standalone staged planning pass or a durable orchestrated multi-skill workflow with shared artifacts, explicit work items, verifier-backed transitions, checkpoints, replay, observability, stage gates, and evidence assurance. Use when asked to scope a research direction, inspect existing research artifacts, choose the next research stage, create a research brief or task board, coordinate a reusable research workflow, build a research roadmap or agenda, organize a research repo, turn notes into a phase plan, define milestones, decide what to do next, or coordinate literature, ideation, novelty, experiments, auditing, review, paper planning, and rebuttal work.
---

# Research Pipeline Planner

## Quick start

1. Inspect the current project and harness state before asking broad reset questions.
2. Use this skill as the default first pass for project-level sequencing, persistent coordination, or work spanning two or more research stages.
3. Stay standalone for a direct one-stage task; use orchestrated mode when work must survive context loss, retries, sessions, tools, or agent handoffs.
4. In orchestrated mode, initialize the harness with `scripts/init_research_pack.py`, then use `scripts/harness_runtime.py` as the only writer for work-item and run state.
5. Freeze one bounded work item with explicit inputs, outputs, acceptance checks, permissions, budgets, dependencies, predecessor failures, and evidence class.
6. Run the assigned stage skill as a worker, require an episode package, and authorize transition only after verifier inspection.
7. Apply `references/epistemic-assurance-contract.md` to any evidence promotion and `references/agentic-harness-contract.md` to runtime control.

## Routing triggers

Prefer this skill before a sibling stage skill when the user asks for a research roadmap, research agenda, project plan, phase plan, milestones, what to do next, repo organization, notes-to-plan conversion, or coordination across literature review, idea discovery, novelty review, experiments, results audit, paper planning, review, and rebuttal.

Do not force this skill for a clear one-stage request unless the user asks for persistent state, resumability, repeated execution, multiple agents, or cross-stage control.

## Modes

### Standalone mode

- Work from the prompt and available artifacts without requiring a suite root.
- Keep the workflow lightweight and directly invoke the relevant stage skill.
- Do not claim durable execution, replay, independence, or verifier-backed completion.

### Orchestrated mode

- Follow `references/agentic-harness-contract.md` and `references/suite-contract.md`.
- Treat `harness-events.jsonl` as canonical machine history; `HARNESS_STATE.json` and `work-items.json` are replayable projections.
- Use `scripts/harness_runtime.py`; do not hand-edit dynamic machine state.
- Keep one active work item by default. Increase concurrency only with disjoint write scopes or external isolation and conflict handling.
- Treat stage skills as bounded workers. The planner owns scheduling and transition authority, not every stage's substantive work.
- Keep `artifact-index.md` current, but never use Markdown status alone as scheduling authority.
- Preserve evidence class, selection history, predecessor failures, and negative evidence across handoffs.

## Input contract

- Minimum: topic or problem, current state, and desired outcome.
- Prefer: intended audience, success criteria, constraints, deadlines, budget, existing artifacts, requested evidence class, known predecessor failures, approval boundaries, and tool/data permissions.
- For an existing suite, inspect `HARNESS_STATE.json`, `work-items.json`, the event-log tail, active episode, checkpoints, and artifact index before proposing work.

## Hard stops

- Stop if the objective is too vague to define a verifier-readable work item.
- Stop if critical constraints, permissions, or acceptance criteria are missing and execution could cause substantial waste or consequential side effects.
- Do not advance from prose, file presence, a worker's self-report, or a validator pass alone.
- Do not let a worker change its frozen objective, acceptance checks, selection rule, metric, or gate after starting; create or revise the work item and record an event.
- Do not retry an unchanged failed action without a documented changed hypothesis or transient-failure basis.
- Do not call same-process verification independent; disclose self-review.
- Do not promote exploratory or outcome-informed evidence because the artifact is polished, internally consistent, structurally valid, or harness-complete.
- Stop confirmatory or high-stakes promotion when the decision contract is incomplete, failure states are omitted, hidden truth leaks, independence is nominal, or predecessor failures lack evidence-backed disposition.

## Workflow

### 1) Inspect and reconstruct state

- Distinguish no structured artifacts, legacy suite, harness-backed suite, and standalone stage artifacts.
- For a harness suite, run:

```bash
python scripts/harness_runtime.py --root <suite> replay
python scripts/harness_runtime.py --root <suite> status
```

- Identify active work, blocked items, attempts, latest checkpoint, unverified episodes, unresolved predecessor failures, and projection drift.
- Never infer completion from absence of visible work or a polished output.

### 2) Choose the operating mode

- Stay standalone for a direct answer or one-off stage.
- Initialize orchestrated mode when multiple stages need stable handoffs, long-running execution, resumability, traceability, retries, approvals, or agent delegation.
- Create new harness packs by default; use `--legacy` only for compatibility testing.

### 3) Freeze one bounded work item

Use `harness_runtime.py add` and include:

- stable work-item ID;
- stage and owner skill;
- exact objective;
- minimal context manifest;
- expected output artifacts;
- acceptance checks with stable IDs;
- dependencies;
- attempt and tool-call budgets;
- permission policy and write scope;
- predecessor failures;
- evidence class.

Prefer one next blocking decision over a speculative long queue. Context manifests are allowlists; do not dump the full project history into every worker.

### 4) Start and supervise the worker episode

- Start through the runtime to create the attempt and idempotency key.
- Require the worker to read only assigned context, confirm dependencies and objective, work incrementally, preserve failures, and write only inside declared scope.
- Record material observations and tool failures.
- Checkpoint before expensive runs, destructive edits, external writes, approval boundaries, and context-window transitions.
- Keep secrets and credentials outside worker context and model-generated environments.

### 5) Submit a structured episode

The worker must write an episode JSON matching `references/agentic-harness-contract.md` and submit it with `harness_runtime.py submit`.

A completed episode must:

- point to existing artifacts;
- preserve failures and deviations;
- provide passing, evidence-bearing results for every acceptance check;
- request `approve`, `revise`, or `block`;
- remain within budgets and permissions.

Structural episode validity establishes traceability, not scientific correctness.

### 6) Verify and authorize transition

- Re-read the frozen work item and inspect the actual artifacts.
- Re-run deterministic checks where feasible.
- Confirm failure accounting, permission compliance, selection history, and evidence class.
- Invoke `research-results-auditor` when experimental outputs determine advancement.
- Apply the assurance contract to evidence promotion.
- Record `approve`, `revise`, or `block` through the runtime with concrete evidence.
- A worker cannot approve its own transition. Sequential self-review is allowed only when disclosed and must not be described as independent.

### 7) Recover, retry, or escalate

- Classify failures as specification, missing context, tool/connector, permission, execution/resource, verification, scientific/evidential, or harness defects.
- Retry only plausibly transient or changed-condition failures within the attempt budget.
- Use the same idempotency key for replay of the same logical attempt; use a new attempt when inputs or policy change.
- Preserve all attempts and failures in the event log.
- Pause for human judgment at irreversible actions, ambiguous acceptance contracts, sensitive-data boundaries, normative evidence-class decisions, or unenforceable permissions.

### 8) Evaluate and maintain the harness

Track task success, verifier reversals, false completion, retries, blocked work, tool usage, permission violations, recovery after interruption, context volume, stale context, and cross-task transfer.

Every harness change must state its predicted effect, affected tasks, risk, rollback path, and evaluation result. Maintain regression cases for clean transition, missing artifact, retry, interruption/resume, malformed episode, blocked evidence promotion, predecessor-failure carry-forward, and event completeness.

Run recurring entropy-audit work items to remove stale instructions, duplicate schemas, orphan artifacts, dead work, and obsolete workarounds.

## References

- `references/agentic-harness-contract.md`
- `references/epistemic-assurance-contract.md`
- `references/suite-contract.md`
- `references/stage-gates.md`
- `references/review-stage-contract.md`
- `references/research-brief-template.md`
- `references/task-board-template.md`
- `references/decision-log-template.md`
- `references/tabmol-ddi-ood-adapter.md`

## Scripts

- `scripts/init_research_pack.py`: initialize a harness-backed suite by default; `--legacy` creates the compatibility layout.
- `scripts/harness_runtime.py`: single-writer event-sourced runtime for work items, episodes, verification, checkpoints, pause/resume, retries, replay, and status.
- `scripts/validate_research_pack.py`: validate legacy or harness profiles, including event-chain integrity and replayed projection consistency.
