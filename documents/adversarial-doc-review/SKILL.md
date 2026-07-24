---
name: adversarial-doc-review
description: Pedantic, adversarial stress-testing of documents (often Markdown .md) with claim-by-claim scrutiny, internal consistency checks, citation auditing, and up-to-date fact-checking via web search. Use when asked to critique, peer-review, red-team, verify references, or pressure-test time-sensitive statements; default deliverable is a structured report in chat.
---

# Adversarial Doc Review

## Quick start

1. Get the document (path/URL/pasted text) plus the intended audience and stakes.
2. Build a claim ledger: every definition, assumption, factual claim, normative claim, control claim, and route-authorization claim must be traceable to a location in the document.
3. Stress-test internally for consistency, logic, edge cases, evidence, citations, non-vacuity, and specification gaming.
4. Verify externally by default: use a web browsing/search tool to fact-check time-sensitive and externally-checkable claims.
5. When the document authorizes research evidence or stage advancement, apply `../../research/research-pipeline-planner/references/epistemic-assurance-contract.md` and test whether labels correspond to actual properties.
6. Produce a structured report in chat by default using `references/report-template.md` and `references/review-checklist.md`. If a file is requested, write `<docname>.review.md` next to the document.

## Workflow decision points

- If web browsing is unavailable or disallowed, ask for permission or user-provided sources; otherwise label items as **unverified** and state what would verify them.
- If the document is long, ask which sections matter; still scan the rest for contradictions, definitional drift, unsupported strong claims, and stage-advancing statements.
- If the document claims validation, verification, independence, immutability, isolation, replay, auditability, or route readiness, inspect the mechanism and evidence rather than accepting the label.
- Default deliverable: structured report in chat. If a file is requested, write `<docname>.review.md` in the same folder as the input document.

## Inputs supported

- Pasted text, Markdown (`.md` file paths), LaTeX, PDF, DOCX, web pages.
- Prefer reviewing the canonical version (repo path, published PDF). Record the version/date you reviewed.
- For `.md` inputs, cite `path:line` plus the nearest heading, for example `docs/P2.md:143 (## Assumptions)`.

## Adversarial review workflow

### 1) Intake and scope

- Ask for purpose, target audience, required rigor, whether you may browse the web, and whether the document is intended to authorize evidence promotion or a consequential decision.
- Record title, authors, version/commit, and review date.
- Identify the key conclusions the document wants the reader to accept.
- Identify any claimed evidence class: exploratory, confirmatory, independently verified, or operational/high-stakes.

### 2) Build a claim ledger exhaustively

- Extract and list:
  - definitions: terms, symbols, acronyms, assurance labels, and where they first appear
  - assumptions and scope limits, explicit and implicit
  - factual claims, including numbers, dates, rankings, “state of the art,” “most,” and “first”
  - normative claims such as “should” and “must,” plus policy requirements
  - causal claims, correlations, and generalizations
  - control claims such as immutable, isolated, replayed, blinded, independent, verified, validated, or audited
  - route-authorization claims such as proceed, gate passed, ready, safe, or sufficient
- For each entry, tag:
  - type: definitional / factual / quantitative / normative / causal / speculative / control / route authorization
  - verifiability: internal-only vs external-checkable
  - time sensitivity: stable vs time-sensitive
  - evidence class and provenance when relevant
- Keep every entry traceable with short quotes and location pointers: Markdown `path:line` plus nearest heading; PDF page; LaTeX section; web URL plus heading when possible.

### 3) Internal stress-test

- Consistency:
  - Find contradictions, changing terminology, inconsistent notation, unit mismatches, and evidence-class drift.
  - Verify every variable, symbol, assurance term, and gate condition is defined and used consistently.
- Logic and argumentation:
  - Find missing steps, unsupported leaps, hidden quantifiers, category errors, and conclusions stronger than the premises.
  - Construct counterexamples and edge cases; check whether the document already rules them out.
- Evidence and methodology:
  - Check that strong claims have commensurate evidence.
  - Flag selection bias, cherry-picked examples, unclear baselines, missing ablations, missing failure states, and missing sanity checks.
  - Check whether cases, metrics, or conclusions were selected after inspecting relevant outcomes.
- Citations:
  - Flag missing citations and citation laundering: a citation is present but does not support the attached claim.

### 4) Run the assurance and specification-gaming pass

For documents that claim controls, verification, or research-route readiness:

- Distinguish the property from its label or proxy.
- Test common substitutions explicitly:
  - self-hash versus external immutability
  - environment flag versus actual isolation
  - copied digest versus regenerated replay
  - role name versus material independence
  - file or field presence versus semantic completeness
  - shared implementations agreeing versus genuinely diverse evidence
  - feature-absence comparator versus substantive distinctness
- Check non-vacuity:
  - Can competing systems, policies, or actions differ on any plausible case?
  - Can the comparator win under plausible conditions?
  - Does the loss or decision contract penalize every decision-relevant error, including failure to act?
- Check complete outcome accounting:
  - successes, wrong actions, missed actions, skips, nulls, retries, timeouts, initial failures, and resource failures
- Check hidden-information boundaries and whether the evaluated process could read oracle truth or outcome labels.
- State actual independence across context, data, implementation, evaluation, and advancement authority. The same agent or team performing multiple roles is self-review unless materially separated.
- Carry material predecessor failures forward. Reclassification, replacement, renaming, or omission is not resolution.

### 5) External verification

- For each externally-checkable or time-sensitive claim:
  - Search the web and verify against reputable, current sources, preferring primary sources, standards bodies, official documentation, peer-reviewed venues, or widely trusted data providers.
  - Record source, publication/update date, and what exactly it confirms or refutes.
  - If sources disagree, report the disagreement and what would resolve it.
- Verify references:
  - Confirm the cited work exists and plausibly supports the statement it is attached to.
- Do not guess. If you cannot verify, label the claim **unverified** and state what evidence is needed.

### 6) Produce the adversarial report

- Use `references/report-template.md`.
- Prioritize major issues that would change conclusions, correctness, safety, evidence class, or route authorization.
- Provide concrete fixes: rewrites, added definitions, missing citations, alternative framing, corrected evidence classification, or additional experiments/analyses.
- Separate:
  - incorrect or misleading statements
  - true-but-misleading statements
  - unsupported statements
  - ambiguous statements
  - outdated statements
  - assurance labels not established by the mechanism
  - unresolved predecessor failures
- Use bounded verdicts such as `structurally valid only`, `internally consistent only`, `supports exploratory follow-up`, `supports the confirmatory claim`, or `independently verified`.
- Do not infer malicious intent from a misleading artifact alone. Distinguish intentional misconduct, agent violation of explicit instructions, skill-contract defects, orchestration defects, and ordinary error according to the available provenance.

## Format-specific tips

- Markdown (`.md`):
  - For every issue/claim, cite `path:line` plus the nearest heading.
  - Preserve code fences and tables when quoting; avoid paraphrases that change semantics.
  - Check that internal anchors and external links resolve where feasible.
- LaTeX:
  - Check `\\cite{}` keys exist in `.bib` and that claims align with cited works.
  - Compile if possible; otherwise review `.tex` plus any generated `.bbl`/PDF if available.
- PDF/DOCX:
  - Prefer extracting text for searchability; keep page/section references for every issue.
- Specs/policies:
  - Treat `MUST`, `SHOULD`, and `MAY` as normative; look for loopholes, contradictions, proxies, and missing definitions.

## Resources

- `references/review-checklist.md`: full pedantic checklist.
- `references/report-template.md`: report skeleton to fill.
- `../../research/research-pipeline-planner/references/epistemic-assurance-contract.md`: proportionate evidence-promotion and independence contract.