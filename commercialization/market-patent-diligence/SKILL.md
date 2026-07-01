---
name: market-patent-diligence
description: source-grounded market, competitor, procurement, funding, regulatory, and patent-landscape diligence for academic research commercialization. use when codex needs to search public market or patent information for a research asset, technology, prototype, dataset, method, device, or commercialization thesis; map incumbents, substitutes, buyers, assignees, patent families, citations, ownership signals, public funding, procurement demand, regulatory/reimbursement constraints, and evidence gaps; prepare diligence artifacts for commercialize-academic-research or related research skills.
---

# Market Patent Diligence

## Quick start

1. Require either a bounded `research_asset` or a specific `technology_thesis` plus target market or diligence question. If both are missing, ask for the paper, abstract, invention summary, product idea, patent/application number, assignee, or market hypothesis.
2. Classify the request before searching: `quick scan`, `patent landscape`, `market and competitor scan`, `regulatory/procurement/funding scan`, `full diligence pack`, or `red-team evidence audit`.
3. Create a search plan from the claim: technical nouns, synonyms, adjacent terms, use cases, customer workflow terms, incumbent categories, IPC/CPC/NAICS/SIC/MeSH terms where useful, jurisdictions, date range, and source classes.
4. Use current public sources for changing facts. Prefer primary or official sources over summaries: patent-office databases, assignment/register data, company pages, public filings, procurement notices, regulator/reimbursement pages, grants/funding databases, clinical or standards registries, and customer-visible pricing.
5. Log every nontrivial source and query. Do not present market size, competitor status, patent ownership, legal status, regulatory status, procurement demand, reimbursement, funding, or pricing claims as facts without a source and retrieval date.
6. Separate `source-backed fact`, `user-provided fact`, `inference`, `hypothesis`, and `speculation` in the output.
7. For persistent work, initialize a diligence pack with `python3 scripts/init_diligence_pack.py <case-name> --path <output-dir>` and validate it with `python3 scripts/validate_diligence_pack.py <case-dir>` before returning artifacts.
8. End with a handoff: what the evidence says, what it does not say, the weakest commercialization assumptions, and which sibling skill should consume the results next.

## Modes

### Quick scan

Use for a bounded 30-90 minute-style pass. Produce a concise source-backed read on market/competitor/patent signals, strongest evidence, red flags, and next searches. Do not imply exhaustive coverage.

### Patent landscape

Use when the user asks about patents, assignees, prior art, claims, ownership, patent families, citation networks, or freedom-to-operate signals. This mode produces patent signals only; it does not give legal advice, patentability opinions, infringement opinions, validity opinions, or freedom-to-operate conclusions.

### Market and competitor scan

Use when the user asks who sells, buys, funds, reimburses, procures, regulates, or substitutes for the research asset. Prioritize concrete buyer/workflow evidence over generic TAM.

### Regulatory, procurement, and funding scan

Use when adoption depends on public purchasing, reimbursement, regulatory clearance, standards, non-dilutive funding, or translational-program fit. Log the exact program, agency, rule, procurement notice, award, grant, or guidance page used.

### Full diligence pack

Use when the user asks for persistent artifacts or a case pack. Create all required files in the output contract and validate them.

### Red-team evidence audit

Use when reviewing someone else's market or patent claims. Lead with unsupported claims, weak sources, missing jurisdictions, stale evidence, assignee ambiguity, family/legal-status confusion, and customer/buyer inference leaps.

## Relationship to sibling skills

- `commercialize-academic-research` is the downstream decision orchestrator. This skill supplies source-grounded market, competitor, procurement, funding, regulatory, and patent evidence; `commercialize-academic-research` converts that evidence into path choice, wedge, validation sprint, and `kill / pivot / continue` decisions.
- `research-systematic-literature-review` owns systematic academic evidence synthesis. Invoke it or consume its artifacts when commercialization depends on a body of published efficacy, safety, SOTA, benchmark, clinical, or scientific evidence rather than market or patent facts.
- `research-novelty-review` owns adversarial novelty and prior-art positioning across academic work. This skill may contribute patent and market prior-art signals, but `research-novelty-review` should decide whether the research contribution is novel enough for paper or scientific positioning claims.
- `research-results-auditor` owns validity checks for experimental, statistical, benchmark, clinical, or ablation results. Use it before treating a result as a competitive advantage or buyer-relevant proof point.
- `research-experiment-plan` owns decisive technical validation design. Use it when diligence reveals that the blocking risk is a technical proof, reproducibility, reliability, or field-performance gap.
- `research-zotero` owns curated paper corpus sync and citation export. Use it for literature-heavy technical corpora, but do not treat a Zotero library as market evidence.
- `research-pipeline-planner` owns multi-stage research coordination. Recommend it when diligence implies more than one technical follow-up stage, such as literature review plus novelty review plus experiment planning.
- `research-paper-review` and `research-review-loop` may consume this skill's market/patent findings when a paper makes translational-impact, related-work, or application claims that require external market/IP grounding.

## Input contract

### Required input

One of:

- `research_asset`: paper, abstract, invention disclosure summary, prototype description, technical memo, dataset, method, device spec, patent/application number, or lab result.
- `technology_thesis`: a concise technology or product hypothesis plus a target market, buyer, application, assignee, or diligence question.

### Optional inputs with defaults

- `geography`: default `US, PCT/WIPO, EP/EPO, and material markets implied by the asset`.
- `time_range`: default `last 10 years for market signals; patent search begins earlier if foundational prior art is likely`.
- `diligence_depth`: default `quick scan unless user asks for a full diligence pack`.
- `source_scope`: default `official/primary sources first, credible secondary sources only when primary evidence is unavailable or used for leads`.
- `patent_scope`: default `published applications, granted patents, family members, assignees, citations, assignment/legal-status signals where accessible`.
- `market_scope`: default `incumbents, substitutes, buyers, procurement/funding signals, regulatory/reimbursement constraints, customer-visible pricing or budget proxies`.
- `output_format`: default `chat summary unless persistent artifacts requested`.

## Hard-stop and failover rules

- Stop if the user asks for legal advice, infringement analysis, patentability opinion, validity opinion, or formal freedom-to-operate conclusion. Offer source-grounded patent landscape signals and recommend attorney review for legal conclusions.
- Stop if both the technical subject and the diligence question are too vague to search. Ask for one concrete claim, application, assignee, or product hypothesis.
- Do not use generic market-size claims unless they affect a decision and are sourced. Prefer buyer counts, procurement notices, installed base, pricing proxies, public revenue segments, awards, or comparable purchases.
- Do not infer that a patent is enforceable, owned by a party, expired, or blocking without checking source context and labeling uncertainty.
- Do not treat patents as proof of customer demand or publications as proof of market pull.
- Do not claim exhaustive patent coverage unless the search used multiple patent sources, synonyms/classes, jurisdictions, family deduplication, and a documented stopping rule.

## Default output contract

When the user wants persistent artifacts, create one diligence directory containing:

- `<case>.scope.md`
- `<case>.source-log.md`
- `<case>.patent-landscape.md`
- `<case>.market-map.md`
- `<case>.competitor-substitute-map.md`
- `<case>.regulatory-procurement-funding.md`
- `<case>.evidence-ledger.md`
- `<case>.handoff-to-commercialization.json`

## Required answer shape

Use this shape unless the user requests otherwise:

1. `Diligence read`: state the strongest market/IP signal and confidence.
2. `Scope and search posture`: state asset, geography, date range, source classes, and whether coverage is quick, bounded, or full-pack.
3. `Source-backed findings`: separate patents, assignees, competitors/substitutes, buyers/procurement/funding, regulatory/reimbursement/standards, and customer-visible economics.
4. `Evidence ledger`: include `Claim | Source type | Source/date | Confidence | Commercial implication | Missing proof`.
5. `Patent landscape signals`: summarize families, assignees, claims/themes, citations, legal-status/assignment signals if checked, and limits.
6. `Market and competitor map`: summarize incumbents, substitutes, buying context, pricing/budget proxies, adoption blockers, and gaps.
7. `Red flags and weak links`: list assumptions most likely to invalidate the commercialization thesis.
8. `Handoff`: recommend whether to send results to `commercialize-academic-research`, `research-pipeline-planner`, `research-systematic-literature-review`, `research-novelty-review`, `research-results-auditor`, or `research-experiment-plan`.

## Workflow

### 1) Bound the claim and commercial question

- Translate the asset into one or more searchable technical claims and application hypotheses.
- Identify what decision the diligence should inform: market pull, competitor density, licensing targets, patent crowding, procurement demand, funding route, regulatory path, or commercialization path selection.
- Write the search spine as `technology terms -> application terms -> customer/workflow terms -> incumbent/substitute terms -> patent classes/assignees -> regulatory/procurement/funding terms`.

### 2) Build a source plan

- Use `references/source-taxonomy.md` to choose source classes and reliability labels.
- Use patent-office and official registry sources for patent records, assignments, family/status signals, and jurisdictional coverage.
- Use company pages, product docs, pricing pages, SEC filings, procurement notices, agency awards, regulator pages, reimbursement/coverage pages, standards bodies, and credible industry reports for market evidence.
- For each source class, define what it can and cannot prove.

### 3) Search patent and prior-art signals

- Use `references/patent-search-guide.md` for query expansion, class search, family grouping, assignee normalization, citation review, and legal-status caveats.
- Search across synonyms and application terms, not only the research paper's vocabulary.
- Track publication numbers, patent numbers, titles, assignees/applicants, inventors when relevant, priority dates, publication/grant dates, jurisdictions, family members, CPC/IPC classes, claim themes, citation relationships, assignment/legal-status source, and search limitations.
- Deduplicate families and avoid overcounting continuation/divisional family members as independent inventions.

### 4) Search market, competitor, buyer, and adoption evidence

- Use `references/market-diligence-guide.md` to map incumbent products, substitutes, buyer roles, budget proxies, public filings, procurement notices, grant/award signals, reimbursement/regulatory requirements, and standards.
- Distinguish product competitors, workflow substitutes, in-house workarounds, research prototypes, and platform incumbents.
- Prioritize evidence of purchase behavior or budget over evidence of interest.

### 5) Build evidence ledgers and maps

- Record every important claim with source type, retrieval date, reliability, supported claim, confidence, and missing proof.
- Map competitors by buyer, workflow, product category, value proposition, evidence source, and commercial relevance.
- Map patents by family, assignee, claim theme, jurisdiction, timeline, and relevance to the commercial wedge.

### 6) Stress-test conclusions

- Ask whether each conclusion would survive a missing synonym, a different jurisdiction, stale source, assignee rename, non-practicing patent owner, unlaunched product, private-company opacity, or regulatory/reimbursement change.
- Flag when evidence only proves research interest, patenting activity, press interest, or funding availability rather than willingness to pay.

### 7) Prepare handoff

- For commercialization decisions, write `handoff-to-commercialization.json` with ranked evidence, confidence, weak links, recommended path questions, and next skill.
- If the main uncertainty is academic evidence quality or technical validity, hand off to the appropriate research skill rather than forcing a market conclusion.

## Quality bar

- Prefer primary, official, and customer-visible evidence.
- Be explicit about coverage limits, especially private-market opacity and patent-search incompleteness.
- Treat patent counts as weak evidence unless connected to claim scope, assignee behavior, citations, family breadth, and commercial relevance.
- Treat market reports as weak unless their data source and decision relevance are clear.
- Never equate patent existence with freedom to operate, patentability, demand, or defensibility.
- Make the next search or validation step cheap and decision-relevant.

## Resources

- `scripts/init_diligence_pack.py`: scaffold a persistent market and patent diligence pack.
- `scripts/validate_diligence_pack.py`: validate required diligence files, sections, source logs, and handoff JSON fields.
- `references/source-taxonomy.md`: source hierarchy, source classes, and evidence-strength rules.
- `references/patent-search-guide.md`: patent search protocol, field schema, family/citation/assignee rules, and legal caveats.
- `references/market-diligence-guide.md`: competitor, buyer, procurement, regulatory, reimbursement, standards, and funding search patterns.
- `references/output-templates.md`: compact templates for chat answers and persistent artifacts.
