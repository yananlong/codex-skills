# Result Audit and Paper Claim-Evidence Binding Contract

Use this contract when experimental results move from execution history into audited evidence and then into manuscript claims.

## Authority map

| Artifact | Authority | May define | Must not redefine |
| --- | --- | --- | --- |
| `research-commitment.json` | canonical paper identity | paper ID, identity version, minimum claim, evidence obligation, pivot controls | experiment result or manuscript support status |
| `experiment-plan/claim-map.json` | canonical source claims | experiment-facing claim IDs and decision contracts | audited verdict or manuscript wording |
| `work-items.json` plus event-backed episodes/verifications | canonical local execution projection | run ID, episode digest, gate result, disposition, scoped claim effects, artifact digests, verifier decision | audit verdict or paper claim action |
| `results-audit/results-audit.json` | canonical audited evidence | run coverage, attained assurance, bounded verdict, audited claim effect, scope, checks, limitations, failure dispositions | source run history or paper identity |
| `results-audit/results-audit.md` | explanatory view | reasoning and caveats | machine verdict or assurance class |
| `paper-plan/claim-evidence-bindings.json` | canonical manuscript support | paper claim IDs, audit coverage/exclusions, support status, manuscript action, evidence links, scope, limitations | source audit content or experiment history |
| paper-plan Markdown files | human-readable views | outline, matrix, exhibits, citation needs | canonical support status or action |

Do not create a second source of truth for the same field.

## Result-audit invariants

- Every audit has a stable `audit_id`, one source `claim_id`, and an exact scope.
- The linked profile requires `source_mode=orchestrated`.
- Every run eligible under the same paper ID, identity version, and source claim must be included or explicitly excluded with a substantive rationale.
- An orchestrated source run binds the exact work item, episode ID/digest, run ID, block, gate, scoped submitted effect, lineage, verifier decision, verified gate/disposition, and self-review disclosure.
- A positive orchestrated verdict requires an approved source run.
- Confirmatory-or-stronger support requires an approved run with verified gate `pass`, verified disposition `supports_claim`, and submitted effect `strengthen`.
- An audit may downgrade a submitted interpretation after finding confounds; it may not rewrite the source run.
- Experiment evidence paths and digests must match a bound source episode.
- Required checks carry status, rationale, and evidence paths. Operational/high-stakes support requires every required check to pass.
- Independent verification requires actual separation, not a role label.

## Paper-binding invariants

- Every manuscript claim has a stable ID, bounded text, exact scope, evidence mode, support status, and manuscript action.
- Every result audit targeting a listed source claim must be linked or explicitly excluded. Same-scope audits cannot be excluded.
- A paper claim may be asserted only when supported.
- Empirical and mixed assertion requires a positive same-scope audit at or above the required assurance class and no linked negative audit.
- `partial` requires explicit limitations and missing evidence.
- `blocked`, `contradicted`, and `withdrawn` cannot be asserted.
- Active empirical and mixed claims require audited evidence paths; mixed claims also require nonempirical support.
- Paper validation must revalidate the exact result-audit JSON, narrative, and work-item bindings before promotion.
- The Markdown matrix contains exactly the canonical claims and exact linked/excluded audit IDs.
- Exhibit and citation links are reciprocal in both directions and use stable nonblank IDs.

## Assurance boundary

The validators establish repository-local structural and cross-artifact consistency. They do not establish authenticated execution, executor isolation, external immutability, scientific validity, citation correctness, material independence beyond recorded evidence, or correctness of manuscript prose outside the declared bindings.

## Validation order

For orchestrated empirical claims:

1. validate the commitment and harness pack;
2. validate experiment planning and execution history;
3. validate `results-audit.json` and its narrative against commitment, claim map, and work items;
4. revalidate that audit pack while validating `claim-evidence-bindings.json`;
5. run adversarial manuscript review against the resulting claim ledger.

A later validator does not retroactively certify an earlier stage. Preserve every bounded verdict, exclusion, limitation, and negative result.
