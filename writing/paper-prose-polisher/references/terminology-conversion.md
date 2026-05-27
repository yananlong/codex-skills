# Terminology Conversion

## Purpose

Use this reference when a draft is full of names that make sense inside the project but not to outside readers. The job is to convert internal labels into terms that carry the same meaning for an academic audience without silently changing the claim.

## What to Look For

Watch for:

1. Project nicknames.
2. Internal abbreviations that are not standard in the field.
3. Implementation labels such as bucket names, pipeline stage names, or experiment codenames.
4. Team-specific verbs such as "archive it," "roleplay it," or "stress it" when those verbs hide the actual operation.
5. Names that encode an interpretation rather than a neutral description.
6. Acronyms introduced in notes but not defined for the target paper audience.
7. Variable, model, dataset, or condition names that expose implementation history rather than research function.

## Safe Rewrite Rule

Translate only when the text itself makes the meaning clear. Use the source passage, nearby definitions, tables, or section headings to infer the reader-facing term.

If the mapping is uncertain, do not force a clean rewrite. Preserve the original term and ask for a glossary, or keep the original once and follow it with a brief neutral gloss that the draft supports.

## Preferred Conversions

Prefer:

- Function over nickname.
- Reader-facing role over implementation jargon.
- Neutral description over internally persuasive framing.
- Standard field terminology over local abbreviations.
- Stable terms over several near-synonyms for the same object.

Examples:

- "our sandbox pass" -> "the controlled evaluation pass" when the text defines it as a control condition.
- "the red-team bucket" -> "the adversarial condition" when the task actually varies adversarial prompting.
- "micro-archive" -> "a compact curated archive" when the archive structure is described.
- "semantic ladder" -> a narrower descriptive term if the draft really means "increasingly demanding evidence conditions."
- "v2 judge" -> "the revised evaluator" when the revision is what matters, or keep the label if the version identity is needed for reproducibility.

## Common Failure Modes

Wrong abstraction:
The rewrite turns a concrete local term into a vague academic label that hides the mechanism.

Over-interpretation:
The rewrite upgrades a neutral internal term into a theoretical claim the draft does not support.

Premature normalization:
The rewrite swaps in standard field terminology even though the mapping is only partial.

Silent drift:
The rewrite sounds smoother but changes which condition, artifact, or mechanism the sentence refers to.

## Practical Procedure

1. Underline every term that a new reader would not understand without project context.
2. Decide whether the meaning is explicit, inferable, or uncertain.
3. Replace only the explicit and inferable cases.
4. Keep uncertain terms visible and request a terminology map.
5. Re-read the paragraph to make sure the new terms still distinguish the right objects and conditions.

If the same internal term appears many times, choose one reader-facing replacement and use it consistently. Do not introduce a different polished synonym each time, because that can make one condition appear to be several distinct objects.
