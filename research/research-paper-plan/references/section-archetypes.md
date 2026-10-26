# Section Archetypes

Pick the archetype from the contribution type and the register, then plan each section's job
before its content. These are the expectations reviewers in each community bring; the plan should
meet them or say why it does not.

## Contribution archetypes

- **Empirical finding**: the result is the contribution. Lead with the question, the measurement,
  and the headline finding with its uncertainty. Methodological novelty stays modest; analysis,
  robustness, and the caveats that bound the finding carry the paper.
- **Method or mechanism**: the mechanism is the contribution. Lead with the insight (one design
  principle, not a list of modules), then the strongest fair comparison, then the ablations that
  isolate the claimed factor. A method paper without an isolating ablation is a finding paper.
- **Benchmark, dataset, or artifact**: the artifact is the contribution. Front-load why it is
  needed, what is new about it, how evaluation on it avoids triviality or leakage, and what it
  cannot measure.
- **Theory**: the theorems are the contribution. State definitions and hypotheses before results,
  give intuition before proofs, say which assumptions are essential and which are simplifying, and
  put full proofs in an appendix with sketches in the main text. Do not add empirical hedges to
  proved statements.
- **Position or analysis**: the argument is the contribution. State the thesis in one sentence
  early, name the positions it argues against as real positions in the literature, make each
  premise visible, and say what evidence would change the conclusion.
- **Negative or mixed result**: the absence or the inconsistency is the contribution. State what
  was expected and by whom, the power of the test to have found it, and what the result rules out.

## Section jobs

Abstract: problem, approach, concrete finding, implication, in that order and proportion. Say what
the paper finds, not what it looks for. No literature in the abstract.

Introduction: move from the field problem to the specific gap to this paper's intervention, and
give the main result in the introduction itself. Readers decide here. The related-work paragraph
is a story with a "however" (what others did, what remains open, what this paper does about it),
not an annotated bibliography; discuss the five to ten closest works and state each one's
limitation as well as its finding. Close with a roadmap that names landmarks, not section numbers.

Method: design choices, controls, data, assumptions, and procedures, in the order a reader needs
to judge validity. Implementation detail only where it affects validity or reproducibility.

Results: the finding first, then the comparison or condition that grounds it, with uncertainty
attached to every headline number. Keep interpretation adjacent to the evidence and calibrated to
what was measured. Every number traces to a registered source (see the claim-evidence binding).

Discussion: the supported implication stated directly, then boundary conditions and unresolved
alternatives where they change interpretation. Do not frame the discussion around what the result
does not establish.

Limitations: the material constraint and its consequence for interpretation or transfer, stated
once, specifically. No hypothetical objections raised only to be dismissed.

Conclusion: the strongest supported contribution restated, compared against the abstract and the
contribution list so that the paper's claim has not shrunk between its first page and its last.

## Register notes

- Empirical ML (ICLR, ICML, NeurIPS, ACL): contribution bullets are conventional; results belong
  in the introduction; reproducibility and compute statements are expected.
- Theory: numbered statements, hypotheses as scope, proof location stated.
- Vision and systems: method figure early, component names conventional, compute and latency
  reported.
- Position papers and HCI or social science: argumentative contrast is normal; coined terms carry
  the thesis and are defined on first use; a study section follows the empirical archetype.
- Economics-style empirical writing (useful for any quantitative social science): triangular
  order (most important first), one central contribution written down in one paragraph, concrete
  magnitudes in the introduction, literature as part of the introduction.

## Use with the claims-evidence matrix

Each section job above consumes specific claim-evidence rows. When a section has no bound claim
behind it, the plan says what the section will assert and marks it as framing rather than
evidence. When a bound claim has no section, the plan is incomplete.
