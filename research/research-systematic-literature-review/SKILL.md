---
name: research-systematic-literature-review
description: Run or audit literature discovery and evidence synthesis with explicit review profiles, high-recall discovery, seed and challenge-set testing, citation searching, corpus freezing, PRISMA 2020 core accounting, evidence extraction, confidence grading, and adversarial stress-testing across publications. Prefer peer-reviewed published versions over preprints. Use for systematic reviews, bounded evidence maps, state-of-the-art surveys with explicit methods, citation-integrity checks, novelty-critical prior-art searches, confidence-rated conclusions, or when a research commitment depends on reliable literature coverage.
---

# Research Systematic Literature Review

## Quick start

1. Require a clear domain and research question before substantive review work. In paper-context mode, infer the domain from the target paper summary only when unambiguous; otherwise stop.
2. Declare one review profile: `comprehensive-systematic`, `bounded-systematic`, `critical-evidence-map`, `rapid-scan`, or `novelty-prior-art`.
3. Collect optional inputs, including whether the user wants `standard` or `detailed_math` exposition. Apply non-domain defaults only when safe and log every assumption.
4. Check search, corpus, and Zotero access. Stop or narrow the review profile when the requested assurance is impossible.
5. Initialize the full review pack with `scripts/init_review_pack.py` for systematic profiles; use paper-context mode only for bounded contextualization.
6. Complete discovery assurance before expensive extraction: coverage map, visible seed set, optional withheld challenge set, multi-channel search decisions, backward and forward citation searching, search repair, recall audit, stopping rationale, and candidate-corpus freeze.
7. After freeze, deduplicate, resolve preprints to canonical publications, screen, extract evidence, synthesize, grade confidence, and run adversarial checks.
8. Record a canonical `publication_url` for every included work, preferring the published or accepted venue record over a preprint when one exists.
9. Generate PRISMA flow accounting and validate the declared process profile with `scripts/validate_review_pack.py`.
10. State exactly what the review assurance supports. Structural validity and PRISMA consistency do not establish that all important publications were found.
11. If the user asks for project-level sequencing or a decision across multiple stages, invoke `research-pipeline-planner` first.

## Review profiles

### Comprehensive systematic

Use only when broad, high-recall coverage is required and source access supports it. Require visible seeds, a withheld challenge set when feasible, performed backward and forward citation searching, explicit venue/author/benchmark/grey-literature decisions, materially separate search-strategy review when feasible, corpus freeze, and a strong stopping rationale.

### Bounded systematic

Use when the review is systematic within explicit source, venue, date, language, corpus, or publication-type boundaries. Apply the same discovery-assurance machinery inside those boundaries and state what remains outside them.

### Critical evidence map

Use for structured, adversarial contextualization without a completeness claim. Log sources, queries, inclusion decisions, important omissions, and confidence limits.

### Rapid scan

Use when speed is prioritized and omissions are expected. Return orientation, provisional evidence clusters, and next-search recommendations rather than a definitive synthesis.

### Novelty-prior-art

Use for closest-work and claim-killing discovery around a concrete contribution. Prefer `research-novelty-review` for the final positioning decision, while this skill owns broader retrieval assurance when needed.

## Paper-context evidence-map mode

Use when `research-paper-review` needs external context for one paper's novelty, impact, related-work adequacy, benchmark coverage, or SOTA claims.

- This is a bounded evidence map, not a full systematic review, unless the full systematic workflow is completed.
- Inputs should come from `research-paper-review/summary.md` when available: title/domain, one-sentence contribution, novelty dimensions, cited closest prior work, benchmark context, and targeted context questions.
- When invoked from a paper-review workspace, write outputs under `<review_dir>/context/`; otherwise use one explicit output directory.
- Required outputs are `literature-context.md`, `literature-context-search-log.md`, `literature-context-evidence-table.md`, and `literature-context-decision.json`.
- Use `scripts/paper_context_artifacts.py init` and `validate` when useful.
- Preserve original paths and provenance when later stages consume the context bundle.

## Relationship to sibling skills

- `research-pipeline-planner` owns whether literature assurance is sufficient for commitment or route advancement.
- `research-paper-review` owns technical critique of one paper; this skill supplies bounded context or a full review.
- `research-idea-discovery` consumes landscape evidence but owns idea generation and ranking.
- `research-novelty-review` owns adversarial novelty and positioning decisions and should consume this skill's recall-audited corpus when available.
- `research-zotero` owns library sync and citation export; Zotero records remain candidates until screened.
- `research-review-loop` tracks whether literature omissions and overclaims are actually repaired.
- `research-paper-plan` uses the narrowest claims supported by the review and its assurance verdict.

## Input contract

Required:

- `domain`
- `research_question` or a topic specific enough to derive one
- a declared or explicitly defaulted `review_profile`

Prefer:

- intended use of the review and decision it will support
- target venue or audience
- inclusion and exclusion criteria
- source, venue, date, language, publication-type, and grey-literature boundaries
- known landmark publications
- a separately held challenge set when available
- databases, publisher indexes, conference venues, Zotero collections, or user corpora
- population/context, outcomes or conceptual questions, study/work types, and quality threshold
- `technical_exposition=standard|detailed_math`
- whether the review will authorize paper commitment, a strong novelty claim, or expensive execution

## Hard stops

- Stop when domain or question is missing.
- Stop comprehensive claims when browsing, database, corpus, or citation access is inadequate.
- Stop expensive extraction when a systematic profile lacks a visible seed set, citation-search decisions, recall-audit plan, and corpus-freeze plan.
- Do not treat PRISMA counts, canonical URLs, file presence, or validator success as evidence of adequate recall.
- Do not manually insert a major missed publication without documenting why the strategy missed it and how the search was repaired.
- Do not default theoretical, mathematical, philosophical, benchmark, software, or fast-moving AI reviews to a biomedical primary-study ontology.
- Do not call a bounded or rapid review comprehensive because its artifacts are polished.
- Stop strong priority or first-of-kind language when recall assurance is inadequate.

## Output contract

Full review packs produce:

- `<topic>.protocol.md`
- `<topic>.search-log.md`
- `<topic>.recall-audit.md`
- `<topic>.corpus-manifest.json`
- `<topic>.screening-log.md`
- `<topic>.evidence-table.md`
- `<topic>.review.md`
- `<topic>.prisma-flow.md`

The report must include `Protocol`, `Discovery Assurance`, `Search Strategy`, `Screening Decisions`, `Evidence Table`, `Synthesis`, `Adversarial Stress Test`, `Limitations`, `Confidence Assessment`, and `PRISMA flow accounting`.

Every included record must have a canonical publication URL and explicit publication status. A preprint URL is canonical only when no published or accepted version exists.

## Workflow

### 1) Define protocol and domain adapter

- Record the review profile, research question, intended decision, inclusion/exclusion criteria, foundational horizon, current-evidence horizon, update horizon, language, publication types, outcomes or conceptual questions, and quality threshold.
- Select an adapter: empirical intervention, methodological, theoretical/mathematical, benchmark/dataset, software/system, interdisciplinary conceptual, novelty/prior-art, or emerging-field.
- Record defaults and deviations.
- If `technical_exposition=detailed_math`, require formal definitions, notation, key equations/objectives, and theorem statements or proof sketches where relevant.

### 2) Build coverage map and seeds

- Map expected intellectual lineages, method families, formal objects, evidence types, venues, time strata, and supporting, competing, critical, negative, or null positions.
- Define visible quasi-gold seeds from recognized foundations, recent close anchors, prior reviews, expert knowledge, and user-provided works.
- When feasible, define a withheld challenge set controlled by a separate reviewer or hidden until evaluation.
- Seeds test retrieval performance; they do not define the complete relevant corpus.

### 3) Execute multi-channel discovery

Record decisions and yields for:

- database, publisher, and broad scholarly search
- backward citation searching
- forward citation searching
- related-paper graph exploration
- venue census
- author or laboratory expansion
- benchmark and dataset tracing
- prior-review harvesting
- grey literature and repository search
- Zotero or user-corpus cross-check

For each query or expansion, log the coverage target, linked coverage-question IDs, exact query or seed, filters, retrieval date, records returned, unique candidates, included yield, new vocabulary, and next repair action.

For major ML conferences hosted on OpenReview, use accepted venue records when venue status is clear; do not treat rejected, withdrawn, or merely submitted records as canonical publications.

### 4) Repair search and audit recall

- Test whether ordinary discovery recovers every visible seed.
- For each miss, identify terminology, indexing, venue, author, date, or source failure and repair the strategy.
- Evaluate withheld challenge recovery when available.
- Record unique and marginal yield by channel and expansion round.
- Reconsider the original strategy when citation searching or late challenge work yields material additions.
- Obtain a materially separate PRESS-style search-strategy review for commitment, high-stakes novelty, or expensive execution when feasible; otherwise disclose self-review.

### 5) Close coverage questions and freeze the candidate corpus

- Keep coverage questions inside `<topic>.corpus-manifest.json`; do not create a competing frontier authority.
- Give each question a stable ID, decision role, priority, status, reciprocal search-run IDs, record IDs, residual gap, and closure evidence.
- For blocked questions, record mitigation and the exact consequence for supported scope. For out-of-scope questions, cite the protocol boundary.
- Record every material post-freeze question through a reciprocal corpus amendment.
- Create `<topic>.corpus-manifest.json` with versioned records, seed and challenge IDs, coverage questions, search-strategy review, amendments, and assurance verdict.
- Complete `<topic>.recall-audit.md` using `references/recall-assurance-contract.md`.
- State a stopping rationale based on seed/challenge recovery, coverage, marginal yield, constraints, and residual omission risk.
- Freeze before detailed extraction. Record every post-freeze addition and whether it changes conclusions.

### 6) Screen and resolve publication versions

- Record title/abstract and full-text decisions with reasons.
- Deduplicate across databases and publication versions.
- Resolve preprints to accepted or published versions using DOI, journal references, venue pages, title-author search, and citation indexes.
- Preserve the canonical publication URL and any supplemental open-access link.
- Maintain exact PRISMA accounting.

### 7) Extract structured evidence

- Use an adapter-appropriate table.
- Capture bibliographic identity, publication status, design or argument type, population/context or formal setting, methods, outcomes or propositions, key results, limitations, and quality or risk of bias.
- Do not force sample-size, intervention, comparator, or effect-size fields onto theoretical or conceptual work when they are inapplicable.
- Keep claims traceable to evidence rows and retain negative or contradictory evidence.

### 8) Synthesize and grade confidence

- Separate high-confidence findings, mixed evidence, negative or contradictory evidence, unresolved questions, and coverage-dependent conclusions.
- Grade confidence from consistency, methodological or formal quality, directness, venue/publication status, and residual omission risk.
- In paper-context mode, separate closest prior work, context that weakens novelty or impact claims, context that strengthens significance, and benchmark/evaluation norms the paper may be missing.

### 9) Run adversarial checks

- Search specifically for criticism, negative results, predecessor terminology, alternative formulations, and work that would kill the anticipated novelty or conclusion.
- Red-team causal claims, endpoint definitions, subgroup claims, benchmark comparability, publication bias, correlated evidence, and citation integrity.
- Distinguish missing evidence from evidence of absence.
- Report late major omissions and repair the retrieval process, not only the corpus.

### 10) Validate and report assurance

- Generate PRISMA flow markdown with `scripts/prisma_flow_md.py`.
- Validate the protocol, search log, recall audit, corpus manifest, screening log, evidence table, and report with `scripts/validate_review_pack.py`.
- Use bounded verdicts: `insufficient`, `adequate-for-bounded-claims`, or `adequate-for-comprehensive-claim`.
- State source and access limitations prominently.
- A passing validator establishes recorded structural and process consistency, not actual completeness, independent screening, or scientific validity.

## References

- `references/recall-assurance-contract.md`
- `references/protocol-template.md`
- `references/search-strategy-template.md`
- `references/screening-template.md`
- `references/evidence-table-template.md`
- `references/adversarial-literature-checklist.md`
- `references/domain-adapters.md`
- `references/report-template.md`
- `references/paper-context-template.md`
- `../research-zotero/references/zotero-artifact-contract.md`

## Scripts

- `scripts/init_review_pack.py`: initialize a profile-aware review pack, recall audit, and corpus manifest while preserving the previous protocol-scope CLI inputs.
- `scripts/paper_context_artifacts.py`: initialize and validate the four-file paper-context evidence-map exchange bundle.
- `scripts/prisma_flow_md.py`: generate PRISMA flow accounting.
- `scripts/review_pack_coverage.py`: validate coverage-question states and reciprocal question/search/record/amendment links; shared with novelty assurance.
- `scripts/validate_review_pack.py`: validate headings, table fields, PRISMA consistency, canonical URLs, seed recovery, channel completion, coverage-question closure, corpus freeze, and verdict consistency without claiming actual completeness.
