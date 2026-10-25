---
name: technical-writing-drafter
description: Kickstart the writing of a manuscript section, abstract, technical report, or rebuttal response from its supporting artifacts (result audits, data tables and figures, experiment plans, literature reviews and evidence tables, novelty decisions, paper plans and claim-evidence bindings, rebuttal issue boards, author notes). Inventories the artifacts, builds a claim ledger that says what the draft may assert and at what strength, writes a one-page brief, drafts evidence-bearing sections before framing sections under the drafting contract, and gates the draft (every number traced to a source, machine-prose tells under a ceiling, claims matched to the ledger) before handing it to technical-writing-reviser. Use when there is no draft yet, or a section must be written from scratch, or a results folder and literature review need turning into prose, or the first draft of a reviewer response is needed from a decided issue board. Do not use to revise prose that exists (technical-writing-reviser), to smooth flow (prose-flow-improver), to decide the manuscript's claims and exhibits (research-paper-plan), to audit results (research-results-auditor), to decide what a rebuttal concedes (research-rebuttal), or to write claims no artifact supports.
---

# Technical Writing Drafter

## Overview

Write the first draft of reader-facing technical prose from the artifacts a research project
already has, so the writing rules apply at writing time instead of as a later patch. The skill
owns the stretch between "the results, the literature review, and the plan exist" and "a draft
exists that `technical-writing-reviser` can revise". It never decides what the claims are: the
paper plan, the audits, the literature review, and the issue board decide that, and the drafter
turns their decisions into prose at the strength they allow.

## Route the task

| Request | Route | Load first |
| --- | --- | --- |
| "Write the results section from the audit and the tables", "turn the results folder into a report" | Full path: intake, ledger, brief, draft, gates | `references/drafting-contract.md`, `references/artifact-intake.md` |
| "Draft the paper from the paper plan" | Full path with the bindings as the authoritative ledger; sections in the brief's order | `references/drafting-contract.md`, `references/claim-ledger.md` |
| "Write related work from the literature review" | Ledger from the evidence table and novelty decision; one section | `references/section-sources.md` |
| "Draft the response to reviewer 2 from the issue board" | Ledger from the board; response prose back to `research-rebuttal`'s pack | `references/drafting-contract.md`, `references/section-sources.md` (Rebuttal response) |
| "Write the abstract" with a drafted body | Lightweight path: ledger is the body's claims, no scripts beyond the gates | `references/drafting-contract.md` |
| "Draft the intro from my notes", no data or plan | Lightweight path: hand-written ledger with `proposed` entries, author confirms before framing | `references/claim-ledger.md` |
| "Fix the results section", "tighten the intro", a draft exists | Not this skill: `technical-writing-reviser` | |
| "Which claims can we make and which figures do we need" | Not this skill: `research-paper-plan` | |

## Quick start

```bash
D=<path to this skill>
R=<path to technical-writing-reviser>
python3 $D/scripts/inventory_artifacts.py <project root> --out-json writing-intake.json --out-md writing-intake.md
python3 $D/scripts/build_claim_ledger.py --intake writing-intake.json --out-json claim-ledger.json --out-md claim-ledger.md
# write the brief from references/writing-brief-template.md, then draft section by section
python3 $D/scripts/check_draft_numbers.py <draft> --source <results-audit.json> --source <table.csv> ...
python3 $R/scripts/prose_tells.py <draft> --max-density 20
```

For a short piece (an abstract, one paragraph, a brief from notes) skip the two inventory scripts,
write the claim list by hand in the ledger's shape, and still run the two gates.

## Workflow

### 1) Take stock of the artifacts

Run `scripts/inventory_artifacts.py` on the project root, or on the folder that holds the
results, literature, and plan. A research repository often holds several claim packs (one per
venue, workshop, or revision); the intake lists their directories, and the ledger is then built
from the one pack for the piece being drafted, passed to `build_claim_ledger.py` directly
rather than through `--intake`. Read `references/artifact-intake.md` to decide what each artifact
may contribute. Confirm the claim source: bindings are authoritative; audits or a claim map give a
derived ledger the author confirms; with neither, the drafter proposes claims from the data and
marks them `proposed`. Where the owning skill has a validator, run it read-only and record the
result in the brief. Record the intake's gaps; each becomes a marker in the draft or a line in
the handoff saying what was not drafted.

### 2) Build the claim ledger

Run `scripts/build_claim_ledger.py` with the intake or with the sources named directly. Read
`references/claim-ledger.md` for the status rules: `ready` is asserted at the recorded scope,
`careful` carries its limitation in the same passage, `blocked` appears only as
`[EVIDENCE NEEDED: what]` or `[CITATION NEEDED: what]`, `excluded` does not appear. Add
anything the author wants to say that no source carries as a `proposed` entry with the support it
would need. The ledger is the contract's claim list; the draft asserts nothing outside it.

### 3) Write the brief

Fill `references/writing-brief-template.md`: the job and reader, register and format, sources,
claims by status, terminology map, the skeleton with each section's job, ledger entries, and
budget, and the drafting order. Evidence-bearing sections (method, results, limitations) come
first, framing sections (related work, introduction, conclusion, abstract) last, so framing is
written from what the evidence sections actually say. For a full manuscript with no paper plan,
the brief's skeleton is not a substitute for one: run `research-paper-plan` first, or its
lightweight outline path for a short paper or report.

### 4) Draft under the contract

Read `references/drafting-contract.md` and the reviser's `machine-prose-tells.md` once. Then,
section by section in the brief's order, using `references/section-sources.md` for what each
section takes from which artifact:

- Write each asserting sentence against one ledger entry and tag it with a source comment
  (`<!-- PC-3 -->`, `% PC-3`) while drafting.
- Copy numbers from the source file into the sentence; never retype a number from memory or
  round it in the helpful direction. Give each measurement the uncertainty and scope the source
  reports.
- Cite only keys the bibliography, bib inventory, evidence table, or citation plan resolves.
- Write the measurement or the mechanism where a model draft would write an adjective; use a
  comma, period, parentheses, or colon where it would use a dash; end paragraphs on evidence or
  consequence; keep process commentary in the handoff note, not the prose.
- Keep the source format intact: macros, labels, citation keys, comments, and code spans.
- Stop at the budget. What the budget cuts is recorded in the handoff, never silently dropped
  from the claims.

Drafting is serial. A full manuscript is still one agent drafting in order, because framing
depends on the evidence sections; parallel section drafting is for a report whose sections share
no claims, and even then the abstract waits.

### 5) Gate the draft

1. `scripts/check_draft_numbers.py <draft> --source <audit> --source <table> ...`: every untraced
   number is fixed, sourced, marked, or listed with `--allow` and a reason in the brief.
2. `<reviser>/scripts/prose_tells.py <draft> --max-density 20`: revise above the ceiling; the
   target is under 10 per thousand words. Record the summary line.
3. Compare the draft's claims with the ledger. A claim without an entry gets an entry with its
   support or leaves the draft. A `careful` claim whose limitation drifted to another section
   is fixed.
4. Read the draft once as its reader. The scanner measures tells, not whether the passage says
   anything.

### 6) Hand off

Hand the draft, the brief, the ledger, and the gate results to `technical-writing-reviser` for
revision, with the markers and source comments visible. For a rebuttal, the paste-ready text
goes back to `research-rebuttal`'s pack. For a manuscript section, the draft goes to the source
tree and then to `research-review-loop` or `research-paper-review`. Record in the handoff note
or artifact index: the scanner line, the number-check line, the markers left in the draft, the
sections not drafted and why, and any `proposed` claims awaiting the author.

## What this skill does not do

- It does not decide claims, exhibits, or structure for a full manuscript (`research-paper-plan`),
  audit results (`research-results-auditor`), judge novelty (`research-novelty-review`), or decide
  what a rebuttal concedes (`research-rebuttal`).
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
- `scripts/check_draft_numbers.py <draft> --source ... [--allow N] [--format json]
  [--allow-untraced]`: traces every number in the draft to a source value, tolerating rounding
  and percentage conversion, and lists the gap markers. Exit 1 on an untraced number.
- The tells scanner lives in `technical-writing-reviser/scripts/prose_tells.py`; its
  `--max-density` gate is the drafter's ceiling.

## References

- `references/drafting-contract.md`: the one-page contract every first draft is written under.
- `references/artifact-intake.md`: what each artifact contributes and what never enters a draft.
- `references/claim-ledger.md`: ledger schema, derivation rules, and how to draft against it.
- `references/writing-brief-template.md`: the one-page brief and drafting order.
- `references/section-sources.md`: which artifact feeds each kind of section and what it may not do.
- From `technical-writing-reviser`: `claim-discipline.md`, `machine-prose-tells.md`,
  `register-and-format.md`, `terminology-conversion.md`.
