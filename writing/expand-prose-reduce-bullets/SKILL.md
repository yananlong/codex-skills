---
name: expand-prose-reduce-bullets
description: Rewrite or draft responses, documents, reviews, explanations, and notes that are too list-heavy, outline-like, or terse. Use when the user asks for fewer bullet points, more natural prose, fuller paragraphs, smoother narrative flow, or when a draft feels choppy, compressed, or over-structured. Typical triggers include turning notes into paragraphs, softening bullet-heavy summaries, expanding terse explanations, and preserving substance while making writing read like connected prose.
---

# Expand Prose Reduce Bullets

## Overview

Favor paragraph-driven writing when the content is explanatory rather than enumerative. Turn choppy, list-heavy drafts into prose that connects ideas, carries transitions, and preserves specificity without padding.

## Trigger This Skill

Use this skill when the draft feels like notes instead of finished writing, or when the user explicitly asks for fewer bullets, more natural prose, smoother flow, fuller explanation, or a less outline-like response.

Common fits include assistant answers, document sections, summaries, updates, reviews, and explanation-heavy notes that already contain the right facts but need a better shape.

## Do Not Force Prose

Keep lists when the content is inherently list-shaped: steps, options, ranked findings, checklists, inputs, outputs, or field-by-field comparisons.

Convert bullets into paragraphs when the points are fragments, depend on each other, or need connective reasoning to read clearly.

If unsure, prefer two short paragraphs over a stack of thin bullets.

Do not flatten structures that exist for scanning, auditing, or side-by-side comparison. Improve the writing inside the format instead.

## Rewrite Workflow

First diagnose the draft. Identify which bullets are actual list items and which are just chopped-up sentences or adjacent parts of one idea.

Then choose the target shape. Decide whether the rewrite should become one compact paragraph, two short paragraphs, or a mixed structure with a short paragraph plus a small retained list.

Start with the main point, then carry the supporting detail in full sentences. Replace noun-phrase bullets with topic sentences that state the claim plainly.

Merge adjacent bullets that belong to the same idea. Use transitions that show relation rather than just order: cause, contrast, consequence, qualification, or emphasis.

Look for adjacent short paragraphs that are really parts of the same claim. When merging them makes the writing tighter and clearer, combine them into one stronger paragraph.

Prefer combining closely related clauses with conjunctions such as "and," "but," "so," "because," or "while" when that reduces choppiness without obscuring the meaning.

Discourage semicolon-heavy prose. A semicolon can be acceptable in rare cases, but it should not become the default way to join rewritten ideas.

Expand terse lines by adding the missing connective tissue: what happened, why it matters, what it changes, or what constraint it implies. Add substance, not filler.

Keep paragraphs compact. A good default is 2 to 4 sentences per paragraph with one clear job per paragraph.

When two short sentences are really one thought, prefer one stronger sentence over two thin ones.

End with the implication when helpful. If the paragraph explains a decision, result, or concern, make clear what follows from it.

## Calibrate to the Output

For assistant answers and explanations, prefer direct prose with a small number of short paragraphs.

For reviews, findings, or procedural guidance, keep the required structure and improve sentence quality inside it rather than forcing everything into paragraphs.

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

Also check that the rewrite did not quietly delete constraints, soften strong conclusions, overuse semicolons, or turn concise useful content into padded prose.

## Reference

Read [references/rewrite-patterns.md](references/rewrite-patterns.md) when you need concrete before-and-after transformations, target-shape heuristics, or a tighter conversion checklist.
