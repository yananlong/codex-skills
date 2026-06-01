# Review State Schema

Use `REVIEW_STATE.json` to track issue status across rounds.

## Required top-level fields

- `version`: schema version string
- `target`: short description of the reviewed artifact
- `round`: integer review round
- `status`: `open`, `in_progress`, or `closed`
- `summary`: short status summary
- `source_artifacts`: list of upstream artifacts used to seed or update the review state
- `open_issues`: list of unresolved issues
- `resolved_issues`: list of resolved issues
- `accepted_risks`: list of risks that remain by choice

## Issue object

- `id`: stable identifier
- `severity`: `major`, `moderate`, or `minor`
- `impact_rating`: optional integer 1-5, preserved from `research-paper-review` when available
- `confidence_rating`: optional integer 1-5, preserved from `research-paper-review` when available
- `title`: short issue name
- `status`: `open`, `resolved`, or `accepted`
- `evidence`: short evidence note
- `required_action`: fix, rewrite, experiment, or verification needed
- `source_quote`: optional exact quote from the reviewed artifact
- `source_section`: optional section, table, figure, or file location
- `related_sections`: optional list of related locations
- `origin`: optional source such as `paper-review/final_issues.json`, `round-2 internal pass`, or `external verification`

## Example

```json
{
  "version": "1.0",
  "target": "research brief",
  "round": 1,
  "status": "open",
  "summary": "Two major issues block acceptance.",
  "source_artifacts": ["paper-review/example_review/final_issues.json"],
  "open_issues": [
    {
      "id": "R1",
      "severity": "major",
      "impact_rating": 4,
      "confidence_rating": 5,
      "title": "Claim lacks supporting evidence",
      "status": "open",
      "evidence": "No result artifact tied to the claim.",
      "required_action": "Add result table or narrow the claim.",
      "source_quote": "We show that the method generalizes across all settings.",
      "source_section": "Abstract",
      "related_sections": ["Experiments"],
      "origin": "paper-review/example_review/final_issues.json"
    }
  ],
  "resolved_issues": [],
  "accepted_risks": []
}
```
