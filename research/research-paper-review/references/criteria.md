# Review Criteria

## What to check

1. **Mathematical / formula errors** -- wrong formulas, sign errors, missing factors, incorrect derivations, subscript or index errors
2. **Notation inconsistencies** -- symbols used differently than defined
3. **Text vs formal definition mismatch** -- prose says one thing but equation or table says another
4. **Parameter / numerical inconsistencies** -- stated values contradict derivable values; aggregate statistics with unclear or conflated denominators
5. **Insufficient justification** -- non-trivial derivation steps skipped; thresholds or design choices stated without rationale
6. **Questionable claims** -- overstatement of what has been shown; novelty claims that cited work may satisfy; domain-norm mismatches
7. **Misleading ambiguity** -- only if a careful reader could reasonably reach an incorrect conclusion
8. **Underspecified methods** -- procedure too vague to reproduce; key parameters left implicit; components mentioned but never described
9. **Internal contradictions** -- a claim contradicted by another section; a stated mitigation undermined later
10. **Self-consistency of standards** -- does the paper apply to its own methodology the same rigor it demands of others, such as statistical significance, evaluation protocols, or sample sizes?

## Reasoning style

For each issue:

- describe what concerned you
- describe what you checked to resolve it
- state what specifically remains problematic
- acknowledge what the authors got right when relevant

Reference standard results or conventions when they materially affect the judgment.

## Be lenient with

- introductory sections that intentionally simplify
- forward references that are likely resolved later
- notation that is not yet defined at first use but is introduced later
- informal prose that paraphrases a formal result without every qualifier

## Do not flag

- formatting, typesetting, or capitalization issues
- references to sections or equations outside the assigned scope when they are clearly elsewhere in the paper
- trivial observations that a field expert would immediately resolve

## Output format

Write findings as a JSON array. Each issue is a JSON object with:

- `title`
- `quote`
- `explanation`
- `comment_type`
- `impact_rating`
- `confidence_rating`
- `source_section`
- `related_sections`

If there are no issues, write `[]`.
