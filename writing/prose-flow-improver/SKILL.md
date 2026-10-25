---
name: prose-flow-improver
description: Improve the flow, shape, and readability of existing prose while preserving substance, specificity, tone, and constraints, including planned multi-agent section, paragraph-range, or chunk-level revision for substantial documents when workers are available. Use when the agent needs to make explanatory writing less choppy, less list-heavy, less fragmented, or less over-paragraphed; combine related sentences or paragraphs aggressively but readably; add connective reasoning; favor conjunctions, relative clauses, subordinate clauses, and clean participial phrasing over semicolons; or turn terse notes into natural connected prose. Do not use when the content is inherently list-shaped, procedural, tabular, or governed by a stricter task-specific format, and do not use it alone when the task also changes claims, evidence framing, or technical terminology (run technical-writing-reviser first).
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

Avoid em dashes by default as well. They are the most recognizable habit of model-written prose. The dash policy is stated once, in `technical-writing-drafter/references/drafting-contract.md`: a comma for an aside, a period for a new thought, parentheses for a true parenthetical, a colon for one specification, and where a dash is the only mark that can hold an interruption, one pair per page at most (`---` in LaTeX).

Expand or compress as needed. Add missing connective tissue when the reader would otherwise have to infer what happened, why it matters, what it changes, or what constraint it implies. Remove redundant framing when the prose already carries the meaning.

Give each paragraph one clear job and let its length follow that job. Paragraphs of identical length and identical shape (topic sentence, two supports, implication) read as tiled machine prose; a one-sentence paragraph and a long one are both fine when the content has that shape.

When two short sentences are really one thought, prefer one stronger sentence over two thin ones. Keep a short sentence when it carries one fact; vary the rhythm rather than levelling it.

End a paragraph on its evidence or on the consequence the reader needs. Do not end every paragraph with an implication, and do not close with a short sentence that lands a point; a flourish at the end of each paragraph is a tell, not a style.

### Machine-Prose Tells

Smoothing prose must not introduce the habits that make text read as model-written: em dashes as the default joint, deny-then-claim contrasts ("not X but Y"), signpost adverbs (Importantly, Notably), significance adjectives (crucial, robust, nuanced), participial tails that announce importance (", highlighting the need for"), tricolons where the content has two items, summary chains ("This means", "This suggests"), and paragraph kickers. A flow pass that joins sentences with these devices has made the text worse while making it smoother. When `technical-writing-reviser` is installed beside this skill, run its `scripts/prose_tells.py` on the source and the revision (`--baseline <source> --fail-if-worse`) and read its `references/machine-prose-tells.md` for the recipe behind each tell. Without it, apply the list in `references/rewrite-patterns.md`.

## Agent Orchestration

Default to a serial single-agent pass whenever the whole artifact fits comfortably in context, which covers a conference paper or a long report of up to roughly thirty pages. A serial pass still builds the shape brief below and still runs the preservation audit on its own output. Fan out to workers only for longer artifacts, for several independent documents, or when the user asks for parallel revision. If this skill is itself running inside a subagent, run serially.

When workers are used, keep the plan small: at most one worker per major section or coherent chunk, and any cross-cutting pass (transitions, repetition, rhythm) is comment-only, returning findings to the parent and never editing text, so ownership stays disjoint. When `technical-writing-reviser` also applies, this skill is one serial final pass counted in the reviser's budget, and its connective rules bind the reviser's workers; there is never a second orchestration. Only the skill the user invoked spawns workers and sets the chain's budget (quick 1, standard up to 3, deep 5 to 8); reached by handoff, this skill never spawns.

### Parent Shape Brief Before Workers

The parent agent owns the full-document view. Before assigning work, read the whole draft or enough surrounding context to identify the target reader, purpose, required format, tone, facts and constraints that must survive revision, and any structures that should remain list-shaped.

Build a short shape brief before launching workers. Include:

- Target shape: compact paragraph, two-paragraph explanation, mixed paragraph-plus-list, retained list, or sectioned prose.
- Global tone and level of formality.
- Facts, caveats, filenames, commands, numbers, examples, and constraints that must not be dropped.
- Lists, headings, tables, or procedural structures that should remain intact.
- Sentence-shape preference, including aggressive but readable joining, relative clauses, and minimal semicolon use.
- Boundaries where the draft should keep a short sentence for emphasis or a real shift in idea.
- Any length or page budget, and what the budget may not cut (facts, caveats, numbers, constraints); "expand" below is bounded by it.

Do not launch workers until the shape brief is clear enough that local rewrites will not fight the document's intended form.

### Flow Pass Plan

Build a concrete pass plan before spawning or running workers:

- one section, paragraph-range, or coherent-chunk pass per major unit of the main body;
- at most one comment-only cross-cutting pass for transitions, paragraph boundaries, retained list quality, repetition, or sentence rhythm, and only when the parent's merge audit would not cover it.

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

- State that the worker writes only to its assigned output and that the parent alone edits the source.
- State the worker's assigned scope and owned output target.
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

This skill never writes the first draft of reader-facing prose. First drafts are written by `technical-writing-drafter` under its `references/drafting-contract.md`, or by the skill that owns the content applying that contract, and this skill runs after, as a constrained pass. For technical or academic artifacts, use this skill for flow and sentence shape only. Use `technical-writing-reviser` when the task also requires claim discipline, technical terminology conversion, or evidence-aware revision. When both apply, the reviser runs first and this skill is a constrained final pass that may not change which relation a connective asserts.

For marked-up sources, preserve the format as well as the words. In LaTeX, never join a line that ends in an unescaped `%` comment with the following line, keep every macro, citation key, label, and cross-reference byte-identical and attached to the same clause, do not edit inside math or comments, and compare the visible text before and after. In Markdown, preserve code spans, links, and footnote markers.

For user-provided drafts, preserve the author's intent, level of formality, and technical precision unless the user asks for a stronger tonal change.

### Routing near misses

- "Turn these meeting notes into a paragraph", the facts are already there in sentences or fragments: this skill. Notes that need claims, numbers, or citations introduced to become a section: `technical-writing-drafter`.
- "The results section reads choppy, smooth it": this skill, if no claim or connective changes. "The results paragraph overclaims": `technical-writing-reviser`.
- "Merge these two thin paragraphs": this skill. "Cut related work by a third": `technical-writing-reviser`, with the budget in the brief.
- "Write the abstract from the body": `technical-writing-drafter`.
- "Fix typos and LaTeX warnings": neither writing skill.

## Preserve Signal

Keep concrete nouns, exact constraints, filenames, commands, numbers, and caveats. Make the prose fuller without blurring technical precision.

In technical or research prose, connectives are claims. "Because", "so", "therefore", "rather than", and "but" each assert a causal, evidential, or contrastive relation. Add one only when the source states that relation. When two facts sit side by side without a stated relation, join them with "and" or keep them separate, and do not frame a point by first denying an adjacent proposition the source never raised.

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
