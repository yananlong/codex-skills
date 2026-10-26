# Venue Adapters

- If the venue is unknown, stay venue-agnostic and keep the structure conservative.
- If the venue has a tight page budget, prioritize the core claim, strongest evidence, and one clear exhibit plan.
- If the venue is method-heavy, ensure the mechanism and isolation evidence are explicit.
- If the venue is empirical, keep the evaluation protocol and strongest comparisons front and center.

## Venue facts

Page limits, response rules, anonymity, and timelines come from the shared venue table, `references/venues.json`, which `research-rebuttal` reads too. Never write a venue number into a plan from memory.

```bash
python3 scripts/venue_table.py show iclr-2026        # one venue's recorded facts
python3 scripts/venue_table.py diff iclr-2026 icml-2026   # what changes when porting between venues
```

Porting a paper between venues starts from that diff: each changed field (page limits, response format, revision policy, link rules) becomes a planning constraint. A row older than a year, or not `verified`, is flagged; treat its facts as assumptions to check, and record the gap in `paper-plan.md` rather than inventing a requirement. Where the table says `not stated`, the source is silent.
