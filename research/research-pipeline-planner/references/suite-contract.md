# Research Suite Contract

Use this contract only when the work benefits from shared stage artifacts. Do not force it for one-off standalone tasks.

## Root layout

| Artifact | Canonical path | Purpose |
| --- | --- | --- |
| research brief | `./research-brief.md` | problem framing and current stage |
| task board | `./task-board.md` | stage tracker and next actions |
| decision log | `./decision-log.md` | checkpoint decisions |
| artifact index | `./artifact-index.md` | canonical path registry |
| literature review | `./literature-review/` | outputs from `research-systematic-literature-review` |
| novelty review | `./novelty-review/` | outputs from `research-novelty-review` |
| experiment plan | `./experiment-plan/` | outputs from `research-experiment-plan` |
| paper plan | `./paper-plan/` | outputs from `research-paper-plan` |
| review loop | `./review-loop/` | outputs from `research-review-loop` |

## Operating rules

- Standalone mode may ignore this layout entirely.
- Orchestrated mode should prefer these paths so later stages can find the right artifacts.
- Any sibling skill may still run directly; orchestration does not make `research-pipeline-planner` a mandatory entrypoint.
- If an artifact is produced outside the canonical path, record the actual path in `artifact-index.md`.

## Handoff map

| Need | Preferred skill | Minimum upstream context |
| --- | --- | --- |
| broad evidence gathering | `research-systematic-literature-review` | topic, domain, and review question |
| skeptical novelty pressure test | `research-novelty-review` | concrete method or claim description |
| decisive validation design | `research-experiment-plan` | frozen claim and evaluation goal |
| result sanity check | `research-results-auditor` | result artifact plus target claim |
| iterative red-team review | `research-review-loop` | artifact under review |
| manuscript structuring | `research-paper-plan` | claims plus supporting evidence |

## Collaboration rules

- Standalone mode must remain multi-skill friendly.
- If another skill would materially improve the answer, say so and collaborate instead of staying artificially local.
- If independent review or delegation is explicitly available and permitted, use it only for bounded side work that benefits from a second pass.
