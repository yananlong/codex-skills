# Research Suite Contract

Use this contract only when work benefits from shared cross-stage artifacts. Do not force it for one-off standalone tasks.

## Root layout

| Artifact | Canonical path | Authority | Purpose |
| --- | --- | --- | --- |
| harness event log | `./harness-events.jsonl` | canonical | append-only transition and observation history |
| harness state | `./HARNESS_STATE.json` | projection | current scheduler state, rebuildable from events |
| work items | `./work-items.json` | projection | bounded work definitions and lifecycle state |
| episodes | `./episodes/` | canonical evidence | one worker-attempt package per submission |
| checkpoints | `./checkpoints/` | recovery aid | resumable state snapshots |
| research brief | `./research-brief.md` | canonical intent | problem frame, constraints, success criteria, harness policy |
| task board | `./task-board.md` | human-readable view | convenience summary; not scheduling authority |
| decision log | `./decision-log.md` | human-readable rationale | consequential decisions mirrored by machine events |
| artifact index | `./artifact-index.md` | canonical map | paths, authority, and status of project artifacts |
| zotero | `./zotero/` | stage output | outputs from `research-zotero` |
| literature review | `./literature-review/` | stage output | outputs from `research-systematic-literature-review` |
| ideation | `./ideation/` | stage output | outputs from `research-idea-discovery` |
| novelty review | `./novelty-review/` | stage output | outputs from `research-novelty-review` |
| experiment plan | `./experiment-plan/` | stage output | outputs from `research-experiment-plan` |
| results audit | `./results-audit/` | stage output | outputs from `research-results-auditor` |
| paper review | `./paper-review/` | stage output | outputs from `research-paper-review` |
| paper plan | `./paper-plan/` | stage output | outputs from `research-paper-plan` |
| review loop | `./review-loop/` | stage output | outputs from `research-review-loop` |
| rebuttal | `./rebuttal/` | stage output | outputs from `research-rebuttal` |

## Operating rules

- Standalone mode may ignore this layout entirely.
- Orchestrated mode must follow `agentic-harness-contract.md`.
- Use `scripts/harness_runtime.py` as the only writer for dynamic machine state.
- Treat `harness-events.jsonl` as authoritative and rebuild projections with `replay` after interruption or drift.
- Keep one active work item by default; allow concurrency only with disjoint write scopes or external isolation and conflict handling.
- Any sibling skill may still run directly, but an orchestrated stage runs as the owner of a frozen work item and submits an episode package.
- If an artifact is produced outside the canonical path, record the actual path in `artifact-index.md` and the episode.
- Do not let task-board prose, artifact presence, or a worker summary advance machine state.
- Do not reconstruct upstream work from conversational memory when a concrete artifact or episode exists.

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
| deep paper critique | `research-paper-review` | concrete paper artifact or URL, review rubric, output bundle |
| result validity audit | `research-results-auditor` | result artifact, target claim, protocol, failure ledger |
| iterative red-team review | `research-review-loop` | target artifact, prior issue state, required closure evidence |
| manuscript structuring | `research-paper-plan` | supported claims, evidence map, limitations |
| venue-aware author response | `research-rebuttal` | concrete reviews, venue rules, permitted analyses and changes |

## Worker protocol

For an orchestrated stage:

1. Read the assigned work item, harness state, and only allowlisted context artifacts.
2. Confirm the item is `running`, dependencies are complete, and owner skill matches.
3. Preserve the frozen objective and acceptance checks.
4. Work only within the declared write scope and permission policy.
5. Record material observations, failures, and scope changes.
6. Checkpoint before risky, expensive, destructive, or interruptible operations.
7. Write an episode package and request `approve`, `revise`, or `block`.
8. Never approve its own transition.

## Collaboration rules

- Standalone mode remains multi-skill friendly.
- Orchestrated collaboration must be represented as separate work items or explicit bounded tool/handoff calls inside an episode.
- Context passed to another skill or agent must be filtered through the work item's context manifest.
- A role name does not establish independence. Record actual separation across context, data, implementation, evaluation, and authority.
- Keep credentials and secrets outside worker context and generated execution environments.

## Review-stage handoff

Use `review-stage-contract.md` for file-level compatibility among:

- `research-paper-review`
- `research-systematic-literature-review`
- `research-novelty-review`
- `research-review-loop`
- `research-rebuttal`

The harness contract governs scheduling, state, retries, checkpoints, and transition authority; the review-stage contract governs substantive artifact shape.
