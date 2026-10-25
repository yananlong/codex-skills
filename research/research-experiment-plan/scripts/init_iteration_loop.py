#!/usr/bin/env python3
"""Create the files for an autonomous iteration loop: program.md, results.tsv, experiments.md, ideas.md.

See references/iteration-loop-contract.md. The loop edits a bounded set of files, runs a frozen
evaluator under a fixed budget, keeps improvements, reverts regressions, and logs every run.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

LEDGER_HEADER = "commit\tmetric\tcost\tstatus\tdescription\n"

PROGRAM_TEMPLATE = """# Iteration loop: {name}

This file is edited by the human. The agent reads it and runs the loop in
`references/iteration-loop-contract.md` (research-experiment-plan).

## Exam (frozen; the agent never edits these)

- Evaluator: {evaluator}
- Metric: `{metric}` ({direction} is better), printed by the evaluator as `{metric}: <number>`
- Budget per run: {budget}
- Secondary cost recorded per run: {cost} (soft constraint; tolerance: state it here)

## Study (mutable; the only files the agent edits)

- {mutable}

## Rules

- Install nothing and add no dependencies.
- Simplicity criterion: a gain smaller than <threshold> does not justify more than <N> added
  lines; an equal result from deleting code is kept.
- Crash policy: fix a trivial error once, otherwise log `crash` and move on.
- Stop criterion: {stop}
- Never pause to ask whether to continue before the stop criterion.

## Run

```
{run_command} > run.log 2>&1
grep "^{metric}:" run.log
```

## Records

- `results.tsv`: append one row per run (commit, metric, cost, status, description). Do not
  commit it on the experiment branch. The first row is the untouched baseline.
- `experiments.md`: one notebook entry per run, written before the run as a hypothesis and
  completed after it.
- `ideas.md`: advisory idea queue with priorities and tags.
- Validate the ledger at any time: `python3 <skill>/scripts/validate_iteration_ledger.py results.tsv --direction {direction}`
"""

NOTEBOOK_TEMPLATE = """# Experiment notebook: {name}

One entry per run. Write Changed, Why, Expected, and Prior before the run; add Result, Lesson,
and Next after it. Keep the entry heading as `## <commit> <status>` so the ledger validator can
match entries to rows.

## <commit> <status>
- Changed:
- Why:
- Expected:
- Prior:
- Result:
- Lesson:
- Next if this fails:
"""

IDEAS_TEMPLATE = """# Idea queue: {name}

Advisory. One idea per line: `- [priority 1-3] [tag] hypothesis`. Take the highest priority
untried idea unless you have a stronger hypothesis; append new ideas as the notebook teaches you.
Mark tried ideas with the commit that tried them.

- [1] [baseline] run the untouched configuration to establish the baseline row
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target_dir", type=Path, help="Directory for the loop files")
    parser.add_argument("--name", default="loop", help="Short loop name")
    parser.add_argument("--metric", default="val_metric", help="Primary metric name printed by the evaluator")
    parser.add_argument("--direction", choices=("lower", "higher"), default="lower", help="Which direction is better")
    parser.add_argument("--evaluator", default="<path to the frozen evaluator>", help="Frozen evaluator path")
    parser.add_argument("--budget", default="<fixed budget per run, e.g. 300 s wall clock>", help="Budget per run")
    parser.add_argument("--cost", default="peak memory (GB)", help="Secondary cost recorded per run")
    parser.add_argument("--mutable", default="<the one file the agent may edit>", help="Mutable file set")
    parser.add_argument("--run-command", default="<command that runs one evaluation>", help="Run command")
    parser.add_argument("--stop", default="<iteration count, wall-clock limit, or target metric>", help="Stop criterion")
    parser.add_argument("--force", action="store_true", help="Overwrite existing loop files")
    args = parser.parse_args()

    target = args.target_dir
    target.mkdir(parents=True, exist_ok=True)
    files = {
        "program.md": PROGRAM_TEMPLATE.format(
            name=args.name, metric=args.metric, direction=args.direction, evaluator=args.evaluator,
            budget=args.budget, cost=args.cost, mutable=args.mutable, run_command=args.run_command,
            stop=args.stop,
        ),
        "results.tsv": LEDGER_HEADER,
        "experiments.md": NOTEBOOK_TEMPLATE.format(name=args.name),
        "ideas.md": IDEAS_TEMPLATE.format(name=args.name),
    }
    existing = [name for name in files if (target / name).exists()]
    if existing and not args.force:
        print(f"[ERROR] refusing to overwrite existing files without --force: {', '.join(existing)}", file=sys.stderr)
        return 1
    for name, content in files.items():
        (target / name).write_text(content, encoding="utf-8")
    print(f"Wrote {', '.join(files)} to {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
