# Domain Adapters

Start with the generic bias rubric and then apply the relevant domain adapter. Record the adapter ID in the protocol `domain_adapter` field: `ai-ml`, `biomedical`, `social-science`, `policy-governance`, `theoretical-mathematical`, or `conceptual-interdisciplinary`. When none fits, name the closest adapter and record the deviations.

## Generic bias rubric

- Selection bias
- Measurement bias
- Confounding bias
- Reporting/publication bias
- Reproducibility risk

## AI/ML adapter (`ai-ml`)

- Verify benchmark comparability and protocol parity.
- Verify ablation completeness and baseline strength.
- Verify compute/data differences are disclosed.
- Verify robustness, calibration, and failure-case reporting.

## Biomedical adapter (`biomedical`)

- Verify endpoint clinical relevance.
- Verify randomization/blinding/allocation reporting where applicable.
- Verify attrition handling and adverse-event reporting.
- Verify population representativeness and external validity.

## Social science adapter (`social-science`)

- Verify identification strategy credibility.
- Verify instrument validity and measurement reliability.
- Verify robustness checks and alternative specifications.
- Verify subgroup analysis controls for multiple comparisons.

## Policy and governance adapter (`policy-governance`)

- Verify legal and jurisdictional assumptions.
- Verify implementation feasibility constraints.
- Verify incentive and gaming risks.
- Verify equity/distributional impact considerations.

## Theoretical and mathematical adapter (`theoretical-mathematical`)

Use for reviews whose evidence is definitions, theorems, proofs, and formal constructions rather than measured outcomes. Do not apply sample-size, intervention, comparator, or effect-size fields.

- Record the formal setting of each work: objects, structures, axioms, and standing assumptions.
- Record the key definitions and whether they match, generalize, or specialize the target formulation.
- Record theorem status: proved, proof sketch only, conjectured, or claimed without proof. Note whether the proof was checked, and by whom.
- Trace equivalence or reduction to known results: same result under different names or notation, a special case of an older theorem, or a reduction to a standard construction.
- Search older and adjacent formal literatures (for example category theory, order theory, logic, programming-language semantics, statistics) under their own terminology, not only the target field's vocabulary.
- Extract counterexamples, impossibility results, and boundary cases as evidence against the claim.
- Quality signals: completeness of proofs, explicit assumptions, and independent verification or formalization, not venue alone.

## Conceptual and interdisciplinary adapter (`conceptual-interdisciplinary`)

Use for reviews whose evidence is arguments, distinctions, and frameworks, including philosophy, theory-heavy social science, and cross-field conceptual work.

- Record the thesis of each work in one sentence and the distinctions or concepts it introduces.
- Map dialectical opponents: which positions each work argues against, and which works argue against it.
- Trace the lineage of each named concept across fields, including earlier uses under other names.
- Record operationalisation: whether and how the concept is made measurable or testable, and by whom.
- Separate conceptual claims from empirical claims that the work borrows or asserts without evidence.
- Search each contributing discipline in its own venues and vocabulary; one field's index rarely covers another's.
- Quality signals: clarity of definitions, engagement with the strongest objections, and consistency of use across works, not citation counts alone.
