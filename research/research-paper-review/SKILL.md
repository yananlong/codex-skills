---
name: research-paper-review
description: Run academic paper review with OCR extraction, multi-method CLI review, local visualization, and deep section-level critique workflows integrated into the research skill suite. Use when Codex needs an initial or first-pass review of one paper artifact or arXiv URL, including OCR, extraction, section-level critique, or viz JSON generation. Prefer `research-review-loop` once a tracked review state or revised artifact already exists, `research-novelty-review` for prior-art and positioning questions, `research-rebuttal` when concrete reviewer comments already exist, and `adversarial-doc-review` for non-paper documents.
---

# Research Paper Review

## Quick start

1. Decide whether the user needs:
   - fast review or extraction via the upstream CLI
   - a local viz server for existing result JSON
   - a deep paper-review pass with section-level scrutiny
2. Bootstrap the upstream engine once with `python3 scripts/install_engine.py`.
3. For orchestrated research packs, prefer `./paper-review/` as the canonical stage root and record non-canonical output paths in `artifact-index.md`.
4. Use `references/engine-usage.md` for flags, provider environment variables, and OCR engine details.
5. Use `references/rating-rubric.md` and the 1-5 issue/output scales instead of coarse three-bucket judgments.

## Modes

### CLI mirror mode

- Preserve the upstream OpenAIReview CLI surface through `scripts/run_openaireview.py`.
- Use this for:
  - `review`: generate result JSON quickly with `zero_shot`, `local`, `progressive`, or `progressive_full`
  - `extract`: OCR or parse a paper into Markdown with metadata
  - `serve`: browse saved result JSON in a local UI
- Do not re-implement upstream review logic locally when the CLI already covers the request.

### Deep review mode

- Use this when the user wants a stronger paper critique than a single-pass CLI review.
- Adapt the upstream skill workflow to Codex and the research suite:
  - prepare a review workspace
  - understand the full paper
  - run section-level and cross-cutting review passes
  - consolidate, tier, and save issues into viz-compatible JSON
- Prefer this mode when the paper-review stage will feed `research-review-loop`, `research-paper-plan`, or `research-rebuttal`.

## Relationship to sibling skills

- `research-paper-review` owns paper ingestion, OCR, first-pass critique, and viz output for a single paper.
- `research-review-loop` owns iterative tracked review after there is already a first-pass critique, revision cycle, or explicit issue ledger.
- `research-novelty-review` owns prior-art pressure testing and positioning, not first-pass technical critique of a paper artifact.
- `research-rebuttal` owns responses to external reviewer comments, not initial manuscript diagnosis.
- `adversarial-doc-review` owns broad document red-teaming outside the paper-review workflow, especially non-paper Markdown or policy/spec documents.

## Input contract

- Minimum:
  - one concrete paper artifact or URL
- Supported inputs through the upstream engine:
  - local `.pdf`, `.docx`, `.tex`, `.txt`, `.md`
  - arXiv `abs` or `html` URLs
- Prefer:
  - venue or audience
  - whether the user wants quick scoring, issue discovery, or rebuttal-grade critique
  - model, provider, OCR engine, and token/cost constraints
- Environment:
  - at least one supported API key when running LLM review
  - optional OCR backends for `mistral` or `deepseek`

## Hard stops

- Stop if there is no concrete paper artifact or URL.
- Stop if the task would require invented evidence, fabricated quotes, or guessed paper contents.
- Stop before deep review when the paper is too incomplete to support meaningful section-level scrutiny.
- If the upstream engine is missing, install it with `scripts/install_engine.py` instead of trying to recreate the package inline.

## Output contract

- In orchestrated mode, preserve the active review workspace under `./paper-review/<slug>_review/` unless a different path is explicitly recorded in `artifact-index.md`.
- Required handoff files for downstream stages:
  - `<review_dir>/summary.md`
  - `<review_dir>/final_issues.json`
  - `<review_dir>/review_summary.json`
  - `<review_dir>/overall_assessment.txt`
- Required support files:
  - `<review_dir>/metadata.json`
  - `<review_dir>/full_text.md`
  - `<review_dir>/sections/index.json`
- Optional but strongly preferred:
  - `<review_dir>/comments/all_comments.json`
  - `./review_results/<slug>_skill.json`
- Record the exact active review workspace path and any viz JSON path in `artifact-index.md` so later skills do not guess.
- `review_summary.json` is the numeric summary artifact for downstream routing. It should include:
  - `overall_paper_rating` (1-5)
  - `decision_relevance_rating` (1-5)
  - `rating_confidence` (1-5)
  - `top_blockers`

## Workflow

### 0) Track the review explicitly

- If a task tracker is available, create tasks for:
  - prepare workspace
  - understand the paper
  - run review passes
  - consolidate and tier findings
  - write handoff artifacts
  - save viz output
- Mark progress as you move. A deep paper review should not become an opaque one-shot blob of reasoning.

### 1) Bootstrap the upstream engine

- Run `python3 scripts/install_engine.py` before the first use on a machine.
- Default install source is the upstream GitHub repo so this skill tracks the referenced project directly.
- Use `--with mistral` or `--with deepseek` when those OCR backends are needed.
- The install path defaults to `./.openaireview-venv` inside the skill directory unless `OPENAIREVIEW_VENV` is set.

### 2) Route to the correct execution path

- Quick review:
  - `python3 scripts/run_openaireview.py review <paper> ...`
- Extraction only:
  - `python3 scripts/run_openaireview.py extract <paper> ...`
- Viz only:
  - `python3 scripts/run_openaireview.py serve --results-dir <dir> --port <port>`
- Deep review:
  - continue with the staged workflow below

### 3) Prepare the deep-review workspace

- In orchestrated mode, prefer `./paper-review/` as the stage root and `./review_results/` for viz JSON.
- Run:

```bash
python3 scripts/prepare_workspace.py "<input>" \
  --criteria references/criteria.md \
  --output-dir ./paper-review
```

- The upstream workspace contains:
  - `metadata.json`
  - `full_text.md`
  - `criteria.md`
  - `sections/index.json`
  - `comments/`
- Record the review directory and slug immediately, and write the resolved review directory into `artifact-index.md` if you are in a suite pack.

### 4) Build a full-paper model before criticizing details

- Read `full_text.md` completely, including appendices, tables, and formal sections.
- Write `summary.md` in the review directory using this structure:

```markdown
# Paper Summary: [Title]

## Research Question
[One sentence]

## Core Hypothesis / Thesis
[What the paper claims to show]

## Methodology Overview
[2-3 sentences]

## Key Definitions & Notation
- [Term/symbol]: [definition]

## Key Numerical Parameters
- [Parameter]: [value and context]

## Main Claims (with evidence location)
1. "[Claim]" — [Section X, Table Y]

## Section Map
- [Section N] ([Title]): [one-line summary]

## Notable Cross-References
- [Section X] references [Section Y] for [what]
```

- Do not launch detailed review passes until the summary is good enough that another agent could use it as global context.

### 5) Run section and cross-cutting review passes

- Read `sections/index.json` and plan a review set, typically:
  - 4-7 section-focused passes covering each major section or logical cluster
  - 3-5 cross-cutting passes for claims vs evidence, evaluation fairness, statistical consistency, notation coherence, or paper-specific risks
- Group small or tightly coupled sections together rather than creating trivial one-section passes.
- Use `references/subagent_templates.md` for prompt structure and `references/criteria.md` for issue format.
- If the runtime explicitly allows parallel subagents, launch them in parallel.
- If parallel subagents are unavailable, run the same passes serially in the current agent and keep outputs separate under `comments/`.
- Favor deep, merged root-cause arguments over surface-level issue spam, but do not collapse distinct issues that require different fixes.
- Each pass should write a JSON array into `comments/`. Empty arrays are valid; missing output files are not.

### 6) Consolidate and tier findings

- Run:

```bash
python3 scripts/consolidate_comments.py <review_dir>
```

- Deduplicate by root cause, not wording alone.
- For any singleton finding that appears in only one pass, read the full explanation before dropping it. Singleton comments are often the best signals, not the weakest.
- Verify that every kept quote appears in the paper text.
- Remove false positives resolved by later context, standard conventions, or leniency rules in `criteria.md`.
- Reclassify comment types into:
  - `methodology`
  - `claim_accuracy`
  - `presentation`
  - `missing_information`
- Assign:
  - `impact_rating` on a 1-5 scale
  - `confidence_rating` on a 1-5 scale
- Use `references/rating-rubric.md`.
- Keep singleton findings unless a concrete check disproves them.
- As a calibration check, a thorough deep review of a publishable paper usually yields a double-digit total issue count across impact levels. If you have only a handful of findings, check whether you over-merged or skipped cross-cutting passes. If you rate nearly everything `4` or `5`, re-check whether some issues are really localized `2` or `3` findings.

### 7) Save final results for browsing and downstream use

- Write `final_issues.json` in the review directory. Each issue needs:
  - `title`
  - `quote`
  - `explanation`
  - `comment_type`
  - `impact_rating`
  - `confidence_rating`
- Write `review_summary.json` in the review directory with:
  - `overall_paper_rating`
  - `decision_relevance_rating`
  - `rating_confidence`
  - `top_blockers`
- Write `overall_assessment.txt` as one short paragraph.
- Build viz JSON:

```bash
python3 scripts/save_viz_json.py <review_dir> --slug-suffix _skill
```

- The output lands in `./review_results/` unless overridden.
- Use `python3 scripts/run_openaireview.py serve` to browse results locally.
- Run `python3 scripts/validate_review_bundle.py --review-dir <review_dir>` before treating the bundle as stable.
- Treat `summary.md`, `final_issues.json`, `review_summary.json`, and `overall_assessment.txt` as the canonical handoff bundle for `research-review-loop`, `research-paper-plan`, and `research-rebuttal`.

## References

- `references/engine-usage.md`
- `references/criteria.md`
- `references/rating-rubric.md`
- `references/subagent_templates.md`
- `../research-pipeline-planner/references/review-stage-contract.md`

## Scripts

- `scripts/install_engine.py`: create or update a virtualenv with the upstream OpenAIReview engine
- `scripts/run_openaireview.py`: mirror the upstream `openaireview` CLI
- `scripts/prepare_workspace.py`: delegate to the packaged deep-review workspace preparer
- `scripts/validate_review_bundle.py`: validate required handoff files and 1-5 rating fields for downstream use
- `scripts/consolidate_comments.py`: delegate to the packaged consolidation helper
- `scripts/save_viz_json.py`: delegate to the packaged viz JSON helper
