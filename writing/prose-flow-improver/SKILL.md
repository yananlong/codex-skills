---
name: prose-flow-improver
description: Improve the flow, shape, and readability of existing prose while preserving substance, specificity, tone, and constraints, including default multi-agent section-level revision for substantial documents when workers are available. Use when Codex needs to make explanatory writing less choppy, less list-heavy, less fragmented, or less over-paragraphed; combine related sentences or paragraphs; add connective reasoning; use conjunctions, subordinate clauses, or participial phrasing to make relationships clearer; or turn terse notes into natural connected prose. Do not use when the content is inherently list-shaped, procedural, tabular, or governed by a stricter task-specific format.
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

Prefer combining closely related clauses with conjunctions such as "and," "but," "so," "because," or "while" when that reduces choppiness without obscuring the meaning.

Use subordinate clauses or participial phrases when they make the relation clearer and the subject remains unambiguous. Do not use them merely to sound polished, and avoid dangling or overloaded constructions.

Discourage semicolon-heavy prose. A semicolon can be acceptable in rare cases, but it should not become the default way to join rewritten ideas.

When using em dashes, put a space before and after each dash.

Expand or compress as needed. Add missing connective tissue when the reader would otherwise have to infer what happened, why it matters, what it changes, or what constraint it implies. Remove redundant framing when the prose already carries the meaning.

Keep paragraphs compact. A good default is 2 to 4 sentences per paragraph with one clear job per paragraph.

When two short sentences are really one thought, prefer one stronger sentence over two thin ones.

End with the implication when helpful. If the paragraph explains a decision, result, or concern, make clear what follows from it.

## Agent Orchestration

Default to multi-agent orchestration for substantial document-level prose-flow revision when the runtime supports subagents. Read the whole draft first, choose the target shape, then spawn one worker per planned section, paragraph range, or coherent chunk.

Use serial single-agent execution only as a fallback when subagents are unavailable, disabled, blocked by the runtime, clearly disproportionate for a short passage, or explicitly overridden by a quick single-pass request. Execute the same section plan serially and state the fallback when it matters.

The parent agent owns the full-document view. Identify the target shape, preserve global constraints, assign disjoint sections or paragraph ranges, and perform the final merge. Do not delegate final style harmonization or preservation checks.

Each worker should receive one section or range, the local rewrite goal, and any global constraints. A worker may rewrite only its assigned text and should return revised prose plus brief notes on preserved constraints, retained lists, and uncertainty. Workers must not invent facts, rewrite unrelated sections, or coordinate by modifying each other's outputs.

After worker passes complete, merge in the parent. Smooth section boundaries, remove duplicated transitions, restore any dropped constraints, ensure headings and lists still serve the document, and run the normal final pass.

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

Also check that the rewrite did not quietly delete constraints, soften strong conclusions, overuse semicolons, create dangling participial phrases, or turn concise useful content into padded prose.

## Reference

Read [references/rewrite-patterns.md](references/rewrite-patterns.md) when you need concrete before-and-after transformations, target-shape heuristics, or a tighter conversion checklist.
