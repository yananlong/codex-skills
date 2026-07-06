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
