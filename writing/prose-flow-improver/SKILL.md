---
name: prose-flow-improver
description: Improve the flow, shape, and readability of existing prose while preserving substance, specificity, tone, and constraints, including planned multi-agent section, paragraph-range, or chunk-level revision for substantial documents when workers are available. Use when Codex needs to make explanatory writing less choppy, less list-heavy, less fragmented, or less over-paragraphed; combine related sentences or paragraphs aggressively but readably; add connective reasoning; favor conjunctions, relative clauses, subordinate clauses, and clean participial phrasing over semicolons; or turn terse notes into natural connected prose. Do not use when the content is inherently list-shaped, procedural, tabular, or governed by a stricter task-specific format.
---

# Prose Flow Improver

## Overview

Improve explanatory prose so it reads as connected writing rather than fragments, notes, or unnecessarily split paragraphs. Use sentence and paragraph structure to show relationships among ideas while preserving the original substance, specificity, and level of certainty.

## Trigger This Skill

Use this skill when the draft feels choppy, over-segmented, list-heavy, under-connected, or note-like, or when the user explicitly asks for smoother flow, fewer short sentences, fewer paragraphs, fewer bullets, fuller explanation, or more natural connected prose.

Common fits include assistant answers, document sections, summaries, updates, reviews, and explanation-heavy notes that already contain the right facts but need a better shape.

## Do Not Force Prose

Keep lists when the content is inherently list-shaped: steps, options, ranked findings, checklists, inputs, outputs, or field-by-field comparisons.

Convert bullets into paragraphs when the points are fragments, depend on each other, or need connective reasoning to read clearly.

If unsure, prefer two short paragraphs over a stack of thin bullets.

Do not flatten structures that exist for scanning, auditing, or side-by-side comparison. Improve the writing inside the format instead.

## Rewrite Workflow

First diagnose the draft. Identify which bullets, sentences, or paragraphs are actual independent units and which are chopped-up parts of one idea.

Then choose the target shape. Decide whether the rewrite should become one compact paragraph, two short paragraphs, or a mixed structure with a short paragraph plus a small retained list.

Start with the main point, then carry the supporting detail in full sentences. Replace noun-phrase bullets with topic sentences that state the claim plainly.

Merge adjacent bullets, sentences, or paragraphs that belong to the same idea. Use transitions that show relation rather than just order: cause, contrast, consequence, qualification, or emphasis.

Look for adjacent short paragraphs that are really parts of the same claim. When merging them makes the writing tighter and clearer, combine them into one stronger paragraph.

Treat tight prose as permission to join closely related sentences aggressively when doing so improves rhythm, reduces repetition, or makes relationships clearer. Prefer conjunctions, relative clauses, appositives, and clean subordination over a sequence of short, separate sentences.

Lean toward relative pronouns such as "that," "which," and "who" when they let the rewrite attach context, constraints, or consequences directly to the noun they modify. Combine clauses when they belong to the same thought and the resulting sentence remains easy to read. Keep a short sentence only when it gives useful emphasis, prevents overload, or marks a real shift in idea.

Use subordinate clauses or participial phrases when they make the relation clearer and the subject remains unambiguous. Participial phrases should genuinely compress the sentence without creating dangling modifiers, unclear subjects, or a mannered style.

Avoid semicolons by default. Use one only when it is clearly cleaner than a period, conjunction, relative clause, or subordinate clause, and do not use semicolons as the main mechanism for tightening prose.

When using em dashes, put a space before and after each dash.

Expand or compress as needed. Add missing connective tissue when the reader would otherwise have to infer what happened, why it matters, what it changes, or what constraint it implies. Remove redundant framing when the prose already carries the meaning.

Keep paragraphs compact. A good default is 2 to 4 sentences per paragraph with one clear job per paragraph.

When two short sentences are really one thought, prefer one stronger sentence over two thin ones.

End with the implication when helpful. If the paragraph explains a decision, result, or concern, make clear what follows from it.

## Agent Orchestration

Default to multi-agent orchestration for substantial document-level prose-flow revision when the runtime supports subagents. Use it when the artifact has multiple sections, repeated transitions, uneven paragraphing, many list-to-prose conversions, or enough length that local smoothing could create inconsistent shape or tone. Use a quick single-pass rewrite for short passages, isolated paragraphs, or low-risk assistant answers.

Use serial single-agent execution only when subagents are unavailable, disabled, blocked by the runtime, clearly disproportionate for the artifact, or explicitly overridden by a quick request. Execute the same shape plan serially and state the fallback when it matters.

### Parent Shape Brief Before Workers

The parent agent owns the full-document view. Before assigning work, read the whole draft or enough surrounding context to identify the target reader, purpose, required format, tone, facts and constraints that must survive revision, and any structures that should remain list-shaped.

Build a short shape brief before launching workers. Include:

- Target shape: compact paragraph, two-paragraph explanation, mixed paragraph-plus-list, retained list, or sectioned prose.
- Global tone and level of formality.
- Facts, caveats, filenames, commands, numbers, examples, and constraints that must not be dropped.
- Lists, headings, tables, or procedural structures that should remain intact.
- Sentence-shape preference, including aggressive but readable joining, relative clauses, and minimal semicolon use.
- Boundaries where the draft should keep a short sentence for emphasis or a real shift in idea.

Do not launch workers until the shape brief is clear enough that local rewrites will not fight the document's intended form.

### 3-7 Pass Flow Plan

Build a concrete 3-7 pass plan before spawning or running workers:

- 2-5 section, paragraph-range, or coherent-chunk passes that cover the main body.
- 1-2 cross-cutting passes for transitions, paragraph boundaries, retained list quality, repetition, or sentence rhythm.

Group tightly coupled paragraphs rather than splitting one argument across workers. Do not assign a worker a range whose opening or closing sentence depends heavily on an unassigned neighbor unless the prompt includes that neighbor as read-only context.

Each pass plan entry should include:

- `pass_id`
- `kind` (`section`, `paragraph_range`, `chunk`, or `cross_cutting`)
- assigned source text or file/line range
- read-only neighboring context when needed
- one-sentence flow goal
- structures to retain, merge, or convert
- likely failure modes to avoid
- owned draft output target when workers can write files

### Disjoint Worker Ownership And Owned Draft Outputs

Use one worker per planned pass when workers are available. Worker ownership must be disjoint: a worker rewrites only its assigned text and writes only to its owned draft output target when files are involved. Workers should draft revised prose, not directly edit the canonical document, unless the parent explicitly assigns a non-overlapping file or range and the environment can prevent conflicts.

### Worker Prompt Requirements For Facts, Constraints, Lists, And Context

Each worker prompt should:

- State that the worker is not alone in the workspace.
- State the worker's assigned scope and owned output target.
- State that the worker must not edit shared files or other workers' outputs.
- Provide the shape brief, local flow goal, required retained facts, and any read-only neighboring context.
- Require revised prose plus brief notes on retained constraints, converted or retained lists, merged paragraphs, and any uncertainty.
- Require an empty but explicit result if no safe flow improvement is possible.

Workers must not invent facts, add unsupported motivation, rewrite unrelated sections, delete constraints for smoothness, or coordinate by modifying each other's outputs. They may keep a list, heading, or short sentence when converting it would harm scanning, emphasis, or accuracy.

### Parent-Only Merge And Rhythm Audit

While workers run, the parent should do non-overlapping work only: check source coverage, refine merge criteria, inspect global constraints, or prepare the final document structure. Do not redo a worker's assigned pass before reviewing its output.

After all passes complete, merge in the parent. Smooth section boundaries, remove duplicated transitions, restore any dropped constraints, ensure headings and lists still serve the document, and harmonize paragraph density, sentence rhythm, tone, and joining style across the full artifact.

Run a final rhythm and preservation audit after merging:

- Check that the rewrite did not drop concrete facts, caveats, examples, filenames, commands, numbers, or constraints.
- Check that neighboring paragraphs have distinct jobs, and merge them when they are really one thought.
- Check that joined sentences remain readable, have clear subjects, and do not bury the main point.
- Check that relative clauses and participial phrases clarify relationships rather than creating compression for its own sake.
- Check that semicolons are rare and not the main tightening mechanism.
- Check that retained lists are genuinely easier to scan than prose.

If the revision is file-based, preserve the user's requested output format and avoid generating a parallel report unless requested. If brief notes are useful, keep them focused on retained structures, unresolved ambiguity, and places where flow could not be improved without changing substance.

## Calibrate to the Output

For assistant answers and explanations, prefer direct prose with a small number of short paragraphs.

For reviews, findings, or procedural guidance, keep the required structure and improve sentence quality inside it rather than forcing everything into paragraphs.

For technical or academic artifacts, use this skill for flow and sentence shape only. Use `technical-writing-reviser` when the task also requires claim discipline, technical terminology conversion, or evidence-aware revision.

For user-provided drafts, preserve the author's intent, level of formality, and technical precision unless the user asks for a stronger tonal change.

## Preserve Signal

Keep concrete nouns, exact constraints, filenames, commands, numbers, and caveats. Make the prose fuller without blurring technical precision.

Retain headings when they help scanning, but avoid turning every thought into its own bullet.

Use lists sparingly and flatly when they genuinely improve comprehension. When a list remains necessary, write each item as a complete sentence rather than a fragment.

## Respect Higher-Priority Formats

Do not override task-specific formatting requirements. If the user or system requires enumerated findings, procedural steps, checklists, tables, or strict templates, keep that structure and improve sentence quality within it.

Do not force prose onto content that would become harder to scan or compare.

## Final Pass

Read the draft once for structure and once for tone.

On the structure pass, remove redundant bullets, combine related points, and ensure each paragraph has a clear center.

Also merge neighboring paragraphs when they do not carry distinct jobs and read better as one unit.

On the tone pass, cut filler, repeated framing, and generic transitions. Keep the prose direct, specific, and calm.

Also check that the rewrite did not quietly delete constraints, soften strong conclusions, overuse semicolons, create dangling participial phrases, bury the main claim in an overloaded sentence, or turn concise useful content into padded prose.

## Reference

Read [references/rewrite-patterns.md](references/rewrite-patterns.md) when you need concrete before-and-after transformations, target-shape heuristics, or a tighter conversion checklist.
