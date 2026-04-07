---
name: research-paper-plan
description: Turn supported claims and evidence into a research paper plan that works either as a standalone manuscript-structuring pass or as the paper stage inside a coordinated research workflow. Use when asked to outline a paper, map claims to evidence, plan figures and citations, align experiments to manuscript claims, or keep limitations and threats to validity explicit.
---

# Research Paper Plan

## Quick start

1. Start from supported claims, not from section titles.
2. Decide whether this is a standalone paper plan or the paper stage inside an orchestrated suite.
3. Initialize `paper-plan.md`, `claims-evidence-matrix.md`, `figure-plan.md`, and `citation-plan.md` only when tracked outputs will help.
4. Block on missing evidence instead of writing around it.
5. Plan figures, citations, and limitations as first-class parts of the manuscript story.

## Modes

### Standalone mode

- Work from the user prompt plus any local claims, results, notes, or drafts already present.
- Do not require a suite root.
- Collaboration is still allowed: if novelty review, experiment plan, results audit, or review-loop artifacts exist, use them; if another skill would materially improve the manuscript plan, recommend or invoke it.

### Orchestrated mode

- Prefer the canonical directory `./paper-plan/`.
- Read upstream context from `research-brief.md`, `artifact-index.md`, `./novelty-review/`, `./experiment-plan/`, `./review-loop/`, and `./zotero/` when present.
- Keep the paper outputs legible to later drafting and review passes.

## Input contract

- Minimum:
  - one or more claims the paper wants the reader to accept
  - evidence or source artifacts that support those claims
- Prefer:
  - target venue or audience
  - known weaknesses or reviewer objections
  - desired exhibit list
  - existing novelty, experiment, results-audit, or review-loop artifacts
  - existing Zotero exports or library artifacts

## Hard stops

- Stop if the user wants a paper plan but there is no credible evidence behind the main claim.
- Stop if claims outrun the available artifacts and the gap cannot be made explicit.
- Stop if the venue constraints matter but remain unknown.
- In standalone mode, do not create excess structure when a compact direct outline is enough.

## Output contract

- Primary files:
  - `paper-plan.md`
  - `claims-evidence-matrix.md`
  - `figure-plan.md`
  - `citation-plan.md`
- In orchestrated mode, these live under `./paper-plan/`.
- In standalone mode, any target directory is valid.

## Workflow

### 1) Freeze the supported claims

- Use `references/claims-evidence-matrix-template.md`.
- Separate:
  - main contribution claims
  - supporting claims
  - limitation claims
- Downgrade or remove claims that do not have a clear evidence path.

### 2) Fit the paper shape to the evidence

- Use `references/paper-outline-template.md`, `references/section-archetypes.md`, and `references/venue-adapters.md`.
- Choose a structure that matches what the evidence can actually support.
- Treat page budget and venue expectations as constraints, not afterthoughts.

### 3) Plan exhibits deliberately

- Use `references/exhibit-plan-checklist.md`.
- Every figure and table should answer a paper question or defend a claim.
- Mark exhibits as:
  - mandatory
  - helpful
  - cut

### 4) Build the citation plan carefully

- Use `references/citation-verification-rules.md`.
- If a Zotero library already exists for the project, invoke `research-zotero` or consume `./zotero/` artifacts before inventing citation structure from memory.
- Record which claims need citations versus which require empirical evidence.
- Keep citation verification explicit instead of inventing references from memory.

### 5) Keep collaboration open

- Pull in `research-results-auditor` when the evidence quality is unclear.
- Pull in `research-review-loop` when the story needs an adversarial pass.
- Pull in `research-novelty-review` when positioning remains unstable.
- Pull in `research-zotero` when citation grounding, BibTeX export, or CSL-JSON export would materially improve the paper plan.
- Missing evidence remains a block in every mode. Do not write unsupported paper stories.

## References

- `references/paper-outline-template.md`
- `references/claims-evidence-matrix-template.md`
- `references/section-archetypes.md`
- `references/venue-adapters.md`
- `references/exhibit-plan-checklist.md`
- `references/citation-verification-rules.md`
- `references/tabmol-ddi-ood-adapter.md`

## Script

- `scripts/init_paper_pack.py`: create the core paper-planning files in a standalone directory or the suite's `paper-plan/` directory.
