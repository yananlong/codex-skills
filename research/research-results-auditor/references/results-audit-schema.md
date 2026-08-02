# Machine-Readable Results Audit Schema

`results-audit.json` is an object with `schema_version`, `paper_id`, `identity_version`, `status`, and `audits`.

- `schema_version`: currently `1.0`.
- `paper_id`: stable commitment paper ID; required when complete.
- `identity_version`: positive integer.
- `status`: `draft`, `complete`, or `superseded`.
- `audits`: list of audit records.

## Audit record

Each complete audit records:

- `audit_id`: stable identifier.
- `claim_id`: source experiment claim ID.
- `claim_text`: bounded claim under audit.
- `scope`: exact population, task, split, condition, and metric boundary.
- `source_mode`: `standalone` or `orchestrated`; the linked profile requires `orchestrated`.
- `requested_assurance_class` and `attained_assurance_class`.
- `verdict`: one bounded verdict from the skill contract.
- `audited_claim_effect`: `strengthen`, `weaken`, `kill`, `unchanged`, or `inconclusive`.
- `source_runs`: exact run and verifier bindings.
- `run_selection`: coverage rule plus explicit exclusions.
- `evidence_artifacts`: audited paths, kinds, sources, and digests.
- `check_results`: one record for every required check.
- `independence`: self-review flag, actual dimensions, and evidence.
- `limitations`, `predecessor_failures`, `minimum_corrective_action`, and `narrative_anchor`.

## Source-run binding

Each orchestrated source run records:

- `work_item_id`, `episode_id`, `episode_digest`, `run_id`, `block_id`, and `gate_id`;
- submitted `gate_result`, `scientific_disposition`, `submitted_claim_effect`, and `submitted_claim_scope`;
- `lineage_relation` and `parent_run_id`;
- `verification_decision`, `verified_gate_result`, `verified_scientific_disposition`, and `verification_self_review`.

The linked validator resolves these fields from `work-items.json` and rejects disagreement.

## Run-selection coverage

`run_selection` contains:

```json
{
  "selection_rule": "Include every eligible run for the active paper identity and source claim.",
  "excluded_runs": [
    {"run_id": "RUN-X", "rationale": "Different preregistered population."}
  ]
}
```

Every run whose experiment binding has the same `paper_id`, `identity_version`, and `claim_id` is eligible. Each eligible run must appear in `source_runs` or `excluded_runs`; a run cannot appear in both. Exclusions require a substantive rationale and remain visible to downstream paper planning.

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

Each uses `pass`, `fail`, `inconclusive`, or `not_assessed`, with a rationale and declared evidence paths. Operational/high-stakes support requires every check to pass. Independent support additionally requires actual separation and no self-review.
