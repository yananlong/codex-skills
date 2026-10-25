# Claim Ledger

The ledger is the drafting contract's claim list built from the project's artifacts. The draft
may assert only what the ledger carries, at the strength the ledger allows.
`scripts/build_claim_ledger.py` derives it from the machine-readable sources; this page gives
the schema and the rules the script applies, so a ledger written by hand (when no source exists)
follows the same shape.

## Entry

```json
{
  "id": "PC-3",
  "text": "The calibrated scorer reduces expected calibration error on two of three task families.",
  "support": "measured",
  "status": "ready",
  "source": {"kind": "paper_plan.bindings", "path": "paper/claim-evidence-bindings.json", "locator": "claims[2]"},
  "sections": ["results", "abstract"],
  "evidence": ["results/audit/ece-by-family.csv"],
  "limitations": ["one model family"],
  "missing_evidence": [],
  "notes": "manuscript_action=qualify; scope: held-out families A, B, C"
}
```

- `support`: how the claim is held up. `measured` (an audited or tabulated result), `formal` (a
  proved statement with its hypotheses), `cited` (a source that was read and quoted), `argued`
  (an argument the text makes, written with "we argue"), `planned` (an experiment that has not
  produced evidence yet), `contradicted` (the evidence says otherwise), `missing`.
- `status`: what the draft may do. `ready` means assert at the scope recorded. `careful` means
  assert with the limitation in the same sentence or the next, or present as a limitation.
  `blocked` means the draft may only name the gap with a marker. `excluded` means omit, and
  the handoff note says why. `proposed` means the drafter derived the claim from data without a
  claim source and the author has not confirmed it.
- `sections`: where the claim is planned to appear. A claim with no section is not drafted.
- `evidence`: the artifact paths the sentence cites or draws numbers from.

## Derivation rules

| Source | Status rule |
| --- | --- |
| Paper-plan binding | `supported` → ready; `partial` → careful; `blocked`, `contradicted` → blocked; `withdrawn` or `manuscript_action: omit` → excluded; `manuscript_action: limitation` demotes ready to careful |
| Results audit | `audited_claim_effect` `strengthen` or `unchanged` → ready; `weaken` → careful; `kill` or `inconclusive` → blocked |
| Experiment claim map | always blocked (`planned`) until an audit or table for the same claim exists |
| Literature evidence table | `fetch_status: read` with a verbatim quote → ready at rung 1 or 2, careful at rung 3 or 4; no quote or not read → blocked |
| Rebuttal issue board | a decided strategy with a non-open status → ready; a strategy with an open status → careful; no strategy → blocked |

When bindings exist they are authoritative. An audit or claim-map entry whose ID a binding also
carries is kept for its evidence paths but is asserted through the binding, never on its own.

## Using the ledger while drafting

- Each sentence that asserts a result, a positioning claim, a theorem, or a concession is written
  against one ledger entry. Mark the entry ID in a draft comment (`<!-- PC-3 -->` in Markdown,
  `% PC-3` in LaTeX) while drafting; the reviser strips the comments or leaves them for the
  author.
- A `careful` entry's limitation travels with it. Writing the claim in the results section and the
  limitation only in the limitations section is the overclaim the audit was meant to prevent.
- A `blocked` entry appears as `[EVIDENCE NEEDED: <what the audit or table would show>]` in the
  place the claim would go, so the reader of the draft sees the shape of the missing argument.
- A claim the drafting discovers that the ledger lacks is added to the ledger with its support
  first, or removed from the draft. The after-writing comparison in the contract checks this.
- A `proposed` entry is written only in an evidence-bearing section and never in the abstract,
  introduction, or conclusion until the author confirms it.
