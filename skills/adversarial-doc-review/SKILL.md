---
name: adversarial-doc-review
description: Pedantic, adversarial stress-testing of documents (often Markdown .md) with claim-by-claim scrutiny, internal consistency checks, citation auditing, and up-to-date fact-checking via web search. Use when asked to critique, peer-review, red-team, verify references, or pressure-test time-sensitive statements; default deliverable is a structured report in chat.
---

# Adversarial Doc Review

## Quick start

1. Get the document (path/URL/pasted text) plus the intended audience and stakes.
2. Build a claim ledger (every definition, assumption, and claim must be traceable to a location in the doc).
3. Stress-test internally (consistency, logic, edge cases, evidence, citations).
4. Verify externally (default: use a web browsing/search tool to fact-check time-sensitive and externally-checkable claims).
5. Produce a structured report in chat by default using `references/report-template.md` and `references/review-checklist.md`. If a file is requested, write `<docname>.review.md` next to the document.

## Workflow decision points

- If web browsing is unavailable or disallowed, ask for permission or user-provided sources; otherwise label items as **unverified** and state what would verify them.
- If the doc is long, ask which sections matter; still scan the rest for contradictions, definitional drift, and unsupported strong claims.
- Default deliverable: structured report in chat. If a file is requested, write `<docname>.review.md` in the same folder as the input document.

## Inputs supported

- Pasted text, Markdown (`.md` file paths), LaTeX, PDF, DOCX, web pages.
- Prefer reviewing the canonical version (repo path, published PDF). Record the version/date you reviewed.
- For `.md` inputs, cite `path:line` plus the nearest heading (e.g., `docs/P2.md:143 (## Assumptions)`).

## Adversarial review workflow

### 1) Intake and scope

- Ask for: purpose, target audience, required rigor, and whether you may browse the web.
- Record: title, authors, version/commit, and the review date.
- Identify: the key conclusions the document wants the reader to accept.

### 2) Build a claim ledger (be exhaustive)

- Extract and list:
  - Definitions (terms, symbols, acronyms) and where they first appear.
  - Assumptions and scope limits (explicit and implicit).
  - Factual claims (including numbers, dates, rankings, “state of the art”, “most”, “first”).
  - Normative claims (“should”, “must”) and policy requirements.
  - Causal claims (“X causes Y”), correlations, and generalizations.
- For each entry, tag:
  - Type: definitional / factual / quantitative / normative / causal / speculative.
  - Verifiability: internal-only vs external-checkable.
  - Time sensitivity: stable vs time-sensitive (anything involving “current”, “recent”, laws, standards, prices, releases, benchmarks).
- Keep every entry traceable with short quotes and location pointers (Markdown: `path:line` + nearest heading; PDF: page; LaTeX: section; web: URL + heading when possible).

### 3) Internal stress-test (try to break it)

- Consistency:
  - Find contradictions, changing terminology, inconsistent notation, and unit mismatches.
  - Verify every variable/symbol is defined and used consistently.
- Logic and argumentation:
  - Find missing steps, unsupported leaps, hidden quantifiers (“often”, “generally”), and category errors.
  - Construct counterexamples and edge cases; check whether the document already rules them out.
- Evidence and methodology:
  - Check that strong claims have commensurate evidence.
  - Flag selection bias, cherry-picked examples, unclear baselines, and missing ablations/sanity checks.
- Citations:
  - Flag missing citations and “citation laundering” (citation present but does not support the stated claim).

### 4) External verification (default: do it)

- For each externally-checkable or time-sensitive claim:
  - Search the web and verify against reputable, current sources (prefer primary sources, standards bodies, official docs, peer-reviewed venues, or widely trusted data providers).
  - Record: source, publication/update date, and what exactly it confirms or refutes.
  - If sources disagree, report the disagreement and what would resolve it.
- Verify references:
  - Confirm the cited work exists and plausibly supports the statement it is attached to.
- Do not guess. If you cannot verify, label as **unverified** and say what evidence is needed.

### 5) Produce the adversarial report

- Use `references/report-template.md`.
- Prioritize “major issues” that would change conclusions, correctness, or safety.
- Provide concrete fixes: rewrites, added definitions, missing citations, alternative framing, or additional experiments/analyses.
- Separate:
  - Incorrect / misleading statements
  - True-but-misleading statements
  - Unsupported statements
  - Ambiguous statements
  - Outdated statements

## Format-specific tips (optional)

- Markdown (`.md`):
  - For every issue/claim, cite `path:line` plus the nearest heading.
  - Preserve code fences and tables when quoting; avoid paraphrases that change semantics.
  - Check that internal anchors and external links resolve (where feasible).
- LaTeX:
  - Check `\\cite{}` keys exist in `.bib` and that claims align with cited works.
  - Compile if possible; otherwise review `.tex` plus any generated `.bbl`/PDF if available.
- PDF/DOCX:
  - Prefer extracting text for searchability; keep page/section references for every issue.
- Specs/policies:
  - Treat “MUST/SHOULD/MAY” as normative; look for loopholes, contradictions, and missing definitions.

## Resources

- `references/review-checklist.md`: full pedantic checklist.
- `references/report-template.md`: report skeleton to fill.
