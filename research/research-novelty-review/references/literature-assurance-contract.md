# Novelty Literature-Assurance Contract

`novelty-decision.json` is the novelty-positioning authority. When its `literature_assurance.mode` is `linked`, it must bind the exact seven-file literature pack:

- protocol
- search log
- recall audit
- corpus manifest
- screening log
- evidence table
- review report

The binding records the exact paths, a SHA-256 digest for every bound file, the redundant corpus-manifest digest, corpus version, review profile, assurance verdict, and the complete set of unresolved high-priority novelty-critical coverage-question IDs.

Linked validation verifies every file digest, reruns the full literature-review validator over those exact paths, and rejects files that change during validation before interpreting the novelty rating. Matching a manifest digest alone is insufficient. A decision whose `literature_assurance.mode` is `linked` must be validated with `--assurance-profile linked`; structural mode cannot launder a linked decision.

## Rating gates

- Ratings `4` and `5` require `adequate-for-bounded-claims` or `adequate-for-comprehensive-claim` and no unresolved high-priority novelty-critical question.
- Rating `3` may survive insufficient assurance or unresolved critical questions only with a substantive narrow positioning, a concrete statement of what would change the decision, and explicit claims to qualify.
- Ratings govern novelty positioning only. They do not certify empirical validity, confirmatory status, implementation correctness, or evidence promotion.

The Markdown report must exactly project the three ratings, narrowest positioning, change condition, literature-assurance mode and verdict, and unresolved critical question IDs from the JSON decision.
