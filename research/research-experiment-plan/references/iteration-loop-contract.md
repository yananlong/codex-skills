# Iteration Loop Contract

Use this contract for autonomous hill-climbing on one frozen metric: the agent edits a bounded
set of files, runs a fixed-budget evaluation, keeps the change if the metric improved and reverts
it otherwise, logs every attempt, and repeats without pausing. The design follows Karpathy's
autoresearch loop (one mutable file, one metric, a fixed time budget, an append-only ledger, keep
or discard by commit) and its forks (experiment cards with hypotheses and lessons, an advisory
idea queue, a frozen exam the optimizer cannot edit).

The loop is the right tool when the question is "how good can this get under a fixed budget", not
"is this claim true". A loop result is exploratory evidence until a results audit says otherwise.

## Separation of exam and study

Two sets of files, declared in `program.md` before the first run:

- **Mutable set**: what the agent may edit. Keep it small, ideally one file, so each diff is
  reviewable and each iteration tests one idea.
- **Frozen set**: the evaluator, data preparation, metric definition, and run budget. The agent
  never edits these during the loop. If the exam must change, stop the loop, change it with a
  human, re-run the baseline, and start a new ledger.

The agent that builds the exam and the agent that studies for it must not be the same run. A loop
that can move its own goalposts measures nothing.

## The metric and the budget

One primary metric with a stated direction (lower or higher is better), computed by the frozen
evaluator and printed as a greppable line. One fixed budget per run (wall-clock seconds, steps,
tokens, or dollars) enforced by the frozen code, so every iteration is comparable regardless of
what the agent changed. Secondary costs (memory, latency, parameter count) are soft constraints
recorded per run, with a stated tolerance.

## The simplicity criterion

All else equal, simpler is better. A small gain that adds ugly complexity is not worth keeping.
An equal result from deleting code is a win and is kept. State the exchange rate in `program.md`
(for example: a change of less than X in the metric does not justify more than N added lines).

## The ledger

`results.tsv` is append-only, tab-separated, one row per completed run, never edited after the
fact and never committed on the experiment branch (it is the record of the branch, not part of
it). Columns:

```
commit	metric	cost	status	description
```

- `commit`: the 7-character short hash of the commit that was evaluated.
- `metric`: the primary metric as printed by the evaluator; `0` for a crash.
- `cost`: the recorded secondary cost (for example peak memory in GB); `0` for a crash.
- `status`: `keep`, `discard`, or `crash`.
- `description`: one line, no tabs, saying what the run tried.

The first row is always the untouched baseline. `keep` rows must improve on the best kept metric
so far in the declared direction; the validator enforces this, so a keep that did not improve is
a logging error, not a judgment call.

## The lab notebook

`experiments.md` holds one entry per run, written before the run as a hypothesis and completed
after it. The entry is what lets a later agent, or the same agent after a context reset, learn
from the attempt rather than repeat it:

```
## <commit> <status>
- Changed: <the specific edit, not "improved X">
- Why: <the failure pattern or observation that motivated it>
- Expected: <the predicted effect and the risk>
- Prior: <commits or ideas this builds on>
- Result: <metric and cost; what actually happened>
- Lesson: <what this teaches about the search space>
- Next if this fails: <the fallback>
```

## The idea queue

`ideas.md` is an advisory queue. Each line is a hypothesis with a priority and a tag. The agent
takes the highest-priority idea it has not tried unless it has a stronger hypothesis of its own,
and appends ideas as the notebook teaches it. Coverage by tag (how many attempts, how many kept,
best gain) tells the agent where the search has not looked.

## The loop

```
LOOP until the iteration budget or stop criterion in program.md is reached:
  1. Read the ledger tail and the notebook; pick an idea.
  2. Write the notebook entry (Changed, Why, Expected, Prior).
  3. Edit the mutable set. Commit.
  4. Run the frozen evaluator with output redirected to a log file; read only the metric lines.
  5. Empty metric line means a crash: read the log tail. Fix a trivial error once; otherwise log
     `crash` and move on.
  6. Append the ledger row. Complete the notebook entry (Result, Lesson, Next).
  7. Improved: keep the commit. Otherwise: reset the mutable set to the last kept commit.
```

Do not pause to ask whether to continue. The stop criterion is in `program.md`: an iteration
count, a wall-clock limit, a target metric, or the human interrupting. Out of ideas means think
harder: re-read the frozen code, combine near-misses, try a larger structural change, and
record the attempt either way.

## Handing the loop to the auditor

When the loop ends, the ledger and notebook are the run accounting that `research-results-auditor`
needs. Audit the final kept state as an exploratory standalone claim: the ledger lists every run
(no selection by hand), the frozen evaluator is the protocol, and the baseline row is the
comparator. A loop result becomes confirmatory only through a separate evaluation the loop never
saw.
