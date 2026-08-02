# Research Suite Contract

Use this contract only when work benefits from shared cross-stage artifacts. Do not force it for one-off standalone tasks.

## Root layout

| Artifact | Canonical path | Authority | Purpose |
| --- | --- | --- | --- |
| harness event log | `./harness-events.jsonl` | canonical | runtime-appended, hash-chained local transition and observation history; not externally immutable |
| harness state | `./HARNESS_STATE.json` | projection | current scheduler state, rebuildable from events |
| work items | `./work-items.json` | projection | bounded work definitions and lifecycle state |
| episodes | `./episodes/` | canonical evidence | one digest-anchored worker-attempt package per submission |
| checkpoints | `./checkpoints/` | recovery aid | no-overwrite, digest-anchored local state snapshots |
| research brief | `./research-brief.md` | canonical intent | problem frame, constraints, success criteria, harness policy |
| task board | `./task-board.md` | human-readable view | convenience summary; not scheduling authority |
| decision log | `./decision-log.md` | human-readable rationale | consequential decisions mirrored by machine events |
| artifact index | `./artifact-index.md` | canonical map | paths, authority, and status of project artifacts |
| zotero | `./zotero/` | stage output | outputs from `research-zotero` |
| literature review | `./literature-review/` | stage output | outputs from `research-systematic-literature-review` |
| ideation | `./ideation/` | stage output | outputs from `research-idea-discovery` |
| novelty review | `./novelty-review/` | stage output | outputs from `research-novelty-review` |
| experiment plan | `./experiment-plan/` | stage output | claim map, run blocks, gates, and execution bridge from `research-experiment-plan` |
| results audit | `./results-audit/` | stage output with canonical machine record | `results-audit.json` owns audited verdicts and assurance; `results-audit.md` is the explanatory view |
| paper review | `./paper-review/` | stage output | outputs from `research-paper-review` |
| paper plan | `./paper-plan/` | stage output with canonical machine binding | `claim-evidence-bindings.json` owns manuscript support/action; Markdown plans are views |
| review loop | `./review-loop/` | stage output | outputs from `research-review-loop` |
| rebuttal | `./rebuttal/` | stage output | outputs from `research-rebuttal` |

Experiment execution adds no new root-level authority. Its frozen binding is stored in the work-item event, its run metadata is stored in the submitted episode event, and its lineage view is derived from those records.

## Operating rules

- Standalone mode may ignore this layout entirely.
- Orchestrated mode must follow `agentic-harness-contract.md`.
- Use `scripts/harness_runtime.py` as the only writer for dynamic machine state.
- Treat `harness-events.jsonl` as authoritative local history and rebuild projections with `replay` after interruption or drift. Use an external append-only store or signed anchor when external immutability is required.
- Keep one active work item by default; allow concurrency only with disjoint write scopes or external isolation and conflict handling.
- Any sibling skill may still run directly, but an orchestrated stage runs as the owner of a frozen work item and submits an episode package.
- If an artifact is produced outside the canonical path, record the actual path in `artifact-index.md` and the episode.
- Do not let task-board prose, artifact presence, a worker summary, or a Markdown claims matrix advance machine state or evidence class.
- Do not reconstruct upstream work from conversational memory when a concrete artifact or episode exists.
- Treat actor, permission, context, write-scope, usage, and declared snapshot fields as repository-validated declarations unless an external executor supplies authenticated identity and enforcement evidence.
- For experiment work, keep technical completion, verification approval, scientific disposition, and gate result separate.
- A structural dependency may establish order; a gate-conditioned activation establishes scientific permission to open a later experiment.
- Treat `results-audit.json` as the audited-evidence authority and `claim-evidence-bindings.json` as the manuscript-support authority.
- Validate the result audit before using it in a paper binding; a downstream validator does not retroactively certify an upstream stage.

## Work-item handoff map

| Need | Preferred owner skill | Minimum frozen context |
| --- | --- | --- |
| project sequencing, scheduler state, or cross-stage transition | `research-pipeline-planner` | harness state, active work item, desired outcome, existing artifacts |
| curated Zotero corpus or citation export | `research-zotero` | access method, collection/tags/query, expected export artifact |
| broad evidence gathering | `research-systematic-literature-review` | review question, scope, source constraints, expected evidence artifacts |
| bounded paper-context evidence map | `research-systematic-literature-review` | paper-review summary, contribution claim, targeted context questions |
| broad direction to grounded candidate ideas | `research-idea-discovery` | research direction, landscape or corpus, constraints, acceptance checks |
| skeptical novelty pressure test | `research-novelty-review` | concrete claim, selection history, closest-work expectations |
| decisive validation design | `research-experiment-plan` | frozen claim, evaluation goal, evidence class, predecessor failures |
| bound experiment execution | declared experiment runner | commitment, claim map, run blocks, one block ID, decision gate, declared snapshots, required outputs, lineage policy |
| deep paper critique | `research-paper-review` | concrete paper artifact or URL, review rubric, output bundle |
| result validity audit | `research-results-auditor` | commitment, source claim, result artifacts, work item, episode, verifier record, run lineage, gate result, failure ledger |
| iterative red-team review | `research-review-loop` | target artifact, prior issue state, required closure evidence |
| manuscript structuring | `research-paper-plan` | commitment, source claim map, validated result audits, theoretical/citation evidence, limitations |
| venue-aware author response | `research-rebuttal` | concrete reviews, venue rules, permitted analyses and changes |

## Experiment-stage handoff

Use `experiment-execution-binding.md` when moving from a stable experiment plan into tracked execution.

The handoff must preserve:

- commitment paper ID and identity version;
- claim-map and run-block paths plus digests;
- one block ID and its decision gate;
- expected outputs and write scope;
- declared input and evaluator snapshot paths;
- allowed lineage relations;
- any predecessor gate result required to activate the work.

The episode returns:

- stable run ID;
- block ID;
- lineage relation and parent or rationale;
- submitted gate result;
- scientific disposition;
- scoped claim effects;
- output artifacts and failures.

The verifier records the same gate result and disposition after inspection. A correctly executed negative result may complete while leaving a pass-conditioned downstream item queued.

## Result-audit and paper-plan handoff

Use `result-audit-paper-binding-contract.md` when results become manuscript evidence.

The result-audit work item must preserve:

- paper ID and identity version;
- source experiment claim ID;
- exact source run and episode digest;
- submitted and verified gate/disposition records;
- verifier decision and self-review disclosure;
- result artifact paths and digests;
- exact audit scope, requested assurance, check results, limitations, and predecessor failures;
- a run-selection rule covering every eligible run, with explicit exclusion rationales.

It returns `results-audit/results-audit.json`, whose audit IDs and bounded verdicts become the only result-audit inputs paper planning may use for empirical promotion.

The paper-plan work item must preserve:

- paper identity;
- stable paper claim IDs and source claim IDs;
- linked result-audit IDs, explicit audit exclusions, and required assurance thresholds;
- audited evidence paths and exact compatible scope;
- support status and allowed manuscript action;
- scope, limitations, missing evidence, exhibits, and citation needs.

A negative or inadequate audit must remain visible in the paper binding. Every relevant audit must be linked or explicitly excluded with a real scope difference and rationale. The paper validator must revalidate the exact audit JSON, narrative, and work-item bindings; do not bypass this by selecting only a preferred run, passing a skeletal audit object, or adding an extra Markdown claim row.

## Worker protocol

For an orchestrated stage:

1. Read the assigned work item, harness state, and only allowlisted context artifacts.
2. Confirm the item is `running`, dependencies are complete, owner skill matches, and any activation conditions were satisfied.
3. Preserve the frozen objective and acceptance checks.
4. Work only within the declared write scope and permission policy; recognise that repository validation cannot detect undisclosed external reads, writes, or tool calls.
5. For experiment work, preserve the bound block and commitment identity, use a stable run ID, and retain negative or inconclusive outcomes.
6. For result audit and paper planning, preserve source claim IDs, audit IDs, paper identity, negative evidence, and assurance boundaries.
7. Record material observations, failures, and scope changes.
8. Checkpoint before risky, expensive, destructive, or interruptible operations.
9. Write an episode package and request `approve`, `revise`, or `block`.
10. Do not present self-review as independent verification. When the same actor label verifies its own work, pass `--self-review` and disclose the limitation.

## Collaboration rules

- Standalone mode remains multi-skill friendly.
- Orchestrated collaboration must be represented as separate work items or explicit bounded tool/handoff calls inside an episode.
- Context passed to another skill or agent must be filtered through the work item's context manifest.
- A role name does not establish independence. Record actual separation across context, data, implementation, evaluation, and authority.
- Keep credentials and secrets outside worker context and generated execution environments.
- Do not use experiment lineage as a substitute for paper-identity history; D3-D4 remains governed by `research-commitment.json`.
- Do not use a paper claim binding to rewrite a source result audit. Re-audit or create a new audit record when evidence changes.

## Review-stage handoff

Use `review-stage-contract.md` for file-level compatibility among:

- `research-paper-review`
- `research-systematic-literature-review`
- `research-novelty-review`
- `research-review-loop`
- `research-rebuttal`

The harness contract governs scheduling, state, retries, checkpoints, experiment activation, and transition authority; the review-stage contract governs substantive review artifact shape. The result-audit/paper-binding contract governs the evidence chain from experiment claim to audited result to manuscript claim.
