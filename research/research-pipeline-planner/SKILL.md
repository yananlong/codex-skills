---
name: research-pipeline-planner
description: Coordinate research as either a standalone staged planning pass or a durable orchestrated multi-skill workflow with shared artifacts, explicit work items, paper-level commitment, verifier-backed transitions, checkpoints, replay, observability, stage gates, evidence assurance, and controlled pivots. Use when asked to scope a research direction, inspect existing research artifacts, choose the next research stage, create a research brief or task board, coordinate a reusable research workflow, build a research roadmap or agenda, organize a research repo, turn notes into a phase plan, define milestones, decide what to do next, coordinate literature, ideation, novelty, experiments, auditing, review, paper planning, and rebuttal work, or prevent a project from drifting between paper identities.
---

# Research Pipeline Planner

## Quick start

1. Inspect the current project, harness state, and `research-commitment.json` before asking broad reset questions.
2. Use this skill as the default first pass for project-level sequencing, persistent coordination, or work spanning two or more research stages.
3. Stay standalone for a direct one-stage task; use orchestrated mode when work must survive context loss, retries, sessions, tools, or agent handoffs.
4. In orchestrated mode, initialize the suite with `scripts/init_research_pack.py`, then use `scripts/harness_runtime.py` as the only writer for work-item and run state.
5. Freeze one paper identity before moving from exploration into a paper-bearing route; keep one active paper identity and one active work item by default.
6. Freeze each work item with explicit inputs, outputs, acceptance checks, permissions, budgets, dependencies, predecessor failures, evidence class, and relation to the commitment contract.
7. Run the assigned stage skill as a bounded worker, require an episode package, and authorize transition only after verifier inspection.
8. Apply `references/epistemic-assurance-contract.md`, `references/agentic-harness-contract.md`, `references/stage-gates.md`, and `references/research-commitment-contract.md` as appropriate.
9. Treat D3-D4 identity changes as pivot requests, not ordinary revisions.

## Routing triggers

Prefer this skill before a sibling stage skill when the user asks for a research roadmap, research agenda, project plan, phase plan, milestones, what to do next, repo organization, notes-to-plan conversion, or coordination across literature review, idea discovery, novelty review, experiments, results audit, paper planning, review, and rebuttal.

Do not force this skill for a clear one-stage request unless the user asks for persistent state, resumability, repeated execution, multiple agents, cross-stage control, or protection against paper-identity drift.

## Modes

### Standalone mode

- Work from the prompt and available artifacts without requiring a suite root.
- Keep the workflow lightweight and directly invoke the relevant stage skill.
- Do not claim durable execution, replay, independence, commitment enforcement, or verifier-backed completion.

### Orchestrated mode

- Follow `references/agentic-harness-contract.md` and `references/suite-contract.md`.
- Treat `harness-events.jsonl` as canonical machine history; `HARNESS_STATE.json` and `work-items.json` are replayable projections.
- Treat `research-commitment.json` as canonical paper-level intent once the project has a paper-bearing route.
- Use `scripts/harness_runtime.py`; do not hand-edit dynamic machine state.
- Keep one active work item by default. Increase concurrency only with disjoint write scopes or external isolation and conflict handling.
- Treat stage skills as bounded workers. The planner owns scheduling, transition authority, and D3-D4 pivot authorization, not every stage's substantive work.
- Keep `artifact-index.md` current, but never use Markdown status alone as scheduling authority.
- Preserve evidence class, selection history, predecessor failures, negative evidence, and commitment identity across handoffs.

## Input contract

- Minimum: topic or problem, current state, and desired outcome.
- Prefer: intended audience, success criteria, constraints, deadlines, budget, existing artifacts, requested evidence class, known predecessor failures, approval boundaries, tool/data permissions, and current commitment status.
- For an existing suite, inspect `research-commitment.json`, `HARNESS_STATE.json`, `work-items.json`, the event-log tail, active episode, checkpoints, and artifact index before proposing work.

## Hard stops

- Stop if the objective is too vague to define a verifier-readable work item.
- Stop if critical constraints, permissions, or acceptance criteria are missing and execution could cause substantial waste or consequential side effects.
- Stop a committed route if `research-commitment.json` is missing or invalid.
- Do not advance from prose, file presence, a worker's self-report, or a validator pass alone.
- Do not let a worker change its frozen objective, acceptance checks, selection rule, metric, gate, or paper identity after starting; create or revise the work item and record an event.
- Do not authorize conceptual reconsideration before the declared next mandatory evidence artifact unless a recorded pivot trigger or kill condition has fired.
- Do not enact D3-D4 changes without an explicit pivot request and planner authorization.
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

- Identify the active paper identity, active work, blocked items, attempts, latest checkpoint, unverified episodes, unresolved predecessor failures, projection drift, and any apparent D0-D4 identity change.
- Never infer completion from absence of visible work or a polished output.

### 2) Choose the operating mode and establish paper identity

- Stay standalone for a direct answer or one-off stage.
- Initialize orchestrated mode when multiple stages need stable handoffs, long-running execution, resumability, traceability, retries, approvals, or agent delegation.
- Create new harness packs by default; use `--legacy` only for compatibility testing.
- During exploration, preserve candidate, rejection, and selection history without prematurely freezing a paper.
- Before moving to `committed`, populate the main question, central object or phenomenon, contribution class, minimum publishable claim, primary evidence obligation, next mandatory evidence artifact, permitted refinements, pivot triggers, kill conditions, successor policy, and reconsideration gate.
- Require literature assurance proportionate to any novelty or priority claim used to justify commitment.
- After commitment, route attractive alternatives to the successor policy unless a declared pivot trigger or kill condition has fired.

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
- evidence class;
- paper ID and identity version when the route is committed;
- whether the work produces the next mandatory evidence artifact.

Prefer one next blocking decision over a speculative long queue. Context manifests are allowlists; do not dump the full project history into every worker.

### 4) Start and supervise the worker episode

- Start through the runtime to create the attempt and idempotency key.
- Require the worker to read only assigned context, confirm dependencies, objective, and commitment identity, work incrementally, preserve failures, and write only inside declared scope.
- Record material observations, tool failures, selection changes, and apparent D3-D4 drift.
- Checkpoint before expensive runs, destructive edits, external writes, approval boundaries, and context-window transitions.
- Keep secrets and credentials outside worker context and model-generated environments.

### 5) Submit a structured episode

The worker must write an episode JSON matching `references/agentic-harness-contract.md` and submit it with `harness_runtime.py submit`.

A completed episode must:

- point to existing artifacts;
- preserve failures and deviations;
- provide passing, evidence-bearing results for every acceptance check;
- request `approve`, `revise`, or `block`;
- remain within budgets and permissions;
- preserve the active paper identity or explicitly request a pivot.

Structural episode validity establishes traceability, not scientific correctness.

### 6) Verify and authorize transition

- Re-read the frozen work item and commitment contract, then inspect the actual artifacts.
- Re-run deterministic checks where feasible.
- Confirm failure accounting, permission compliance, selection history, evidence class, and identity consistency.
- Invoke `research-results-auditor` when experimental outputs determine advancement.
- Apply the assurance contract to evidence promotion.
- Record `approve`, `revise`, `block`, `pivot-request`, or `park-successor` with concrete evidence in the appropriate machine and human-readable records.
- A worker cannot approve its own transition. Sequential self-review is allowed only when disclosed and must not be described as independent.

### 7) Apply paper-identity and stage gates

- Use `references/stage-gates.md` for stage-specific decisions.
- D0-D2 changes may proceed when documented and consistent with the contract.
- D3 requires a pivot request covering the fatal defect or fired trigger, why D0-D2 repair is insufficient, switching cost, discarded evidence, new literature and validation burden, and successor-project feasibility.
- D4 closes or parks the current lineage and initializes a new paper ID.
- Reframing, renaming, deletion, or contribution-class substitution does not resolve predecessor failures.

### 8) Recover, retry, stop, or split

- Classify failures as specification, missing context, tool/connector, permission, execution/resource, verification, scientific/evidential, identity-drift, or harness defects.
- Retry only plausibly transient or changed-condition failures within the attempt budget.
- Use the same idempotency key for replay of the same logical attempt; use a new attempt when inputs or policy change.
- Preserve all attempts, failures, and negative evidence in the event log.
- Pause for human judgment at irreversible actions, ambiguous acceptance contracts, sensitive-data boundaries, normative evidence-class decisions, D3-D4 pivots, or unenforceable permissions.
- Prefer submit, split, park, or kill over indefinite conceptual expansion once the mandatory evidence route is exhausted.

### 9) Evaluate and maintain the harness

Track task success, verifier reversals, false completion, retries, blocked work, tool usage, permission violations, identity-drift events, pivot requests, late literature omissions, recovery after interruption, context volume, stale context, and cross-task transfer.

Every harness change must state its predicted effect, affected tasks, risk, rollback path, and evaluation result. Maintain regression cases for clean transition, missing artifact, retry, interruption/resume, malformed episode, blocked evidence promotion, predecessor-failure carry-forward, event completeness, unapproved D3-D4 drift, and literature-recall failure.

Run recurring entropy-audit work items to remove stale instructions, duplicate schemas, orphan artifacts, dead work, and obsolete workarounds.

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
- `references/tabmol-ddi-ood-adapter.md`

## Scripts

- `scripts/init_research_pack.py`: initialize a harness-backed suite and an exploring paper-commitment artifact by default; `--legacy` creates the compatibility layout. `--force` preserves stage outputs and the existing commitment, while `--force --reset-stage-artifacts` or `--force --reset-commitment` explicitly resets those scopes.
- `scripts/init_research_commitment.py`: initialize or explicitly replace `research-commitment.json`.
- `scripts/validate_research_commitment.py`: validate commitment structure and D3-D4 authorization records without claiming scientific validity.
- `scripts/harness_runtime.py`: single-writer event-sourced runtime for work items, episodes, verification, checkpoints, pause/resume, retries, replay, and status.
- `scripts/validate_research_pack.py`: validate legacy or harness profiles, commitment structure, event-chain integrity, and replayed projection consistency.
