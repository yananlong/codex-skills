# Writing Brief

One page written before the first sentence of prose. It fixes what the draft is for, what it may
say, and in what order it is written. Fill it from the intake and the ledger; keep it beside the
draft and hand it on with the draft.

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

## Skeleton and drafting order
| Order | Section | Job | Ledger entries | Budget |
| --- | --- | --- | --- | --- |
| 1 | Method | what was done, bounded to the protocol | <IDs> | <words> |
| 2 | Results | what was measured, numbers from <sources> | <IDs> | <words> |
| 3 | Limitations | what the audits and partial claims say | <IDs> | <words> |
| 4 | Related work | positioning from the novelty decision, one sentence per read source | <IDs> | <words> |
| 5 | Introduction | motivation and contributions as the results sections state them | <IDs> | <words> |
| 6 | Abstract | one sentence per primary ready claim | <IDs> | <words> |

## Gates before handoff
- `check_draft_numbers.py <draft> --source <...>`: <result>
- `prose_tells.py <draft> --max-density 20`: <summary line>
- Ledger comparison: <claims added or removed>
- Read once as the reader: <one-line verdict>

## Handoff
- To: technical-writing-reviser (revision), then prose-flow-improver if asked, then <review stage>
- Markers left in the draft: <count and list>
- Not drafted: <sections and why>
```

The evidence-bearing sections come first because the framing sections are written from what they
actually say. An abstract drafted before the results section describes the paper the author
hoped to write.
