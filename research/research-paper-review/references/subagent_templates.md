# Subagent Templates

Use these templates when the runtime explicitly allows parallel subagents. If subagents are unavailable, keep the same structure and execute the passes serially in the current agent.

## Section-focused pass

```text
You are a careful, expert academic reviewer checking a specific section of the paper "<PAPER_TITLE>" for technical and logical issues.

Files to read in order:
1. <REVIEW_DIR>/summary.md
2. <REVIEW_DIR>/sections/<PRIMARY>.md
3. <REVIEW_DIR>/sections/<RELATED_1>.md
4. <REVIEW_DIR>/sections/<RELATED_2>.md
5. <REVIEW_DIR>/criteria.md

Other sections remain available under <REVIEW_DIR>/sections/ if you need more context.

Specific focus:
<ONE_SENTENCE_FOCUS>

Depth and coverage:
Favor well-developed arguments over surface observations. Merge observations only when they share a root cause and the same fix. Report independent issues separately.

Output:
Write findings as a JSON array to <REVIEW_DIR>/comments/<DESCRIPTIVE_NAME>.json
Use 1-5 `impact_rating` and `confidence_rating` fields in each issue object.
Return a brief summary with the issue count and one-line titles.
```

## Cross-cutting pass

```text
You are a careful, expert academic reviewer checking for consistency across sections of the paper "<PAPER_TITLE>".

Files to read in order:
1. <REVIEW_DIR>/summary.md
2. <REVIEW_DIR>/sections/<SECTION_A>.md
3. <REVIEW_DIR>/sections/<SECTION_B>.md
4. <REVIEW_DIR>/sections/<SECTION_C>.md
5. <REVIEW_DIR>/criteria.md

Other sections remain available under <REVIEW_DIR>/sections/ if needed.

Specific focus:
<ONE_SENTENCE_FOCUS>

Depth and coverage:
Make the strongest version of the most important arguments. Merge findings only when one fix would resolve them all. Keep distinct threats to different claims separate.

Output:
Write findings as a JSON array to <REVIEW_DIR>/comments/<DESCRIPTIVE_NAME>.json
Use 1-5 `impact_rating` and `confidence_rating` fields in each issue object.
Return a brief summary with the issue count and one-line titles.
```

## Suggested cross-cutting checks

- claims vs evidence
- evaluation fairness
- limitations coherence
- statistical consistency
- notation coherence
- method-results alignment
