# Skill evaluations

This folder holds the evaluation material for the skills in this repository. It borrows two
practices from public skill tooling: trigger evaluation sets in the style of Anthropic's
skill-creator (realistic prompts labelled should-trigger or should-not-trigger, with the hard
cases being near misses that share vocabulary with the skill), and the with-skill versus
without-skill comparison that the same tool and the Superpowers writing-skills guidance both use
to show that a skill changes behavior rather than restating what the model already does.

## trigger-evals/

One JSON file per skill:

```json
[
  {"query": "realistic prompt as the owner would type it", "should_trigger": true},
  {"query": "near miss that shares keywords but needs another skill", "should_trigger": false, "expected_skill": "other-skill"}
]
```

Rules for adding queries:

- Write prompts a real user would type, with file names, venue names, and casual phrasing.
  Abstract one-liners test nothing.
- Make the negative cases near misses, not unrelated requests. Name the skill that should fire
  instead in `expected_skill`.
- Keep the set at roughly ten to twenty queries, about half positive.

Running them needs a model. With the Claude Code CLI, the skill-creator's description
optimization loop (`anthropics/skills`, `skill-creator/scripts/run_loop.py`) accepts this file
format directly and reports trigger rates per query over several runs. Without it, run each
query once in a session that has the catalog loaded and record which skill was consulted.

A description change is accepted when the held-out trigger rate improves and no positive query
drops below its previous rate.

## Task evaluations

The stress test behind `plan/research-writing-skill-overhaul.md` produced realistic task prompts
per skill, run against the owner's real repositories. Those prompts reference private material
and live outside this repository. The pattern to reuse is: run the same prompt with and without
the skill (or with the previous version of the skill), save outputs side by side, grade with
objective assertions where the output is checkable (a validator exits 0, a file exists, a number
matches), and judge subjective outputs by reading them. Fixtures committed here must be
structure-only, with synthetic names and no manuscript text or real results.

## prospective/

Maintainer studies of the research suite itself, moved out of `research-pipeline-planner` so skill
packages no longer carry them. See `prospective/README.md`.
