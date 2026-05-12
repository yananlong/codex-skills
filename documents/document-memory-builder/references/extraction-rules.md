# Extraction Rules

Apply these rules when deciding what should become durable memory.

## Keep

- Stable definitions, terminology, and notation.
- Durable facts that appear central to the project or corpus.
- Reusable workflows, operating procedures, and decision rules.
- Important entities, components, and relationships.
- Constraints, assumptions, non-goals, and repeated caveats.
- High-signal examples only when they teach a reusable pattern.

## Usually exclude

- Temporary status updates and tactical discussion.
- One-off brainstorms that were never adopted.
- Old plans superseded by more authoritative documents.
- Raw quotations when a concise synthesis is clearer.
- Volatile numeric values unless the user explicitly wants them remembered.

## Conflict resolution

1. Prefer normative or authoritative documents over commentary.
2. Prefer newer documents when authority is comparable.
3. Preserve unresolved disagreements in `open-questions` instead of forcing a merge.

## Compression rules

- Deduplicate repeated claims.
- Merge near-synonyms into one normalized term and note aliases when needed.
- Generalize examples into patterns when possible.
- Keep historical detail only if it helps future reasoning or conflict resolution.

## Long-form chunking heuristics

Use these rules for books, chaptered drafts, long reports, or large corpus refreshes:

1. Build a structure map first: chapters, sections, appendices, scenes, or argument arcs.
2. Chunk by meaning, not token size. Each chunk should have one coherent job.
3. If a chunk is too large, split only at subheadings or major conceptual turns.
4. Track boundary context for each chunk: what came before, what must carry forward, and what follows.
5. Keep one shared terminology and constraints sheet for all chunks.
6. Prefer independent chunks first when planning parallel delegation.

## Compact subagent prompt template

Use this when delegation is explicitly allowed:

```text
You are extracting durable memory from one chunk of a larger document set.

User goal:
<what future reuse this memory should optimize for>

Authority and conflict policy:
<source precedence + recency tie-break rule>

Shared terminology and locked constraints:
<terms, names, definitions, invariants, non-goals>

Assigned chunk boundaries:
<start heading/marker> to <end heading/marker>

Boundary context:
- Prior context summary: <2-4 lines>
- Next context summary: <2-4 lines>

Output:
1) Memory candidates for this chunk, grouped by the memory-pack sections, with source pointers.
2) Notes:
   - Preserved facts and constraints
   - Unresolved continuity/conflict issues
   - Cross-chunk transition or dependency needs
```

## Integration checklist

After chunk outputs return, run this in the main agent:

1. Reassemble outputs in canonical document order.
2. Normalize terminology, naming, and claim granularity.
3. Remove duplicate facts and repeated framing.
4. Reconcile cross-chunk conflicts using authority and recency rules.
5. Route unresolved contradictions to `open-questions`.
6. Verify every substantive item still has traceable source support.
7. Run one whole-corpus pass for coherence before writing final pack files.

## Traceability rules

- Attach source pointers to every substantive memory item.
- Label inferred conclusions as `Inference`.
- If support is weak, keep the item out of canonical facts and move it to `open-questions`.
