---
name: technical-writing-reviser
description: Revise existing technical writing into clear, audience-facing prose while preserving evidence, technical meaning, uncertainty, and scope, including planned multi-agent section or issue-cluster revision for substantial artifacts when workers are available. Use for academic manuscripts, industrial technical reports, whitepapers, evaluation summaries, methods/results/limitations prose, technical claims, contribution or decision framing, and terminology conversion from internal shorthand to reader-facing language. Use after critique from research-paper-review or research-review-loop when the task is to revise the artifact's prose and claims, not to re-review it. Do not use when the main task is generic prose flow, citation work, paper planning, novelty review, experiment design, market strategy, or writing unsupported claims.
---

# Technical Writing Reviser

## Overview

Revise existing technical text so an outside reader can understand the claim, method, result, limitation, design decision, or technical implication without first learning the author's internal shorthand. Prefer reader-facing technical prose that states what matters, what supports it, and what the reader should conclude, while keeping the original evidential and scope limits intact.

## Default Output

Return revised prose first unless the user asks for diagnosis, markup, or alternatives. Keep commentary brief: include only important terminology questions or evidence mismatches that materially affect the revision. Do not add disclaimers merely because a stronger claim could be imagined.

When the source is fragmentary, preserve the author's meaning and produce the most coherent technical version possible. Do not add invented transitions, citations, results, metrics, product claims, deployment facts, or motivation to make the passage feel complete.

## Keep the Scope Narrow

Treat this skill as a revision skill, not a planning, review, or evidence-generation skill. Improve wording, terminology, sentence shape, paragraph logic, claim framing, and limitation language, but do not invent citations, experiments, metrics, benchmarks, customer evidence, deployment details, product capabilities, novelty, or venue-specific requirements.

Preserve numbers, methods, caveats, uncertainty, negative results, and justified confidence. If a source claim exceeds its available support, weaken or flag that specific claim, but do not turn every bounded claim into a disclaimer about a stronger proposition the source never made.

Use `research-paper-plan` when the real need is manuscript structure, claim-to-evidence mapping, or figure planning. Use `research-paper-review` or `research-review-loop` when the real need is critique. Use `research-novelty-review` when the real need is positioning against prior work. Use `commercialize-academic-research` when the real need is buyer, budget, or commercialization analysis. Use `prose-flow-improver` alongside this skill when the draft is also too choppy, list-heavy, or note-like.

## Calibrate the Revision

Choose the lightest revision that solves the problem. If the draft is already reader-facing technical prose, preserve sentence order and mainly tighten phrasing. If it reads like a lab note, engineering memo, internal status update, or sales-adjacent whitepaper draft, restructure paragraphs around claim, method, evidence, consequence, and limitation. If it is a pile of fragments, build coherent paragraphs but flag missing support only when the gap materially affects what the passage can claim.

Preserve authorial commitments and justified confidence. A rewrite may clarify "we test," "we find," "we argue," "the report shows," or "the system supports," but should not turn a preliminary observation into a result, a result into a mechanism, a prototype into a production capability, or a local finding into a general market or field-wide claim. Likewise, do not lower a supported claim merely because a more ambitious unsupported claim is conceivable.

## Rewrite Workflow

First identify the job of the passage: motivation, technical background, contribution framing, method, implementation summary, evaluation result, operational finding, recommendation, discussion, limitation, or transition. Rewrite toward the expectations of that section instead of applying one generic "technical tone" everywhere.

Then mark any internal language that will confuse an outside reader on first pass: project nicknames, code names, lab shorthand, implementation labels, and locally meaningful terms. Replace them with reader-facing terminology when the mapping is obvious, and preserve the meaning rather than the local wording.

Next identify the support level of each sentence. Separate what the text actually shows from why it matters, and keep that boundary visible in the rewrite. Use qualifiers when they are needed to keep a claim within the source's support, but do not add precautionary qualification to claims that are already appropriately scoped.

Finally tighten the prose into reader-facing technical form. Replace lab-log narration, internal memo phrasing, procedural diary language, and unsupported promotional language with sentences that foreground the technical object, method, evidence, result, decision, limitation, or implication. Join closely related sentences aggressively when a conjunction, relative clause, appositive, or subordinate clause can make the technical relationship clearer without changing the claim. Lean toward relative pronouns such as "that," "which," and "who" when they attach constraints, assumptions, mechanisms, or consequences to the specific technical object they modify. Make paragraphs do one clear job each and end with the practical inference when that helps the reader.

### Prefer Direct Positive Framing

State the supported proposition directly instead of first denying an adjacent stronger, weaker, or mistaken proposition. Do not invent a rejected interpretation merely to distinguish the author's actual claim from it.

Rewrite constructions such as "X is not A. X is B," "the point is not A but B," "this does not mean A," "we are not claiming A," "rather than A, this shows B," and "not merely A but B" as direct affirmative statements when A is not already salient in the source or necessary to the argument.

Use corrective negation only when the source is explicitly correcting a misconception, distinguishing genuinely confusable concepts, reporting an absence or exclusion that is itself a technical fact, answering a live objection, or ruling out an alternative explanation. When the rejected proposition is doing no real argumentative work, lead with the supported proposition and omit the invented contrast.

Do not manufacture caution by naming claims the author supposedly is not making. Preserve genuine qualifications, but express the intended claim positively whenever its evidential boundary can be conveyed through precise scope, conditions, nouns, and verbs.

Read [references/claim-discipline.md](references/claim-discipline.md) when the draft mixes claims, interpretation, speculation, and missing evidence.

## Agent Orchestration

Default to multi-agent orchestration for substantial document-level technical revision when the runtime supports subagents. Use it when the artifact has multiple sections, repeated terminology, high claim-risk, reviewer comments, or enough length that local edits could create inconsistent voice or scope. Use a quick single-pass rewrite for short passages, isolated paragraphs, or low-risk copy.

Use serial single-agent execution only when subagents are unavailable, disabled, blocked by the runtime, clearly disproportionate for the artifact, or explicitly overridden by a quick request. Execute the same revision plan serially and state the fallback when it matters.

### Parent Brief Before Workers

The parent agent owns the global technical interpretation. Before assigning work, read the full artifact or enough surrounding context to identify the audience, purpose, stakes, terminology, claim boundaries, evidence limits, and any critique artifacts from `research-paper-review`, `research-review-loop`, or `adversarial-doc-review`.

Build a short revision brief before launching workers. Include:

- Audience and intended section role.
- Document-level thesis, contribution, decision, or recommendation.
- Key claims with source locations and support level.
- Important caveats, negative results, uncertainty, scope limits, and justified confidence that must survive revision.
- Terminology map for internal labels, symbols, acronyms, product names, and reader-facing replacements.
- Known critique items or reviewer issues to resolve.
- Claims that genuinely require verification when verification is part of the task.

Do not launch section workers until the brief is strong enough that another agent can revise locally without guessing the document's global meaning.

### Revision Pass Plan

Build a concrete pass plan before spawning or running workers. For a substantial document, aim for 4-8 passes:

- 2-6 section or claim-cluster passes that cover the document's major sections, logical units, or reviewer-issue clusters.
- 1-3 cross-cutting passes for claim discipline, terminology consistency, reader-facing flow, limitation language, notation, or evidence-to-conclusion fit.

Group small or tightly coupled sections rather than creating trivial one-paragraph passes. Choose cross-cutting passes from the artifact's actual risks; do not run generic style passes that have no claim or reader-value target.

Each pass plan entry should include:

- `pass_id`
- `kind` (`section`, `issue_cluster`, or `cross_cutting`)
- assigned source text or file/line range
- relevant critique, evidence, or caveat notes
- one-sentence revision goal
- likely failure modes to avoid
- owned draft output target when workers can write files

### Worker Execution

Use one worker per planned pass when workers are available. Worker ownership must be disjoint: a worker revises only its assigned text or issue cluster and writes only to its owned output target when files are involved. Workers should draft revised prose, not directly edit the canonical document, unless the parent explicitly assigns a non-overlapping file or range and the environment can prevent conflicts.

Each worker prompt should:

- State that the worker is not alone in the workspace.
- State the worker's assigned scope and owned output target.
- State that the worker must not edit shared files or other workers' outputs.
- Provide the revision brief, audience, terminology map, claim constraints, and relevant critique notes.
- Require revised prose plus brief notes on any material claim-strength changes, preserved caveats, unresolved terminology, and missing support.
- Require an empty but explicit result if no safe revision is possible.

Workers must not invent citations, experiments, metrics, deployment facts, product claims, mechanisms, generalizations, or cross-section commitments. They may weaken a claim only when that claim exceeds the supplied support, and they must not introduce a stronger rejected alternative merely to disclaim it.

### Parent Merge And Audit

While workers run, the parent should do non-overlapping work only: check source coverage, refine merge criteria, inspect critique artifacts, or prepare the final document structure. Do not redo a worker's assigned pass before reviewing its output.

After all passes complete, merge in the parent. The parent must harmonize terminology, claim strength, tense, notation, contribution framing, limitation language, section transitions, and sentence rhythm across the whole artifact. Prefer the clearest supported rewrite over the most polished local sentence when those conflict, while preserving the source's justified confidence.

Run an adversarial final audit after merging:

- Check that every strengthened sentence is supported by the source, critique artifacts, or provided evidence.
- Restore any source caveat, negative result, uncertainty, baseline condition, or scope limit that a local rewrite softened.
- Check for definitional drift, inconsistent terminology, unsupported causal language, and conclusions that no longer follow from the revised paragraph.
- Verify that cross-section transitions do not imply evidence, chronology, deployment status, or novelty that the source did not establish.
- Scan for corrective negation, anticipatory disclaimers, and objection-answering language that the source did not motivate. For each occurrence, ask whether the rejected interpretation is already salient or materially necessary. If not, delete the rejected proposition and state the supported proposition directly.
- Do not label source claims "unverified" merely because they are externally checkable. Verification belongs to a review or fact-checking task unless the user explicitly requested it as part of revision.

If the revision is file-based, preserve the user's requested output format and avoid generating a parallel report unless requested. If brief notes are useful, keep them focused on evidence gaps or terminology uncertainties that materially constrain the rewrite.

## Handle Terminology Carefully

Translate internal names only when the mapping is safe. A project nickname like "micro-archive" may become "a compact curated archive" if the meaning is clear from context. An implementation label like "control bucket B" may become "the stricter control condition" if the distinction is explicit in the source. A product or deployment label may become a neutral technical description only when the source supports that description.

When the intended meaning is uncertain, do not guess. Keep the original term, add a short neutral gloss if one is supported by the text, and ask for a terminology map or glossary. A wrong translation is worse than a visible internal label because it silently changes the claim.

Read [references/terminology-conversion.md](references/terminology-conversion.md) when the draft contains project-internal names, shorthand, or audience-hostile labels.

## Rewrite Toward Technical Prose

Prefer motivation over scene-setting, method or design over chronology, result over observation log, and limitation over apology. Replace sentences that narrate what the authors or team did in time order with sentences that explain what was done and why that choice matters.

Keep contribution and value framing specific and proportional to the evidence. State the artifact's contribution as what it provides, clarifies, tests, measures, supports, or argues, and preserve stronger framing when the source supports it rather than weakening it by default.

Use section-appropriate prose. Methods and technical approach sections should foreground design choices, controls, data, assumptions, architecture, and procedures. Results and evaluation sections should foreground findings at the scope supported by the evidence. Reports and whitepapers should distinguish measured behavior from interpretation, recommendation, and positioning. Limitations should state material constraints and their consequences without adding hypothetical objections.

Read [references/technical-writing-patterns.md](references/technical-writing-patterns.md) when the draft reads like a lab report, project memo, internal research note, engineering status update, or under-supported whitepaper. Read [references/rewrite-examples.md](references/rewrite-examples.md) when a concrete before-and-after pattern will help.

## Final Pass

Check that the rewrite still says exactly what the source can support and preserves the source's supported strength. Make sure internal labels are either translated cleanly or left visible with a note of uncertainty.

Check that each paragraph has a single center and that the prose sounds like technical writing for informed outsiders rather than a note written for teammates or a claim written for persuasion without support. Avoid semicolons by default, using one only when it is cleaner than a period, conjunction, relative clause, or subordinate clause. Leave the draft more legible and more credible without making it either more or less certain than the evidence warrants.
