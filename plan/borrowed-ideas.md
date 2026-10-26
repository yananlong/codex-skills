# Borrowed Designs for the Skill Overhaul

Companion to `research-writing-skill-overhaul.md`. This document records what was read, what was
borrowed, what was deliberately not borrowed, and where each borrowing lands. The sources are
public skill repositories and the autoresearch loop; text was not copied, designs were.

## Sources read

| Source | What it is | Read |
| --- | --- | --- |
| karpathy/autoresearch | One agent, one mutable file, one metric, a five-minute budget, a keep-or-discard git loop, an append-only `results.tsv`, a human-edited `program.md` | README, program.md, train.py |
| shehral/autoresearch-commons | Fork adding experiment cards with hypothesis, lesson, tags, and prior-card lineage; a coverage map by tag; an advisory experiment queue filled by a director agent; periodic synthesis | program.md, director.md, commons.py, README |
| rungalileo/autoresearch-for-agents | Same loop applied to a system prompt against a frozen adversarial test suite; a sub-1000-character prompt constraint; mandatory pre-run experiment notes (changed, why, thesis, learnings, next if it fails); a proportional scorer to give the loop a gradient | program.md, README |
| anthropics/skills, skill-creator | Draft, run with and without the skill on realistic prompts, grade, review, improve; description optimization against twenty should and should-not trigger queries with held-out scoring; explain the why instead of all-caps musts; bundle a script when every run reinvents one | SKILL.md and layout |
| obra/superpowers | brainstorming, writing-plans, executing-plans, subagent-driven-development, dispatching-parallel-agents, test-driven-development, verification-before-completion, systematic-debugging, writing-skills and its discovery and bulletproofing references | SKILL.md files |
| agentskills.io specification | Frontmatter fields, progressive disclosure (metadata, under 500 lines of body, references on demand), one-level-deep file references | Specification page |
| jin-s13/ai-research-writing-skill | Paper writing as claim-evidence engineering: route table at the top of the skill, `paper_state.json`, a research-handoff contract that exports evidence not prompts, numeric-evidence v2 (every manuscript number registered with a selector into a data file and recomputed), paper story with claims to make, be careful about, and avoid, reviewer evidence notes with IDs, mode-aware quality gates | SKILL.md, workflow, numeric-evidence, research-handoff, paper-story, reviewer references |
| samasarvii/literature-review | Source ladder, claim cards with a verbatim quote and a per-row fetch status, a search cap per sub-question, consensus, disagreement, and open bins, derived confidence with GRADE-style drops, a "what would change it" line, folklore labelled rather than dropped | SKILL.md |
| labarba/sciwrite | Five sentence-level audit passes; keyword consistency (the banana rule); numerical consistency between abstract, text, and tables; the telephone-game citation audit | SKILL.md |
| hanlulong/econ-writing-skill | Triangular order, one central contribution written in one paragraph, concrete findings in the introduction, literature review as a story inside the introduction, propositions in plain English before formalism | SKILL.md |

## What was borrowed and where it landed

### 1. The autoresearch loop as a first-class experiment mode

Our experiment-plan skill planned confirmatory experiments and had no mode for "how good can this
get under a fixed budget". That is the loop the owner's own projects run by hand (sweeps, prompt
tuning, recomputation audits). Borrowed, in `research-experiment-plan`:

- `references/iteration-loop-contract.md`: frozen exam versus mutable study set (autoresearch and
  Galileo's two-phase rule that the optimizer cannot move its goalposts), one metric with a
  direction, a fixed budget, the simplicity criterion with a stated exchange rate, the append-only
  `results.tsv` with the original five columns, a per-run notebook entry written before and after
  the run (Galileo's notes), an advisory idea queue with coverage by tag (commons' queue and
  coverage map), never pausing before the stop criterion, and a handoff of the ledger to the
  results auditor as the complete run accounting.
- `scripts/init_iteration_loop.py` writes `program.md`, `results.tsv`, `experiments.md`, and
  `ideas.md`; `scripts/validate_iteration_ledger.py` enforces the ledger (hashes, statuses,
  baseline first, keep rows improve in the declared direction, crash rows zeroed) and cross-checks
  notebook entries.

Not borrowed: the director agent and shared knowledge base. The planner already owns scheduling;
a second scheduler would recreate the ownership problem the stress test found. The queue stays a
file the single loop agent reads.

### 2. Route tables instead of contract sprawl

The research-writing skill opens with "choose the smallest route that covers the request; load
only the listed references first". Our stress test found that a planner handoff needs about
fifteen thousand words of contracts and that the paper-review skill's first-pass path is buried
under engine and provenance text. Borrowed: a route table at the top of `research-pipeline-planner`
and `research-paper-review` naming the request shape, the route, the files to load first, and the
sibling skill when the request is not this skill's. This is the mechanism behind the overhaul
plan's "lightweight path" items and should be added to every skill whose body exceeds the
agentskills.io guidance of five thousand tokens.

### 3. Claim cards, source ladder, fetch status, derived confidence

The literature-review skill from samasarvii solves the exact defect the stress test found in our
search logs: columns that invite counts a web-search model cannot report honestly, and channels
marked performed after one spot check. Borrowed, in `research-systematic-literature-review`:
`references/claim-cards-and-source-ladder.md`, and `fetch_status`, `rung`, and `quote` columns
in the evidence table, with the rule that only read rows support a sentence. This fixes the
design for overhaul decision D18 (search-log columns): replace hit counts with
`results_inspected` and the tool used, one query per row, and a spot-checked channel status that
does not count as performed.

### 4. Numeric evidence as the machine form of value slots

The research-writing skill's numeric-evidence v2 registers every manuscript number with a selector
(file, column, row filter, aggregate, tolerance) and recomputes it. One of the owner's manuscripts
already does this by hand with slot macros and a values registry, and the stress test found
paper-plan cannot bind to it (paper F-10). This is the design for overhaul decision D15: the
`value_slots` binding in `research-paper-plan` should carry a selector and a tolerance so a checker
can recompute the number, and the results-audit `measurements` object (D6) should emit the same
selector shape so the auditor and the paper plan share one locator. Deferred to D6 and D15
because both are schema changes.

### 5. Evidence notes with IDs for reviews

Reviewer evidence notes (ID, location, already supplied, observation, fact versus inference,
impact, question, minimum resolving evidence) match what overhaul decision D10 needs as the single
review-issue schema. The three-lens review (methodology, positioning, statistics) and the rule to
check appendices before objecting are good additions to the paper-review pass plan. Deferred to
D10 so the rebuttal and review-loop consumers change together.

### 6. Register-aware section archetypes

`research-paper-plan/references/section-archetypes.md` was a six-line stub. It now carries six
contribution archetypes, a job for every section (including the economics-style rules: concrete
findings in the introduction, literature as a story with a however, triangular order), and
register notes that agree with the reviser's `register-and-format.md`. Venue facts stay deferred
to D14, since they need verified-on dates.

### 7. Term and number consistency passes

Sciwrite's keyword-consistency and numerical-consistency passes were added to the reviser's
patterns reference and final pass as flag-only checks: the reviser reports a term that changed
between methods and results, or a number that disagrees between abstract and table, and never
resolves either itself.

### 8. Trigger evaluation sets

The skill-creator's description optimization works from twenty realistic queries per skill, half
near misses. Our stress test produced those near misses for eight skills. They now live in
`evals/trigger-evals/<skill>.json` with the skill that should fire on each negative case, and
`evals/README.md` says how to run them. Description edits in the overhaul should be accepted only
when the held-out trigger rate improves.

### 9. Rulings, not stalls

Superpowers' executing-plans records every autonomous decision as
`Ruling: what | why | cost if wrong` and collects them into the final report. The planner's
decision-log template now carries that line format and a cost-if-wrong field. The planner's event
log already provides the durable record; the ruling line is the human-readable projection of a
decision made without a human.

### 10. Style rules for the overhaul itself

Three rules from the skill-writing guidance apply to how the overhaul rewrites skill text:

- **Form matches the failure** (Superpowers writing-skills). A discipline failure gets a
  prohibition, a rationalization table, and red flags. A shaping failure (wrong output shape,
  restated spec, missing element) gets a positive recipe or a required slot in a template, because
  prohibitions measurably backfire on shaping problems. Most of what the stress test found in our
  skills is shaping failure, and most of our skill text is prohibition. Rewrites should state what
  the output is.
- **Explain the why, keep it lean** (skill-creator). All-caps musts and rigid structures are a
  yellow flag; the model follows reasons better than orders. Remove text that is not pulling its
  weight, and read transcripts for wasted work before adding more text.
- **Tell the model what to do, not how to think; a flat priority list beats a decision tree**
  (Galileo's measured lesson on prompt structure).

### 11. Description discipline

Two sources disagree. Superpowers says a description names only when to use the skill and never
summarizes the workflow, because an agent that reads a workflow summary follows it instead of
reading the skill. The skill-creator says descriptions should be a little pushy and cover both
what and when, because models under-trigger. Our descriptions do both at length and summarize
their workflows. The resolution for the overhaul: a description names the triggering situations
and the near misses that should route elsewhere, in concrete user phrasing, and does not list the
skill's steps or artifacts. The trigger sets in `evals/` are how a rewrite is checked.

## Deliberately not borrowed

- Superpowers' hard gates (nothing is built until a design document is approved) and its
  mandatory subagent-per-task execution. The stress test found our skills already over-ceremonial;
  the gates that matter here are the planner's verifier transitions, not approval dialogs.
- The autoresearch rule to never stop until interrupted. Our loop stops at a criterion written in
  `program.md`, because the owner's runs cost money and a kept state needs an audit before anything
  is claimed.
- The research-writing skill's image-generation default for method figures. Generated figures are
  not evidence, and the owner's venues want deterministic plots.
- Econ-writing's venue-specific page counts and tense rules as hard rules. They are register notes
  in the archetypes, not requirements, until the venue table (D14) carries verified facts.
