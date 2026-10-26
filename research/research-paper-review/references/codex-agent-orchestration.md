# Agent Orchestration

Use this reference for `research-paper-review` whenever it runs workers.

## Ownership and budget rule

- Only the skill the user invoked spawns workers, and it sets one budget for the whole chain: quick depth uses no workers; standard uses up to 3; deep uses 5 to 8. A skill reached by handoff never spawns, so a paper review started by `research-review-loop` or `research-pipeline-planner` runs serially inside that skill's budget.
- When the user invoked this skill, the budget is authorization enough: do not ask again before spawning. Default to standard; use deep when the user asks for a deep, thorough, or venue-grade review or the paper is long. An explicit request for agents or parallel review is a request for deep depth unless the user names a number.
- The budget counts agents, not review checks. The pass plan keeps its 7 to 10 passes; workers each run a share of them.
- Prepare the workspace, write `summary.md`, build `comments/PASS_PLAN.md`, then launch the workers.

## Parent responsibilities

The parent agent owns the global review state:

- prepare the workspace
- read the full paper and write `summary.md`
- write `comments/PASS_PLAN.md`
- assign the planned passes to at most the budget's workers
- ensure every planned comments file exists and contains valid JSON
- run `scripts/consolidate_comments.py`
- deduplicate, validate quotes, and assign final 1-5 ratings
- write `final_issues.json`, `review_summary.json`, and `overall_assessment.txt`
- run `scripts/save_viz_json.py` and `scripts/validate_review_bundle.py`

The parent must not delegate its immediate blocking task. In practice, this means the parent writes the summary and pass plan locally before launching workers.

## Worker ownership

Each pass has exactly one comments file, written only by the worker assigned that pass:

```text
<review_dir>/comments/<pass_id>.json
```

A worker that runs several passes owns several files, one per pass.

Workers may read:

- `<review_dir>/summary.md`
- their assigned section files under `<review_dir>/sections/`
- `<review_dir>/criteria.md`
- other section files only when needed to resolve a cross-reference

Workers must not modify:

- `summary.md`
- `full_text.md`
- `metadata.json`
- `sections/index.json`
- `criteria.md`
- any other worker's comment file
- `comments/all_comments.json`
- `final_issues.json`
- `review_summary.json`
- `overall_assessment.txt`

## Spawn pattern

Launch the budgeted workers in parallel after Pass A, each with its list of passes.

Use `worker` agents for passes that write comment JSON. Tell workers they are not alone in the workspace, that other workers own other files, and that they must not revert or modify others' work.

Use this structure for each worker prompt:

```text
You are one worker in a parallel academic paper review. You are not alone in the workspace: other workers are reviewing other sections and own other comment files. Do not edit shared files and do not modify any file except your owned output file.

Paper: <PAPER_TITLE>
Review directory: <REVIEW_DIR>
Owned output file: <REVIEW_DIR>/comments/<PASS_ID>.json

Read in order:
1. <REVIEW_DIR>/summary.md
2. <PRIMARY_OR_SECTION_A>
3. <RELATED_SECTION_FILES>
4. <REVIEW_DIR>/criteria.md

Focus:
<ONE_SENTENCE_FOCUS>

Likely failure modes to check:
- <FAILURE_MODE_1>
- <FAILURE_MODE_2>

Write a valid JSON array to your owned output file. Each issue object must include:
- title
- quote
- explanation
- comment_type
- impact_rating
- confidence_rating
- source_section
- related_sections

If you find no issues, write [].

Final response: list the owned file path, issue count, and issue titles only.
```

## Failure handling

- If a worker fails or does not write valid JSON, rerun only that pass or execute it serially in the parent.
- If a worker returns JSON in the final response but the file is not present, the parent writes that JSON to the owned output file.
- If two workers report overlapping issues, keep both raw comments until consolidation; do not ask workers to coordinate after the fact.
- If fewer than 15 total raw comments appear for a normal full-length paper, inspect whether the pass plan was too narrow before deduplication.
