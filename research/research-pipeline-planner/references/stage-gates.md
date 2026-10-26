# Research Stage Gates

Each gate decides whether to proceed, revise scope, request a pivot, park a successor idea, or stop. Gates live with the skill that owns the stage, so a skill installed alone still carries its own test. This file is the index.

## Cross-stage gates (planner)

| Gate | Where it lives |
| --- | --- |
| Paper identity: apply before every consequential cross-stage transition | `research-pipeline-planner/SKILL.md`, `### Paper-identity gate` |
| Evidence promotion: apply whenever an artifact or result is promoted beyond exploratory | `research-pipeline-planner/SKILL.md`, `### Evidence-promotion gate` |

## Stage gates

| Stage | Owner | Where it lives |
| --- | --- | --- |
| Literature review | `research-systematic-literature-review` | `research-systematic-literature-review/SKILL.md`, `## Stage gate` |
| Ideation | `research-idea-discovery` | `research-idea-discovery/SKILL.md`, `## Stage gate` |
| Novelty review | `research-novelty-review` | `research-novelty-review/SKILL.md`, `## Stage gate` |
| Experiment plan | `research-experiment-plan` | `research-experiment-plan/SKILL.md`, `## Stage gate` |
| Results audit | `research-results-auditor` | `research-results-auditor/SKILL.md`, `## Stage gate` |
| Paper plan | `research-paper-plan` | `research-paper-plan/SKILL.md`, `## Stage gate` |
| Paper review | `research-paper-review` | `research-paper-review/SKILL.md`, `## Stage gate` |
| Review loop | `research-review-loop` | `research-review-loop/SKILL.md`, `## Stage gate` |
| Rebuttal | `research-rebuttal` | `research-rebuttal/SKILL.md`, `## Stage gate` |

## Applying gates in an orchestrated project

Read `research-commitment.json` and `research-commitment-contract.md` before authorizing any transition. Apply the paper-identity gate first, then the gate of the stage being left or entered. A stage gate may recommend `continue`, `narrow`, `pivot-request`, `kill`, or `park-successor` (the route actions in `suite-contract.md`); D3 and D4 changes go through `harness_runtime.py pivot-request`, never through a stage skill.
