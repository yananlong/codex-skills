---
name: technical-writing-reviser
description: Revise existing technical writing into clear, audience-facing prose while preserving evidence, technical meaning, uncertainty, and scope. Use for academic manuscripts, industrial technical reports, whitepapers, evaluation summaries, methods/results/limitations prose, technical claims, contribution or decision framing, and terminology conversion from internal shorthand to reader-facing language. Use after critique from research-paper-review or research-review-loop when the task is to revise the artifact's prose and claims, not to re-review it. Do not use when the main task is generic prose flow, citation work, paper planning, novelty review, experiment design, market strategy, or writing unsupported claims.
---

# Technical Writing Reviser

## Overview

Revise existing technical text so an outside reader can understand the claim, method, result, limitation, design decision, or technical implication without first learning the author's internal shorthand. Prefer reader-facing technical prose that states what matters, what supports it, and what the reader should conclude, while keeping the original evidential and scope limits intact.

## Default Output

Return revised prose first unless the user asks for diagnosis, markup, or alternatives. Keep commentary brief: include only important uncertainty notes, terminology questions, or places where the evidence does not support a stronger rewrite.

When the source is fragmentary, preserve the author's meaning and produce the most coherent technical version possible. Do not add invented transitions, citations, results, metrics, product claims, deployment facts, or motivation to make the passage feel complete.

## Keep the Scope Narrow

Treat this skill as a revision skill, not a planning, review, or evidence-generation skill. Improve wording, terminology, sentence shape, paragraph logic, claim framing, and limitation language, but do not invent citations, experiments, metrics, benchmarks, customer evidence, deployment details, product capabilities, novelty, or venue-specific requirements.

Preserve numbers, methods, caveats, uncertainty, and negative results. If the draft is weak because the evidence is missing, say so plainly instead of polishing it into a stronger claim than the source supports.

Use `research-paper-plan` when the real need is manuscript structure, claim-to-evidence mapping, or figure planning. Use `research-paper-review` or `research-review-loop` when the real need is critique. Use `research-novelty-review` when the real need is positioning against prior work. Use `commercialize-academic-research` when the real need is buyer, budget, or commercialization analysis. Use `prose-flow-improver` alongside this skill when the draft is also too choppy, list-heavy, or note-like.

## Calibrate the Revision

Choose the lightest revision that solves the problem. If the draft is already reader-facing technical prose, preserve sentence order and mainly tighten phrasing. If it reads like a lab note, engineering memo, internal status update, or sales-adjacent whitepaper draft, restructure paragraphs around claim, method, evidence, consequence, and limitation. If it is a pile of fragments, build coherent paragraphs but flag missing support instead of hiding gaps.

Preserve authorial commitments. A rewrite may clarify "we test," "we find," "we argue," "the report shows," or "the system supports," but should not turn a preliminary observation into a result, a result into a mechanism, a prototype into a production capability, or a local finding into a general market or field-wide claim.

## Rewrite Workflow

First identify the job of the passage: motivation, technical background, contribution framing, method, implementation summary, evaluation result, operational finding, recommendation, discussion, limitation, or transition. Rewrite toward the expectations of that section instead of applying one generic "technical tone" everywhere.

Then mark any internal language that will confuse an outside reader on first pass: project nicknames, code names, lab shorthand, implementation labels, and locally meaningful terms. Replace them with reader-facing terminology when the mapping is obvious, and preserve the meaning rather than the local wording.

Next identify the support level of each sentence. Separate what the text actually shows from why it matters, and keep that boundary visible in the rewrite. Prefer explicit qualifiers over overstated certainty.

Finally tighten the prose into reader-facing technical form. Replace lab-log narration, internal memo phrasing, procedural diary language, and unsupported promotional language with sentences that foreground the technical object, method, evidence, result, decision, limitation, or implication. Make paragraphs do one clear job each and end with the practical inference when that helps the reader.

Read [references/claim-discipline.md](references/claim-discipline.md) when the draft mixes claims, interpretation, speculation, and missing evidence.

## Handle Terminology Carefully

Translate internal names only when the mapping is safe. A project nickname like "micro-archive" may become "a compact curated archive" if the meaning is clear from context. An implementation label like "control bucket B" may become "the stricter control condition" if the distinction is explicit in the source. A product or deployment label may become a neutral technical description only when the source supports that description.

When the intended meaning is uncertain, do not guess. Keep the original term, add a short neutral gloss if one is supported by the text, and ask for a terminology map or glossary. A wrong translation is worse than a visible internal label because it silently changes the claim.

Read [references/terminology-conversion.md](references/terminology-conversion.md) when the draft contains project-internal names, shorthand, or audience-hostile labels.

## Rewrite Toward Technical Prose

Prefer motivation over scene-setting, method or design over chronology, result over observation log, and limitation over apology. Replace sentences that narrate what the authors or team did in time order with sentences that explain what was done and why that choice matters.

Keep contribution and value framing modest and specific. State the artifact's contribution as what it provides, clarifies, tests, measures, supports, or argues, not as a sweeping claim about a field, market, product category, or deployment environment unless the evidence really supports that scope.

Use section-appropriate prose. Methods and technical approach sections should foreground design choices, controls, data, assumptions, architecture, and procedures. Results and evaluation sections should foreground findings and their evidential limits. Reports and whitepapers should distinguish measured behavior from interpretation, recommendation, and positioning. Limitations should state the constraint and its consequence.

Read [references/technical-writing-patterns.md](references/technical-writing-patterns.md) when the draft reads like a lab report, project memo, internal research note, engineering status update, or under-supported whitepaper. Read [references/rewrite-examples.md](references/rewrite-examples.md) when a concrete before-and-after pattern will help.

## Final Pass

Check that the rewrite still says exactly what the source can support, no more and no less. Make sure internal labels are either translated cleanly or left visible with a note of uncertainty.

Check that each paragraph has a single center and that the prose sounds like technical writing for informed outsiders rather than a note written for teammates or a claim written for persuasion without support. Leave the draft more legible and more credible, but never more certain than the evidence allows.
