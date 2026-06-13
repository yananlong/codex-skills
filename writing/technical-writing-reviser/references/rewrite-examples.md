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
"We evaluate whether archive-constrained prompting reduces shortcut-consistent behavior across a set of controlled tasks. The results suggest that the constraint improves behavior in some settings, but the effect varies by task family."

## Introduction Framing

Before:
"Our project started because we kept seeing weird cases where the model looked good but probably was not doing the thing we wanted."

After:
"Models can appear successful on tasks that permit shortcut strategies, making it difficult to determine whether observed performance reflects the target capability. This paper studies that ambiguity by comparing unconstrained prompts with conditions designed to limit shortcut explanations."

## Technical Report Framing

Before:
"The prototype is ready for enterprise deployment because it handled the pilot workload."

After:
"The prototype handled the pilot workload under the tested configuration, which supports continued evaluation in enterprise-like settings. The result does not by itself establish production readiness, because deployment risk still depends on reliability, integration, monitoring, and operational support under broader conditions."

## Whitepaper Framing

Before:
"This approach will change how teams manage compliance reviews."

After:
"This approach reduces the manual review burden in the evaluated workflow by separating evidence collection from reviewer judgment. The supported claim is therefore about workflow efficiency under the tested process, not a general change in compliance practice."

## Methods Prose

Before:
"We first tried the baseline prompts, then we added the stricter bucket, then we ran the archive version to see what breaks."

After:
"We compare the baseline prompts with a stricter control condition and an archive-based condition to test which behaviors persist once the task limits common shortcut explanations."

## Results Prose

Before:
"Interesting thing: the effect mostly holds in courtroom but gets weird for fabricated citations."

After:
"The pattern remains visible in the courtroom condition, but it weakens in the fabricated-citation condition, which suggests that the behavior depends on how strongly the task constrains unsupported inference."

## Overclaim Control

Before:
"These results prove that the model has semantic-pragmatic competence."

After:
"These results are consistent with semantic-pragmatic competence under the evaluated conditions, but they do not rule out all shortcut explanations."

## Limitation Prose

Before:
"This is probably narrow and we have not really checked everything yet."

After:
"This analysis is narrow in scope and does not establish that the same behavior would persist across broader task families, so the claim should be read as conditional on the evaluated settings."
