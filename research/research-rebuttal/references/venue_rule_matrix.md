# Venue Rule Matrix

Last updated: 2026-03-24 (row dates now live in `venues.json`)

Use this file to select the correct rebuttal workflow for a target venue.

## Reading guide

Each venue entry tracks:

- primary artifact structure: one-shot PDF, per-review text response, threaded discussion, rolling review response, or single-feedback response
- interaction style: one-shot, threaded, or rolling
- submission mechanics
- revision policy during discussion
- notable prohibitions
- timeline details when available

Use `primary artifact structure` as the main routing key. Treat `interaction style` as a secondary execution detail.

## Matrix

The venue facts live in one table shared with `research-paper-plan`: `references/venues.json`. Each row records the rebuttal mode, response format and numeric limit, page limits, revision policy, anonymity and link rules, timeline details, sources, the date the facts were checked (`verified_on`), and a status (`verified`, `inferred` from official pages that say nothing, or `unverified`).

```bash
python3 scripts/venue_table.py list                 # every venue with its limit and freshness
python3 scripts/venue_table.py show icml-2026       # one row in full
python3 scripts/venue_table.py diff icml-2025 icml-2026   # what changes when porting
python3 scripts/venue_table.py check                # validate the table, flag stale or unverified rows
```

A row older than a year, or not `verified`, is flagged wherever it is printed. Re-check its sources before relying on it, then update the row and its `verified_on` date in `research-paper-plan` and copy the file here.

## Notes by family

### One-shot PDF venues

Representative venues:

- CVPR
- ICCV
- ECCV

Recommended workflow:

1. Aggregate repeated concerns.
2. Prioritize the 2-4 issues most likely to affect decisions.
3. Use compact tables or tiny figures only if explicitly allowed.
4. Avoid speculative promises that cannot fit into the one-page artifact.

### Threaded discussion venues

Representative venues:

- ICLR
- NeurIPS
- AISTATS
- UAI

Recommended workflow:

1. Reply quickly to major concerns.
2. Use per-review structure when the platform expects it.
3. Track follow-up questions and convert them into task items.
4. Keep revisions modest unless the venue explicitly invites stronger updates.
5. Check whether the venue allows paper revision during discussion at all, because AISTATS does not.

### Rolling-review venues

Representative venues:

- ARR
- ACL main conference via ARR
- TMLR

Recommended workflow:

1. Distinguish concerns that can be resolved now from concerns requiring a deeper revision.
2. Avoid spending too much space arguing with entrenched reviewers.
3. Prepare a revision plan, not just a response draft.

### Single-feedback venues

Representative venues:

- AAAI
- The Web Conference research tracks
- ACL Industry Track

Recommended workflow:

1. Assume there may be only one effective response window.
2. Prioritize reviewer questions that are explicitly decision-relevant.
3. Keep a separate task list of paper changes, because some venues do not allow revised manuscripts during feedback.

### Per-review rebuttal venues

Representative venues:

- ICML
- KDD Research / ADS
- The Web Conference 2026 Industry Track

Recommended workflow:

1. Keep each reply scoped to one review rather than a global essay.
2. Still maintain an internal merged-concern table to avoid contradictory answers.
3. Generate reviewer-specific drafts and a separate cross-review consistency check.

## Gaps to fill

The matrix still needs more complete official confirmation for:

- AAAI exact author feedback artifact format
- whether KDD imposes explicit character or page limits on each rebuttal response
- exact The Web Conference 2025 research-track rebuttal mechanics from an archived call or venue config
- whether SIGIR or WSDM publish separate workflow instructions outside the CFP that introduce an author-response stage
- additional CS venues such as COLM, WSDM industry tracks, UIST, SIGGRAPH, RSS, CoRL if desired

## Interpretation notes

- Entries that say "No official rebuttal stage found" are explicit conservative inferences from the cited official CFP pages as checked on 2026-03-24. They should be re-verified if a separate reviewer workflow page later appears.
- Entries that say "partially unconfirmed" should not be used for automatic skill routing without a fresh venue-specific check.
