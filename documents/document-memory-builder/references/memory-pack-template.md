# Memory Pack Template

Use this structure for every pack unless the user explicitly asks for a different format.

## `<memory_name>.memory.md`

Required sections:

- `Scope`
- `Canonical Facts`
- `Terminology and Conventions`
- `Entities and Relationships`
- `Workflows and Decision Rules`
- `Constraints and Non-Goals`
- `Change Watchlist`

Guidance:

- Keep this file short enough to scan quickly.
- Prefer normalized language over document-specific phrasing.
- Cite sources inline for any nontrivial claim.
- Mark cross-document inferences explicitly.

## `<memory_name>.source-map.md`

Required sections:

- `Source Inventory`
- `Canonical Sources`
- `Coverage Gaps`

Guidance:

- Record every document that materially informed the memory.
- Note authority and recency, not just file names.
- Explain which documents should win when conflicts arise.

## `<memory_name>.open-questions.md`

Required sections:

- `Contradictions`
- `Missing Information`
- `Follow-Up Reads`

Guidance:

- Keep unresolved issues out of canonical memory.
- Phrase each question so a later agent can resolve it efficiently.
