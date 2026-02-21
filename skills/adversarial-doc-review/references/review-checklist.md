# Adversarial Review Checklist

Use this as a “nothing gets a free pass” checklist. Prefer concrete, traceable findings over general vibes.

## 1) Scope and framing

- State what the document is trying to do (and what it is not trying to do).
- Identify target audience and implied prerequisites.
- Flag scope creep, unstated goals, or bait-and-switch between sections.
- Check that the abstract/summary matches the body.

## 2) Definitions and notation (pedantic mode)

- Verify every key term is defined before use.
- Flag overloaded terms (“alignment”, “robust”, “significant”, “safety”) and demand operational definitions.
- Check for circular definitions and definitional drift across sections.
- Verify every symbol, acronym, and abbreviation is defined once and used consistently.
- Check units and dimensions on all quantitative values.

## 3) Claim-by-claim scrutiny

- Rewrite each important claim in a falsifiable form (“Under assumptions A–C, X implies Y with metric M”).
- Flag weasel words and hidden quantifiers (“often”, “generally”, “can”, “may”, “in practice”).
- Distinguish:
  - Descriptive vs normative claims
  - Correlation vs causation
  - Empirical claims vs conjectures
- Identify what would change your mind (what evidence would refute the claim).

## 4) Internal consistency and logic

- Check for contradictions between sections, figures, tables, and captions.
- Verify arguments do not smuggle in extra assumptions mid-proof/mid-paragraph.
- Construct edge cases and counterexamples; check whether the doc handles them.
- Look for category errors and conflations (e.g., “capability” vs “deployment”, “metric” vs “objective”).

## 5) Evidence quality and methodology (if empirical)

- Identify datasets, baselines, and evaluation metrics; check they match the claim.
- Flag missing baselines, missing ablations, or unclear experimental controls.
- Check that comparisons are fair (same compute, same data, same protocol).
- Check whether reported improvements are practically meaningful (not only statistically significant).
- Flag cherry-picking (best-case examples) and unclear selection criteria.

## 6) Figures, tables, and numbers

- Verify axes, units, and denominators are stated.
- Check rounding, inconsistent totals, and “percentage of what?” issues.
- Demand sources for any external numbers (market sizes, adoption rates, benchmarks, “X% of users…”).
- Check whether figures support the text’s interpretation (and not the opposite).

## 7) Citations and reference integrity

- For each citation: state what exact claim it is supposed to support.
- Flag “citation laundering” (citation attached but the cited work does not support the claim).
- Flag missing citations for strong claims.
- Check that the doc is not citing secondary summaries where a primary source exists.

## 8) External fact-checking (default)

- Identify time-sensitive statements (“current”, “recent”, “as of”, “latest”, laws/regs, standards, product behavior, prices, benchmarks).
- For each externally-checkable claim:
  - Find at least one high-quality, current source.
  - Record source + publication/update date + what it confirms/refutes.
  - Cross-check with a second independent source when stakes are high.
- If sources disagree, report the disagreement and the likely reason (definitions, date, geography, methodology).

## 9) Adversarial angle (red-team the document)

- Write the strongest plausible objection a hostile reviewer would make.
- Identify ambiguity that an opponent could exploit.
- Identify failure modes, misuse risks, and incentive mismatches.
- For specs/policies: look for loopholes, undefined terms, and inconsistent requirements.

## 10) Clarity and reader experience

- Flag sentences with unclear referents (“this”, “it”, “they”) and ambiguous scope.
- Flag claims hidden in footnotes/captions/parentheticals.
- Check that each section earns its existence; flag repetition and missing transitions.

## 11) Markdown-specific checks (if `.md`)

- Cite findings with `path:line` plus the nearest heading for traceability.
- Check that internal anchors and external links resolve (where feasible).
- Treat code fences and tables as semantics-bearing; avoid “fixes” that change meaning.
