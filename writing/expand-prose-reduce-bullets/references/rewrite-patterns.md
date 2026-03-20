# Rewrite Patterns

## Use Cases

Use this reference when the draft already exists and the problem is structural rather than factual. It is especially useful for converting bullet-heavy explanations, status updates, summaries, and assistant answers into smoother prose.

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

## Rewrite Moves

Promote the main point:
Turn the strongest bullet into the topic sentence of the paragraph.

Group related detail:
Fold nearby bullets into supporting sentences under the same paragraph.

Add the missing relation:
State whether the next sentence explains cause, contrast, consequence, constraint, or emphasis.

Expand only where the reader would otherwise have to infer:
Do not add padding, scene-setting, or generic transitions that say little.

End with the practical implication:
If the paragraph explains a decision or result, finish by stating what follows from it.

## Before and After

Example 1:

Before:
- Latency improved.
- Caching reduced repeated lookups.
- Tail latency still spikes during batch imports.

After:
Latency improved because caching removed many repeated lookups from the hot path. The gain is real, but it is not uniform: tail latency still spikes during batch imports, so the system remains sensitive to bursty write-heavy workloads.

Example 2:

Before:
- Need more detail.
- Current section is too short.
- Reader cannot see why the choice matters.

After:
This section needs more detail because it states the choice without explaining why it matters. The core problem is not length by itself; it is that the reader cannot see the consequence of the decision or the tradeoff it resolves.

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

## Default Heuristics

Prefer paragraphs for explanation.

Prefer lists for selection, sequencing, and auditing.

Prefer one short paragraph over three weak bullets.

Prefer one strong bullet over one vague paragraph when the task requires quick scanning.
