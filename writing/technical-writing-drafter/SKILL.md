---
name: technical-writing-drafter
description: Kickstart the writing of a manuscript section, abstract, technical report, or rebuttal response from its supporting artifacts (result audits, data tables and figures, experiment plans, literature reviews and evidence tables, novelty decisions, paper plans and claim-evidence bindings, rebuttal issue boards, author notes), working with the author at checkpoints. Inventories the artifacts, builds a claim ledger that says what the draft may assert and at what strength, produces a paragraph-level outline for the author to edit before any prose is written, then drafts section by section under the drafting contract, evidence-bearing sections first, showing each section with its gates (every number traced to a source, machine-prose tells under a ceiling, claims matched to the ledger) before handing the whole to technical-writing-reviser. Use when there is no draft yet, when the author wants an outline before committing to prose, when a results folder and literature review need turning into a paper or report, or when the first draft of a reviewer response is needed from a decided issue board. Do not use to revise prose that exists (technical-writing-reviser), to smooth flow (prose-flow-improver), to decide the manuscript's claims and exhibits (research-paper-plan), to audit results (research-results-auditor), to decide what a rebuttal concedes (research-rebuttal), or to write claims no artifact supports.
---

# Technical Writing Drafter

## Overview

Write the first draft of reader-facing technical prose from the artifacts a research project
already has, so the writing rules apply at writing time instead of as a later patch. The skill
owns the stretch between "the results, the literature review, and the plan exist" and "a draft
exists that `technical-writing-reviser` can revise". It never decides what the claims are: the
paper plan, the audits, the literature review, and the issue board decide that, and the drafter
turns their decisions into prose at the strength they allow.

It works with the author rather than ahead of them. The first deliverable is an outline, one line
per paragraph with the claims and exhibits each carries, which the author edits before a sentence
of prose exists. Drafting then proceeds section by section, each shown with its gate results, with
the author able to change the outline between sections. `references/checkpoints.md` fixes the four
stopping points, what is shown at each, and the defaults taken when the author is away.

## Route the task

| Request | Route | Load first |
| --- | --- | --- |
| "Write the results section from the audit and the tables", "turn the results folder into a report" | Full path: intake, ledger, outline (checkpoint), draft section by section, gates | `references/checkpoints.md`, `references/artifact-intake.md` |
| "Give me an outline of the paper from the plan and the audits before we write anything" | Outline path: intake, ledger, outline, stop at checkpoint 3 | `references/checkpoints.md`, `references/claim-ledger.md` |
| "Draft the paper from the paper plan" | Full path with the bindings as the authoritative ledger; sections in the outline's order | `references/drafting-contract.md`, `references/claim-ledger.md` |
| "Write related work from the literature review" | Ledger from the evidence table and novelty decision; one-section outline, then the section | `references/section-sources.md` |
| "Draft the response to reviewer 2 from the issue board" | Ledger from the board; outline is one line per issue; response prose back to `research-rebuttal`'s pack | `references/section-sources.md` (Rebuttal response) |
| "Write the abstract" with a drafted body | Lightweight path: ledger is the body's claims, a five-line outline shown once, then the paragraph | `references/drafting-contract.md` |
| "Draft the intro from my notes", no data or plan | Lightweight path: hand-written ledger with `proposed` entries, outline shown, author confirms before prose | `references/claim-ledger.md`, `references/checkpoints.md` |
| "Fix the results section", "tighten the intro", a draft exists | Not this skill: `technical-writing-reviser` | |
| "Which claims can we make and which figures do we need" | Not this skill: `research-paper-plan` | |

## Quick start

```bash
D=<path to this skill>
R=<path to technical-writing-reviser>
python3 $D/scripts/inventory_artifacts.py <project root> --out-json writing-intake.json --out-md writing-intake.md
# checkpoint 1: show the intake summary, settle the pack, reader, register
python3 $D/scripts/build_claim_ledger.py --bindings <pack>/claim-evidence-bindings.json --results-audit <pack>/results-audit.json \
    --evidence-table <topic>.evidence-table.md --out-json claim-ledger.json --out-md claim-ledger.md
# checkpoint 2: show the ledger table, settle proposed and careful claims
python3 $D/scripts/outline_from_ledger.py --ledger claim-ledger.json --out outline.md --piece manuscript
# checkpoint 3: the author edits outline.md; then
python3 $D/scripts/outline_from_ledger.py --ledger claim-ledger.json --check outline.md
# draft one section, then gate it and show it (checkpoint 4), then the next
python3 $D/scripts/check_draft_numbers.py <section> --source <results-audit.json> --source <table.csv> ...
python3 $R/scripts/prose_tells.py <section> --max-density 20
```

For a short piece (an abstract, one paragraph, a brief from notes) skip the inventory script,
write the claim list by hand in the ledger's shape, show a five-line outline once, and still run
the two gates.

## Workflow

### 1) Take stock of the artifacts, then checkpoint 1

Run `scripts/inventory_artifacts.py` on the project root, or on the folder that holds the
results, literature, and plan. A research repository often holds several claim packs (one per
venue, workshop, or revision); the intake lists their directories, and the ledger is then built
from the one pack for the piece being drafted, passed to `build_claim_ledger.py` directly
rather than through `--intake`. Read `references/artifact-intake.md` to decide what each artifact
may contribute. Where the owning skill has a validator, run it read-only.

Show the author the intake summary (the piece, the pack, the sources, the gaps, the validator
results) and ask only what it could not settle: which pack, which reader and register, whether an
existing section is redrafted. Defaults are in `references/checkpoints.md`.

### 2) Build the claim ledger, then checkpoint 2

Run `scripts/build_claim_ledger.py` with the chosen sources. Read `references/claim-ledger.md`
for the status rules: `ready` is asserted at the recorded scope, `careful` carries its limitation
in the same passage, `blocked` appears only as `[EVIDENCE NEEDED: what]` or
`[CITATION NEEDED: what]`, `excluded` does not appear. Anything the author wants to say that no
source carries enters as a `proposed` entry with the support it would need.

Show the ledger as a compact table grouped by section. Settle each `proposed` entry (confirm,
reword, drop), any `careful` entry the author wants asserted, and marker-or-omit for `blocked`
entries. The ledger is the contract's claim list; the draft asserts nothing outside it.

### 3) Outline, then checkpoint 3

Run `scripts/outline_from_ledger.py --ledger claim-ledger.json --out outline.md --piece <kind>`.
The outline has one line per paragraph: the topic sentence or job, the ledger IDs it carries, and
the exhibit it draws on, with sections in drafting order (evidence-bearing first, framing last)
and a budget per section. Fill in the outline's questions list (at most three, each with its
default) and the short brief from `references/writing-brief-template.md` (job, reader, register,
format, sources, terminology).

Show the outline and stop. The author edits lines, reorders, deletes, or adds; then run
`outline_from_ledger.py --check outline.md` and show the result. No prose is written until the
author approves the outline or says in so many words to draft without review. When the author
is away, the outline with its questions and defaults is the deliverable, and the handoff note
says so. For a full manuscript with no paper plan, the outline is not a substitute for one: run
`research-paper-plan` first, or its lightweight outline path for a short paper or report.

### 4) Draft section by section under the contract, checkpoint 4 between sections

Read `references/drafting-contract.md` and the reviser's `machine-prose-tells.md` once. Then take
the sections in the outline's order, using `references/section-sources.md` for what each section
takes from which artifact:

- Write each paragraph from its outline line and each asserting sentence against one ledger
  entry, tagged with a source comment (`<!-- PC-3 -->`, `% PC-3`) while drafting.
- Copy numbers from the source file into the sentence; never retype a number from memory or
  round it in the helpful direction. Give each measurement the uncertainty and scope the source
  reports.
- Cite only keys the bibliography, bib inventory, evidence table, or citation plan resolves.
- Write the measurement or the mechanism where a model draft would write an adjective; use a
  comma, period, parentheses, or colon where it would use a dash; end paragraphs on evidence or
  consequence; keep process commentary in the checkpoint message, not the prose.
- Keep the source format intact: macros, labels, citation keys, comments, and code spans.
- Stop at the budget. What the budget cuts is recorded in the handoff, never silently dropped
  from the claims.

After the first section, run the two gates on it and show it with the gate lines and its markers.
Ask whether to accept, revise, or change the outline. Then continue section by section, and stop
once more before the first framing section, where authors most often want a different emphasis
than the evidence sections suggest. "Draft the rest" after the first section means one pass with
that single remaining stop.

Drafting is serial. A full manuscript is one agent drafting in order, because framing depends on
the evidence sections; parallel section drafting is for a report whose sections share no claims,
and even then the abstract waits.

### 5) Gate each section and the whole

1. `scripts/check_draft_numbers.py <draft> --source <audit> --source <table> ...`: every untraced
   number is fixed, sourced, marked, or listed with `--allow` and a reason in the brief.
2. `<reviser>/scripts/prose_tells.py <draft> --max-density 20`: revise above the ceiling; the
   target is under 10 per thousand words. Record the summary line.
3. Compare the draft's claims with the ledger and the outline. A claim without an entry gets an
   entry with its support or leaves the draft. A `careful` claim whose limitation drifted to
   another section is fixed. A paragraph the outline did not have is either added to the outline
   or removed.
4. Read the draft once as its reader. The scanner measures tells, not whether the passage says
   anything.

### 6) Hand off

Hand the draft, the brief, the ledger, the approved outline, and the gate results to
`technical-writing-reviser` for revision, with the markers and source comments visible. For a
rebuttal, the paste-ready text goes back to `research-rebuttal`'s pack. For a manuscript section,
the draft goes to the source tree and then to `research-review-loop` or `research-paper-review`.
Record in the handoff note or artifact index: the scanner line, the number-check line, the
markers left in the draft, the sections not drafted and why, any `proposed` claims awaiting the
author, and the defaults taken at checkpoints the author did not answer.

## What this skill does not do

- It does not decide claims, exhibits, or structure for a full manuscript (`research-paper-plan`),
  audit results (`research-results-auditor`), judge novelty (`research-novelty-review`), or decide
  what a rebuttal concedes (`research-rebuttal`).
- It does not draft ahead of the author. The outline is approved before prose exists, and each
  section is shown before the next is written, unless the author asks for one pass.
- It does not revise prose that exists (`technical-writing-reviser`) or smooth flow
  (`prose-flow-improver`). A draft that comes back from review with wording problems goes to the
  reviser; a section that must be rewritten from scratch against new evidence comes back here.
- It does not write a result, a number, a citation, or a concession that no artifact supports.
  The marker is the honest sentence for a gap.

## Scripts

- `scripts/inventory_artifacts.py <root> [--out-json] [--out-md]`: classifies the project's
  files into claim sources, evidence, data, literature, critique, structure, source, notes, and
  reports the gaps.
- `scripts/build_claim_ledger.py [--intake] [--bindings] [--results-audit] [--claim-map]
  [--evidence-table] [--issue-board] [--out-json] [--out-md]`: derives the ledger with status
  per claim. Exit 1 when no source yields a claim, so a hand-written ledger is needed.
- `scripts/outline_from_ledger.py --ledger L --out outline.md [--piece manuscript|report|response]
  [--sections a,b,c]`: one line per paragraph from the ledger, in drafting order, with unplaced
  entries and a questions list; `--check outline.md` exits 1 when a ready or careful claim has no
  paragraph, an ID is not in the ledger, or a blocked claim appears without a marker.
- `scripts/check_draft_numbers.py <draft> --source ... [--allow N] [--format json]
  [--allow-untraced]`: traces every number in the draft to a source value, tolerating rounding
  and percentage conversion, and lists the gap markers. Exit 1 on an untraced number.
- The tells scanner lives in `technical-writing-reviser/scripts/prose_tells.py`; its
  `--max-density` gate is the drafter's ceiling.

## References

- `references/drafting-contract.md`: the one-page contract every first draft is written under.
- `references/artifact-intake.md`: what each artifact contributes and what never enters a draft.
- `references/claim-ledger.md`: ledger schema, derivation rules, and how to draft against it.
- `references/checkpoints.md`: the four stopping points, what is shown, what is asked, the defaults.
- `references/writing-brief-template.md`: the short brief that travels with the outline.
- `references/section-sources.md`: which artifact feeds each kind of section and what it may not do.
- From `technical-writing-reviser`: `claim-discipline.md`, `machine-prose-tells.md`,
  `register-and-format.md`, `terminology-conversion.md`.
