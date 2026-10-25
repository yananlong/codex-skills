---
name: research-pipeline-planner
description: Coordinate research as either a standalone staged planning pass or a durable orchestrated multi-skill workflow with shared artifacts, explicit work items, paper-level commitment, verifier-backed transitions, checkpoints, replay, observability, stage gates, evidence assurance, and controlled pivots. Use when asked to scope a research direction, inspect existing research artifacts, choose the next research stage, create a research brief or task board, coordinate a reusable research workflow, build a research roadmap or agenda, organize a research repo, turn notes into a phase plan, define milestones, decide what to do next, coordinate literature, ideation, novelty, experiments, auditing, review, paper planning, and rebuttal work, or prevent a project from drifting between paper identities.
---

# Research Pipeline Planner

## Route the task

Choose the smallest route that covers the request, and load only the listed files first. The rest of this skill and its references are read on demand.

| Request | Route | Load first |
| --- | --- | --- |
| "What should I do next", a milestone list, a phase plan, notes to a plan | Standalone: read the project's current-status documents, write a brief or phase plan, route to one stage skill | `references/research-brief-template.md` |
| Inspect an existing suite's state | Read-only: locate `harness-events.jsonl`, run `status`, report | `references/suite-contract.md` |
| Start or continue durable multi-stage work the user asked to make resumable | Orchestrated: commitment, work items, verifier transitions | `references/agentic-harness-contract.md`, `references/research-commitment-contract.md`, `references/stage-gates.md` |
| Bind an experiment to the harness | Orchestrated, experiment stage | `references/experiment-execution-binding.md` |
| Audit results and hand to paper planning | Orchestrated, results stage | `references/result-audit-paper-binding-contract.md` |
| A pivot, park, or paper-identity change | Orchestrated, pivot request | `references/research-commitment-contract.md` (D-classes) |
| Hill-climb one metric under a fixed budget | Not this skill: `research-experiment-plan` iteration loop mode | |

## Quick start

Choose the mode first. Use orchestrated mode only when the project already has a `harness-events.jsonl` (see workflow step 1 to locate it) or the user explicitly asks for durable state. Otherwise stay standalone.

### Standalone (default)

1. Read the project's current-status documents and any `research-commitment.json`; do not initialize a harness or require a suite root.
2. Produce the requested brief, phase plan, milestones, or next decision directly. A brief or plan is reader-facing prose: write it under the drafting contract (`writing/technical-writing-drafter/references/drafting-contract.md`) rather than drafting it and patching it later.
3. Route the next piece of work to one stage skill. When the next piece of work is manuscript or response prose, the stage skill is `technical-writing-drafter`, fed by the plan, audits, literature review, or issue board that owns the content.
4. Treat a proposed D3-D4 identity change as a question for the user, not an ordinary revision.

### Orchestrated

1. Locate the suite root that holds `harness-events.jsonl`, then inspect harness state and `research-commitment.json` before asking broad reset questions.
2. Initialize a new suite with `scripts/init_research_pack.py` (`--adopt` for an existing project), then use `scripts/harness_runtime.py` as the only writer for work-item and run state.
3. Freeze one paper identity before moving from exploration into a paper-bearing route; keep one active paper identity and one active work item by default.
4. Freeze each work item with explicit inputs, outputs, acceptance checks, permissions, budgets, dependencies, predecessor failures, evidence class, and relation to the commitment contract.
5. For experiment execution, bind the work item to one frozen claim map, run block, decision gate, and declared snapshot set using `references/experiment-execution-binding.md`.
6. Run the assigned stage skill as a bounded worker, require an episode package, and authorize transition only after verifier inspection.
7. Apply `references/epistemic-assurance-contract.md`, `references/agentic-harness-contract.md`, `references/stage-gates.md`, and `references/research-commitment-contract.md` as appropriate.
8. Treat D3-D4 identity changes as pivot requests, not ordinary revisions.

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
- Bind executable experiment work to one `run-blocks.json` block and preserve technical outcome, scientific disposition, and decision-gate result as separate dimensions.
- Keep `artifact-index.md` current, but never use Markdown status alone as scheduling authority.
- Preserve evidence class, selection history, predecessor failures, negative evidence, and commitment identity across handoffs.

## Input contract

- Minimum: topic or problem, current state, and desired outcome.
- Prefer: intended audience, success criteria, constraints, deadlines, budget, existing artifacts, requested evidence class, known predecessor failures, approval boundaries, tool/data permissions, and current commitment status.
- For an existing suite, inspect `research-commitment.json`, `HARNESS_STATE.json`, `work-items.json`, the event-log tail, active episode, checkpoints, and artifact index before proposing work.

## Hard stops

- Orchestrated: stop if the objective is too vague to define a verifier-readable work item.
- Both modes: stop if critical constraints, permissions, or acceptance criteria are missing and execution could cause substantial waste or consequential side effects.
- Orchestrated: stop a committed route if `research-commitment.json` is missing or invalid.
- Orchestrated: never run `harness_runtime.py` at a root without `harness-events.jsonl`.
- Both modes: do not advance from prose, file presence, a worker's self-report, or a validator pass alone.
- Orchestrated: do not let a worker change its frozen objective, acceptance checks, selection rule, metric, gate, or paper identity after starting; create or revise the work item and record an event.
- Both modes: do not treat technical experiment completion as scientific gate success.
- Orchestrated: do not unlock a downstream experiment solely because its predecessor completed; require its declared activation gate when one exists.
- Both modes: do not authorize conceptual reconsideration before the declared next mandatory evidence artifact unless a recorded pivot trigger or kill condition has fired.
- Both modes: do not enact D3-D4 changes without an explicit pivot request and authorization (planner authorization in orchestrated mode, the user's in standalone mode).
- Both modes: do not retry an unchanged failed action without a documented changed hypothesis or transient-failure basis.
- Both modes: do not call same-process verification independent; disclose self-review.
- Both modes: do not promote exploratory or outcome-informed evidence because the artifact is polished, internally consistent, structurally valid, or harness-complete.
- Both modes: stop confirmatory or high-stakes promotion when the decision contract is incomplete, failure states are omitted, hidden truth leaks, independence is nominal, or predecessor failures lack evidence-backed disposition.

## Workflow

### 1) Inspect and reconstruct state

- Distinguish no structured artifacts, legacy suite, harness-backed suite, and standalone stage artifacts.
- Locate suites before running anything: suites are often nested below the repo root (for example `projects/*/`, `plan/*/`, `experiments/*/`). Find them with `find . -path ./.git -prune -o \( -name harness-events.jsonl -o -name research-commitment.json \) -print`.
- Never run runtime commands at a root without `harness-events.jsonl`. `status` and `experiment-lineage` are read-only and refuse such a root; `replay` is the only command that rewrites projections.
- For a harness suite, run:

```bash
python scripts/harness_runtime.py --root <suite> status
python scripts/harness_runtime.py --root <suite> replay   # only to rewrite drifted projections
```

- Identify the active paper identity, active work, blocked items, attempts, latest checkpoint, unverified episodes, unresolved predecessor failures, projection drift, and any apparent D0-D4 identity change.
- Never infer completion from absence of visible work or a polished output.

### 2) Choose the operating mode and establish paper identity

- Stay standalone by default, including for milestone plans, phase plans, and next-step decisions.
- Use orchestrated mode only for an existing `harness-events.jsonl` or an explicit user request for durable state, such as resumable multi-stage execution, retries, approvals, or agent delegation. Spanning several sessions alone is not a reason to initialize a harness.
- Create new harness packs by default; use `--adopt` for an existing project and `--legacy` only for compatibility testing.
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

For experiment execution, also include:

- claim-map and run-block paths;
- one bound block ID and its decision gate;
- the commitment artifact;
- declared input and evaluator snapshot paths;
- required outputs;
- allowed lineage relations;
- any gate-conditioned activation rule for downstream work.

Prefer one next blocking decision over a speculative long queue. Context manifests are allowlists; do not dump the full project history into every worker.

### 4) Start and supervise the worker episode

- Start through the runtime to create the attempt and idempotency key.
- For experiment-bound work, start records digest snapshots of the declared inputs and evaluator artifacts. This is a repository-local continuity check, not an isolation claim.
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
- preserve the active paper identity or explicitly request a pivot;
- for any reader-facing prose artifact it produced, record the `prose_tells.py` summary line and the drafting-contract claim list in the episode notes, so the verifier can see that the prose was drafted under the contract rather than patched afterwards.

An experiment-bound episode must additionally record a stable run ID, lineage relation and parent, gate result, scientific disposition, scoped claim effects, and interpretation. Structural episode validity establishes traceability, not scientific correctness.

### 6) Verify and authorize transition

- Re-read the frozen work item and commitment contract, then inspect the actual artifacts.
- Re-run deterministic checks where feasible.
- Confirm failure accounting, permission compliance, selection history, evidence class, and identity consistency.
- For experiment work, verify the submitted gate result and scientific disposition exactly; approval confirms completion and inspection, not that the gate passed.
- Invoke `research-results-auditor` when experimental outputs determine advancement.
- Apply the assurance contract to evidence promotion.
- Record `approve`, `revise`, `block`, `pivot-request`, or `park-successor` with concrete evidence in the appropriate machine and human-readable records.
- A worker cannot approve its own transition. Sequential self-review is allowed only when disclosed and must not be described as independent.

### 7) Apply paper-identity and stage gates

- Use `references/stage-gates.md` for stage-specific decisions.
- Use activation conditions to distinguish structural dependency completion from scientific permission to open a later experiment.
- D0-D2 changes may proceed when documented and consistent with the contract.
- D3 requires a pivot request covering the fatal defect or fired trigger, why D0-D2 repair is insufficient, switching cost, discarded evidence, new literature and validation burden, and successor-project feasibility.
- D4 closes or parks the current lineage and initializes a new paper ID.
- Reframing, renaming, deletion, or contribution-class substitution does not resolve predecessor failures.

### 8) Recover, retry, stop, or split

- Classify failures as specification, missing context, tool/connector, permission, execution/resource, verification, scientific/evidential, identity-drift, or harness defects.
- Retry only plausibly transient or changed-condition failures within the attempt budget.
- Use the same idempotency key for replay of the same logical attempt; use a new attempt when inputs or policy change.
- Preserve all attempts, failures, negative evidence, and experiment lineage in the event log.
- Pause for human judgment at irreversible actions, ambiguous acceptance contracts, sensitive-data boundaries, normative evidence-class decisions, D3-D4 pivots, or unenforceable permissions.
- Prefer submit, split, park, or kill over indefinite conceptual expansion once the mandatory evidence route is exhausted.

### 9) Evaluate and maintain the harness

Track task success, verifier reversals, false completion, retries, blocked work, tool usage, permission violations, identity-drift events, pivot requests, late literature omissions, experiment-gate mismatches, recovery after interruption, context volume, stale context, and cross-task transfer.

Every harness change must state its predicted effect, affected tasks, risk, rollback path, and evaluation result. Maintain regression cases for clean transition, missing artifact, retry, interruption/resume, malformed episode, blocked evidence promotion, predecessor-failure carry-forward, event completeness, unapproved D3-D4 drift, literature-recall failure, failed experiment gates, and lineage replay.

Run recurring entropy-audit work items to remove stale instructions, duplicate schemas, orphan artifacts, dead work, and obsolete workarounds.

## References

- `references/research-commitment-contract.md`
- `references/research-commitment.schema.json`
- `references/agentic-harness-contract.md`
- `references/experiment-execution-binding.md`
- `references/epistemic-assurance-contract.md`
- `references/suite-contract.md`
- `references/stage-gates.md`
- `references/review-stage-contract.md`
- `references/result-audit-paper-binding-contract.md`: authority map when audited results move into paper claims; read for a results-to-paper handoff.
- `references/semantic-assurance-contract.md`: commitment-transition ledger and identity anchors; read when recording D0-D4 transitions in `commitment-transitions.json`.
- `references/prospective-evaluation-contract.md`: maintainer study protocol for evaluating the suite itself; not needed for project work.
- `references/research-brief-template.md`
- `references/task-board-template.md`
- `references/decision-log-template.md`
- `references/tabmol-ddi-ood-adapter.md`

## Scripts

- `scripts/init_research_pack.py`: initialize a harness-backed suite and an exploring paper-commitment artifact in a new directory; `--legacy` creates the compatibility layout. For an existing project without `harness-events.jsonl`, use `--adopt`: it creates only missing control files and directories, deletes and overwrites nothing, refuses if an event log exists, and records one `legacy_import` observation listing pre-existing stage directories with file digests. `--force` deletes and regenerates `task-board.md`, `artifact-index.md`, `HARNESS_STATE.json`, `work-items.json`, `harness-events.jsonl`, `episodes/`, `checkpoints/`, and `.harness.lock`; it refuses when the event log holds more than one event unless `--discard-event-history` is also passed. `--force` never deletes `research-brief.md` or `decision-log.md`; it writes `research-brief.template.md` and `decision-log.template.md` beside them. `--force --reset-stage-artifacts` also deletes every stage-output directory, and `--force --reset-commitment` also deletes `research-commitment.json`.
- `scripts/init_research_commitment.py`: initialize or explicitly replace `research-commitment.json`.
- `scripts/validate_research_commitment.py`: validate commitment structure, optional `identity_anchors`, and D3-D4 authorization records (which must name the current `to_identity_version`; legacy unversioned entries pass with a warning) without claiming scientific validity.
- `scripts/harness_runtime.py`: single-writer event-sourced runtime for work items, experiment bindings, lineage, gate-conditioned activation, episodes, verification, checkpoints, pause/resume, retries, replay, and status. `status` and `experiment-lineage` are read-only; `replay` is the only command that rewrites projections; all three refuse a root without `harness-events.jsonl`.
- `scripts/validate_semantic_assurance.py`: validate the commitment-transition ledger, literature semantics, and evidence semantics against `references/semantic-assurance-contract.md`.
- `scripts/init_prospective_evaluation.py` and `scripts/validate_prospective_evaluation.py`: maintainer tooling for prospective studies of the suite under `references/prospective-evaluation-contract.md`; not used in project work.
- `scripts/validate_research_pack.py`: validate legacy or harness profiles, commitment structure, event-chain integrity, replayed projection consistency, experiment bindings, submission snapshots, and gate/lineage references.
