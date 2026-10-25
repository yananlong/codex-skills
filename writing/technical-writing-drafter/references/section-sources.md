# Section Sources

Where each kind of section takes its content from, and what it may not do. The section
archetypes in `research-paper-plan/references/section-archetypes.md` say what each section is
for; this page says which artifact feeds it.

## Method, experimental setup, protocol

- Draws on the experiment plan and run blocks (what was run, on what, with which metric, against
  which baselines), the iteration loop's `program.md` when the work was a loop, the manuscript's
  existing notation.
- Write what was done in the past tense or the paper's convention, with every parameter and
  dataset name as the artifacts spell it. A hyperparameter not in the artifacts is
  `[EVIDENCE NEEDED: value of ...]`, not a plausible number.
- Never describe a run the run blocks do not contain, or a baseline the plan did not run.

## Results

- Draws on the results audit first (claim text, scope, verdict, limitations), then the tables and
  figures the audit names. Numbers are copied from the source file, never retyped from memory;
  `check_draft_numbers.py` is the check.
- One paragraph per audited claim or per exhibit, in the order the paper plan gives. State the
  measurement, the comparison, the uncertainty the source reports, and the scope. A `careful`
  claim carries its limitation in the same paragraph.
- Never aggregate across runs the audit excluded, round in the direction that helps, or state
  a mechanism the audit did not test.

## Limitations

- Draws on the audits' `limitations` and `scope`, the bindings' `partial` and `blocked` claims with
  their `missing_evidence`, the novelty decision's caveats, the author's own list.
- State each limitation once, as what the work covers and what it does not, without apology and
  without a compensating claim in the same sentence.
- Never list limitations nobody could have raised in order to look careful, or restate the
  scope that the results section already stated.

## Related work and background

- Draws on the literature evidence table (only `read` rows with a quote), the novelty report's
  closest prior work and surviving positioning, the bib inventory's resolved keys.
- One sentence per source, saying what it did and how the present work differs, in the terms the
  novelty decision uses. Group by the dimension of difference, not by year.
- Never cite a key the bibliography does not resolve, characterize a paper from its title or
  abstract when the evidence table says it was not read, or claim a difference the novelty
  review did not find.

## Introduction and contributions

- Draws on the idea brief or research brief (motivation), the ledger's `ready` primary claims
  (contributions), the results section as drafted.
- Each contribution sentence corresponds to one ledger entry and matches the strength of the
  results paragraph that supports it. Written after the results and limitations.
- Never promise a contribution the ledger marks `careful` or `blocked`, or widen the
  committed paper identity.

## Abstract and conclusion

- Draws on the drafted sections only.
- The abstract states the question, the method in one clause, the primary results with their
  numbers as the results section gives them, and the scope. The conclusion restates nothing the
  reader just read at the same length; it says what follows.
- Never contain a number or a claim that the body does not contain.

## Rebuttal response

- Draws on the issue board (issue, reviewer, strategy, status), the task list (what was done in
  response), the manuscript or new evidence the task produced.
- One response per issue in the board's order, opening with what the reviewer raised in neutral
  words, then what was done or why not, then where in the revision it appears. Concede exactly
  what the strategy says and no more.
- Never thank at length, concede an issue the board marks as contested, or cite evidence a
  task did not produce.

## Technical report and brief

- Draws on the audits, tables, and the planner's brief for a report; the project's status documents
  for a brief.
- The report's claim list is the audit's; a report on unaudited data describes what was
  measured and marks each interpretive sentence as the author's reading.
- Never carry a recommendation the evidence section does not support.
