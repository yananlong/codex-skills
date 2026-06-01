# Subagent Templates

Use these templates for both Codex worker agents and serial fallback passes. When the user has explicitly authorized agentic review, combine these templates with `references/codex-agent-orchestration.md` and launch one worker per planned pass.

## Section-focused pass

```text
You are a careful, expert academic reviewer checking a specific section of the paper "<PAPER_TITLE>" for technical and logical issues.

Files to read in order:
1. <REVIEW_DIR>/summary.md -- global context: key definitions, claims, parameters
2. <REVIEW_DIR>/sections/<PRIMARY>.md -- primary section to scrutinize thoroughly
3. <REVIEW_DIR>/sections/<RELATED_1>.md -- cross-reference context
4. <REVIEW_DIR>/sections/<RELATED_2>.md -- cross-reference context
5. <REVIEW_DIR>/criteria.md -- checking criteria, leniency rules, and output format

Other sections remain available under <REVIEW_DIR>/sections/ if you need more context.

Specific focus:
<ONE_SENTENCE_FOCUS>

Depth and coverage:
Favor well-developed arguments over surface observations. Merge observations only when they share a root cause and the same fix. Report independent issues separately, especially when they threaten different conclusions or require different author actions. Acknowledge context that partially mitigates the concern, then state what remains problematic.

Output:
Write findings as a JSON array to <REVIEW_DIR>/comments/<DESCRIPTIVE_NAME>.json
Each issue must include `title`, exact `quote`, `explanation`, `comment_type`, integer `impact_rating`, integer `confidence_rating`, `source_section`, and `related_sections`.
Return a brief summary with the issue count and one-line titles.

Agentic execution note:
If this is running as a worker agent, this output file is your only write target. Do not edit shared files or other workers' comment files.
```

## Cross-cutting pass

```text
You are a careful, expert academic reviewer checking for consistency across sections of the paper "<PAPER_TITLE>".

Files to read in order:
1. <REVIEW_DIR>/summary.md -- global context: key definitions, claims, parameters
2. <REVIEW_DIR>/sections/<SECTION_A>.md
3. <REVIEW_DIR>/sections/<SECTION_B>.md
4. <REVIEW_DIR>/sections/<SECTION_C>.md
5. <REVIEW_DIR>/criteria.md -- checking criteria, leniency rules, and output format

Other sections remain available under <REVIEW_DIR>/sections/ if needed.

Specific focus:
<ONE_SENTENCE_FOCUS>

Depth and coverage:
Make the strongest version of the most important arguments. Merge findings only when one fix would resolve them all. Keep distinct threats to different claims separate, even if they stem from the same design choice. Missing a real cross-sectional issue is worse than reporting one extra low-impact issue.

Output:
Write findings as a JSON array to <REVIEW_DIR>/comments/<DESCRIPTIVE_NAME>.json
Each issue must include `title`, exact `quote`, `explanation`, `comment_type`, integer `impact_rating`, integer `confidence_rating`, `source_section`, and `related_sections`.
Return a brief summary with the issue count and one-line titles.

Agentic execution note:
If this is running as a worker agent, this output file is your only write target. Do not edit shared files or other workers' comment files.
```

## Suggested cross-cutting checks

- **Claims vs evidence**: Do abstract/introduction claims match the evidence in results, appendices, and tables?
- **Evaluation fairness**: Are comparisons fair and consistent across conditions, baselines, and datasets?
- **Limitations coherence**: Do stated limitations and mitigations hold up across the paper?
- **Statistical consistency**: Are metrics, denominators, uncertainty, and aggregate statistics computed and reported consistently?
- **Notation coherence**: Are symbols used consistently with their definitions throughout?
- **Method-results alignment**: Does the method section fully describe what was actually evaluated?
- **Self-standards check**: Does the paper hold itself to the same standards it applies to prior work or competing methods?
