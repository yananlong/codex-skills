# Artifact Intake

A draft is written from what the project already has. Before any prose, take stock of the
supporting artifacts, decide what each may contribute, and record what is missing so the draft
can show the gap instead of writing around it. `scripts/inventory_artifacts.py <root>` does the
mechanical part and writes `writing-intake.md` and `writing-intake.json`; this page says how to
read the result.

## What each artifact contributes

| Artifact (suite name, or the ordinary equivalent) | Contributes | Treat as |
| --- | --- | --- |
| `claim-evidence-bindings.json`, `claims-evidence-matrix.md`, `paper-plan.md` (research-paper-plan) | The manuscript's claims with support status, planned sections, exhibits, citation needs | Authoritative claim list and skeleton; the draft asserts nothing the bindings do not carry |
| `results-audit.json`, `results-audit.md` (research-results-auditor) | Audited bounded claims, verdicts, scope, limitations, evidence paths | The source of every result sentence and every number in the results section; a `weaken` effect makes the claim `careful`, `kill` or `inconclusive` makes it `blocked` |
| Result tables (`results.tsv`, CSV, JSON under results or metrics folders) | Raw numbers, run identities, configurations | Numbers only; a table without an audit supports a description of what was measured, not a verdict about what it shows |
| `claim-map.json`, `run-blocks.json`, `experiment-plan.md` (research-experiment-plan) | What was planned, falsifiers, anti-claims, protocol, metrics, baselines | Method and protocol prose; a planned claim is `blocked` until an audit or table tests it |
| `program.md`, `results.tsv`, `experiments.md` (iteration loop) | The frozen evaluation, the kept and discarded changes, the metric trajectory | Method prose about the loop and a results description bounded to the frozen metric |
| `<topic>.evidence-table.md`, `<topic>.review.md`, corpus manifest (research-systematic-literature-review) | Studies with fetch status, rung, key result, verbatim quote | Related-work and background sentences, one per `read` row with a quote; rows not read or without a quote are `[CITATION NEEDED]` |
| `novelty-report.md`, `prior-art-matrix.md`, `novelty-decision.json` (research-novelty-review) | The positioning that survived review, the closest prior work, the differences that hold | The exact positioning sentence for introduction and related work; never a stronger one |
| `literature-context.md`, `citation-plan.md`, `bib-inventory.json`, `citation-audit.md` | Citation keys that exist, keys that are missing, what each need covers | Only keys listed as resolved may be cited; a need with no key is `[CITATION NEEDED: what]` |
| `issue-board.md`, `task-list.md` (research-rebuttal) | What each reviewer raised, the decided strategy, what may be conceded | Response prose follows the board's strategy per issue; an issue without a strategy is not drafted |
| `REVIEW_STATE.json`, `final_issues.json` (review loop, paper review) | Open critique against an existing draft | Revision input for `technical-writing-reviser`, not drafting input, unless a section is being redrafted from scratch |
| `research-brief.md`, `artifact-index.md`, `research-commitment.json` (pipeline planner) | Paper identity, the committed claims, the stage the project is in | Scope and identity; a draft may not widen the committed identity |
| `idea-brief.md` (research-idea-discovery) | Motivation and the question as first posed | Motivation prose, checked against what the evidence later supported |
| LaTeX or Markdown manuscript source, `.bib` files | Existing sections, macros, labels, citation keys, register | Source format and register; existing sections are revision input, missing ones are drafting targets |
| Figures (`figures/`, `figs/`, `plots/`) | Exhibits with their captions and the numbers they show | Referenced by label; a figure's number is a source for the number checker only if the data behind it is also present |
| Author notes, README, meeting notes | Intent, framing the author wants, terminology | Framing and terminology; never evidence |

## Reading the intake

1. Pick the pack. A repository with several experiment plans or paper packs lists each
   directory under `claim_pack_dirs`; the ledger is built from the one pack that belongs to the
   piece being drafted, and the intake's other packs are context, not claims.
2. Confirm the claim source. With bindings, the ledger follows them. With audits or a claim map
   only, the ledger is derived and the author confirms it before framing sections are drafted.
   With neither, the drafter proposes claims the data can bear, marks every one `proposed`, and
   drafts only the evidence-bearing sections until the author confirms the list.
3. Check freshness and validation where the owning skill has a validator (`validate_paper_pack.py`,
   `validate_results_audit.py`, `validate_experiment_pack.py`, `validate_iteration_ledger.py`).
   Run it read-only. A pack that fails validation still informs the draft, but the brief records
   the failure and the draft does not assert anything that depends on the failed part.
4. Note the format and register from the manuscript source or the venue. Read the reviser's
   `register-and-format.md` for LaTeX or for anything outside empirical machine learning.
5. Record the gaps the intake names. Each becomes either a `[EVIDENCE NEEDED]` or
   `[CITATION NEEDED]` marker in the draft, or a line in the handoff note saying the section was
   not drafted.

## What never enters a draft

- A number that is not in a data artifact or an audit (`check_draft_numbers.py` enforces this).
- A citation key that no bibliography, bib inventory, evidence table, or citation plan lists.
- A result for a claim the ledger marks `blocked`, in any wording.
- A reviewer concession the issue board did not decide.
- Private material the project marks as not for the manuscript (internal notes, unreleased data,
  names of people who did not consent). When in doubt, leave it out and say so in the handoff.
