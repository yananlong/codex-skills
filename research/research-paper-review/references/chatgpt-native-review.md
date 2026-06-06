# ChatGPT-Native Review

Use this path inside ChatGPT/Codex when the user wants an LLM paper review and has not explicitly asked to spend external provider/API-key calls. Python scripts bundled with a skill cannot call the hidden ChatGPT conversation model on their own; the active assistant must perform the LLM judgment directly and use scripts only for deterministic file preparation, validation, and optional visualization.

## Routing rule

- Default to ChatGPT-native review for `review`, deep review, contextualized review, and agentic review requests inside ChatGPT/Codex.
- Default ChatGPT-native paper review to Claude-style / multi-agent orchestration: build the full-paper summary, plan review passes, then spawn one worker per pass when subagents are available.
- Use serial single-agent review only as a fallback when subagents are unavailable, disabled, blocked by the runtime, or clearly disproportionate for a very short or explicitly quick review.
- Do not run `python3 scripts/run_openaireview.py review ...` unless the user explicitly requests the upstream provider-backed OpenAIReview CLI or sets `OPENAIREVIEW_USE_EXTERNAL_LLM=1` / passes `--external-llm` and has provider keys configured.
- It is still fine to use upstream deterministic helpers for extraction, workspace preparation, consolidation, validation, and local visualization when available. If those helpers fail because the upstream package is absent, either install the engine with `scripts/install_engine.py` or create the same workspace files directly.

## Native execution contract

The active chat model owns the LLM work:

1. Ingest the paper text from the uploaded artifact, extracted Markdown, arXiv text, or an existing `full_text.md`.
2. Create or reuse a review workspace under `./paper-review/<slug>_review/`.
3. Ensure these files exist before detailed review:
   - `metadata.json`
   - `full_text.md`
   - `sections/index.json`
   - `criteria.md`
   - `comments/`
4. Write `summary.md` after reading the full paper.
5. Build `comments/PASS_PLAN.md` with section and cross-cutting passes.
6. Spawn the planned review passes as parallel subagents when available. Each pass writes one JSON array under `comments/`.
7. If subagents are unavailable, run the same planned passes serially in the current agent and record the fallback reason in `review_summary.json`.
8. Consolidate findings into `final_issues.json`, `review_summary.json`, and `overall_assessment.txt` using the normal schema.
9. Run `python3 scripts/validate_review_bundle.py --review-dir <review_dir>` before treating the bundle as stable.
10. Optionally run `python3 scripts/save_viz_json.py <review_dir> --slug-suffix _skill` if the upstream engine is installed and visualization JSON is useful.

## Required native artifacts

`metadata.json` should include at least:

```json
{
  "title": "Paper title or best available slug",
  "slug": "paper_slug",
  "source": "uploaded file, arXiv URL, or user-provided text",
  "review_mode": "chatgpt_native"
}
```

`review_summary.json` should identify how the native review actually ran:

```json
{
  "execution_mode": "multi_agent",
  "fallback_reason": null,
  "overall_paper_rating": 3,
  "decision_relevance_rating": 4,
  "rating_confidence": 4,
  "top_blockers": []
}
```

Use `execution_mode: "serial_fallback"` and a concrete `fallback_reason` when the worker plan had to run in one agent.

`sections/index.json` should be a JSON array. Each item should include:

```json
{
  "section_id": "s1",
  "title": "Introduction",
  "path": "sections/s1_introduction.md",
  "start_hint": "optional source location or heading"
}
```

If splitting into section files is not worth it for a short paper, keep `sections/index.json` as a section map over `full_text.md` and make each `path` point to `full_text.md` with a heading hint.

Each comment file under `comments/` must be a JSON array of issue candidates. Use the same fields as `final_issues.json` when possible:

```json
[
  {
    "title": "Specific issue title",
    "quote": "Short exact quote or table/figure reference from the paper",
    "explanation": "Why this matters and what conclusion it affects",
    "comment_type": "methodology",
    "impact_rating": 4,
    "confidence_rating": 4
  }
]
```

Allowed `comment_type` values are `methodology`, `claim_accuracy`, `presentation`, and `missing_information`.

## Refusal and fallback rules

- Do not fabricate quotes. If an issue is real but no exact quote is available, reference the section, table, figure, or equation precisely and say that no exact quote was available.
- If the paper text cannot be extracted or inspected, stop and ask for a readable artifact or text.
- If the user asks for a quick review and no file-writing tools are available, return the review in chat using the same issue schema instead of pretending a bundle was saved.
- If subagents are unavailable, do not skip pass planning. Run the same pass plan serially, preserve one JSON file per pass, and record `execution_mode: "serial_fallback"`.
- If the user explicitly asks for upstream OpenAIReview scoring with a provider model, use the external CLI path and require configured provider keys.
