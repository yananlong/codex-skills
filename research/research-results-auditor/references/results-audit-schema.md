# Machine-Readable Results Audit Schema

`results-audit.json` is an object with:

- `schema_version`: currently `1.0`.
- `paper_id`: stable commitment paper ID; required when complete.
- `identity_version`: positive integer.
- `status`: `draft`, `complete`, or `superseded`.
- `audits`: list of audit records.

## Audit record

Required fields:

- `audit_id`: stable identifier.
- `claim_id`: source experiment claim ID.
- `claim_text`: bounded claim under audit.
- `source_mode`: `standalone` or `orchestrated`.
- `requested_assurance_class`: exploratory, confirmatory, independently verified, or operational/high-stakes.
- `attained_assurance_class`: `none` or one of the requested assurance classes; it cannot exceed the requested class.
- `verdict`: one bounded verdict from the skill contract.
- `audited_claim_effect`: `strengthen`, `weaken`, `kill`, `unchanged`, or `inconclusive`.
- `source_runs`: exact run and verification bindings for orchestrated evidence.
- `evidence_artifacts`: audited paths, kind, source, and digest where required.
- `check_results`: one record for each required check.
- `independence`: self-review flag, actual dimensions, and evidence.
- `limitations`: substantive list.
- `predecessor_failures`: failure ID, status, and rationale.
- `minimum_corrective_action`: bounded next step.
- `narrative_anchor`: location in `results-audit.md`.

## Source-run binding

Each orchestrated source run records:

- `work_item_id`
- `episode_id`
- `episode_digest`
- `run_id`
- `block_id`
- `gate_id`
- submitted `gate_result`
- submitted `scientific_disposition`
- `lineage_relation`
- `parent_run_id`
- `submitted_claim_effect`
- `verification_decision`
- `verified_gate_result`
- `verified_scientific_disposition`
- `verification_self_review`

The linked validator resolves the run and verifier record from `work-items.json` and rejects disagreement.

## Required checks

- `protocol_integrity`
- `metric_validity`
- `baseline_fairness`
- `outcome_accounting`
- `inferential_support`
- `confound_control`
- `provenance`
- `snapshot_continuity`
- `independence`

Each uses `pass`, `fail`, `inconclusive`, or `not_assessed`, with a rationale and evidence paths declared in the audit.
