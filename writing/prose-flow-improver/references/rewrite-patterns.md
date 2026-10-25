# Prose Flow Patterns

## Use Cases

Use this reference when the draft already exists and the problem is structural or stylistic rather than factual. It is especially useful for smoothing choppy explanations, merging thin sentences or paragraphs, converting bullet-heavy notes into prose, and making status updates, summaries, and assistant answers read more naturally.

## Target Shapes

Choose one of these shapes before rewriting:

1. One compact paragraph for a single claim with supporting detail.
2. Two short paragraphs when the draft has a natural split such as result plus implication, or issue plus recommendation.
3. A mixed shape when a short explanatory paragraph should introduce a small retained list.

If you cannot name the target shape, you probably have not grouped the ideas clearly enough yet.

## Quick Checklist

Ask four questions before rewriting:

1. Is this content inherently list-shaped?
2. Which bullets belong to the same idea?
3. What connective reasoning is missing between points?
4. What detail is essential and must stay exact?

If the answer to the first question is yes, keep the list and improve sentence quality instead of flattening it.

## Common Failure Modes

Too many bullets:
The draft uses bullets for points that are not independent. The result reads like notes, not finished writing.

Terse prose:
The draft names conclusions without stating the reason, implication, or tradeoff.

Fragment stacking:
Each bullet is only a phrase, so the reader has to infer the relationship between them.

Overcorrection:
The rewrite removes bullets that were actually useful for steps, options, or findings.

Tone drift:
The rewrite sounds more polished but no longer matches the original level of directness, certainty, or technical density.

Quiet loss of constraints:
The rewrite reads smoothly but drops filenames, numbers, caveats, or explicit limitations.

Semicolon substitution:
The rewrite replaces bullet choppiness with semicolon chains instead of building cleaner sentence flow.

Artificial paragraph breaks:
The rewrite keeps multiple short paragraphs even though they are doing the work of one paragraph.

Dangling compression:
The rewrite uses a participial phrase or subordinate clause whose subject is ambiguous, making the sentence smoother but less precise.

## Rewrite Moves

Promote the main point:
Turn the strongest bullet into the topic sentence of the paragraph.

Group related detail:
Fold nearby bullets into supporting sentences under the same paragraph.

Merge paragraphs with the same job:
If two adjacent paragraphs are both explaining the same claim, result, or recommendation, combine them unless the split improves emphasis or scanning.

Add the missing relation:
State whether the next sentence explains cause, contrast, consequence, constraint, or emphasis, when the source states or clearly implies that relation. In technical or research prose, do not supply a causal or contrastive relation that the source does not assert; join with "and" or keep the sentences separate.

Prefer conjunctions over punctuation tricks:
If two bullets belong in one sentence, first try joining them with "and," "but," "so," "because," or "while" before reaching for a semicolon.

Use participial phrasing when it clearly tightens flow:
When the actor is clear and the second sentence names a direct result, condition, or accompanying action, prefer a participial phrase over leaving a thin sentence pair intact. For example, "The migration failed. It left the index half-built." can become "The migration failed, leaving the index half-built." Do not use this move when it obscures who did what or stacks too many actions onto one sentence.

Expand only where the reader would otherwise have to infer:
Do not add padding, scene-setting, or generic transitions that say little.

End on the evidence or the consequence:
If the paragraph explains a decision or result, make what follows from it clear, in a sentence of ordinary length. Do not end every paragraph this way, and do not close on a short sentence that lands a point.

Keep one sharp list when it earns its place:
If a short list materially improves scanning, keep it and write a paragraph around it instead of flattening everything.

## Before and After

Example 1:

Before:
- Latency improved.
- Caching reduced repeated lookups.
- Tail latency still spikes during batch imports.

After:
Latency improved, and caching reduced repeated lookups on the hot path. Tail latency still spikes during batch imports, so the system remains sensitive to bursty write-heavy workloads.

The source lists the latency gain and the caching change side by side without saying one caused the other, so the rewrite keeps "and" rather than asserting "because". Write "because" only when the source states the causal link.

Example 2:

Before:
- Need more detail.
- Current section is too short.
- Reader cannot see why the choice matters.

After:
This section needs more detail because it states the choice without explaining why it matters. The reader cannot see the consequence of the decision or the tradeoff it resolves.

Example 3:

Before:
- Findings:
- Missing retry logic.
- Timeout values inconsistent.
- Tests do not cover partial failure.

After:
Keep the list. This content is inherently findings-shaped, and forcing it into prose would make it harder to scan. Improve the items instead:

1. Missing retry logic leaves transient upstream failures unhandled.
2. Timeout values are inconsistent across call sites, which makes failure behavior difficult to reason about.
3. Tests do not cover partial-failure scenarios, so this path can regress silently.

Example 4:

Before:
- We should keep the migration small.
- The risky part is the schema rename.
- Everything else is mechanical.
- If we split it, rollback is easier.

After:
We should keep this migration small because the schema rename is the only meaningfully risky part, while most of the remaining work is mechanical. Splitting the change also makes rollback easier, which reduces the cost of discovering a problem late.

Example 5:

Before:
- Summary:
- Revenue was up.
- Margin improved after pricing changes.
- Churn is still elevated in SMB.

After:
Revenue increased, and margin improved after the pricing changes took effect. SMB churn remains elevated, however, so the improvement still depends on fixing retention.

## Machine-Prose Tells to Avoid While Smoothing

Joining sentences is where these habits enter. Each line names the habit and the plain alternative:

- Em dash as the joint: comma, period, parentheses, or colon instead; one dash pair per page at most.
- "Not X but Y", "not just X", "rather than X, Y": state Y precisely; keep the contrast only when X is a real position the reader holds.
- Sentence-opening Importantly, Notably, Crucially, Interestingly, Ultimately, Moreover, Furthermore, Additionally: delete, or use "and", a new sentence, or a real ordinal.
- Crucial, robust, nuanced, pivotal, comprehensive, seamless, leverage, landscape, underscore, delve, foster: the measurement or mechanism the word stands in for, or nothing.
- ", highlighting / underscoring / suggesting / enabling / paving the way for ..." tails: end at the fact; a real implication gets its own sentence and its own support.
- Three parallel items for two-item content; three short parallel sentences; antithesis for effect: write the number of items the content has.
- "This suggests / This means / This highlights" chains: one interpretation per piece of evidence, next to it.
- A short closing sentence after long ones, and one-sentence drumbeat paragraphs: end on the evidence, vary paragraph endings.
- Paragraphs all of the same length and shape: let length follow the argument.
- "It is worth noting", "it is important to note", "the key insight is": delete the frame.
- Rhetorical questions and "Let's": ask the question of yourself, write the answer.
- Bolded lead-ins and bullets for argument: prose for argument, lists for list-shaped content.

## Default Heuristics

Prefer paragraphs for explanation.

Prefer lists for selection, sequencing, and auditing.

Prefer one short paragraph over three weak bullets.

Prefer one strong bullet over one vague paragraph when the task requires quick scanning.

Prefer preserving exact constraints over achieving a smoother rhythm.

Prefer fewer, stronger sentences joined by clear conjunctions over a trail of short sentences or semicolons.

Prefer one solid paragraph over two thin paragraphs when both are serving the same point.
