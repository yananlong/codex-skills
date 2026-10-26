# Novelty Literature-Assurance Contract

`novelty-decision.json` is the novelty-positioning authority. Its `literature_assurance.mode` says how much literature stands behind the rating, and the mode sets the highest rating the validator accepts.

| Mode | Bound evidence | Validated with | Highest rating |
| --- | --- | --- | --- |
| `unlinked` | none; the review's own prior-art matrix and search log | default structural profile | 3 |
| `context` | the four-file paper-context evidence map from `research-systematic-literature-review` | default structural profile | 5 |
| `linked` | the seven-file literature pack | `--assurance-profile linked` | 5 |

## Prior-art rows

In `unlinked` and `context` mode a rating needs one filled row in `prior-art-matrix.md` for each point above 1: a 3 needs two rows, a 5 needs four. A row counts when its Work cell names a work. This is a floor on how much was examined, and it says nothing about how threatening those works are.

## Unlinked mode

Use it for the lightweight path, such as "find the prior art I am missing in this draft". Ratings above 3 fail with a message naming the two ways up: bind a paper context or bind a seven-file pack.

## Context mode

The decision binds a four-file paper context:

- `literature-context.md`
- `literature-context-search-log.md`
- `literature-context-evidence-table.md`
- `literature-context-decision.json`

The binding records `context_dir` (relative to the decision) and `context_sha256`, one SHA-256 digest per file, with `assurance_verdict: paper-context-validated`. Validation checks every digest, reruns the paper-context validator with placeholders disallowed, and for a rating of 4 or 5 requires `coverage_confidence_rating` of at least 3 in the context decision. Editing the context after binding fails validation until the decision is linked again.

## Linked mode

The decision binds the exact seven-file literature pack:

- protocol
- search log
- recall audit
- corpus manifest
- screening log
- evidence table
- review report

The binding records the exact paths, a SHA-256 digest for every bound file, the redundant corpus-manifest digest, corpus version, review profile, assurance verdict, and the complete set of unresolved high-priority novelty-critical coverage-question IDs.

Linked validation verifies every file digest, reruns the full literature-review validator over those exact paths, and rejects files that change during validation before interpreting the novelty rating. Matching a manifest digest alone is insufficient. A decision whose mode is `linked` must be validated with `--assurance-profile linked`, so structural validation cannot pass a linked decision.

Linked rating gates:

- Ratings `4` and `5` require `adequate-for-bounded-claims` or `adequate-for-comprehensive-claim` and no unresolved high-priority novelty-critical question.
- Rating `3` may survive insufficient assurance or unresolved critical questions only with a substantive narrow positioning, a concrete statement of what would change the decision, and explicit claims to qualify.

## Helpers

- `scripts/novelty_assurance.py link --decision <json> --context <dir>` binds a paper context and updates the report's assurance lines.
- `scripts/novelty_assurance.py link --decision <json> --pack-dir <dir>` binds a seven-file pack, reading corpus identity, verdict, and unresolved question IDs from its manifest.
- `scripts/init_novelty_pack.py <dir> --link-context <dir>` or `--link <pack dir>` does the same when the pack is created.
- `research-systematic-literature-review/scripts/paper_context_artifacts.py promote --out-dir <context> --pack-dir <dir>` turns a paper context into a seven-file pack skeleton. Rows are copied as written and every other field is a TODO placeholder, so the pack fails validation until a real search fills it.
- `scripts/novelty_assurance.py migrate --decision <json> [--prior-art-matrix <md>]` brings a decision written before schema 1.1 up to date. It sets mode `unlinked`, lowers a novelty rating above 3 to 3 (and to one point above the filled prior-art rows when the matrix is given), records the original rating under `migration`, and never raises a rating.

## What validation establishes

Ratings govern novelty positioning only. They do not certify empirical validity, confirmatory status, implementation correctness, or evidence promotion.

The Markdown report must exactly project the three ratings, narrowest positioning, change condition, literature-assurance mode and verdict, and unresolved critical question IDs from the JSON decision.

A passing linked or context validation establishes repository-local byte continuity and consistency with the selected upstream validator. It does not establish external immutability, trusted execution, reviewer independence, literature completeness, or scientific novelty.
