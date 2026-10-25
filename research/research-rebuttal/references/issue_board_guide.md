# Issue Board Guide

Last updated: 2026-03-24

Use this file when building or maintaining the Issue Board during the rebuttal workflow. The board is the single source of truth for tracking reviewer concerns across all stages.

Design influences: the issue board concept is adapted from the rebuttal skill by wanshuiyin ([source](https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep)).

## Board Schema

| Field | Values | Description |
|---|---|---|
| `issue_id` | EXT-R1-1, EXT-R1-2, EXT-R2-1, ... | `EXT-<reviewer handle>-<n>`; the `EXT-` prefix keeps external IDs apart from internal review-loop or paper-review IDs such as `R2-1` or `F3` |
| `reviewer` | R1, R2, R3, ... | Reviewer handle as recorded in the score matrix (`Platform ID` keeps the full platform name, e.g. `Reviewer xK3p`) |
| `internal_issue_ids` | (optional) F3, PR12, ... | Matching internal issue IDs from `REVIEW_STATE.json` or `final_issues.json` |
| `severity` | Major-Blocking / Major-Addressable / Minor / Misunderstanding | Decision impact level |
| `category` | soundness, novelty, baselines, ablations, clarity, theory, limitations, ethics, reproducibility, minor-edits | Concern type |
| `strategy` | Accept, Clarify, Partial-agree, Defend, Out-of-scope, Escalate, or combos | Response approach from Stage 2 |
| `reviewer_stance` | Champion / Persuadable / Entrenched | Reviewer's overall disposition |
| `status` | open → in-progress → drafted → done / deferred | Resolution progress |
| `shared_with` | (optional) Other issue_ids for the same concern | Cross-reviewer grouping |
| `notes` | (optional) Free text | Evidence sources, blockers, decisions |

## Worked Example

Scenario: 3 reviewers for an ICML 2026 submission. Scores: R1=4, R2=6, R3=5. Here R1-R3 stand in for the platform reviewer handles.

### After Stage 1 (Analysis)

```
issue_id | reviewer | severity          | category     | strategy | stance      | status | shared_with
EXT-R1-1 | R1       | Major-Blocking    | baselines    | (TBD)    | Entrenched  | open   | EXT-R3-2
EXT-R1-2 | R1       | Major-Addressable | theory       | (TBD)    | Entrenched  | open   |
EXT-R1-3 | R1       | Minor             | clarity      | (TBD)    | Entrenched  | open   |
EXT-R2-1 | R2       | Major-Addressable | ablations    | (TBD)    | Persuadable | open   |
EXT-R2-2 | R2       | Minor             | minor-edits  | (TBD)    | Persuadable | open   |
EXT-R3-1 | R3       | Misunderstanding  | novelty      | (TBD)    | Persuadable | open   |
EXT-R3-2 | R3       | Major-Blocking    | baselines    | (TBD)    | Persuadable | open   | EXT-R1-1
EXT-R3-3 | R3       | Minor             | clarity      | (TBD)    | Persuadable | open   |
```

Key observations:
- EXT-R1-1 and EXT-R3-2 share the same baseline concern — respond once in a global section.
- R1 is Entrenched (score 4) — invest in evidence density, not persuasion.
- R2 and R3 are Persuadable — primary conversion targets.

### After Stage 2 (Strategy Selection)

```
issue_id | severity          | strategy                | status
EXT-R1-1 | Major-Blocking    | Accept + New evidence   | open       [global: shared with EXT-R3-2]
EXT-R1-2 | Major-Addressable | Partial-agree + Narrow  | open
EXT-R1-3 | Minor             | Accept                  | open
EXT-R2-1 | Major-Addressable | Accept + New evidence   | open
EXT-R2-2 | Minor             | Accept                  | open
EXT-R3-1 | Misunderstanding  | Clarify + Accept partial| open
EXT-R3-2 | Major-Blocking    | (see EXT-R1-1)          | open
EXT-R3-3 | Minor             | Clarify                 | open
```

### After Stage 5 (Pre-submission)

```
issue_id | severity          | strategy                | status
EXT-R1-1 | Major-Blocking    | Accept + New evidence   | done   ✓
EXT-R1-2 | Major-Addressable | Partial-agree + Narrow  | done   ✓
EXT-R1-3 | Minor             | Accept                  | done   ✓
EXT-R2-1 | Major-Addressable | Accept + New evidence   | done   ✓
EXT-R2-2 | Minor             | Accept                  | done   ✓
EXT-R3-1 | Misunderstanding  | Clarify + Accept partial| done   ✓
EXT-R3-2 | Major-Blocking    | (see EXT-R1-1)          | done   ✓
EXT-R3-3 | Minor             | Clarify                 | done   ✓
```

All Major-Blocking and Major-Addressable issues are done → Coverage Gate passes.

### After Stage 6 Round 1 (Follow-up from R1)

R1 pushes back on EXT-R1-1, asking for a specific additional dataset. New issue added:

```
issue_id | severity          | strategy              | status
EXT-R1-4 | Major-Addressable | Accept + New evidence | open    [follow-up to EXT-R1-1]
```

## Cross-Review Consistency Check

Before finalizing, scan the board for contradictions:

1. **Shared concerns**: If EXT-R1-1 and EXT-R3-2 are the same concern, verify both reviewers receive the same answer (or that the per-reviewer framing is consistent).
2. **Claim scope**: If you narrowed a claim for R1 (EXT-R1-2: "narrowed Theorem 2"), verify you did not leave the broad claim intact in a response to R3.
3. **Evidence reuse**: If you cite a new experiment for EXT-R2-1, check whether the same experiment addresses any other open issues on the board.

## Coverage Gate Verification

Run this check before marking the rebuttal as final:

1. Filter the board to `severity = Major-Blocking OR Major-Addressable`.
2. Verify every filtered issue has `status = done`.
3. If any issue is `deferred`, confirm the user explicitly approved the deferral and that the rebuttal acknowledges it (e.g., as a stated limitation or future work).
4. Minor issues should be at least acknowledged — a single sentence ("We have corrected all typos") suffices for grouped minor items.
