---
name: research-systematic-literature-review
description: Run or audit literature discovery and evidence synthesis with explicit review profiles, high-recall discovery, seed and challenge-set testing, citation searching, corpus freezing, PRISMA accounting, evidence extraction, confidence grading, and adversarial stress-testing. Use for systematic reviews, bounded evidence maps, state-of-the-art surveys, novelty-critical prior-art searches, or when a research commitment depends on reliable literature coverage.
---

# Research Systematic Literature Review

## Quick start

1. Require a clear domain and research question before substantive work.
2. Declare one review profile: `comprehensive-systematic`, `bounded-systematic`, `critical-evidence-map`, `rapid-scan`, or `novelty-prior-art`.
3. Check search, corpus, and Zotero access; stop or narrow the profile when the requested assurance is impossible.
4. Initialize the full review pack with `scripts/init_review_pack.py` for systematic profiles; use paper-context mode only for bounded contextualization.
5. Complete discovery assurance before expensive extraction: seed set, optional withheld challenge set, multi-channel search decisions, citation search, search repair, recall audit, stopping rationale, and corpus freeze.
6. Screen, deduplicate, resolve preprints to canonical publications, extract evidence, synthesize, and grade confidence only after the candidate corpus is frozen.
7. Generate PRISMA flow accounting and validate the declared assurance profile with `scripts/validate_review_pack.py`.
8. State exactly what the review assurance supports. Structural validity and PRISMA consistency do not establish that all important publications were found.

## Review profiles

### Comprehensive systematic

Use only when broad, high-recall coverage is required and source access supports it. Require visible seeds, a withheld challenge set when feasible, backward and forward citation searching, explicit venue/author/benchmark/grey-literature decisions, search-strategy review, corpus freeze, and a strong stopping rationale.

### Bounded systematic

Use when the review is systematic within explicit source, venue, date, language, corpus, or publication-type boundaries. Apply the same discovery-assurance machinery inside those boundaries and state what remains outside them.

### Critical evidence map

Use for structured, adversarial contextualization without a completeness claim. Log sources, queries, important omissions, and confidence limits, but do not imply systematic recall.

### Rapid scan

Use when speed is prioritized and omissions are expected. Return orientation and next-search recommendations rather than a definitive synthesis.

### Novelty-oriented prior-art

Use for closest-work and claim-killing discovery around a concrete contribution. Prefer `research-novelty-review` for the final positioning decision, while this skill owns broader retrieval assurance when needed.

## Paper-context mode

Use when `research-paper-review` needs bounded context for novelty, impact, related work, benchmark coverage, or SOTA claims. This mode remains a bounded evidence map unless the full systematic workflow is completed. Required outputs are `literature-context.md`, `literature-context-search-log.md`, `literature-context-evidence-table.md`, and `literature-context-decision.json`.

## Input contract

Required:

- `domain`
- `research_question` or a topic specific enough to derive one
- `review_profile`

Prefer:

- intended use of the review
- target venue or audience
- scope boundaries
- known landmark publications
- a separately held challenge set when available
- databases, publisher indexes, conference venues, Zotero collections, or user corpora
- date, language, publication-type, and grey-literature policies
- desired technical or mathematical exposition
- whether the review will authorize paper commitment, novelty claims, or expensive execution

## Hard stops

- Stop when domain or question is missing.
- Stop comprehensive claims when browsing, database, corpus, or citation access is inadequate.
- Stop expensive extraction when systematic profiles lack a seed set, citation-search decision, recall audit plan, and corpus-freeze plan.
- Do not treat PRISMA counts, canonical URLs, file presence, or validator success as evidence of adequate recall.
- Do not manually insert a major missed publication without documenting why the strategy missed it and how the search was repaired.
- Do not default theoretical, mathematical, philosophical, benchmark, or fast-moving AI reviews to a biomedical primary-study ontology.

## Output contract

Full systematic profiles produce:

- `<topic>.protocol.md`
- `<topic>.search-log.md`
- `<topic>.recall-audit.md`
- `<topic>.corpus-manifest.json`
- `<topic>.screening-log.md`
- `<topic>.evidence-table.md`
- `<topic>.review.md`
- `<topic>.prisma-flow.md`

The report must include `Protocol`, `Discovery Assurance`, `Search Strategy`, `Screening Decisions`, `Evidence Table`, `Synthesis`, `Adversarial Stress Test`, `Limitations`, `Confidence Assessment`, and `PRISMA flow accounting`.

Every included record must have a canonical `publication_url`, preferring the published or accepted venue record over a preprint when one exists.

## Workflow

### 1) Define the review protocol and adapter

- Declare the review profile, intended decision, boundaries, inclusion and exclusion criteria, foundational horizon, current-evidence horizon, update horizon, outcomes or conceptual questions, and quality criteria.
- Select a domain adapter: empirical intervention, methodological, theoretical/mathematical, benchmark/dataset, interdisciplinary conceptual, novelty/prior-art, or emerging-field.
- Record defaults and deviations.

### 2) Build a coverage map and seed set

- Map expected intellectual lineages, method families, formal objects, evidence types, venues, time strata, and supporting/competing/critical positions.
- Define visible quasi-gold seeds from user knowledge, recognized foundations, and recent close anchors.
- When feasible, define a withheld challenge set controlled by a separate reviewer or hidden until evaluation.
- Seeds test retrieval performance; they do not define the complete relevant corpus.

### 3) Execute multi-channel discovery

Record decisions and yields for:

- database, publisher, and broad scholarly search;
- backward citation searching;
- forward citation searching;
- related-paper graph exploration;
- venue census;
- author or laboratory expansion;
- benchmark and dataset tracing;
- prior-review harvesting;
- grey literature and repository search;
- Zotero or user-corpus cross-check.

For each query or expansion, log the coverage target, exact query or seed, filters, records returned, unique candidates, included yield, new vocabulary, and next repair action.

### 4) Repair search and audit recall

- Test whether ordinary discovery recovers every visible seed.
- For each miss, identify terminology, indexing, venue, author, or date failure and repair the strategy.
- Evaluate withheld challenge recovery when available.
- Record unique yield and marginal yield by expansion round.
- Reconsider the original search when citation searching or late challenge work yields material additions.
- Obtain a materially separate PRESS-style search-strategy review for high-stakes uses when feasible; otherwise disclose self-review.

### 5) Freeze the candidate corpus

- Create `<topic>.corpus-manifest.json` with a versioned list of candidate records, seeds, challenge records, search-strategy review, and assurance verdict.
- Create `<topic>.recall-audit.md` using `references/recall-assurance-contract.md`.
- State a stopping rationale based on recovery, coverage, marginal yield, constraints, and residual omission risk.
- Freeze before detailed extraction. Record every post-freeze addition and whether it changes conclusions.

### 6) Screen and resolve versions

- Deduplicate across databases and publication versions.
- Resolve preprints to accepted or published versions using DOI, venue, title-author, and citation-index searches.
- Record title/abstract and full-text decisions with reasons.
- Preserve the canonical publication URL and any supplemental open-access link.
- Maintain exact PRISMA accounting.

### 7) Extract structured evidence

Use an adapter-appropriate table. Capture bibliographic identity, design or argument type, population/context or formal setting, methods, outcomes or propositions, key results, limitations, quality or risk of bias, and relevance to the review question.

Do not force sample-size, intervention, or effect-size fields onto theoretical or conceptual work when they are inapplicable.

### 8) Synthesize and grade confidence

- Separate high-confidence findings, mixed evidence, negative or contradictory evidence, unresolved questions, and coverage-dependent conclusions.
- Grade confidence using consistency, quality, directness, publication or venue status, and residual omission risk.
- When technical exposition is requested, define objects precisely and present equations, objectives, theorem statements, or proof sketches without overstating source claims.

### 9) Run adversarial checks

- Search specifically for criticism, negative results, predecessor terminology, alternative formulations, and work that would kill the anticipated novelty or conclusion.
- Check citation integrity and whether each cited source supports the attached statement.
- Distinguish missing evidence from evidence of absence.
- Report late major omissions and repair the search process, not only the corpus.

### 10) Validate and report assurance

- Generate PRISMA flow markdown.
- Run `scripts/validate_review_pack.py` with the protocol, search log, recall audit, corpus manifest, screening log, evidence table, and report.
- Use bounded verdicts: `insufficient`, `adequate-for-bounded-claims`, or `adequate-for-comprehensive-claim`.
- State source and access limitations prominently.

## Relationship to sibling skills

- `research-pipeline-planner` owns whether literature assurance is sufficient for commitment or route advancement.
- `research-novelty-review` owns the adversarial positioning decision and should consume the recall-audited corpus.
- `research-zotero` supplies curated seeds and exports but does not establish inclusion or recall.
- `research-paper-review` consumes bounded context or a full review without duplicating discovery.
- `research-review-loop` tracks whether omissions and overclaims are actually repaired.
- `research-paper-plan` uses the narrowest claims supported by the evidence and assurance level.

## References

- `references/recall-assurance-contract.md`
- `references/protocol-template.md`
- `references/search-strategy-template.md`
- `references/screening-template.md`
- `references/evidence-table-template.md`
- `references/prisma-core-checklist.md`
- `references/adversarial-literature-checklist.md`
- `references/domain-adapters.md`
- `references/report-template.md`
- `references/paper-context-template.md`

## Scripts

- `scripts/init_review_pack.py`: initialize the systematic review, recall audit, and corpus manifest artifacts.
- `scripts/paper_context_artifacts.py`: initialize and validate bounded paper-context outputs.
- `scripts/prisma_flow_md.py`: generate PRISMA flow accounting.
- `scripts/validate_review_pack.py`: validate structural consistency and the declared discovery-assurance profile without claiming actual completeness.
