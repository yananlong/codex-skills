# Paper Claim-Evidence Binding Schema

`claim-evidence-bindings.json` is an object with:

- `schema_version`: currently `1.0`.
- `paper_id`: stable commitment paper ID; required when complete.
- `identity_version`: positive integer.
- `status`: `draft` or `complete`.
- `claims`: list of paper claim bindings.

## Paper claim binding

Each claim records:

- `paper_claim_id`: stable manuscript-facing ID.
- `claim`: bounded claim text.
- `claim_type`: `primary`, `supporting`, `limitation`, or `context`.
- `evidence_mode`: `empirical`, `theoretical`, `citation`, `mixed`, or `limitation`.
- `support_status`: `supported`, `partial`, `blocked`, `contradicted`, or `withdrawn`.
- `manuscript_action`: `assert`, `qualify`, `limitation`, or `omit`.
- `required_assurance_class`: `none`, `exploratory`, `confirmatory`, `independently_verified`, or `operational_high_stakes`.
- `source_claim_ids`: source experiment claim IDs.
- `audit_ids`: machine-readable result-audit IDs.
- `evidence_artifacts`: audited evidence paths used by the paper claim.
- `planned_sections`: manuscript locations.
- `exhibit_ids`: stable figure/table IDs.
- `citation_need_ids`: stable citation-plan IDs.
- `limitations`: explicit caveats.
- `missing_evidence`: blockers or requirements.
- `scope`: exact population/task/condition boundary.
- `rationale`: why the status and action follow from the evidence.

## Status/action constraints

- `supported` may be asserted or qualified, but not omitted.
- `qualify` requires explicit limitations.
- `partial` requires qualification or limitation treatment, limitations, and missing evidence.
- `blocked`, `contradicted`, and `withdrawn` may only be omitted or presented as limitations.
- Empirical and mixed active claims require source claim IDs and result-audit IDs.
- A supported empirical or mixed claim requires a positive audit at or above the required assurance class.
- A contradicted claim requires negative audit evidence and no adequate positive audit under the same binding.
- Supported theoretical claims require concrete evidence artifacts.
- Supported citation claims require citation-need IDs.
