---
name: research-paper-plan
description: Turn supported claims and evidence into a research paper plan that works either as a standalone manuscript-structuring pass or as the paper stage inside a coordinated research workflow. Use when asked to outline a paper, map claims to evidence, bind audited results to manuscript claims, plan figures and citations, align experiments to manuscript language, or keep limitations and threats to validity explicit.
---

# Research Paper Plan

## Quick start

1. Start from claims and evidence, not section titles.
2. Decide whether this is standalone planning or the paper stage inside an orchestrated suite.
3. In tracked work, initialize `paper-plan.md`, `claims-evidence-matrix.md`, `claim-evidence-bindings.json`, `figure-plan.md`, and `citation-plan.md` with `scripts/init_paper_pack.py`.
4. Treat `claim-evidence-bindings.json` as the manuscript-support authority; Markdown files are views.
5. For empirical claims, consume validated `results-audit.json` records rather than inferring support from plots, gate labels, or filenames.
6. Block, qualify, contradict, or omit claims that outrun the available audit assurance.
7. Validate with `scripts/validate_paper_pack.py`; use the linked profile in orchestrated work.

## Modes

### Standalone mode

- Work from the prompt plus local claims, results, notes, proofs, citations, or drafts.
- Do not require a suite root.
- Keep structure compact when a direct outline is sufficient.
- Invoke `research-results-auditor` when empirical evidence quality is unclear and `research-idea-discovery` when the project has not selected a paper-bearing idea.

### Orchestrated mode

- Use the canonical directory `./paper-plan/`.
- Read `research-commitment.json`, `experiment-plan/claim-map.json`, `results-audit/results-audit.json`, relevant literature/citation artifacts, predecessor failures, and review-loop state.
- Preserve paper ID and identity version across every binding.
- Keep claims, exhibits, citations, and manuscript actions legible to drafting, review-loop, paper review, and rebuttal stages.

## Input contract

Minimum:

- one or more paper claims;
- concrete evidence or source artifacts;
- enough information to classify each claim's evidence mode.

Prefer:

- validated result-audit JSON;
- source experiment claim map;
- commitment identity;
- target venue and page budget;
- known weaknesses and reviewer objections;
- desired exhibits;
- verified citation exports or Zotero artifacts.

## Output contract

### Canonical machine binding

Write `claim-evidence-bindings.json` as the authority for what the manuscript may assert. Each paper claim records:

- stable paper claim ID and bounded text;
- claim type and evidence mode;
- support status and manuscript action;
- required assurance class;
- source experiment claim IDs and result-audit IDs;
- audited evidence artifacts;
- planned sections, exhibit IDs, and citation-need IDs;
- limitations, missing evidence, scope, and rationale.

Use `references/claim-evidence-binding-schema.md` and `../research-pipeline-planner/references/result-audit-paper-binding-contract.md`.

### Human-readable views

- `paper-plan.md`: paper shape, venue constraints, and section reasoning.
- `claims-evidence-matrix.md`: exact one-row-per-JSON-claim view.
- `figure-plan.md`: exhibits with stable IDs and reciprocal paper-claim links.
- `citation-plan.md`: citation needs with stable IDs and reciprocal paper-claim links.

A complete matrix may not contain extra noncanonical claim rows.

## Evidence modes

- `empirical`: primarily supported by audited experimental results.
- `theoretical`: supported by proofs, formal arguments, or theory artifacts.
- `citation`: contextual or prior-work claim supported by verified sources.
- `mixed`: requires both audited empirical and nonempirical support.
- `limitation`: records a bounded weakness, failure, or threat to validity.

## Support status and manuscript action

Support status:

- `supported`
- `partial`
- `blocked`
- `contradicted`
- `withdrawn`

Manuscript action:

- `assert`
- `qualify`
- `limitation`
- `omit`

Rules:

- `assert` requires `supported` status.
- Empirical or mixed assertion requires at least one positive audit at or above the required assurance class and no unresolved linked negative audit.
- `qualify` requires explicit limitations.
- `partial` requires qualification or limitation treatment plus explicit limitations and missing evidence.
- `blocked`, `contradicted`, and `withdrawn` claims cannot be asserted.
- `contradicted` requires negative audit evidence and cannot coexist with an adequate positive audit under the same scope without reclassification.

## Hard stops

- Stop if the main paper claim has no credible evidence path.
- Do not write around missing evidence with rhetorical structure.
- Do not treat experiment completion, a passing validator, or a polished figure as claim support.
- Do not let Markdown status differ from the canonical JSON binding.
- Do not use a result audit for a different source claim or paper identity.
- Do not assert a confirmatory claim from exploratory-only audit assurance.
- Do not hide negative audits by linking only the preferred run.
- Do not treat citations as substitutes for empirical evidence or empirical results as novelty citations.
- If venue constraints materially affect the plan and remain unknown, preserve the gap rather than inventing requirements.

## Workflow

### 1) Freeze paper claims

- Assign stable paper claim IDs.
- Separate primary, supporting, limitation, and context claims.
- Specify evidence mode, scope, required assurance, and manuscript action.
- Preserve source experiment claim IDs instead of silently rewriting them.

### 2) Bind evidence

For empirical and mixed claims:

- link exact result-audit IDs;
- confirm each audit targets a listed source claim ID;
- compare attained assurance with required assurance;
- preserve negative and inconclusive audit records;
- link only evidence artifacts declared by those audits.

For theoretical claims, link concrete proof or argument artifacts. For citation claims, link stable citation-need IDs and verified sources.

### 3) Decide support status and language

- Use `supported` only when evidence reaches the required threshold.
- Use `partial` when evidence is promising but below threshold or materially incomplete.
- Use `blocked` when required evidence is absent.
- Use `contradicted` when linked audits materially weaken or kill the claim.
- Use `withdrawn` when the paper no longer advances the claim.
- Map each status to an allowed manuscript action and state limitations explicitly.

### 4) Fit paper structure to evidence

- Use `references/paper-outline-template.md`, `references/section-archetypes.md`, and `references/venue-adapters.md`.
- Give the strongest evidence the clearest space; do not let thin evidence carry a central section.
- Treat page budget and venue expectations as constraints.

### 5) Plan exhibits and citations with stable links

- Give every figure/table a stable exhibit ID and reciprocal paper-claim IDs.
- Mark exhibits mandatory, helpful, or cut.
- Give every citation need a stable ID and reciprocal paper-claim IDs.
- Distinguish motivation, novelty, method provenance, benchmark context, and empirical support.
- Use `research-zotero` or existing Zotero artifacts rather than inventing citations from memory.

### 6) Validate and hand off

- Ensure the Markdown matrix contains exactly the canonical claims.
- Ensure exhibit and citation references are reciprocal.
- Run structural validation for standalone packs and linked validation for orchestrated packs.
- Hand the validated pack to drafting or `research-review-loop`; missing evidence remains a block.

## Validation

Structural validation:

```bash
python scripts/validate_paper_pack.py \
  --plan paper-plan.md \
  --matrix claims-evidence-matrix.md \
  --bindings claim-evidence-bindings.json \
  --figure-plan figure-plan.md \
  --citation-plan citation-plan.md
```

Orchestrated linked validation:

```bash
python scripts/validate_paper_pack.py \
  --plan paper-plan/paper-plan.md \
  --matrix paper-plan/claims-evidence-matrix.md \
  --bindings paper-plan/claim-evidence-bindings.json \
  --figure-plan paper-plan/figure-plan.md \
  --citation-plan paper-plan/citation-plan.md \
  --assurance-profile linked \
  --commitment research-commitment.json \
  --claim-map experiment-plan/claim-map.json \
  --results-audit results-audit/results-audit.json
```

A passing validator establishes declared linkage and consistency, not scientific validity, citation correctness, or independent verification beyond the linked audit record.

## References

- `references/paper-outline-template.md`
- `references/claims-evidence-matrix-template.md`
- `references/claim-evidence-binding-schema.md`
- `references/section-archetypes.md`
- `references/venue-adapters.md`
- `references/exhibit-plan-checklist.md`
- `references/citation-verification-rules.md`
- `references/tabmol-ddi-ood-adapter.md`
- `../research-pipeline-planner/references/result-audit-paper-binding-contract.md`

## Scripts

- `scripts/init_paper_pack.py`: initialize the four Markdown views plus canonical `claim-evidence-bindings.json`.
- `scripts/validate_paper_pack.py`: validate binding structure, status/action rules, matrix/exhibit/citation reciprocity, paper identity, source claims, result-audit thresholds, and audited artifact paths.
