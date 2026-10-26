# Paper Claim-Evidence Binding Schema

`claim-evidence-bindings.json` is an object with `schema_version`, `paper_id`, `identity_version`, `status`, and `claims`.

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
- `audit_ids`: linked machine-readable result-audit IDs.
- `audit_exclusions`: relevant audits deliberately excluded from this paper claim, each with `audit_id`, `rationale`, and `scope_difference`.
- `evidence_artifacts`: audited evidence paths used by the paper claim.
- `planned_sections`, `exhibit_ids`, and `citation_need_ids`.
- `limitations`, `missing_evidence`, `scope`, and `rationale`.
- `value_bindings`: one entry per reported value, each with `audit_id` (one of the claim's `audit_ids`), `gate_id` (the decision gate whose result the sentence reports), `value_slot` (the reported value: `measurement:<measurement_id>` for an audit measurement, or a dotted field path in the audit record such as `check_results.metric_validity.status`), and an optional `sentence_anchor` locating the sentence. An active empirical or mixed claim without value bindings still validates, with a warning.

## Resolving links

An audit link must resolve to a record in `results-audit.json`; one that does not is an error. The linked profile always resolves links. The structural profile resolves them when `--results-audit` is given and otherwise warns that they were not checked. A value binding's gate must be a gate of its audit (the audit's `gate_id` or a source run's `gate_id`), and its value slot must resolve in the audit. When an audit records no gate, or has no `measurements` list yet, the binding passes with a warning that it is unchecked.

`--work-items` is optional under the linked profile when every bound audit has `source_mode` `standalone`; the upstream audit is then revalidated with the auditor's structural profile, and a standalone audit without a `paper_id` is accepted.

`--report` prints the bindings as a table (claim, sentence anchor, audit, gate, value slot, status), one row per value binding, or one row per linked audit marked `legacy` when a claim has no value bindings.

## Audit coverage and scope

Every audit in `results-audit.json` that targets a listed `source_claim_id` must be linked in `audit_ids` or explicitly listed in `audit_exclusions`. A claim cannot both link and exclude the same audit. Same-scope audits cannot be excluded.

An empirical or mixed assertion needs a positive linked audit at or above the required assurance class whose `scope` exactly matches the paper claim scope. A broader manuscript claim must be narrowed or separately audited.

## Status/action constraints

- `assert` requires `supported` status.
- `qualify` requires explicit limitations.
- `partial` requires qualification or limitation treatment, limitations, and missing evidence.
- `blocked`, `contradicted`, and `withdrawn` may only be omitted or presented as limitations.
- Active empirical and mixed claims require source claim IDs, result-audit IDs, and audited evidence paths.
- A linked negative audit blocks assertion.
- A contradicted claim requires negative audit evidence and cannot coexist with adequate same-scope positive evidence without reclassification.
- Supported theoretical claims require concrete nonempirical evidence artifacts.
- Supported citation claims require citation-need IDs.
- Mixed claims require audited empirical evidence plus at least one nonempirical artifact or citation need.

## Human-readable views

The complete claims-evidence matrix contains exactly the canonical JSON claims and includes linked and excluded audit IDs. Figure and citation rows use stable IDs and reciprocal paper-claim references in both directions. The matrix limitation cell must exactly project the JSON limitation set.
