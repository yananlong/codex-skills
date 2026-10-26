# Idea Score Schema

`idea-scores.json` must be a JSON object with this shape:

```json
{
  "topic": "broad research direction",
  "scoring_scale": "1-5",
  "ideas": [
    {
      "idea_id": "IDEA-001",
      "title": "Concise idea title",
      "summary": "One-paragraph summary",
      "hypothesis": "What should be true and why",
      "contribution_type": "method|empirical|theory|diagnostic|dataset|benchmark|tooling|mixed",
      "source_basis": ["paper, note, artifact, or observation that motivated the idea"],
      "assumptions": ["Assumption this idea depends on"],
      "novelty_questions": ["Question for downstream novelty review"],
      "minimum_validation": "Cheapest useful test",
      "disconfirming_evidence": "Observation that would weaken or kill the idea",
      "kill_criteria": "Concrete condition under which to stop or revise",
      "closest_work": ["paper or artifact"],
      "differentiation": "What is not already covered by closest work",
      "scores": {
        "clarity": 4,
        "novelty_signal": 3,
        "feasibility": 4,
        "testability": 5,
        "significance": 4
      },
      "risk": "low|medium|high",
      "estimated_effort": "hours|days|weeks|months",
      "status": "selected|shortlisted|rejected|needs_research",
      "rationale": "Why this status was assigned",
      "blocking_questions": ["Question that must be resolved before downstream work"]
    }
  ]
}
```

Rules:

- `idea_id` values must be unique.
- Scores must be integers from 1 to 5.
- `status` must be one of `selected`, `shortlisted`, `rejected`, or `needs_research`.
- Every selected or shortlisted idea must include non-empty `source_basis`, `assumptions`, `novelty_questions`, `disconfirming_evidence`, and `kill_criteria`.
- Every `selected` idea must also appear in `ideation-decision.json.selected_idea_ids`.

## Route-level re-ideation fields

When the ideas would replace a failing route inside a live project (`ideation_mode: route_level` in `ideation-decision.json`), every selected or shortlisted idea also records what it inherits and what it costs:

```json
{
  "evidence_class": "exploratory",
  "predecessor_failures": [
    {"failure_id": "F1", "disposition": "targeted", "evidence": ""}
  ],
  "switching_cost": {
    "discarded": "work and artifacts the switch abandons",
    "new_burden": "new literature, data, validation, or venue burden"
  },
  "identity_change_class": "D2",
  "pivot_request_needed": false,
  "next_skill": "research-novelty-review"
}
```

- `evidence_class`: `exploratory`, `confirmatory`, `independently_verified`, or `operational_high_stakes`, the planner's classes. An idea starts exploratory unless traced evidence says otherwise; ranking does not raise it.
- `predecessor_failures`: the failures of the replaced route that the idea inherits, possibly an empty list. `disposition` is `open` (carried unchanged), `targeted` (the idea's minimum validation tests it), `accepted_with_narrowing`, or `resolved`. A `resolved` entry names the `evidence` that resolved it; a new idea or a reframing does not resolve an inherited failure by itself.
- `switching_cost`: both what the switch discards and what new burden it brings.
- `identity_change_class`: `D0` to `D4`, as in the planner's commitment contract. `D3` and `D4` set `pivot_request_needed: true`, and their `next_skill` is `research-pipeline-planner` (which records the pivot request) or `stop`.
- `next_skill`: the sibling skill that takes the idea next, including `research-paper-review` (when the idea is a reframing of an existing draft) and `research-results-auditor`, or `stop`.

In fresh ideation (no live project) these fields are optional. When present they are checked the same way.
