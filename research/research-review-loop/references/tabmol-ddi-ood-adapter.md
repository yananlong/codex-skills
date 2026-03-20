# TabMol DDI/OOD Adapter

Use this adapter when reviewing DDI-as-OOD artifacts.

## Highest-priority attack surfaces

- novelty overreach: is this really a framework rather than another split?
- temporal censoring: could apparent drift be explained by discovery bias?
- pairwise regime ambiguity: does “OOD” mean one new drug, both new drugs, unseen pairs, or unseen scaffolds?
- label semantics: are missing edges treated as negatives without justification?
- metric mismatch: do aggregate metrics hide imbalance, calibration, or regime-specific failures?

## Review prompts

- What exact artifact proves the framework contribution?
- What assumption would a skeptical reviewer attack first?
- Which claim should be narrowed if evidence stays weak?
