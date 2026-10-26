# Checkpoints

The drafter works with the author, not for them in the dark. It stops at four points, shows
something short and editable, asks at most three questions with the default it will take, and
goes on only when the author answers or says to proceed. An outline edited at checkpoint 3 costs
the author a line per change; a draft edited after the fact costs a rewrite and keeps the habits
the draft baked in. The checkpoints exist to move the author's effort to where it is cheap.

## Checkpoint 1: the piece and its sources (after intake)

Show, in under fifteen lines: the piece as understood (what, for whom, in what register and
format), the claim pack chosen when the repository holds several, the artifacts the draft will
lean on, the gaps the intake found, and the validator results.

Ask only what the intake could not settle, for example:
- which pack or venue, when more than one exists (default: the most recently modified);
- the reader and register, when the manuscript source does not fix them (default: the venue's
  norm for the field, named);
- whether an existing section is to be redrafted or left to the reviser (default: left).

## Checkpoint 2: the claims (after the ledger)

Show the ledger as a compact table: ready, careful with the limitation that travels with each,
blocked with what is missing, proposed. Group by section. Hide excluded entries behind a count.

Ask:
- for each `proposed` entry, confirm, reword, or drop (default: drop; a proposed claim is never
  drafted into a framing section without a yes);
- for a `careful` entry the author wants asserted, which evidence would make it ready (default:
  stays careful);
- for a `blocked` entry, whether to leave a marker or omit the paragraph (default: marker).

The author may add a claim here. It enters the ledger with its support named, or as `proposed`.

## Checkpoint 3: the outline (before any prose)

This is the checkpoint that matters most. Show `outline.md`: one line per paragraph with its
topic sentence or job, the ledger IDs it carries, and the exhibit it draws on; sections in
drafting order; the budget per section; the questions list filled in. Ask the author to edit the
file or answer in the conversation, then run `outline_from_ledger.py --check` on the edited
outline and show the result.

Ask:
- whether the order of paragraphs inside each evidence section is the one the argument needs
  (default: the paper plan's order, else the audit's order);
- which exhibits each results paragraph points at (default: the ones the ledger names);
- what to do with unplaced entries (default: dropped from this piece, kept in the ledger).

No sentence of prose is written before the author approves the outline, or says in so many words
to draft without a review. The outline is also the fallback when the author is away: the drafter
finishes the outline, lists its questions with their defaults, and stops there.

## Checkpoint 4: each section (during drafting)

Draft the first section in the outline's order, run the two gates on it, and show it with the
gate lines and the markers it contains. Ask whether to accept it, revise it, or change the outline
before going on. After the author accepts one evidence-bearing section, continue section by
section, stopping again before the first framing section (introduction, abstract, summary),
because those are where an author most often wants a different emphasis than the evidence
sections suggest.

An author who says "draft the rest" after the first section gets the rest in one pass, with a
single checkpoint before the framing sections. An author who says "no checkpoints" at the start
gets the outline shown once and the draft in one pass; the outline is still produced and still
checked, because it is the cheapest place to catch a wrong claim.

## How to ask

- Show before asking. The author answers against something concrete (a table, an outline line),
  never against a description of what the drafter intends to do.
- At most three questions per checkpoint, each with its default. An author who answers nothing
  gets the defaults, and the handoff note records which defaults were taken.
- Ask about claims, order, emphasis, and reader. Do not ask about wording, which is the
  reviser's business, or about anything the artifacts already settle.
- When the runtime offers a structured way to ask (a choice prompt), use it for the defaults;
  otherwise write the questions as a numbered list at the end of the checkpoint message.
- Keep process commentary in the checkpoint message, never in the draft.
