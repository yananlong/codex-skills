---
name: research-systematic-literature-review
description: Full systematic literature review (PRISMA 2020 core) with discovery, screening, evidence extraction, synthesis, confidence grading, and adversarial stress-testing across papers. Prefer peer-reviewed published versions over preprints and use this skill either directly or as the coordinated literature stage inside a larger research workflow. Use when asked to run or audit a literature review, evidence synthesis, state-of-the-art survey with explicit methods, citation integrity checks, or confidence-rated conclusions from research publications.
---

# Research Systematic Literature Review

## Quick start

1. Require `domain` before substantive review work. Stop and ask if missing.
2. Collect optional inputs **including whether the user wants deep technical/mathematical exposition**. If `technical_exposition` is not provided, explicitly ask the user to choose between `standard` vs `detailed_math`. Apply defaults for missing non-domain inputs and log assumptions.
3. Check tool access. If web browsing/search is unavailable and no corpus or Zotero access is provided, stop and ask for browsing access, `research-zotero`, or a user corpus.
4. Initialize the review artifact pack with `scripts/init_review_pack.py`.
5. If Zotero is relevant, invoke `research-zotero` first or consume existing `./zotero/` artifacts.
6. Run discovery, deduplication (including preprint→published version resolution), screening, extraction, synthesis, and adversarial checks.
7. Generate PRISMA flow accounting with `scripts/prisma_flow_md.py` and insert it into `<topic>.review.md`.
7. Validate the full pack with `scripts/validate_review_pack.py` before returning output.

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
- `technical_exposition`: default to `standard`. If set to `detailed_math`, the `<topic>.review.md` **must** include formal definitions/notation, key equations/objectives, and (when relevant) theorem statements or proof sketches in the `Synthesis` section.
- `zotero_library_type`: optional. `user` or `group` when Zotero should be used as a source.
- `zotero_library_id`: optional. Zotero user ID or group ID.
- `zotero_collection_key`: optional. Restrict Zotero sync to a collection.
- `zotero_query`: optional. Zotero free-text query for item discovery.
- `zotero_tags`: optional. Restrict Zotero items by tag.
- `zotero_access_mode`: optional. `api-key`, `oauth-key`, or `mcp`.

## Hard-stop and failover rules

- Stop immediately if `domain` is missing.
- Stop immediately if web browsing/search is unavailable and there is no user-provided corpus and no `research-zotero` artifact or Zotero API/MCP path.
- Continue with soft defaults only for non-domain fields and explicitly log all defaults under "Assumptions applied".

## Default output contract

Primary file:
`<topic>.review.md`

Supporting files:
`<topic>.protocol.md`
`<topic>.search-log.md`
`<topic>.screening-log.md`
`<topic>.evidence-table.md`

Optional support files when Zotero is used:
`<topic>.zotero-items.json`
`<topic>.zotero-sync.md`

Required sections in `<topic>.review.md`:
`Protocol`
`Search Strategy`
`Screening Decisions`
`Evidence Table`
`Synthesis`
`Adversarial Stress Test`
`Limitations`
`Confidence Assessment`
`PRISMA flow accounting`

## Artifact naming rules

- Normalize `<topic>` to lowercase hyphen-case for file names.
- Keep all outputs in one review directory.
- Refuse to overwrite existing artifacts unless explicit overwrite is requested.

## Workflow (PRISMA 2020 core + adversarial pass)

### 1) Define protocol

- Use `references/protocol-template.md`.
- Record topic, domain, question, inclusion/exclusion criteria, date range, outcomes, and quality threshold.
- Log every default assumption.

### 2) Execute discovery and search logging

- Use `references/search-strategy-template.md`.
- Search multiple relevant sources and log exact query strings, filters, and retrieval dates.
- If Zotero access is available, use `research-zotero` or consume its artifacts and decide whether Zotero is:
  - a curated seed library
  - a citation cross-check source
  - a discovery source for saved collections/tags
- If `./zotero/zotero-items.json` already exists, prefer consuming it over re-syncing.
- If Zotero MCP is available in the runtime, `research-zotero` should prefer it for interactive library inspection.
- If Zotero MCP is unavailable but API access is available, `research-zotero` should export items and log the sync before this skill consumes them.
- For major ML conferences hosted on OpenReview (e.g., ICLR/NeurIPS, and others when applicable), include **OpenReview as a first-class discovery source** (especially for 2025+ venue years when recency matters). Use the OpenReview API v2 (`api2.openreview.net`) for reproducible queries (e.g., `notes/search` + `notes?id=...`), and log venue group(s), query terms/fields (title/abstract), and whether you filtered to accepted papers.
- Prefer published/peer-reviewed indexing and publisher sources over preprint aggregators when both exist (e.g., venue/publisher pages, PubMed, ACL Anthology, ACM DL, IEEE Xplore, SpringerLink, etc.).
- Use preprint servers (arXiv/bioRxiv/medRxiv/SSRN) primarily for discovery and open-access full text.
- For every preprint candidate, attempt to resolve the peer-reviewed published version (check preprint DOI/journal-ref fields; search title+authors+venue; use Crossref/OpenAlex/Semantic Scholar as needed).
- If an accepted full conference/journal version exists (publisher page, proceedings, or an accepted OpenReview venue record), treat the preprint as a duplicate publication: keep the accepted/published version as the canonical record/citation; optionally retain the preprint URL only as a full-text access link in notes.
- **arXiv ↔ OpenReview canonicalization rule (ML conferences):** when both an arXiv preprint and an OpenReview forum record exist for the same paper, prefer the OpenReview record **only if** it corresponds to an accepted full venue paper (use `venue` / `venueid` cues; avoid treating `Rejected_Submission` / `Withdrawn_Submission` / “Submitted to …” as canonical). Keep arXiv as an access copy when helpful.
- Track deduplication decisions explicitly.
- Treat Zotero as a curated discovery aid, not as proof that a paper meets the final inclusion criteria. Every included paper still needs screening and evidence extraction.

### 3) Screen records and account for flow

- Use `references/screening-template.md`.
- Record title/abstract and full-text decisions with reasons.
- Deduplicate across versions (preprint vs conference/journal) and record as `duplicate-publication` with a note like "preprint superseded by published version".
- Maintain PRISMA count keys exactly as defined in the template.

### 4) Extract structured evidence

- Use `references/evidence-table-template.md`.
- Capture design, population/context, outcomes, key results, and risk of bias per study.
- Capture DOI, venue, and publication status (published vs preprint) for each included study. Cite the published version when available.

### 5) Synthesize findings and grade confidence

- Use `references/report-template.md`.
- Separate high-confidence findings, mixed evidence, and unresolved questions.
- State confidence rationale from consistency, quality, directness, and risk of bias.
- If `technical_exposition=detailed_math`, make the `Synthesis` section math-forward: define the core objects precisely, write the primary learning objectives/constraints, and summarize theoretical results using correct formal statements (without over-quoting).

### 6) Run adversarial stress-test

- Use `references/adversarial-literature-checklist.md`.
- Red-team causal claims, endpoint definitions, subgroup claims, publication bias, and citation integrity.
- Flag unsupported, misleading, or overgeneralized conclusions with concrete fixes.

### 7) Apply domain adapter

- Use `references/domain-adapters.md`.
- Start from the generic bias rubric and apply the domain-specific adapter before final conclusions.

### 8) Validate and finalize

- Generate PRISMA flow markdown with `scripts/prisma_flow_md.py`.
- Validate structural integrity and count consistency with `scripts/validate_review_pack.py`.
- Return the full review pack with explicit assumptions and known limitations.

## Scripts

- `scripts/init_review_pack.py`: create deterministic Markdown scaffolds for protocol/search/screening/evidence/report.
- `scripts/prisma_flow_md.py`: parse standardized screening counts and emit PRISMA flow accounting Markdown.
- `scripts/validate_review_pack.py`: validate required sections, mandatory fields, and PRISMA count consistency.

## References

- `references/protocol-template.md`
- `references/search-strategy-template.md`
- `references/screening-template.md`
- `references/evidence-table-template.md`
- `references/prisma-core-checklist.md`
- `references/adversarial-literature-checklist.md`
- `references/domain-adapters.md`
- `references/report-template.md`
- `../research-zotero/references/zotero-artifact-contract.md`
