# Rewrite Examples

## Internal Terminology

Before:
"Our micro-archive setup beats the freeform condition once the retrieval gate is on."

After:
"The compact curated archive condition outperforms the unconstrained condition once retrieval is explicitly constrained."

## Contribution Framing

Before:
"We introduce a new way to understand whether models really understand language."

After:
"We introduce an evaluation framework for testing whether a model's behavior remains consistent with semantic-pragmatic competence once shortcut explanations are controlled."

## Abstract Prose

Before:
"We looked at a bunch of tasks where the model might be using shortcuts, and the archive setup seemed to help in some cases."

After:
"We evaluate whether archive-constrained prompting reduces shortcut-consistent behavior across a set of controlled tasks. The results suggest improved behavior in some settings, with the effect varying by task family."

## Introduction Framing

Before:
"Our project started because we kept seeing weird cases where the model looked good but probably was not doing the thing we wanted."

After:
"Models can appear successful on tasks that permit shortcut strategies, making it difficult to determine whether observed performance reflects the target capability. This paper studies that ambiguity by comparing unconstrained prompts with conditions designed to limit shortcut explanations."

## Technical Report Framing

Before:
"The prototype is ready for enterprise deployment because it handled the pilot workload."

After:
"The prototype handled the pilot workload under the tested configuration, supporting continued evaluation in enterprise-like settings."

Add deployment caveats only when production readiness is actually under discussion or the user needs a deployment-readiness assessment.

## Whitepaper Framing

Before:
"This approach will change how teams manage compliance reviews."

After:
"This approach reduces the manual review burden in the evaluated workflow by separating evidence collection from reviewer judgment."

Do not add "not a general change in compliance practice" unless that broader claim is present or otherwise salient in the source.

## Methods Prose

Before:
"We first tried the baseline prompts, then we added the stricter bucket, then we ran the archive version to see what breaks."

After:
"We compare the baseline prompts with a stricter control condition and an archive-based condition to test which behaviors persist once the task limits common shortcut explanations."

## Results Prose

Before:
"Interesting thing: the effect mostly holds in courtroom but gets weird for fabricated citations."

After:
"The pattern remains visible in the courtroom condition but weakens in the fabricated-citation condition, suggesting that the behavior depends on how strongly the task constrains unsupported inference."

## Overclaim Control

Before:
"These results prove that the model has semantic-pragmatic competence."

After, when the evaluation discriminates competence from the controlled shortcuts:
"These results show semantic-pragmatic competence on the evaluated task families once the controlled shortcut strategies are ruled out."

After, only when named alternatives remain live:
"These results are consistent with semantic-pragmatic competence, although a frequency-based strategy remains a live alternative on two task families."

Move down one rung at a time and stop at the first supported form. Do not jump from "prove" to "consistent with" by default. If ruling out shortcut explanations is itself part of the experimental claim, state the surviving alternatives explicitly. Otherwise, do not append a generic sentence saying the results fail to rule out every possible shortcut.

## Evidence Conflict

Before:
"The two conditions are equivalent." (the source's own analysis shows the conditions cannot be distinguished by the data, which is non-identifiability, not equivalence)

After:
Do not weaken to "the conditions appear equivalent", which is still false. Flag: the evidence shows the data cannot distinguish the conditions; the sentence should state non-identifiability or be removed.

## Formal Statement

Before (reviser-damaged):
"Under the evaluated conditions, the construction appears to preserve exactness."

After (restored):
"Under hypotheses (H1) and (H2), the construction preserves exactness (Theorem 3)."

The hypotheses are the scope. An empirical hedge on a proved statement is an error, not caution.

## Limitation Prose

Before:
"This is probably narrow and we have not really checked everything yet."

After:
"The analysis covers three task families in English with one model family, so transfer to morphologically rich languages and to instruction-tuned variants remains untested."

Name the actual boundary and its consequence. A stock sentence about "broader generalization" is the generic disclaimer the skill elsewhere removes.

## Manufactured Contrastive Negation

Before:
"The contribution is not a new retrieval algorithm. It is a framework for evaluating retrieval behavior."

After:
"The contribution is a framework for evaluating retrieval behavior."

Keep the negation only when readers could reasonably confuse the contribution with a retrieval algorithm or the source explicitly makes that distinction.

## Anticipatory Disclaimer

Before:
"We are not claiming that the mechanism generalizes universally. Rather, the results support the mechanism within the tested settings."

After:
"The results support the mechanism within the tested settings."

## Defensive Limitation Contrast

Before:
"The limitation is not primarily dataset size, but the narrow range of deployment conditions."

After:
"The main limitation is the narrow range of deployment conditions."

## Necessary Negation: Technical Absence

Before:
"Our method works without calibration labels."

After:
"Unlike the baseline, the proposed method does not require labeled calibration data."

The negation is useful because absence of the requirement is itself the technical distinction.

## Necessary Negation: Ruled-Out Explanation

Before:
"Frequency might explain the effect, but the control seems okay."

After:
"The control rules out token frequency as the explanation for the observed effect."

The exclusion is central because the experiment is explicitly discriminating between explanations.
