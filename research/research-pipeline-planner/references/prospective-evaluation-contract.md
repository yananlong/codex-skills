# Prospective Research-Suite Evaluation Contract

Use this contract only after the structural and semantic controls from PRs 11-16 are merged. Its purpose is to collect and validate genuinely prospective evidence about research convergence, literature recall, and adverse-evidence retention.

A passing validator establishes repository-local consistency of the study protocol, custody declarations, project accounting, and derived metrics. It does not create prospective observations, prove causal effectiveness, establish literature completeness, or certify scientific validity.

## Canonical artifacts

A study pack contains:

```text
prospective-protocol.json
prospective-observations.json
prospective-summary.json
```

- `prospective-protocol.json` is the frozen study authority.
- `prospective-observations.json` is the complete enrolled-project ledger.
- `prospective-summary.json` is a derived projection and conclusion authority.

The summary may not override the protocol or observations.

## Evidence levels

The study distinguishes:

1. `instrumentation_only`: the artifacts are structurally consistent, but no prospective conclusion is authorized;
2. `prospective_descriptive`: genuinely new projects were observed under a frozen protocol, but no comparative effectiveness claim is authorized;
3. `comparative_exploratory`: a frozen comparison exists, but the design or assurance conditions support only exploratory comparative language;
4. `comparative_confirmatory`: the protocol, allocation, independence, complete accounting, and frozen thresholds support a bounded confirmatory comparison.

Development fixtures, retrospective histories, and topics inspected while tuning the implementation cannot count as prospective observations.

## Protocol freeze

Before any enrolled project starts, freeze:

- study ID and protocol version;
- design class and assurance class;
- primary and secondary endpoints;
- project eligibility and exclusion rules;
- enrollment target and stopping rule;
- missing-data and technical-failure policies;
- challenge custodian and challenge-set digest;
- evaluator independence and self-review status;
- comparison design, allocation, information access, sample-size rule, uncertainty method, and effect thresholds where comparative authority is intended;
- conclusion ceilings and downgrade rules.

The canonical SHA-256 digest excludes only the `protocol_digest` field itself. A frozen protocol whose digest does not match fails.

Outcome-informed amendments are permitted only as explicit, versioned disclosures. They forbid `comparative_confirmatory` authority.

## Project accounting

Every enrolled project appears exactly once as `included` or `excluded`.

An exclusion must:

- cite a rule frozen before outcome inspection;
- be recorded before the outcome;
- provide a substantive rationale;
- provide evidence paths.

An included project must:

- be genuinely new;
- have had no implementation-tuning access;
- start after the protocol freeze;
- record complete outcome accounting;
- use the frozen protocol version;
- end in `execute`, `submit`, `split`, `park`, `kill`, or remain `unresolved`.

A terminal project records an end timestamp. An unresolved project must not claim one.

## Transition evaluation

Each transition observation records:

- stable transition ID;
- blinded or disclosed adjudication;
- ground-truth class: `major` or `nonmajor`;
- suite alert class: `major`, `nonmajor`, or `none`;
- adjudicated D0-D4 class.

Derived metrics include major-drift sensitivity and major-alert false-positive rate.

## Literature challenge custody

The protocol freezes one challenge-set digest and names the custodian before search.

Each project records visible seed IDs and hidden challenge records. A hidden record:

- must not overlap a visible seed;
- must not be visible before search;
- carries a positive importance weight;
- records initial and post-repair recovery;
- names a repair when recovered only after a miss.

Post-repair recovery cannot lose an initially recovered record.

Derived metrics include initial recall, post-repair recall, importance-weighted post-repair recall, and repair gain.

## Evidence retention

Every technically valid scientific outcome is classified as `positive`, `negative`, `null`, or `contradictory`.

Valid adverse outcomes must remain in the audit and receive a manuscript disposition other than unqualified assertion. Derived adverse-evidence retention is computed from the included project records rather than declared in the summary.

## Convergence outcomes

Each project records:

- final route state;
- transition count;
- start and end timestamps;
- late conclusion-changing omissions;
- deviations.

Derived outcomes include terminal-route rate, median days to a terminal state, median identity transitions to a terminal state, and late-omission rate.

## Comparative authority

Comparative conclusions require both `suite` and `comparator` projects under a frozen design.

The summary must reproduce every frozen effect threshold. For a `higher` endpoint, the effect is `suite - comparator`; for a `lower` endpoint, it is `comparator - suite`.

`comparative_confirmatory` additionally requires:

- a confirmatory protocol;
- no outcome-informed amendment;
- non-self review;
- separation across context, evaluation, and advancement authority;
- every frozen threshold met;
- complete project accounting and the frozen enrollment target.

A validator pass does not establish that the comparator is substantively adequate beyond the declared evidence.

## Scripts

- `scripts/init_prospective_evaluation.py`: create deterministic draft protocol, observation, and summary artifacts.
- `scripts/validate_prospective_evaluation.py`: validate structural or completed prospective packs and recompute all metrics.

## Bounded conclusion

Passing structural validation means the declared artifacts are internally consistent under the selected profile. Passing prospective validation means the completed records satisfy the frozen repository-local protocol and support no stronger conclusion authority than the validator accepts.

Neither result proves general effectiveness, causal benefit, literature completeness, scientific correctness, independent replication, authenticated execution, or external immutability.
