# Claim Discipline

## Purpose

Use this reference when a draft sounds more certain, broader, more causal, or more commercially conclusive than the evidence supports, or when the source mixes results, interpretation, speculation, motivation, and positioning.

## Support Levels

Distinguish these levels before rewriting:

1. Observation: the draft reports something noticed in examples, logs, or qualitative inspection.
2. Measurement: the draft reports a quantified result under specified conditions.
3. Comparison: the draft contrasts conditions, baselines, datasets, or settings.
4. Interpretation: the draft explains what the result may mean.
5. Mechanism: the draft claims why the result occurs.
6. Generalization: the draft claims the result transfers beyond the tested setting.
7. Operational or market implication: the draft claims the result changes deployment readiness, buyer value, risk, adoption, or practical decision-making.

Do not move a sentence up this ladder unless the source explicitly supports that move, and do not move a supported sentence down the ladder merely because a stronger unsupported claim could be imagined.

## Direct Supported Claim Shapes

State the strongest supported claim directly. Use bounded verbs or scope qualifiers when the evidence requires them, but avoid pairing a supported claim with an unnecessary disclaimer about a stronger proposition that the source never made.

Useful bounded forms include:

- "suggests" when the evidence is indicative but not decisive.
- "is consistent with" when multiple explanations remain materially plausible.
- "under the evaluated conditions" when the claim depends on a narrow setup.
- "we observe" when the source is qualitative or preliminary.
- "we find" when the source reports a result from a defined evaluation.

Avoid turning:

- correlation into causation.
- a control into proof of mechanism.
- a benchmark improvement into field-wide progress.
- an implementation choice into a conceptual contribution.
- a prototype behavior into production readiness.
- a technical result into a buyer, market, or adoption claim.
- a limitation into a minor caveat if it changes interpretation.

## Avoid Manufactured Rebuttals

Do not introduce a stronger rejected proposition solely to disclaim it. Constructions such as "not X but Y," "this does not establish X," "we are not claiming X," or "the supported claim is Y, not X" are appropriate only when X is already salient, genuinely confusable with Y, explicitly asserted in the source, or materially ruled out by the evidence.

When a direct scoped statement carries the same evidential boundary, prefer it:

- Prefer "The prototype handled the pilot workload under the tested configuration" over "The prototype handled the pilot workload, but this does not establish production readiness" unless production readiness is actually under discussion.
- Prefer "The results support the mechanism under the evaluated settings" over "The results do not prove universal validity; they support the mechanism under the evaluated settings."
- Prefer "The main limitation is the narrow range of deployment conditions" over "The limitation is not dataset size but the narrow range of deployment conditions" unless dataset size is a live alternative.

Preserve negative findings, ruled-out alternatives, absence claims, and explicit corrections when the negation itself carries technical information.

## Missing Evidence

If a sentence exceeds the available support, rewrite that sentence to the strongest supported version. Add a brief note only when the missing evidence materially constrains the user's intended claim or when the user asked for diagnosis.

Do not normally name a hypothetical stronger claim just to explain why it is unsupported. Instead of "The current evidence supports a conditional claim, not a general claim," prefer the conditional claim itself unless the contrast is necessary for interpretation.

## Final Check

For each paragraph, ask whether the conclusion follows from the preceding evidence and whether its scope matches the support. If not, calibrate the conclusion. Then scan for defensive contrast framing and remove rejected propositions that were introduced only to make the supported claim sound cautious.
