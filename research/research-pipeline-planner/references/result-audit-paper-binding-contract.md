# Result Audit and Paper Claim-Evidence Binding Contract

Use this contract when experimental results move from execution history into audited evidence and then into manuscript claims.

## Authority map

| Artifact | Authority | May define | Must not redefine |
| --- | --- | --- | --- |
| `research-commitment.json` | canonical paper identity | paper ID, identity version, minimum claim, evidence obligation, pivot controls | experiment result or manuscript support status |
| `experiment-plan/claim-map.json` | canonical source claims | experiment-facing claim IDs and decision contracts | audited verdict or manuscript wording |
| `work-items.json` plus event-backed episodes/verifications | canonical local execution projection | run ID, episode digest, gate result, disposition, claim effects, artifact digests, verifier decision | audit verdict or paper claim action |
| `results-audit/results-audit.json` | canonical audited evidence | attained assurance, bounded verdict, audited claim effect, checks, limitations, failure dispositions | source run history or paper identity |
| `results-audit/results-audit.md` | explanatory view | reasoning and caveats | machine verdict or assurance class |
| `paper-plan/claim-evidence-bindings.json` | canonical manuscript support | paper claim IDs, support status, manuscript action, evidence links, scope, limitations | source audit content or experiment history |
| paper-plan Markdown files | human-readable views | outline, matrix, exhibits, citation needs | canonical support status or action |

Do not create a second source of truth for the same field.

## Result-audit invariants

- Every audit has a stable `audit_id` and one source `claim_id`.
- Assurance strength and evidential direction are separate. A confirmatory audit may conclude `does_not_support_claim`.
- An orchestrated source run binds the exact work item, episode ID and digest, run ID, block, gate, submitted disposition/effect, lineage, verifier decision, verified gate/disposition, and verifier self-review disclosure.
- A positive orchestrated verdict requires at least one approved source run.
- Confirmatory-or-stronger support requires an approved run with verified gate `pass`, verified disposition `supports_claim`, and submitted effect `strengthen`.
- An audit may downgrade a submitted interpretation after finding confounds or inferential defects. It may not silently rewrite the source run.
- Evidence artifacts marked `experiment` must match paths and digests recorded by a bound source episode.
- Required checks must carry a status, rationale, and evidence paths. Field presence alone is not semantic assurance.
- Independent verification requires actual separation, not an actor label. Record self-review and independence dimensions explicitly.

## Paper-binding invariants

- Every manuscript claim has a stable `paper_claim_id`, bounded text, scope, evidence mode, support status, and manuscript action.
- Empirical and mixed claims preserve their source experiment claim IDs and linked audit IDs.
- A paper claim may be `assert`ed only when its support status is `supported`.
- An asserted empirical or mixed claim needs a positive audit at or above the required assurance class.
- A linked negative audit blocks unqualified assertion. Reclassify the paper claim as qualified, partial, contradicted, or omitted as evidence warrants.
- `partial` requires explicit limitations and missing evidence.
- `blocked`, `contradicted`, and `withdrawn` cannot be asserted.
- Audited evidence paths used by an empirical claim must occur in the linked audit records.
- The Markdown claims-evidence matrix contains exactly the canonical JSON claims. Extra rows are not an escape hatch for unsupported manuscript language.
- Exhibit and citation IDs are reciprocal: the JSON claim and the corresponding Markdown row must reference each other.

## Assurance boundary

The validators establish repository-local structural and cross-artifact consistency. They do not establish:

- authenticated execution or reviewer identity;
- executor isolation or absence of undeclared activity;
- external immutability or non-repudiation;
- scientific validity of a metric, result, proof, or citation;
- material independence beyond the recorded evidence;
- correctness of manuscript prose outside the declared bindings.

## Validation order

For orchestrated empirical claims:

1. validate the research commitment and harness pack;
2. validate the experiment plan and execution history;
3. validate `results-audit.json` against commitment, claim map, and work items;
4. validate `claim-evidence-bindings.json` against commitment, claim map, and the validated result audit;
5. run adversarial manuscript review against the resulting paper claim ledger.

A later validator does not retroactively certify an earlier stage. Preserve each stage's bounded verdict.
