---
name: research-paper-review
description: Run a first-pass academic review of one manuscript (LaTeX source tree, PDF, DOCX, Markdown, or arXiv URL) with a full-paper summary, planned section and cross-cutting review passes, quote-anchored issues with 1-5 ratings, optional OCR extraction and viz JSON, and a validated handoff bundle. Use when the agent needs an initial or first-pass review of one paper artifact, including extraction, multi-agent or serial pass-based critique, contextualized critique, or viz JSON generation. Prefer `research-review-loop` once a tracked review state or revised artifact already exists, `research-novelty-review` for prior-art and positioning questions, `research-rebuttal` when concrete reviewer comments already exist, and `adversarial-doc-review` for non-paper documents.
---

# Research Paper Review

## Route the task

Choose the smallest route that covers the request, and load only the listed files first.

| Request | Route | Load first |
| --- | --- | --- |
| "Review this draft" with no prior review workspace | Native first-pass review: summary, pass plan, quote-anchored issues, validated bundle | `references/chatgpt-native-review.md`, `references/rating-rubric.md` |
| "Review the revised draft" and a review workspace or `REVIEW_STATE.json` exists | Not this skill: `research-review-loop` | |
| Reviewer comments already exist and the user wants a response | Not this skill: `research-rebuttal` | |
| "Is this novel" or "what prior work am I missing" | Contextualized review, or `research-novelty-review` / `research-systematic-literature-review` standalone | `references/criteria.md`, the SLR interface section below |
| Extract text from a PDF, serve the viz UI, or run the upstream provider-backed engine | CLI mirror mode (optional engine) | `references/engine-usage.md` |
| A LaTeX source tree | Native review after `scripts/flatten_latex.py` | the LaTeX source subsection below |
| Validate or continue an existing bundle of unknown provenance | `scripts/validate_review_bundle.py` first, then the provenance section below | |

## Quick start

1. Decide whether the user needs:
   - extraction only
   - a local viz server for existing result JSON
   - the default budgeted paper-review pass (pass plan first, then workers within the budget)
   - contextualized review that also assesses novelty, impact, and related-work coverage
2. Default LLM review to the active agent model in the current runtime. Do not require external LLM API keys for normal review.
3. Build the full-paper summary and the pass plan first, then pick a depth. Ownership when skills chain: only the skill the user invoked spawns workers, and it sets one budget for the whole chain (quick: no workers, the parent does every pass; standard: up to 3 workers; deep: 5 to 8). A skill reached by handoff never spawns. The budget counts agents, not review checks: a worker runs several planned passes and owns one comments file per pass. Default to standard; use deep when the user asks for a deep, thorough, or venue-grade review or the paper is long; use quick when the user asks for a fast read.
4. Run serially, with the same pass plan and the same comment files, at quick depth, when this skill was reached by handoff (from `research-review-loop`, `research-pipeline-planner`, or another skill), and when the runtime has no subagents.
5. Bootstrap the upstream engine with `python3 scripts/install_engine.py` when deterministic helpers are needed for extraction, workspace preparation, viz output, or explicit upstream provider-backed review. The engine is pinned to OpenAIReview 0.3.0 and installs into a versioned virtualenv outside the skill directory (`references/engine-usage.md`).
6. Use the `/openaireview` workspace convention as the canonical stage root: `./review_results/<slug>_review/`. Review-loop rounds for the same paper go to integer `round-<N>/` folders inside it. Record any non-canonical output paths in `artifact-index.md`.
7. Use `references/chatgpt-native-review.md` (the runtime-neutral native review contract), `references/rating-rubric.md`, and the 1-5 issue/output scales.
8. When review quality depends on novelty, impact, or literature context, route through `research-systematic-literature-review` and `research-novelty-review` instead of limiting the critique to internal paper consistency.
9. Find existing review artifacts with `scripts/resolve_review_artifacts.py --root .`, which reports every review home, its layout, the latest round, and the next round's path, instead of assuming a `paper-review/` path. When reusing an existing review workspace, infer its provenance from `metadata.json`, `artifact-index.md`, `final_issues.json`, `review_summary.json`, and any `round-N/` folders before moving files or declaring artifacts missing.
10. Treat `research-systematic-literature-review` as an independent literature-review skill that can either run on its own or attach to this review workspace through `<review_dir>/context/`.
11. If the user asks for project-level sequencing, current-state inspection, or coordination across multiple research stages, invoke `research-pipeline-planner` first instead of treating paper review as the whole task.

## Upstream Claude Skill Compatibility

- The upstream OpenAIReview Claude Code skill lives in `src/reviewer/skill/` and is installed by `openaireview install-skill` into `~/.claude/commands/openaireview`. That install path, the `/openaireview` slash command, and references to Claude's Agent/task tools are specific to Claude Code. In Claude Code the upstream command is a valid way to produce an `openaireview_claude` bundle; in other runtimes, follow the portable workflow below.
- The underlying workflow is portable: prepare a review workspace, collect section-review JSON, consolidate comments, and emit viz-compatible JSON.
- The upstream Claude/OpenAIReview workspace convention is `./review_results/<slug>_review/`, with `summary.md`, `final_issues.json`, `overall_assessment.txt`, `metadata.json`, `full_text.md`, `comments/`, `sections/`, and severity-tiered issues. It may not contain `review_summary.json` or 1-5 rating fields unless a native-schema pass added them.
- Treat Claude-style pass planning as the default review method in this skill. The worker count follows the budget in Quick start step 3, not the upstream skill's one-agent-per-pass default; translate upstream sub-agent instructions into the runtime's own mechanism within that budget.
- If a runtime does not expose subagents, explicitly state that limitation and run the same pass plan serially in the current agent. Preserve the worker-style output contract even in fallback mode by writing one JSON file per planned pass under `comments/`.
- The upstream viz helper accepts `severity`. This skill's canonical handoff uses `impact_rating` and `confidence_rating`; `scripts/save_viz_json.py --derive-severity` can temporarily derive severity values for visualization when that compatibility layer is explicitly requested.

## Provenance and layout harmonization

- Treat these as compatible paper-review provenance families:
  - `openaireview_claude`: `review_results/<slug>_review/`, severity-tiered `final_issues.json`, no required root `review_summary.json`.
  - `codex_native`: `review_results/<slug>_review/`, 1-5 `impact_rating`/`confidence_rating`, and root `review_summary.json`.
  - `review_loop_hybrid`: a first-pass paper-review bundle at the workspace root plus iterative `round-N/` folders from `research-review-loop`.
- Infer provenance from available evidence, not directory name alone. Check `metadata.json` fields such as `review_mode`, `review_loop`, `canonical_handoff_files`, and `round_summaries`; inspect whether `final_issues.json` uses `severity` or 1-5 ratings; and check for `round-N/REVIEW_STATE.json`.
- When importing or continuing an existing OpenAIReview-style workspace, do not move files just to satisfy the native path preference. Record the actual path in `artifact-index.md` and preserve existing relative paths.
- When downstream skills need numeric routing, prefer a root `review_summary.json` if present; otherwise, in a review-loop hybrid, use the newest `round-N/review_summary.json` that validates (rounds may sit inside `<review_dir>` or next to it) and record that provenance in `artifact-index.md`.
- If converting an upstream OpenAIReview bundle to the native 1-5 form (`codex_native` family), add missing 1-5 ratings and a root `review_summary.json` as a deliberate normalization step. Do not silently reinterpret `severity` as a numeric rating without documenting the mapping.

## Modes

### Native review mode

- Use this as the default for paper-review requests in any agent runtime.
- The active agent model performs the LLM critique directly. Scripts may prepare files, validate bundles, or render visualization artifacts, but scripts cannot call the runtime's conversation model on their own.
- Follow `references/chatgpt-native-review.md` for the native artifact contract.
- Do not run `python3 scripts/run_openaireview.py review ...` by default. That upstream provider-backed path is only for explicit external-provider review.

### CLI mirror mode

- Preserve the upstream OpenAIReview CLI surface through `scripts/run_openaireview.py`.
- Use this for:
  - `extract`: OCR or parse a paper into Markdown with metadata
  - `serve`: browse saved result JSON in a local UI
  - `review`: only when the user explicitly asks for upstream provider-backed OpenAIReview scoring and has configured the required provider credentials
- Do not confuse the upstream `review` command with the native default review path.

### Default budgeted review mode

- Use this for normal paper-review tasks.
- Prepare a review workspace.
- Read and understand the full paper.
- Write `summary.md` before launching detailed review passes.
- Build a pass plan with section-level and cross-cutting checks.
- When this skill is the one the user invoked, assign the planned passes to at most the budget's workers (standard: up to 3; deep: 5 to 8), grouping related passes so each worker gets a coherent share. Each pass keeps its own `owned_output_file`.
- Consolidate, tier, and save issues into the canonical bundle.
- Prefer this mode when the paper-review stage will feed `research-review-loop`, `research-paper-plan`, or `research-rebuttal`.

### Serial mode

- Use this at quick depth, when this skill was reached by handoff (the invoking skill owns the budget and the workers), and when subagents are unavailable, disabled, or blocked by the runtime.
- State the reason before or in the final report.
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

### SLR interface mode

- Use this when `research-paper-review` and `research-systematic-literature-review` are invoked semi-autonomously in the same project.
- Preserve independence: the SLR skill owns source discovery, screening, evidence extraction, synthesis, confidence limits, and full PRISMA mode. Paper-review must not rewrite literature-search decisions or treat a bounded evidence map as a full systematic review.
- Preserve synergy: when a paper-review workspace exists, use `<review_dir>/context/` as the shared exchange point for paper-context artifacts. The SLR skill may write there directly or produce an independent literature pack and record its directory in `review_summary.json.context_artifacts`.
- The negotiated paper-context bundle is:
  - `<review_dir>/context/literature-context.md`
  - `<review_dir>/context/literature-context-search-log.md`
  - `<review_dir>/context/literature-context-evidence-table.md`
  - `<review_dir>/context/literature-context-decision.json`
- Paper-review consumes the decision JSON, not just prose. Map `impact_evidence_rating` to `review_summary.json.impact_context_rating`, preserve `contextualization_rating` and `coverage_confidence_rating` under `review_summary.json.context_artifacts`, and convert `related_work_omissions` / `benchmark_context_gaps` into raw comment JSON before consolidation when they affect the paper review.
- If SLR runs first without a paper-review workspace, do not move its artifacts. When paper-review starts later, record the SLR artifact directory in `artifact-index.md` and either copy the four paper-context files into `<review_dir>/context/` or reference them explicitly in `review_summary.json.context_artifacts`.

## Relationship to sibling skills

- `research-paper-review` owns paper ingestion, OCR, first-pass critique, and viz output for a single paper.
- `research-systematic-literature-review` owns external evidence mapping. It remains useful as a standalone full systematic-review workflow; within paper review, use its paper-context mode for bounded related-work, benchmark-context, and impact-evidence checks, and reserve full PRISMA mode for explicit systematic-review requests or broad evidence-coverage decisions.
- `research-review-loop` owns iterative tracked review after there is already a first-pass critique, revision cycle, or explicit issue ledger.
- `research-novelty-review` owns prior-art pressure testing and positioning. Within contextualized paper review, run it after the paper summary and literature-context map exist so novelty judgments are evidence-grounded.
- `research-rebuttal` owns responses to external reviewer comments, not initial manuscript diagnosis.
- `adversarial-doc-review` owns broad document red-teaming outside the paper-review workflow, especially non-paper Markdown or policy/spec documents.

## Research-suite handoff

- Keep the `/openaireview` workspace layout, but write research-suite handoff artifacts into that same review directory.
- `summary.md`, `final_issues.json`, `review_summary.json`, and `overall_assessment.txt` are the stable handoff bundle for `research-review-loop`, `research-paper-plan`, `research-rebuttal`, and `technical-writing-reviser` (which reads `final_issues.json` as critique intake).
- `review_summary.json` is required for native (`codex_native`) runs because sibling skills use it for numeric routing, currentness, top blockers, execution mode, and context provenance.
- Contextual paper-review outputs should live under `<review_dir>/context/` and be listed in `review_summary.json.context_artifacts` so `research-novelty-review` and `research-systematic-literature-review` outputs remain traceable.
- If a project-level `artifact-index.md` exists, record the review directory, viz JSON path, and any sibling-skill context artifact paths there.

## Input contract

- Minimum:
  - one concrete paper artifact or URL
- Supported inputs:
  - local `.pdf`, `.docx`, `.txt`, `.md`
  - a LaTeX source tree (root `.tex` plus the files it `\input`s); see "LaTeX source" below
  - arXiv `abs` or `html` URLs
  - extracted Markdown or existing `full_text.md`
- Prefer:
  - venue or audience
  - whether the user wants quick scoring, issue discovery, rebuttal-grade critique, or contextualized critique
  - OCR engine and token/cost constraints when extraction is needed
- Environment:
  - no external provider key is required for native review
  - optional upstream engine and optional OCR backends may require separate setup

## Hard stops

- Stop if there is no concrete paper artifact, URL, or readable paper text.
- Stop if the task would require invented evidence, fabricated quotes, or guessed paper contents.
- Stop before deep review when the paper is too incomplete to support meaningful section-level scrutiny.
- If the upstream engine is missing and a helper is needed, install it with `scripts/install_engine.py` instead of recreating the package inline. If only native critique is needed, do not install the upstream engine just to perform LLM review.

## Output contract

Reader-facing prose in these artifacts is written under the drafting contract (`writing/technical-writing-drafter/references/drafting-contract.md`): claims listed with their support before writing, no machine-prose tells, and `prose_tells.py --max-density 20` run on the draft before handoff, with its summary line recorded in the artifact index. Do not draft first and patch later. This applies to `summary.md`, the issue explanations, and `overall_assessment.txt`; the paper under review is not edited by this skill.

- Preserve the active review workspace under `./review_results/<slug>_review/` unless a different path is explicitly recorded in `artifact-index.md`.
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
  - `<review_dir>/context/literature-context-search-log.md`
  - `<review_dir>/context/literature-context-evidence-table.md`
  - `<review_dir>/context/literature-context-decision.json`
  - `<review_dir>/context/novelty-context.md`
  - `./review_results/<slug>_skill.json`
- Record the exact active review workspace path and any viz JSON path in `artifact-index.md` so later skills do not guess.
- Imported `openaireview_claude` bundles carry no root `review_summary.json`; the validator accepts them as that family. For review-loop hybrid workspaces, `review_summary.json` may be satisfied by the newest valid `round-N/review_summary.json` (listed in `metadata.json.round_summaries`, inside `<review_dir>`, or next to it); keep this exception explicit in `artifact-index.md` or `metadata.json`.
- `review_summary.json` is the numeric summary artifact for downstream routing. It should include:
  - `overall_paper_rating` (1-5)
  - `decision_relevance_rating` (1-5)
  - `rating_confidence` (1-5)
  - `execution_mode` (`multi_agent`, `serial_fallback`, or `quick_single_pass`)
  - `fallback_reason` when not using multi-agent execution (`quick depth`, `handoff from <skill>`, or the runtime limitation)
  - `depth` (`quick`, `standard`, or `deep`) and `workers_used`, so the chain's budget stays visible
  - `top_blockers`
  - `context_artifacts` when literature or novelty context was used
  - `contextualization_rating`, `coverage_confidence_rating`, and `impact_context_rating` when literature context was used
  - `novelty_decision_rating` and `impact_positioning_rating` when novelty context was used

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
- Do not use `scripts/run_openaireview.py review ...` for normal native review.

#### LaTeX source

- Treat a `.tex` input as a source tree, not a single file. The root is the file with `\documentclass` that no other file `\input`s or `\include`s; if several qualify, prefer the user's choice or `main.tex`, and ask when the choice changes what gets reviewed.
- Flatten it with `python3 scripts/flatten_latex.py <root.tex or source_dir> --output-dir <review_dir>`. It inlines `\input`, `\include`, and `\subfile` recursively, drops the preamble and comments, takes the title from `\title{}`, writes `full_text.md`, and writes `latex_source_map.json` (flattened line -> `file:line`, included files, unreferenced `.tex` files, missing inputs). It also records the title, root, and exclusions in `metadata.json`.
- Review only what the root reaches. List unreferenced `.tex` files (retired drafts, unused sections) as excluded in `summary.md`; never review them as part of the paper.
- Build `sections/index.json` from `\section` boundaries in the flattened text, not from size-based chunks. Cite locations as `file:line` from the source map.
- Value or slot macros (for example a `\resultslot{ID}` resolved from a values file) hide the numbers the reader sees. Expand them from the registry when it is readable; otherwise keep the macro calls and record "values not reviewed" in `review_summary.json.limitations`. A quote that contains a macro call is not evidence of the printed value.
- A compiled PDF, when present, is the authority for page counts, figure and table placement, and float checks. The flattened source is the authority for wording and quotes.
- If the repo has its own manuscript checks (for example `scripts/check_manuscript_integrity.py`, a `review_checks.py`, or a bibliography audit), run or read them and cite their output instead of duplicating that pass.

### 2) Prepare the review workspace

- Prefer `./review_results/` as both the review workspace root and the viz JSON output root, matching `/openaireview`.
- If the upstream workspace helper is available, run:

```bash
python3 scripts/prepare_workspace.py "<input>" \
  --criteria references/criteria.md \
  --output-dir ./review_results
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

### 5) Execute review passes within the budget

- Ownership when skills chain: only the skill the user invoked spawns workers, and it sets one budget for the whole chain (quick: no workers, the parent does every pass; standard: up to 3 workers; deep: 5 to 8). A skill reached by handoff never spawns. The budget counts agents, not review checks: a worker runs several planned passes and owns one comments file per pass.
- Default action when this skill was invoked by the user at standard or deep depth: after `summary.md` is complete, launch at most the budget's workers in parallel and give each a share of the planned passes. Keep a section pass and the cross-cutting passes that read the same sections with the same worker when that keeps the count inside the budget.
- Worker ownership must be disjoint: each pass's JSON array goes to its own `owned_output_file` under `<review_dir>/comments/`, and only the worker assigned that pass writes it. Cross-cutting passes read many sections but still write only their own file.
- Worker prompt requirements:
  - state that the worker is not alone in the workspace
  - state the worker's owned output file
  - state that the worker must not edit shared files or other workers' comment files
  - include the section-focused or cross-cutting template from `references/subagent_templates.md`
  - require valid JSON output even when no issues are found (`[]`)
  - require the final response to list the file path changed and the issue titles
- While workers run, the parent should do non-overlapping work only: inspect `summary.md`, check section coverage, prepare consolidation criteria, or draft the final bundle skeleton. Do not redo a worker's assigned pass.
- Wait for all workers before consolidation. If a worker returns JSON in chat rather than materializing its file, the parent must write that JSON to the worker's owned output file before running consolidation.
- At quick depth, when reached by handoff, or when subagents are unavailable, execute the same pass plan serially in the current agent and record `execution_mode: "serial_fallback"` plus a concrete `fallback_reason` in `review_summary.json`.
- Revision is not part of this skill's budget unless this skill was invoked and the user asked for revision too: review owns diagnosis, `technical-writing-reviser` owns prose per issue cluster, and `prose-flow-improver` is one serial final pass, all inside the invoking skill's budget.

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
- The paper-context SLR exchange must produce or reference all four paper-context artifacts under `<review_dir>/context/`: `literature-context.md`, `literature-context-search-log.md`, `literature-context-evidence-table.md`, and `literature-context-decision.json`. Use the SLR helper `scripts/paper_context_artifacts.py init --review-dir <review_dir> ...` when a deterministic scaffold is useful. The scaffold starts with null ratings and TODO cells and fails `paper_context_artifacts.py validate` until it is filled; pass `--draft` to validate a work-in-progress bundle.
- If the user explicitly asks for a full systematic review, or if a venue-critical claim depends on broad evidence coverage, run the full `research-systematic-literature-review` workflow and record its artifact directory as `systematic_review_artifact_dir` in `review_summary.json.context_artifacts`.
- Invoke `research-novelty-review` when novelty or impact positioning matters. It should consume `summary.md`, `<review_dir>/context/literature-context.md` when present, and any recorded `systematic_review_artifact_dir`. Write or copy its bottom-line decision to `<review_dir>/context/novelty-context.md`.
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
- Do not hand-write a separate `severity` field unless another tool specifically needs it. If a downstream OpenAIReview visualization/export path needs severity tiers, call `scripts/save_viz_json.py` with `--derive-severity` and document that compatibility export.
- Write `review_summary.json` in the review directory with:
  - `overall_paper_rating`
  - `decision_relevance_rating`
  - `rating_confidence`
  - `execution_mode`
  - `fallback_reason` when relevant
  - `depth` and `workers_used`
  - `top_blockers`
  - `context_artifacts`
  - `contextualization_rating`, `coverage_confidence_rating`, and `impact_context_rating` when available from `literature-context-decision.json`
  - `novelty_decision_rating` when available
  - `impact_positioning_rating` when available from novelty context
- Write `overall_assessment.txt` as one short paragraph.
- Build viz JSON when useful and the upstream engine is installed:

```bash
python3 scripts/save_viz_json.py <review_dir> --slug-suffix _skill [--runtime <name>]
```

- `--runtime` labels the viz method key `openaireview__<name>`, the method label, and the model field (default `agent`).

- The output lands in `./review_results/` unless overridden. Add `--derive-severity` only when the visualization/export should explicitly map 1-5 impact ratings to OpenAIReview severity tiers.
- Use `python3 scripts/run_openaireview.py serve` to browse results locally.
- Run `python3 scripts/validate_review_bundle.py --review-dir <review_dir>` before treating the bundle as stable. It prints the inferred provenance family (`openaireview_claude`, `codex_native`, or `review_loop_hybrid`), also on failure, and checks that family's required set: `openaireview_claude` needs the root files and severity-tiered issues and no root `review_summary.json`; `codex_native` needs a root `review_summary.json` and 1-5 ratings; `review_loop_hybrid` needs a resolvable valid round summary. Pass `--family <name>` to validate against a stated family (for example `--family openaireview_claude` to check only the first-pass bundle of a hybrid).
- Treat `summary.md`, `final_issues.json`, `review_summary.json`, and `overall_assessment.txt` as the canonical handoff bundle for `research-review-loop`, `research-paper-plan`, and `research-rebuttal`.

## Stage gate

This skill owns its stage gate. Standalone, it is the proceed, revise, or stop test for the request. In an orchestrated project the planner applies it, together with the paper-identity and evidence-promotion gates in `research-pipeline-planner/SKILL.md`, before work enters or leaves this stage.

- Proceed when there is a concrete paper artifact or URL worth scrutinizing closely.
- Revise when the draft is so incomplete that section-level critique would mostly produce noise.
- Stop when the requested review would require guessing missing paper content or fabricating evidence.
- Record whether proposed fixes are D0-D2 repairs or D3-D4 pivot requests.

## References

- `references/chatgpt-native-review.md`
- `references/engine-usage.md`
- `references/criteria.md`
- `references/codex-agent-orchestration.md`
- `references/rating-rubric.md`
- `references/review-schema.md` (canonical issue and summary schemas, conversion table, known layouts)
- `references/subagent_templates.md`
- `../research-pipeline-planner/references/review-stage-contract.md`

## Scripts

- `scripts/install_engine.py`: install the pinned upstream OpenAIReview engine (0.3.0) into a versioned virtualenv outside the skill directory; the wrappers refuse an installed version that differs from the pin
- `scripts/run_openaireview.py`: mirror the upstream `openaireview` CLI, with provider-backed `review` opt-in only
- `scripts/prepare_workspace.py`: delegate to the packaged deep-review workspace preparer
- `scripts/validate_review_bundle.py`: infer the provenance family, then validate that family's required handoff files, issue schema, and summary; resolves round summaries from `metadata.round_summaries`, `<review_dir>/round-*`, and `<review_dir>/../round-*`, newest valid first; `--family` asserts a family
- `scripts/review_schema.py`: read issues and summaries in any known layout into the canonical schemas (`references/review-schema.md`); shared, byte-identical, with review-loop and rebuttal
- `scripts/resolve_review_artifacts.py`: find review artifacts in any known layout under a root, report each review's latest round and first-pass bundle, and print the canonical next round (`--next-round`; `--slug` starts `review_results/<slug>_review/`); read-only, shared with review-loop and rebuttal
- `scripts/flatten_latex.py`: flatten a LaTeX source tree into `full_text.md` with `latex_source_map.json` and a list of unreferenced `.tex` files (stdlib only, no engine needed)
- `scripts/consolidate_comments.py`: delegate to the packaged consolidation helper
- `scripts/save_viz_json.py`: delegate to the packaged viz JSON helper; `--runtime` sets the method key and model label (default `agent`)
