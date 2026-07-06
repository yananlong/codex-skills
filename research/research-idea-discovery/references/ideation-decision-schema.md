# Ideation Decision Schema

`ideation-decision.json` must be a JSON object with this shape:

```json
{
  "decision": "proceed_to_novelty_review",
  "selected_idea_ids": ["IDEA-001"],
  "confidence": "medium",
  "novelty_check_status": "quick_signal_only",
  "rationale": "Why this decision is justified",
  "next_skill": "research-novelty-review",
  "required_handoffs": [
    "selected-idea.md",
    "idea-scores.json",
    "landscape-map.md"
  ],
  "limits": [
    "Novelty signal is based on quick search only"
  ]
}
```

Allowed decisions:

- `proceed_to_novelty_review`
- `proceed_to_experiment_plan`
- `revise_scope`
- `generate_more`
- `stop`

Allowed next skills:

- `research-novelty-review`
- `research-systematic-literature-review`
- `research-experiment-plan`
- `research-pipeline-planner`
- `null`

Rules:

- `proceed_to_novelty_review` requires at least one selected idea.
- `proceed_to_novelty_review` should set `next_skill` to `research-novelty-review` unless novelty has already been checked.
- `proceed_to_experiment_plan` requires at least one selected idea, `novelty_check_status` of `reviewed`, and `next_skill` of `research-experiment-plan`.
- `research-experiment-plan` should be used only when novelty risk has already been checked and the selected idea is frozen as a claim.
- `stop` must include a rationale and at least one limit.
- `confidence` must be `low`, `medium`, or `high`.
- `novelty_check_status` must be `not_checked`, `quick_signal_only`, or `reviewed`.
