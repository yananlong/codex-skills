# Review State Schema

Use `REVIEW_STATE.json` to track issue status across rounds.

## Required top-level fields

- `version`: schema version string
- `target`: short description of the reviewed artifact
- `round`: integer review round
- `status`: `open`, `in_progress`, or `closed`
- `summary`: short status summary
- `open_issues`: list of unresolved issues
- `resolved_issues`: list of resolved issues
- `accepted_risks`: list of risks that remain by choice

## Issue object

- `id`: stable identifier
- `severity`: `major` or `minor`
- `title`: short issue name
- `status`: `open`, `resolved`, or `accepted`
- `evidence`: short evidence note
- `required_action`: fix, rewrite, experiment, or verification needed

## Example

```json
{
  "version": "1.0",
  "target": "research brief",
  "round": 1,
  "status": "open",
  "summary": "Two major issues block acceptance.",
  "open_issues": [
    {
      "id": "R1",
      "severity": "major",
      "title": "Claim lacks supporting evidence",
      "status": "open",
      "evidence": "No result artifact tied to the claim.",
      "required_action": "Add result table or narrow the claim."
    }
  ],
  "resolved_issues": [],
  "accepted_risks": []
}
```
