# Research Review Checklist

## Scope and framing

- What is the artifact trying to prove or justify?
- What is the intended audience and stakes?
- What would count as a review-blocking failure?

## Claim ledger

- Are all important claims traceable?
- Are definitions and assumptions explicit?
- Are claims separated into factual, quantitative, causal, normative, and speculative?

## Imported paper-review issues

- If `paper-review/final_issues.json` exists, were issue titles, quotes, explanations, impact ratings, confidence ratings, and source sections preserved?
- If the first-pass review came from upstream Claude/OpenAIReview, was its `severity` schema preserved or deliberately normalized rather than silently coerced?
- If the review pack has `round-N/` folders or metadata round summaries, did the new round continue that structure instead of overwriting or relocating root paper-review artifacts?
- Were `impact_rating` values mapped consistently to major, moderate, or minor tracked issues?
- Does each imported issue still point to its origin file instead of being rewritten as an untraceable summary?

## Internal checks

- Are there contradictions or definitional drift?
- Does the argument skip steps?
- Do metrics, baselines, and controls match the claim?

## External checks

- Are time-sensitive facts verified?
- Do citations support the attached claim?
- Are benchmark or “state of the art” claims current?

## Closure checks

- Which issues are major?
- What evidence or rewrite would resolve each issue?
- Which risks remain accepted rather than fixed?
- For each resolved imported issue, is there a concrete revision diff, new evidence artifact, narrowed claim, or accepted-risk rationale?
