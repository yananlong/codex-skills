# Drafting Contract

Any skill that produces prose for a reader (a manuscript section or abstract, a rebuttal
response, a review summary, a literature or novelty report, a research brief) writes it under
this contract from the first draft. Drafting without it and revising afterwards is how bad first
drafts were patched in earlier workflows; one draft written under the contract costs less than
the draft plus the patch, and the patch never fully removes what the draft baked in.

The contract is the revision skill's rules applied at writing time. It is short because the
details live in the references it names, which the drafting agent reads when the case calls for
them.

## Before writing

1. Name the job of the passage (motivation, method, result, limitation, response to a reviewer,
   summary of a critique, recommendation) and the reader (a venue reviewer, an author, a project
   owner). Write toward that job, not toward a generic technical tone.
2. Name the register (empirical ML, ML theory, vision or systems, NLP or position paper, HCI or
   social science, technical report) and the source format (LaTeX, Markdown, plain text). Read
   `register-and-format.md` for anything outside empirical ML in Markdown.
3. List the claims the passage will make with their support (`claim-discipline.md`): the claims to
   make, the claims to be careful about, and the claims to avoid. A draft may not assert a claim
   that has no entry on this list. Where evidence is missing, the draft says so visibly with a
   marker such as `[EVIDENCE NEEDED: what]` rather than writing around the gap.
4. Fix the terminology: defined terms are used exactly and consistently, internal labels are
   translated once (`terminology-conversion.md`), coined terms are kept and glossed.
5. Note any length budget and what the budget may not cut (claims, caveats, results).

## While writing

- State the supported proposition directly. Do not invent a position in order to reject it
  (`claim-discipline.md`, Avoid Manufactured Rebuttals).
- Give a formal statement its hypotheses as scope and no empirical hedge. Give an argument its
  premise and the verb "we argue". Give an empirical result its measurement and its uncertainty.
- Write the measurement or the mechanism where a model draft would write an adjective. Write the
  fact and stop where a model draft would add a participial tail announcing importance. End a
  paragraph on its evidence or its consequence, in a sentence of ordinary length, and vary
  paragraph shape (`machine-prose-tells.md`).
- Use a comma, a period, parentheses, or a colon where a model draft would use a dash.
- Keep every number, citation key, label, macro, and comment attached to the clause it belongs to
  in the source format.
- Keep process commentary out of the prose. Notes to the author go in a separate note, never in
  the manuscript text.

## After writing

1. Run `python3 <technical-writing-reviser>/scripts/prose_tells.py <draft> --max-density 20`.
   A draft above 20 tells per thousand words is revised before it leaves the skill; the target is
   under 10. Record the scanner's summary line in the artifact index or handoff note so the next
   stage can see it.
2. Read the draft once as its reader. The scanner measures tells, not quality; a passage can score
   zero and still say nothing.
3. Compare the draft's claims with the list from step 3 above. A claim that appeared without an
   entry is either added to the list with its support or removed from the draft.
4. Hand the draft on with the claim list and the evidence-needed markers visible. The receiving
   stage (review loop, paper review, the author) decides about the gaps; the draft never hides them.

## Who runs it

- `technical-writing-reviser` in drafting mode owns manuscript prose drafted from a paper plan,
  bound claims, an outline, or notes, and rebuttal response prose drafted from an issue board.
- Every other skill that writes reader-facing prose as part of its own artifacts (a review
  summary, an audit narrative, a novelty or literature report, a research brief) applies this
  contract itself and names it in the artifact.
- `prose-flow-improver` runs after, as a constrained pass, never as the drafter.

When the writing skills are not installed beside a research skill, the contract still applies as
written here; the scanner step is skipped and the handoff note says so.
