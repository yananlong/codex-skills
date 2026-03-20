# TabMol DDI/OOD Adapter

Use this adapter when the planning target is the DDI-as-OOD-framework agenda.

## Planning priorities

- Treat the contribution as a framework and protocol, not a new model.
- Make the deliverables explicit:
  - pairwise OOD threat model
  - split and leakage audit spec
  - shift-severity quantification
  - reporting table and statistical test plan
  - failure-mode catalog

## Mandatory checkpoints

- Define which OOD regimes are in scope: one-new-drug, both-new, scaffold shift, mechanism/class shift, temporal shift, or others.
- Decide whether non-edges are negatives or unlabeled cases.
- Decide how temporal censoring and discovery bias will be handled.
- Define what evidence makes the framework general beyond DDI.

## Artifact hints

- Put the threat model in `research-brief.md`.
- Put split definitions and audit outputs in the task board and artifact index.
- Record every narrowing of the framework claim in the decision log.
