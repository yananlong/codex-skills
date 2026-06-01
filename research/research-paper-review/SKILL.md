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
   - contextualized review that also assesses novelty, impact, and related-work coverage
2. Bootstrap the upstream engine once with `python3 scripts/install_engine.py`.
3. For orchestrated research packs, prefer `./paper-review/` as the canonical stage root and record non-canonical output paths in `artifact-index.md`.
4. Use `references/engine-usage.md` for flags, provider environment variables, and OCR engine details.
5. Use `references/rating-rubric.md` and the 1-5 issue/output scales instead of coarse three-bucket judgments.
6. For Claude-style, agentic, or parallel review requests, use Codex subagents automatically after Pass A; do not ask again once the user has explicitly requested agentic/parallel work.
7. When review quality depends on novelty, impact, or literature context, route through `research-systematic-literature-review` and `research-novelty-review` instead of limiting the critique to internal paper consistency.

## Upstream Claude Skill Compatibility

- The upstream OpenAIReview Claude Code skill lives in `src/reviewer/skill/` and is installed by `openaireview install-skill` into `~/.claude/commands/openaireview`. That install path, the `/openaireview` slash command, and references to Claude's Agent/task tools are Claude-specific and are not directly usable as a native Codex skill.
- The underlying workflow is portable: the skill resources are plain Markdown plus Python scripts that prepare a review workspace, collect section-review JSON, consolidate comments, and emit viz-compatible JSON. This Codex skill is the compatibility layer: keep Codex frontmatter and sibling-skill contracts here, and call the packaged upstream scripts through the local wrappers.
- When upstream instructions say to use parallel Claude sub-agents, translate that into Codex subagents whenever the user explicitly asks for agentic, parallel, multi-agent, subagent, or Claude-style review. In that case, spawning is part of the requested workflow and should happen automatically after Pass A. If the user only asks for a deep or thorough review without agentic/parallel language, run the same planned review passes serially and keep one JSON output file per pass under `comments/`.
- The upstream viz helper still expects `severity`. This skill's canonical handoff uses `impact_rating` and `confidence_rating`; `scripts/save_viz_json.py` adds transient severity values for visualization and labels the viz method as Codex.

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
  - run section-level and cross-cutting review passes, preferably with Codex subagents when explicitly authorized
  - consolidate, tier, and save issues into viz-compatible JSON
- Prefer this mode when the paper-review stage will feed `research-review-loop`, `research-paper-plan`, or `research-rebuttal`.

### Agentic deep review mode

- Use this mode when the user says to use agents, subagents, parallel review, multi-agent review, Claude-style review, or otherwise explicitly delegates parallel agent work.
- Do not stop to ask for confirmation once that authorization is present. Build the full-paper summary first, then spawn all planned review agents in parallel.
- Spawn one worker per review pass. Each worker owns exactly one output file under `<review_dir>/comments/`, such as `section_methods.json` or `cross_claims_vs_evidence.json`.
- Tell each worker that it is not alone in the workspace, that other workers own other comment files, and that it must not modify shared files such as `summary.md`, `full_text.md`, `sections/index.json`, `criteria.md`, `final_issues.json`, or `review_summary.json`.
- Parent agent responsibilities remain local: prepare the workspace, write `summary.md`, design the pass plan, launch workers, wait for results, ensure every planned comments file exists, consolidate, verify quotes, write final handoff files, save viz JSON, and validate the bundle.
- If the runtime does not expose subagents despite the user requesting agentic mode, state that limitation and execute the same pass plan serially.

### Contextualized paper review mode

- Use this mode when the user asks for novelty, significance, impact, related-work adequacy, SOTA/context positioning, venue-grade critique, or a review that should be stronger than OpenAIReview's internal consistency checks.
- After Pass A, extract the paper's:
  - one-sentence contribution claim
  - field/domain and target community
  - claimed novelty dimensions
  - cited closest prior work
  - benchmark/evaluation context
  - impact or significance claims
- Run a bounded `research-systematic-literature-review` paper-context evidence map when the review needs external literature grounding. This is not automatically a full PRISMA review; use the literature skill's paper-context mode unless the user explicitly asks for a full systematic review.
- Run `research-novelty-review` after the literature-context map when the paper makes novelty, contribution, or impact claims. The novelty review should consume both `summary.md` and the literature-context artifacts.
- Fold the outputs back into paper-review findings:
  - related-work omissions become `missing_information` or `claim_accuracy` issues
  - overstated novelty or significance becomes `claim_accuracy`
  - weak impact framing becomes `presentation` unless it affects a core claim
  - benchmark-context gaps become `methodology` or `missing_information`
- Preserve provenance: record the literature and novelty artifact paths in `review_summary.json` and, in orchestrated mode, in `artifact-index.md`.

## Relationship to sibling skills

- `research-paper-review` owns paper ingestion, OCR, first-pass critique, and viz output for a single paper.
- `research-systematic-literature-review` owns external evidence mapping. Within paper review, use its paper-context mode for bounded related-work, benchmark-context, and impact-evidence checks; reserve full PRISMA mode for explicit systematic-review requests.
- `research-review-loop` owns iterative tracked review after there is already a first-pass critique, revision cycle, or explicit issue ledger.
- `research-novelty-review` owns prior-art pressure testing and positioning. Within contextualized paper review, run it after the paper summary and literature-context map exist so novelty judgments are evidence-grounded.
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
  - `<review_dir>/comments/PASS_PLAN.md`
  - `<review_dir>/comments/all_comments.json`
  - `<review_dir>/context/context-plan.md`
  - `<review_dir>/context/literature-context.md`
  - `<review_dir>/context/novelty-context.md`
  - `./review_results/<slug>_skill.json`
- Record the exact active review workspace path and any viz JSON path in `artifact-index.md` so later skills do not guess.
- `review_summary.json` is the numeric summary artifact for downstream routing. It should include:
  - `overall_paper_rating` (1-5)
  - `decision_relevance_rating` (1-5)
  - `rating_confidence` (1-5)
  - `top_blockers`
  - `context_artifacts` when literature or novelty context was used
  - `novelty_decision_rating` and `impact_context_rating` when available

## Workflow

### 0) Track the review explicitly

- If a task tracker is available, create tasks for:
  - prepare workspace
  - understand the paper
  - build pass plan
  - spawn/run review passes
  - consolidate and tier findings
  - write handoff artifacts
  - save viz output
- In agentic mode, add one tracked subtask per worker using the worker's `pass_id` and owned output file.
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

#### 5a) Build the pass plan

- Read `sections/index.json` and write a concrete pass plan in `comments/PASS_PLAN.md` before spawning or running detailed checks.
- Aim for 7-10 total passes for a deep review unless the paper is unusually short or narrow:
  - 4-7 section-focused passes covering each major section or logical cluster, or one per major section when the paper is short
  - 3-5 cross-cutting passes for claims vs evidence, evaluation fairness, statistical consistency, notation coherence, or paper-specific risks
- Group small or tightly coupled sections rather than creating trivial one-section passes. Each section-focused pass should receive its primary section plus 1-3 related sections for cross-reference context.
- Choose cross-cutting passes from the paper's actual risk profile. Common useful checks are abstract/introduction claims vs evidence, fairness of comparisons, limitations coherence, numerical consistency across tables/appendices, method-results alignment, and whether the paper applies its stated standards to itself.
- Each pass plan entry must include:
  - `pass_id`
  - `kind` (`section` or `cross_cutting`)
  - `owned_output_file`
  - primary and related section files
  - one-sentence focus
  - likely failure modes to check
  - expected evidence locations

#### 5b) Execute with Codex agents when authorized

- If the user explicitly requested agents, subagents, parallel review, multi-agent review, or Claude-style review, spawn all planned review workers in parallel after `summary.md` is complete.
- Use one worker per pass. Do not batch unrelated passes into one worker unless there are more planned passes than the runtime can reasonably launch.
- Worker ownership must be disjoint: each worker writes exactly one JSON array to its assigned `owned_output_file` under `<review_dir>/comments/`.
- Worker prompt requirements:
  - state that the worker is not alone in the workspace
  - state the worker's owned output file
  - state that the worker must not edit shared files or other workers' comment files
  - include the section-focused or cross-cutting template from `references/subagent_templates.md`
  - require valid JSON output even when no issues are found (`[]`)
  - require the final response to list the file path changed and the issue titles
- While workers run, the parent should do non-overlapping work only: inspect `summary.md`, check section coverage, prepare consolidation criteria, or draft the final bundle skeleton. Do not redo a worker's assigned pass.
- Wait for all workers before consolidation. If a worker returns JSON in chat rather than materializing its file, the parent must write that JSON to the worker's owned output file before running consolidation.

#### 5c) Serial fallback

- If subagents are not authorized or unavailable, run the exact same pass plan serially in the current agent.
- Keep outputs separate under `comments/` using the same `owned_output_file` paths that agents would have used.
- Do not reduce the number of passes merely because execution is serial; reduce only when the paper is short, incomplete, or the user requested a fast review.

#### 5d) Pass quality bar

- Use `references/codex-agent-orchestration.md` for spawning/ownership rules, `references/subagent_templates.md` for prompt structure, and `references/criteria.md` for issue format.
- Favor deep, merged root-cause arguments over surface-level issue spam, but do not collapse distinct issues that require different fixes or threaten different paper-level conclusions.
- Each pass must write a JSON array into `comments/`. Empty arrays are valid; missing output files are not.
- After all passes, compare `PASS_PLAN.md` against the files in `comments/`; fill or rerun any missing pass before consolidation.

### 5e) Add literature and novelty context when needed

- Before consolidation, decide whether external context is necessary. It is necessary when the paper makes novelty, SOTA, related-work sufficiency, benchmark representativeness, impact, or significance claims that cannot be judged from the paper alone.
- Create `<review_dir>/context/context-plan.md` with:
  - extracted contribution claim
  - domain and target community
  - novelty dimensions to test
  - impact/significance claims to contextualize
  - cited closest prior work
  - proposed literature-context scope
  - whether full systematic review is needed or paper-context mode is enough
- If only bounded context is needed, invoke `research-systematic-literature-review` in paper-context mode with the paper summary, extracted contribution, domain, cited prior work, and 3-8 targeted search questions. Write or copy the resulting summary to `<review_dir>/context/literature-context.md`.
- If the user explicitly asks for a full systematic review, or if a venue-critical claim depends on broad evidence coverage, run the full `research-systematic-literature-review` workflow and record its artifact directory.
- Invoke `research-novelty-review` when novelty or impact positioning matters. It should consume `summary.md`, `<review_dir>/context/literature-context.md` when present, and any `./literature-review/` artifacts. Write or copy its bottom-line decision to `<review_dir>/context/novelty-context.md`.
- Add any context-derived findings to the raw comments set before consolidation, preferably in `comments/cross_literature_context.json` and `comments/cross_novelty_positioning.json`.
- Do not invent literature evidence. If search/corpus access is unavailable, mark context-dependent claims as externally unverified and state what evidence would resolve them.

### 6) Consolidate and tier findings

- Run:

```bash
python3 scripts/consolidate_comments.py <review_dir>
```

- Deduplicate by root cause, not wording alone. If one fix would resolve multiple comments, merge them into the strongest single issue; if comments share a design choice but affect different claims or require different fixes, keep them separate.
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
- Do not drop issues only because they are minor; a low-impact issue should usually remain as `impact_rating` 1 or 2 if it is real.
- As a calibration check, a thorough deep review of a publishable paper usually yields 15-30 total issues across impact levels. A typical publishable paper may have several impact-4 issues, but impact-5 should be reserved for paper-level blockers. If there are fewer than 15 findings after deduplication, check whether you over-merged or skipped cross-cutting passes. If there are more than 10 impact-4/5 issues, re-check that each one threatens a paper-level conclusion rather than a local paragraph.

### 7) Save final results for browsing and downstream use

- Write `final_issues.json` in the review directory. Each issue needs:
  - `title`
  - `quote`
  - `explanation`
  - `comment_type`
  - `impact_rating`
  - `confidence_rating`
- Do not hand-write a separate `severity` field unless another tool specifically needs it; the local viz wrapper derives severity from `impact_rating` when calling the upstream OpenAIReview helper.
- Write `review_summary.json` in the review directory with:
  - `overall_paper_rating`
  - `decision_relevance_rating`
  - `rating_confidence`
  - `top_blockers`
  - `context_artifacts`
  - `novelty_decision_rating` when available
  - `impact_context_rating` when available
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
- `references/codex-agent-orchestration.md`
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
