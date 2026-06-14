---
name: research-systematic-literature-review
description: Full systematic literature review (PRISMA 2020 core) with discovery, screening, evidence extraction, synthesis, confidence grading, and adversarial stress-testing across papers. Prefer peer-reviewed published versions over preprints and use this skill either directly or as the coordinated literature stage inside a larger research workflow. Use when asked to run or audit a literature review, evidence synthesis, state-of-the-art survey with explicit methods, citation integrity checks, or confidence-rated conclusions from research publications.
---

# Research Systematic Literature Review

## Quick start

1. Require `domain` before substantive review work. In paper-context mode, infer it from the target paper summary only when the field is clear; otherwise stop and ask.
2. Collect optional inputs including whether the user wants deep technical/mathematical exposition. If `technical_exposition` is not provided, ask the user to choose between `standard` and `detailed_math` for full systematic reviews; in paper-context mode default to `standard` unless the paper-review task requests mathematical positioning. Apply defaults for missing non-domain inputs and log assumptions.
3. Check tool access. If web browsing/search is unavailable and no corpus or Zotero access is provided, stop and ask for browsing access, `research-zotero`, or a user corpus.
4. Initialize the full review artifact pack with `scripts/init_review_pack.py` for full systematic mode; in paper-context mode, create the smaller paper-context files from `references/paper-context-template.md`.
5. If Zotero is relevant, invoke `research-zotero` first or consume existing `./zotero/` artifacts.
6. Run discovery, deduplication (including preprint-to-published-version resolution), screening, extraction, synthesis, and adversarial checks.
7. For every included study or context work, record a canonical `publication_url`. Prefer the published journal/proceedings/venue page, DOI resolver, PubMed/PMC record, society digital-library page, or accepted venue record. Use a preprint URL only when no published/accepted version exists, and label that status explicitly.
8. For paper-review integration, use paper-context mode when the task is bounded related-work/impact contextualization rather than a full systematic review.
9. Generate PRISMA flow accounting with `scripts/prisma_flow_md.py` and insert it into `<topic>.review.md` for full systematic mode.
10. Validate the full pack with `scripts/validate_review_pack.py` before returning output when full systematic mode is used; in paper-context mode, validate the four-file exchange bundle with `scripts/paper_context_artifacts.py validate`.
11. Preserve independence and synergy: this skill can run as a standalone SLR, but when a paper-review workspace is supplied, write the bounded context exchange bundle into `<review_dir>/context/` so paper-review and novelty-review can consume it without redoing discovery.

## Modes

### Full systematic review mode

- Use this when the user asks for a systematic literature review, evidence synthesis, state-of-the-art survey with explicit methods, or a decision that requires broad coverage.
- Follow the full PRISMA-oriented workflow and output contract below.
- This mode should not be silently substituted with a quick related-work scan.

### Paper-context evidence map mode

- Use this mode when `research-paper-review` needs external context for one paper's novelty, impact, related-work adequacy, benchmark coverage, or SOTA claims.
- This is a bounded evidence map, not a full systematic review, unless the user explicitly asks for full PRISMA coverage.
- Inputs should come from `research-paper-review/summary.md` when available: paper title/domain, one-sentence contribution claim, novelty dimensions, cited closest prior work, benchmark/evaluation context, and 3-8 targeted context questions.
- Output may be smaller than a full review pack, but must still log sources, queries, inclusion decisions, version-resolution decisions, canonical publication URLs, and confidence limits.
- When invoked from a paper-review workspace, write outputs under `<review_dir>/context/`. When invoked independently, keep outputs in a caller-chosen directory and record that directory when a later paper-review stage consumes it.
- Required paper-context outputs: `literature-context.md`, `literature-context-search-log.md`, `literature-context-evidence-table.md`, and `literature-context-decision.json`.
- `literature-context-decision.json` should include `contextualization_rating`, `impact_evidence_rating`, `coverage_confidence_rating`, `closest_prior_work`, `related_work_omissions`, `benchmark_context_gaps`, and `limits_of_search`.

### Independent / orchestrated boundary

- Standalone SLR mode owns its own artifact directory, topic slug, protocol, PRISMA accounting, evidence table, synthesis, and confidence assessment. It must not require a paper-review workspace.
- Orchestrated paper-context mode is an adapter, not a demotion of SLR. It keeps the SLR responsibilities for source discovery, deduplication, screening, evidence extraction, and confidence limits, but scopes them to the target paper claims supplied by paper-review.
- If `research-paper-review` supplies `<review_dir>/summary.md` and `<review_dir>/context/context-plan.md`, treat `<review_dir>/context/` as the exchange directory and use `scripts/paper_context_artifacts.py init --review-dir <review_dir>` to scaffold artifacts when useful.
- If this skill runs first and paper-review runs later, do not relocate the SLR pack. Paper-review should preserve the original paths in `artifact-index.md` or copy only the four bounded paper-context outputs into its `context/` directory with provenance.

## Relationship to sibling skills

- `research-paper-review` owns technical critique of a single paper. When it needs external grounding for related-work, impact, SOTA, benchmark, or significance claims, this skill supplies an independently valid paper-context evidence map or full systematic review.
- `research-novelty-review` owns adversarial novelty and positioning decisions. It should consume this skill's paper-context evidence map when available instead of duplicating broad discovery.
- `research-zotero` owns library sync and citation export. This skill may consume Zotero artifacts but should still screen records against the protocol.
- `research-review-loop` may consume literature-context artifacts as evidence for whether a revised paper has fixed related-work or overclaim issues.
- `research-paper-plan` may consume the synthesis and confidence assessment to decide how strongly the manuscript can frame its contribution.

## Input contract

### Required input

- `domain`: mandatory. Do not continue without this value.

### Optional inputs with defaults

- `research_question`: default to "What does current evidence show about <topic> in <domain>?"
- `inclusion_criteria`: default to peer-reviewed primary studies (published) relevant to topic and domain; use high-quality preprints only when no published version exists or when recency is essential, and label them.
- `exclusion_criteria`: default to off-topic studies, non-substantive summaries, and sources without sufficient methodological detail.
- `date_range`: default to the last 10 years through today.
- `study_types`: default to experimental, observational, benchmarking, and systematic-review studies when relevant.
- `language`: default to English.
- `population/context`: default to the broad population/context implied by topic and domain.
- `outcomes`: default to efficacy/performance, robustness, safety, and transferability outcomes where applicable.
- `quality_threshold`: default to retain studies with at least moderate methodological quality and transparent reporting.
- `technical_exposition`: default to `standard`. If set to `detailed_math`, the `<topic>.review.md` must include formal definitions/notation, key equations/objectives, and when relevant theorem statements or proof sketches in the `Synthesis` section.
- `zotero_library_type`, `zotero_library_id`, `zotero_collection_key`, `zotero_query`, `zotero_tags`, and `zotero_access_mode`: optional Zotero controls.

## Hard-stop and failover rules

- Stop immediately if `domain` is missing.
- In paper-context mode, `domain` may be inferred from `research-paper-review/summary.md` only when unambiguous; log the inference under assumptions.
- Stop immediately if web browsing/search is unavailable and there is no user-provided corpus and no `research-zotero` artifact or Zotero API/MCP path.
- Continue with soft defaults only for non-domain fields and explicitly log all defaults under "Assumptions applied".

## Default output contract

Primary file: `<topic>.review.md`

Supporting files:
- `<topic>.protocol.md`
- `<topic>.search-log.md`
- `<topic>.screening-log.md`
- `<topic>.evidence-table.md`

Optional support files when Zotero is used:
- `<topic>.zotero-items.json`
- `<topic>.zotero-sync.md`

Required sections in `<topic>.review.md`: `Protocol`, `Search Strategy`, `Screening Decisions`, `Evidence Table`, `Synthesis`, `Adversarial Stress Test`, `Limitations`, `Confidence Assessment`, and `PRISMA flow accounting`.

The full-review evidence table must include a `publication_url` column for every included study. The URL must point to the canonical published or accepted venue record when one exists; a preprint URL is acceptable only when no published/accepted version exists and `publication_status` makes that clear.

## Paper-context output contract

When invoked from `research-paper-review` for bounded context, the minimum output is:
- `<review_dir>/context/literature-context.md`
- `<review_dir>/context/literature-context-search-log.md`
- `<review_dir>/context/literature-context-evidence-table.md`
- `<review_dir>/context/literature-context-decision.json`

When invoked independently, use the same four filenames in the selected output directory and record that directory for later handoff.

`literature-context.md` must include `Scope`, `Target paper claims being contextualized`, `Search strategy`, `Closest prior work`, `Related-work coverage assessment`, `Benchmark or evaluation context`, `Impact/significance context`, `Claims that need qualification`, and `Confidence and limitations`.

`literature-context-evidence-table.md` and any closest-prior-work tables must include publication URLs for each retained work, preferring published/accepted venue records over preprint records.

This mode must clearly state: "This is a bounded paper-context evidence map, not a full systematic review" unless the full PRISMA workflow was actually completed.

## Artifact naming rules

- Normalize `<topic>` to lowercase hyphen-case for file names.
- Keep full systematic outputs in one SLR review directory. Keep paper-context outputs in `<review_dir>/context/` when called from paper-review, or in one explicit paper-context directory when called independently.
- Refuse to overwrite existing artifacts unless explicit overwrite is requested.

## Workflow (PRISMA 2020 core + adversarial pass)

### 1) Define protocol

- Use `references/protocol-template.md`.
- Record topic, domain, question, inclusion/exclusion criteria, date range, outcomes, and quality threshold.
- Log every default assumption.
- In paper-context mode, create the four-file exchange bundle before or during protocol definition:

```bash
python3 scripts/paper_context_artifacts.py init --review-dir <review_dir> \
  --summary <review_dir>/summary.md \
  --context-plan <review_dir>/context/context-plan.md
```

- If no paper-review workspace exists, use `--out-dir <context_dir>` instead of `--review-dir`.

### 2) Execute discovery and search logging

- Use `references/search-strategy-template.md`.
- Search multiple relevant sources and log exact query strings, filters, and retrieval dates.
- If Zotero access is available, use `research-zotero` or consume its artifacts and decide whether Zotero is a curated seed library, citation cross-check source, or discovery source for saved collections/tags.
- If `./zotero/zotero-items.json` already exists, prefer consuming it over re-syncing.
- If Zotero MCP is available in the runtime, `research-zotero` should prefer it for interactive library inspection; otherwise it should use available API access when configured.
- For major ML conferences hosted on OpenReview, include OpenReview as a first-class discovery source when applicable, log reproducible query details, and filter to accepted venue papers when using records as canonical publications.
- Prefer published/peer-reviewed indexing and publisher sources over preprint aggregators when both exist.
- Use preprint servers primarily for discovery and open-access full text.
- For every preprint candidate, attempt to resolve the peer-reviewed published version using DOI/journal-ref fields, title+author search, and citation-index sources as needed.
- If an accepted full conference/journal version exists, treat the preprint as a duplicate publication: keep the accepted/published version as the canonical record/citation and `publication_url`; optionally retain the preprint URL only as a full-text access link in notes.
- For ML conference records, prefer an accepted venue record over an arXiv preprint only when the venue status is clear; do not treat rejected, withdrawn, or merely submitted records as canonical.
- Track deduplication and version-resolution decisions explicitly, including the chosen canonical `publication_url` and any supplemental preprint URL.
- Treat Zotero as a curated discovery aid, not as proof that a paper meets the final inclusion criteria. Every included paper still needs screening and evidence extraction.

### 3) Screen records and account for flow

- Use `references/screening-template.md`.
- Record title/abstract and full-text decisions with reasons.
- Deduplicate across versions and record preprint supersession as `duplicate-publication`.
- Preserve the canonical `publication_url` in the decision ledger when promoting a preprint/submission to the published or accepted venue record.
- Maintain PRISMA count keys exactly as defined in the template.

### 4) Extract structured evidence

- Use `references/evidence-table-template.md`.
- Capture design, population/context, outcomes, key results, and risk of bias per study.
- Capture DOI, venue, publication status, and `publication_url` for each included study.
- Cite and link the published/accepted version when available; use preprint links only as supplemental access copies or as canonical links when no published/accepted version exists.

### 5) Synthesize findings and grade confidence

- Use `references/report-template.md`.
- Separate high-confidence findings, mixed evidence, and unresolved questions.
- State confidence rationale from consistency, quality, directness, and risk of bias.
- In paper-context mode, separate closest prior work, context that weakens novelty or impact claims, context that strengthens significance, and benchmark/evaluation norms the paper may be missing.
- If `technical_exposition=detailed_math`, make the `Synthesis` section math-forward: define the core objects precisely, write the primary learning objectives/constraints, and summarize theoretical results using correct formal statements without over-quoting.

### 6) Run adversarial stress-test

- Use `references/adversarial-literature-checklist.md`.
- Red-team causal claims, endpoint definitions, subgroup claims, publication bias, and citation integrity.
- Flag unsupported, misleading, or overgeneralized conclusions with concrete fixes.

### 7) Apply domain adapter

- Use `references/domain-adapters.md`.
- Start from the generic bias rubric and apply the domain-specific adapter before final conclusions.

### 8) Validate and finalize

- In full systematic mode, generate PRISMA flow markdown with `scripts/prisma_flow_md.py`.
- In full systematic mode, validate structural integrity, publication URL fields, and count consistency with `scripts/validate_review_pack.py`.
- In paper-context mode, validate the exchange bundle:

```bash
python3 scripts/paper_context_artifacts.py validate --review-dir <review_dir>
```

- If no paper-review workspace exists, validate with `--out-dir <context_dir>` instead of `--review-dir`.
- Return the full review pack or bounded paper-context map with explicit assumptions and known limitations.

## Scripts

- `scripts/init_review_pack.py`: create deterministic Markdown scaffolds for protocol/search/screening/evidence/report.
- `scripts/paper_context_artifacts.py`: create and validate the four-file paper-context evidence-map exchange bundle.
- `scripts/prisma_flow_md.py`: parse standardized screening counts and emit PRISMA flow accounting Markdown.
- `scripts/validate_review_pack.py`: validate required sections, mandatory fields, publication URL fields, and PRISMA count consistency.

## References

- `references/protocol-template.md`
- `references/search-strategy-template.md`
- `references/screening-template.md`
- `references/evidence-table-template.md`
- `references/prisma-core-checklist.md`
- `references/adversarial-literature-checklist.md`
- `references/domain-adapters.md`
- `references/report-template.md`
- `references/paper-context-template.md`
- `../research-zotero/references/zotero-artifact-contract.md`
