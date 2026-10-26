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

Keep negation when an absence, exclusion, correction, counterexample, converse failure, impossibility result, or ruled-out alternative is itself part of the technical content. In argumentative registers, a position from the literature that the author's thesis is being distinguished from counts as salient.

Do not treat every `not only ... but also` construction as defensive negation. It is an additive emphasis construction and may be appropriate when both elements matter. Because repeated use can make prose formulaic, simplify it when the emphasis is unnecessary or the pattern recurs, but do not remove it solely because it contains `not`.

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

## Consistency Checks

Technical readers treat a changed term as a changed object. Run two checks on any multi-section revision and flag rather than fix what they find:

- **Term consistency.** Extract the defined terms from the methods or definitions (condition names, variable names, technique names, acronyms) and confirm the same term is used in results, discussion, tables, and captions. Do not vary a defined term to avoid repetition; a synonym for a defined term reads as a new category. Every acronym is defined at first use in the abstract, the main text, and each table or figure legend, because readers do not read linearly.
- **Number consistency.** Confirm that sample sizes, counts, and headline values agree between the abstract, the text, and the tables, that percentages match their denominators, and that figures match the table values they illustrate. The reviser never changes a number; it reports the mismatch to the author as an evidence conflict.

## Style Corrections

Prefer concrete nouns and verbs over inflated academic filler.

Prefer explicit causal or evidential links such as "because," "therefore," "under this condition," or "consistent with" over vague transitions such as "notably" or "interestingly."

Prefer calibrated precision over reflexive modesty. Keep conditional or local conclusions conditional or local when the evidence requires it, and preserve strong conclusions when the evidence supports them.

Cut meta-commentary such as "it is worth noting," "the key thing here is," or "what we are trying to show." Replace it with the actual claim and its support.

Scan for repeated defensive patterns such as "not X but Y," "this does not mean X," "we are not claiming X," "this does not establish X," and "rather than X, Y." Keep them only when X is already salient or the negation carries substantive technical information. Treat additive `not only ... but also` separately: reduce repetitive or ornamental use, not legitimate emphasis.

Scan as well for narrowing that is not negation-shaped: concessive priority clauses ("each of these has close precedents, and ..."), self-minimizing scope labels ("the claim is deliberately narrow", "in a limited, operational sense"), and the same scope restated at the opening and closing of one section. State the real scope once, as what the work covers, and remove the apology.
