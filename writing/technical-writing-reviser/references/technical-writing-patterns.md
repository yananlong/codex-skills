# Technical Writing Patterns

## Target Stance

Technical prose should tell the reader what was studied, built, measured, observed, or decided; how the evidence was obtained; what the evidence shows; and what follows from it. It should not read like a chronological lab log, internal status memo, unsupported sales pitch, or running commentary on the team's actions.

## Rewrite Patterns

### Setup to Motivation

Move from "here is the topic we have been thinking about" to "here is the concrete technical problem and why it matters." Prefer one clear motivation over several warm-up sentences.

### Procedure to Method

Replace diary language with design language. Instead of narrating what the team did next, state the method, control, data source, annotation choice, architecture, analysis step, or comparison in a form that explains the technical function.

### Observation to Result

Turn raw noticing into a stated finding with scope. Say what pattern was observed, under what condition, and at the strength supported by the source.

### Note to Claim

Many internal drafts contain fragments such as "important because shortcut explanation still possible." Rewrite these as explicit claims tied to reasoning: "This distinction matters because shortcut explanations remain available unless the control rules them out."

### Caveat to Limitation

Do not bury material constraints in parenthetical hedges. State the limitation directly and give its consequence for interpretation, generalization, or applicability when that consequence matters.

### Contribution to Payoff

When a draft says a contribution is "interesting" or "useful," replace that with the concrete payoff: a framework, dataset, analysis, protocol, or reporting discipline that enables a more defensible evaluation or interpretation.

### Positioning to Supported Value

When a report or whitepaper says a result is "transformative," "production-ready," or "commercially compelling," replace that wording only when the source does not support it. State the strongest supported technical value directly: the measured improvement, reduced failure mode, clarified tradeoff, validated operating condition, or other evidenced payoff.

### Defensive Contrast to Direct Claim

When a sentence first denies a proposition and then states the actual point, ask whether the denied proposition is already salient or technically necessary. If not, remove the denial and state the supported proposition directly.

Prefer "The contribution is an evaluation framework for retrieval behavior" over "The contribution is not a new retrieval algorithm; it is an evaluation framework for retrieval behavior" unless the algorithm/framework distinction is a live issue.

Prefer "The results support the mechanism under the evaluated settings" over "The results do not establish universal validity; rather, they support the mechanism under the evaluated settings" unless universal validity has actually been asserted or is central to the argument.

Keep negation when an absence, exclusion, correction, or ruled-out alternative is itself part of the technical content.

## Section-Specific Guidance

Title or headline:
Prefer precise nouns over slogan-like phrasing. A good title-level phrase names the object, method, or finding without overclaiming broad importance.

Abstract:
Compress the arc into problem, method, result, and implication. Keep the implication proportional to the result and avoid background that belongs in the introduction.

Introduction:
Move from field problem to specific gap to the paper's intervention. Avoid opening with the authors' process or with a list of everything the project touches.

Methods:
Lead with the design choice, dataset, prompting regime, annotation procedure, or control. Keep implementation detail only when it affects validity or reproducibility.

Results:
Lead with the finding, then give the comparison or condition that grounds it. Keep interpretation adjacent to the evidence and calibrated to what was actually measured.

Discussion:
Interpret the result and state its supported implication directly. Add boundary conditions, exclusions, or unresolved alternatives when they materially affect interpretation, but do not automatically frame discussion around what the result "does not establish."

Limitations:
State the material limitation, then state its consequence. Avoid introducing hypothetical objections merely to disclaim them.

Technical report or whitepaper:
Separate technical evidence from positioning. State the observed capability, tested setting, operating assumptions, and decision relevance at the strength the evidence supports, without automatically adding a disclaimer about broader readiness or market demand unless that broader proposition is at issue.

Transitions:
Use transitions to make the research logic explicit. A transition should explain why the next section, experiment, or comparison follows from the previous one, not merely announce that it comes next.

## Style Corrections

Prefer concrete nouns and verbs over inflated academic filler.

Prefer explicit causal or evidential links such as "because," "therefore," "under this condition," or "consistent with" over vague transitions such as "notably" or "interestingly."

Prefer calibrated precision over reflexive modesty. Keep conditional or local conclusions conditional or local when the evidence requires it, and preserve strong conclusions when the evidence supports them.

Cut meta-commentary such as "it is worth noting," "the key thing here is," or "what we are trying to show." Replace it with the actual claim and its support.

Scan for repeated patterns such as "not X but Y," "this does not mean X," "we are not claiming X," "this does not establish X," and "rather than X, Y." Keep them only when X is already salient or the negation carries substantive technical information.
