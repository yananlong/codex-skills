# Writing Brief

Half a page written before the first sentence of prose. It fixes what the draft is for and what
it may say; the paragraph-level skeleton and the drafting order live in `outline.md`. Fill it from
the intake and the ledger at checkpoints 1 and 2, keep it beside the draft, and hand it on.

```markdown
# Writing brief: <artifact> (<date>)

## Job and reader
- Piece: <manuscript section(s) | abstract | technical report | rebuttal response | ...>
- Reader: <venue reviewer | program committee | engineering lead | funder | ...>
- What the reader should be able to do after reading: <one sentence>

## Register and format
- Register: <empirical ML | ML theory | systems | NLP position | HCI or social science | technical report>
- Source format: <LaTeX (macros, labels, bib keys from ...) | Markdown | plain text>
- Venue constraints: <page or word budget, anonymity, required sections>

## Sources (from writing-intake.md)
- Claim source: <bindings | audits | claim map | none: ledger proposed from data>
- Evidence: <audits, tables, figures>
- Literature: <evidence table, bib inventory, novelty report>
- Critique or board: <issue board | none>
- Validation run: <validator and result, or "no validator available">

## Claims (from claim-ledger.md)
- Ready: <IDs>
- Careful, with the limitation that travels with each: <IDs: limitation>
- Blocked, to appear as markers: <IDs: what is missing>
- Proposed, awaiting the author: <IDs>

## Terminology
- <internal label> → <reader-facing term>
- Coined terms kept and glossed on first use: <...>
- Defined terms used exactly: <...>

## Outline
- `outline.md`, built by `outline_from_ledger.py` and edited by the author at checkpoint 3
- Approved on: <date, or "drafting without review at the author's request">
- Drafting order: <sections as the outline lists them>

## Gates before handoff
- `check_draft_numbers.py <draft> --source <...>`: <result>
- `prose_tells.py <draft> --max-density 20`: <summary line>
- Ledger comparison: <claims added or removed>
- Read once as the reader: <one-line verdict>

## Handoff
- To: technical-writing-reviser (revision), then prose-flow-improver if asked, then <review stage>
- Markers left in the draft: <count and list>
- Not drafted: <sections and why>
- Checkpoint defaults taken without an answer: <list, or none>
```

The evidence-bearing sections come first in the outline because the framing sections are written
from what they actually say. An abstract drafted before the results section describes the paper
the author hoped to write.
