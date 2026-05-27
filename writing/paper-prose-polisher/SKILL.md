---
name: paper-prose-polisher
description: Revise existing academic drafts into clear, audience-facing paper prose while preserving evidence, technical meaning, uncertainty, and scope. Use when Codex needs to make a draft read like a paper rather than a lab report, memo, or internal note; convert project nicknames or internal nomenclature into reader-facing terminology; sharpen contribution framing without inventing novelty; or rewrite methods, results, limitations, and discussion prose for an academic audience. Do not use when the main task is paper planning, citation work, novelty review, or experiment design.
---

# Paper Prose Polisher

## Overview

Revise existing research text so an outside reader can understand the claim, method, result, or limitation without learning the lab's internal shorthand first. Prefer paper-style prose that states what matters, what supports it, and what the reader should conclude, while keeping the original evidential limits intact.

## Default Output

Return polished prose first unless the user asks for diagnosis, markup, or alternatives. Keep commentary brief: include only important uncertainty notes, terminology questions, or places where the evidence does not support a stronger rewrite.

When the source is fragmentary, preserve the author's meaning and produce the most coherent paper-style version possible. Do not add invented transitions, citations, results, or motivation to make the passage feel complete.

## Keep the Scope Narrow

Treat this skill as a revision skill, not a paper-planning skill. Improve wording, terminology, sentence shape, paragraph logic, and contribution framing, but do not invent citations, experiments, metrics, claims, baselines, novelty, or venue-specific requirements.

Preserve numbers, methods, caveats, uncertainty, and negative results. If the draft is weak because the evidence is missing, say so plainly instead of polishing it into a stronger claim than the source supports.

Use `research-paper-plan` when the real need is manuscript structure, claim-to-evidence mapping, or figure planning. Use `research-paper-review` or `research-review-loop` when the real need is critique. Use `research-novelty-review` when the real need is positioning against prior work. Use `expand-prose-reduce-bullets` alongside this skill when the draft is also too list-heavy or note-like.

## Calibrate the Revision

Choose the lightest revision that solves the problem. If the draft is already paper-like, preserve sentence order and mainly tighten phrasing. If it reads like a lab note, restructure paragraphs around claim, method, evidence, and consequence. If it is a pile of fragments, build coherent paragraphs but flag missing support instead of hiding gaps.

Preserve authorial commitments. A rewrite may clarify "we test," "we find," or "we argue," but should not turn a preliminary observation into a result, a result into a mechanism, or a mechanism into a general theory.

## Rewrite Workflow

First identify the job of the passage: motivation, contribution framing, methods, results, discussion, limitation, or transition. Rewrite toward the expectations of that section instead of applying one generic "academic tone" everywhere.

Then mark any internal language that will confuse an outside reader on first pass: project nicknames, code names, lab shorthand, implementation labels, and locally meaningful terms. Replace them with reader-facing terminology when the mapping is obvious, and preserve the meaning rather than the local wording.

Next identify the support level of each sentence. Separate what the text actually shows from why it matters, and keep that boundary visible in the rewrite. Prefer explicit qualifiers over overstated certainty.

Finally tighten the prose into paper form. Replace lab-log narration, memo phrasing, and procedural diary language with sentences that foreground the research object, method, evidence, or implication. Make paragraphs do one clear job each and end with the practical inference when that helps the reader.

Read [references/claim-discipline.md](references/claim-discipline.md) when the draft mixes claims, interpretation, speculation, and missing evidence.

## Handle Terminology Carefully

Translate internal names only when the mapping is safe. A project nickname like "micro-archive" may become "a compact curated archive" if the meaning is clear from context. An implementation label like "control bucket B" may become "the stricter control condition" if the distinction is explicit in the source.

When the intended meaning is uncertain, do not guess. Keep the original term, add a short neutral gloss if one is supported by the text, and ask for a terminology map or glossary. A wrong translation is worse than a visible internal label because it silently changes the claim.

Read [references/terminology-conversion.md](references/terminology-conversion.md) when the draft contains project-internal names, shorthand, or audience-hostile labels.

## Rewrite Toward Paper Prose

Prefer motivation over scene-setting, method over chronology, result over observation log, and limitation over apology. Replace sentences that narrate what the authors did in time order with sentences that explain what was done and why that choice matters.

Keep contribution framing modest and specific. State the paper's contribution as what it provides, clarifies, tests, measures, or argues, not as a sweeping claim about the whole field unless the evidence really supports that scope.

Use section-appropriate prose. Methods should foreground design choices, controls, data, and procedures. Results should foreground findings and their evidential limits. Discussion should interpret findings without quietly upgrading them. Limitations should state the constraint and its consequence.

Read [references/paper-prose-patterns.md](references/paper-prose-patterns.md) when the draft reads like a lab report, project memo, or internal research note. Read [references/rewrite-examples.md](references/rewrite-examples.md) when a concrete before-and-after pattern will help.

## Final Pass

Check that the rewrite still says exactly what the source can support, no more and no less. Make sure internal labels are either translated cleanly or left visible with a note of uncertainty.

Check that each paragraph has a single center and that the prose sounds like a paper written for informed outsiders rather than a note written for teammates. Leave the draft more legible and more publishable, but never more certain than the evidence allows.
