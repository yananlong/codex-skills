---
name: research-paper-review
description: Run academic paper review with OCR extraction, ChatGPT-native multi-agent critique, local visualization, and section-level review workflows integrated into the research skill suite. Use when Codex needs an initial or first-pass review of one paper artifact or arXiv URL, including OCR, extraction, default Claude-style or multi-agent review, contextualized critique, or viz JSON generation. Prefer `research-review-loop` once a tracked review state or revised artifact already exists, `research-novelty-review` for prior-art and positioning questions, `research-rebuttal` when concrete reviewer comments already exist, and `adversarial-doc-review` for non-paper documents.
---

# Research Paper Review

## Quick start

1. Decide whether the user needs:
   - extraction only
   - a local viz server for existing result JSON
   - the default multi-agent / Claude-style paper-review pass
   - contextualized review that also assesses novelty, impact, and related-work coverage
2. Inside ChatGPT/Codex, default LLM review to the active chat model. Do not require external LLM API keys for normal review.
3. Default to Claude-style / multi-agent orchestration for paper review. Build the full-paper summary first, then spawn one worker per planned review pass when the runtime supports subagents.
4. Use serial single-agent execution only as a fallback when subagents are unavailable, disabled, or clearly impractical for the paper size or runtime.
5. Bootstrap the upstream engine with `python3 scripts/install_engine.py` only when deterministic helpers are needed for extraction, workspace preparation, viz output, or explicit upstream provider-backed review.
6. For orchestrated research packs, prefer `./paper-review/` as the canonical stage root and record non-canonical output paths in `artifact-index.md`.
7. Use `references/chatgpt-native-review.md`, `references/rating-rubric.md`, and the 1-5 issue/output scales.
8. When review quality depends on novelty, impact, or literature context, route through `research-systematic-literature-review` and `research-novelty-review` instead of limiting the critique to internal paper consistency.
9. When reusing an existing review workspace, infer its provenance from `metadata.json`, `artifact-index.md`, `final_issues.json`, `review_summary.json`, and any `round-N/` folders before moving files or declaring artifacts missing.

## Upstream Claude Skill Compatibility

- The upstream OpenAIReview Claude Code skill lives in `src/reviewer/skill/` and is installed by `openaireview install-skill` into `~/.claude/commands/openaireview`. That install path, the `/openaireview` slash command, and references to Claude's Agent/task tools are Claude-specific and are not directly usable as a native Codex skill.
- The underlying workflow is portable: prepare a review workspace, collect section-review JSON, consolidate comments, and emit viz-compatible JSON.
- The upstream Claude/OpenAIReview workspace convention is `./review_results/<slug>_review/`, with `summary.md`, `final_issues.json`, `overall_assessment.txt`, `metadata.json`, `full_text.md`, `comments/`, `sections/`, and severity-tiered issues. It may not contain `review_summary.json` or 1-5 rating fields unless a Codex-adapted pass added them.
- Treat Claude-style review and multi-agent review as the default paper-review execution style in this skill, not as special opt-in modes. Translate upstream Claude sub-agent instructions into Codex/ChatGPT subagents whenever available.
- If a runtime does not expose subagents, explicitly state that limitation and run the same pass plan serially in the current agent. Preserve the worker-style output contract even in fallback mode by writing one JSON file per planned pass under `comments/`.
- The upstream viz helper still expects `severity`. This skill's canonical handoff uses `impact_rating` and `confidence_rating`; `scripts/save_viz_json.py` adds transient severity values for visualization and labels the viz method as Codex.

## Provenance and layout harmonization

- Treat these as compatible paper-review provenance families:
  - `openaireview_claude`: `review_results/<slug>_review/`, severity-tiered `final_issues.json`, no required root `review_summary.json`.
  - `codex_native`: `paper-review/<slug>_review/`, 1-5 `impact_rating`/`confidence_rating`, and root `review_summary.json`.
  - `review_loop_hybrid`: a first-pass paper-review bundle at the workspace root plus iterative `round-N/` folders from `research-review-loop`.
- Infer provenance from available evidence, not directory name alone. Check `metadata.json` fields such as `review_mode`, `review_loop`, `canonical_handoff_files`, and `round_summaries`; inspect whether `final_issues.json` uses `severity` or 1-5 ratings; and check for `round-N/REVIEW_STATE.json`.
- When importing or continuing an existing OpenAIReview-style workspace, do not move files just to satisfy the Codex-native path preference. Record the actual path in `artifact-index.md` and preserve existing relative paths.
- When downstream skills need numeric routing, prefer a root `review_summary.json` if present; otherwise, in a review-loop hybrid, use the latest existing `round-N/review_summary.json` and record that provenance in `artifact-index.md`.
- If converting an upstream OpenAIReview bundle to Codex-native form, add missing 1-5 ratings and a root `review_summary.json` as a deliberate normalization step. Do not silently reinterpret `severity` as a numeric rating without documenting the mapping.

## Modes

### ChatGPT-native review mode

- Use this as the default for paper-review requests inside ChatGPT/Codex.
- The active chat model performs the LLM critique directly. Scripts may prepare files, validate bundles, or render visualization artifacts, but scripts cannot call the hidden ChatGPT conversation model on their own.
- Follow `references/chatgpt-native-review.md` for the native artifact contract.
- Do not run `python3 scripts/run_openaireview.py review ...` by default. That upstream provider-backed path is only for explicit external-provider review.

### CLI mirror mode

- Preserve the upstream OpenAIReview CLI surface through `scripts/run_openaireview.py`.
- Use this for:
  - `extract`: OCR or parse a paper into Markdown with metadata
  - `serve`: browse saved result JSON in a local UI
  - `review`: only when the user explicitly asks for upstream provider-backed OpenAIReview scoring and has configured the required provider credentials
- Do not confuse the upstream `review` command with the ChatGPT-native default review path.

### Default multi-agent / Claude-style deep review mode

- Use this for normal paper-review tasks unless the user explicitly asks for a quick single-pass response or the runtime cannot support workers.
- Prepare a review workspace.
- Read and understand the full paper.
- Write `summary.md` before launching detailed review passes.
- Build a pass plan with section-level and cross-cutting checks.
- Spawn one worker per planned review pass when subagents are available.
- Consolidate, tier, and save issues into the canonical bundle.
- Prefer this mode when the paper-review stage will feed `research-review-loop`, `research-paper-plan`, or `research-rebuttal`.

### Serial single-agent fallback mode

- Use this only when subagents are unavailable, disabled, blocked by the runtime, or clearly disproportionate for a very short paper or explicitly quick review.
- State the fallback reason before or in the final report.
- Execute the same planned review passes serially in the current agent.
- Keep outputs separate under `comments/` using the same `owned_output_file` paths that workers would have used.
- Do not reduce the number of passes merely because execution is serial; reduce only when the paper is short, incomplete, or the user requested a fast review.

### Contextualized paper review mode

- Use this when the user asks for novelty, significance, impact, related-work adequacy, SOTA/context positioning, venue-grade critique, or a review that should be stronger than internal paper consistency checks.
- After the full-paper summary, extract the paper's:
  - one-sentence contribution claim
  - field/domain and target community
  - claimed novelty dimensions
  - cited closest prior work
  - benchmark/evaluation context
  - impact or significance claims
- Run a bounded `research-systematic-literature-review` paper-context evidence map when the review needs external literature grounding. This is not automatically a full PRISMA review; use the literature skill's paper-context mode unless the user explicitly asks for a full systematic review.
- Run `research-novelty-review` after the literature-context map when the paper makes novelty, contribution, or impact claims. The novelty review should consume both `summary.md` and the literature-context artifacts.
- Fold context outputs back into paper-review findings:
  - related-work omissions become `missing_information` or `claim_accuracy` issues
  - overstated novelty or significance becomes `claim_accuracy`
  - weak impact framing becomes `presentation` unless it affects a core claim
  - benchmark-context gaps become `methodology` or `missing_information`
- Preserve provenance by recording literature and novelty artifact paths in `review_summary.json` and, in orchestrated mode, in `artifact-index.md`.

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
- Supported inputs:
  - local `.pdf`, `.docx`, `.tex`, `.txt`, `.md`
  - arXiv `abs` or `html` URLs
  - extracted Markdown or existing `full_text.md`
- Prefer:
  - venue or audience
  - whether the user wants quick scoring, issue discovery, rebuttal-grade critique, or contextualized critique
  - OCR engine and token/cost constraints when extraction is needed
- Environment:
  - no external provider key is required for ChatGPT-native review
  - optional upstream engine and optional OCR backends may require separate setup

## Hard stops

- Stop if there is no concrete paper artifact, URL, or readable paper text.
- Stop if the task would require invented evidence, fabricated quotes, or guessed paper contents.
- Stop before deep review when the paper is too incomplete to support meaningful section-level scrutiny.
- If the upstream engine is missing and a helper is needed, install it with `scripts/install_engine.py` instead of recreating the package inline. If only ChatGPT-native critique is needed, do not install the upstream engine just to perform LLM review.

## Output contract

- Preserve the active review workspace under `./paper-review/<slug>_review/` unless a different path is explicitly recorded in `artifact-index.md`.
- Required handoff files for downstream stages:
  - `<review_dir>/summary.md`
  - `<review_dir>/final_issues.json`
  - `<review_dir>/review_summary.json`
  - `<review_dir>/overall_assessment.txt`
- Required support files:
  - `<review_dir>/metadata.json`
  - `<review_dir>/full_text.md`
  - `<review_dir>/sections/index.json`
- Required for multi-agent and serial fallback reviews:
  - `<review_dir>/comments/PASS_PLAN.md`
  - one `<review_dir>/comments/*.json` file per planned pass
  - `<review_dir>/comments/all_comments.json` when consolidation is complete
- Optional but strongly preferred:
  - `<review_dir>/context/context-plan.md`
  - `<review_dir>/context/literature-context.md`
  - `<review_dir>/context/novelty-context.md`
  - `./review_results/<slug>_skill.json`
- Record the exact active review workspace path and any viz JSON path in `artifact-index.md` so later skills do not guess.
- For imported Claude/OpenAIReview or review-loop hybrid workspaces, `review_summary.json` may be satisfied by a recorded latest `round-N/review_summary.json`; keep this exception explicit in `artifact-index.md` or `metadata.json`.
- `review_summary.json` is the numeric summary artifact for downstream routing. It should include:
  - `overall_paper_rating` (1-5)
  - `decision_relevance_rating` (1-5)
  - `rating_confidence` (1-5)
  - `execution_mode` (`multi_agent`, `serial_fallback`, or `quick_single_pass`)
  - `fallback_reason` when not using multi-agent execution
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
- Add one tracked subtask per worker using the worker's `pass_id` and owned output file. In serial fallback, keep the same subtasks and mark them as serially executed.
- Mark progress as you move. A deep paper review should not become an opaque one-shot blob of reasoning.

### 1) Prepare or extract the paper text

- If a readable artifact or extracted text is already available, use it directly.
- If extraction is needed and the upstream engine is available, use:

```bash
python3 scripts/run_openaireview.py extract <paper> [flags]
```

- If the upstream engine is unavailable but the runtime has another reliable extraction path, use that path and write `full_text.md` yourself.
- Do not use `scripts/run_openaireview.py review ...` for normal ChatGPT-native review.

### 2) Prepare the review workspace

- Prefer `./paper-review/` as the stage root and `./review_results/` for viz JSON.
- If the upstream workspace helper is available, run:

```bash
python3 scripts/prepare_workspace.py "<input>" \
  --criteria references/criteria.md \
  --output-dir ./paper-review
```

- The workspace must contain:
  - `metadata.json`
  - `full_text.md`
  - `criteria.md`
  - `sections/index.json`
  - `comments/`
- Record the review directory and slug immediately, and write the resolved review directory into `artifact-index.md` if you are in a suite pack.

### 3) Build a full-paper model before criticizing details

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

### 4) Build the pass plan

- Read `sections/index.json` and write a concrete pass plan in `comments/PASS_PLAN.md` before spawning or running detailed checks.
- Aim for 7-10 total passes for a deep review unless the paper is unusually short or narrow:
  - 4-7 section-focused passes covering each major section or logical cluster, or one per major section when the paper is short
  - 3-5 cross-cutting passes for claims vs evidence, evaluation fairness, statistical consistency, notation coherence, related-work adequacy, or paper-specific risks
- Group small or tightly coupled sections rather than creating trivial one-section passes.
- Choose cross-cutting passes from the paper's actual risk profile.
- Each pass plan entry must include:
  - `pass_id`
  - `kind` (`section` or `cross_cutting`)
  - `owned_output_file`
  - primary and related section files
  - one-sentence focus
  - likely failure modes to check
  - expected evidence locations

### 5) Execute review passes with multi-agent default

- Default action: spawn all planned review workers in parallel after `summary.md` is complete.
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
- If subagents are unavailable, execute the same pass plan serially in the current agent and record `execution_mode: "serial_fallback"` plus a concrete `fallback_reason` in `review_summary.json`.

### 6) Pass quality bar

- Use `references/codex-agent-orchestration.md` for spawning/ownership rules, `references/subagent_templates.md` for prompt structure, and `references/criteria.md` for issue format.
- Favor deep, merged root-cause arguments over surface-level issue spam, but do not collapse distinct issues that require different fixes or threaten different paper-level conclusions.
- Each pass must write a JSON array into `comments/`. Empty arrays are valid; missing output files are not.
- After all passes, compare `PASS_PLAN.md` against the files in `comments/`; fill or rerun any missing pass before consolidation.

### 7) Add literature and novelty context when needed

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

### 8) Consolidate and tier findings

- Run the packaged consolidation helper when available:

```bash
python3 scripts/consolidate_comments.py <review_dir>
```

- If the helper is unavailable, consolidate manually in the active agent and still write `comments/all_comments.json` and `final_issues.json`.
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
- As a calibration check, a thorough deep review of a publishable paper usually yields 15-30 total issues across impact levels. A typical publishable paper may have several impact-4 issues, but impact-5 should be reserved for paper-level blockers.

### 9) Save final results for browsing and downstream use

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
  - `execution_mode`
  - `fallback_reason` when relevant
  - `top_blockers`
  - `context_artifacts`
  - `novelty_decision_rating` when available
  - `impact_context_rating` when available
- Write `overall_assessment.txt` as one short paragraph.
- Build viz JSON when useful and the upstream engine is installed:

```bash
python3 scripts/save_viz_json.py <review_dir> --slug-suffix _skill
```

- The output lands in `./review_results/` unless overridden.
- Use `python3 scripts/run_openaireview.py serve` to browse results locally.
- Run `python3 scripts/validate_review_bundle.py --review-dir <review_dir>` before treating the bundle as stable.
- Treat `summary.md`, `final_issues.json`, `review_summary.json`, and `overall_assessment.txt` as the canonical handoff bundle for `research-review-loop`, `research-paper-plan`, and `research-rebuttal`.

## References

- `references/chatgpt-native-review.md`
- `references/engine-usage.md`
- `references/criteria.md`
- `references/codex-agent-orchestration.md`
- `references/rating-rubric.md`
- `references/subagent_templates.md`
- `../research-pipeline-planner/references/review-stage-contract.md`

## Scripts

- `scripts/install_engine.py`: create or update a virtualenv with the upstream OpenAIReview engine
- `scripts/run_openaireview.py`: mirror the upstream `openaireview` CLI, with provider-backed `review` opt-in only
- `scripts/prepare_workspace.py`: delegate to the packaged deep-review workspace preparer
- `scripts/validate_review_bundle.py`: validate required handoff files and 1-5 rating fields for downstream use
- `scripts/consolidate_comments.py`: delegate to the packaged consolidation helper
- `scripts/save_viz_json.py`: delegate to the packaged viz JSON helper
