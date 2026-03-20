---
name: commercialize-academic-research
description: Develop business strategies for commercializing academic research by translating technical work into customer pain points, solution theses, commercialization paths, and validation plans. Use when Codex needs to evaluate market pull for a paper, prototype, dataset, device, algorithm, lab result, or platform technology; investigate industry pain points and unmet needs; compare startup, licensing, partnership, or service routes; identify beachhead markets; or iterate commercialization ideas methodically with the user.
---

# Commercialize Academic Research

## Quick start

1. Require a bounded `research_asset` before doing substantive commercialization work. If missing, ask for the paper, abstract, prototype summary, deck, technical memo, or lab notes.
2. Clarify the commercialization objective only if it materially changes the analysis. Otherwise default to `identify the strongest near-term commercialization path`.
3. Initialize a working pack with `python3 scripts/init_case_pack.py <case-name> --path <output-dir>` when the user wants persistent artifacts.
4. Start from industry pain, workflow friction, and buying context rather than from the technology's novelty.
5. Compare at least two plausible commercialization paths before recommending one.
6. End every pass with explicit assumptions, strongest evidence, weak links, and next experiments or questions.

## Input contract

### Required

- `research_asset`: a paper, abstract, prototype description, device spec, dataset, algorithm summary, lab result, or other bounded technical artifact.

### Optional inputs with defaults

- `goal`: default `identify the best commercialization path`.
- `geography`: default `global, noting region-specific constraints only when material`.
- `time_horizon`: default `12-24 months to first commercial traction`.
- `mode_preference`: default `open across startup, licensing, partnership, and service models`.
- `customer_scope`: default `explore 2-4 plausible customer segments before narrowing`.
- `evidence_standard`: default `separate sourced facts from inferences from speculative ideas`.
- `risk_tolerance`: default `moderate: favor credible beachheads over distant platform visions`.

## Default output contract

When the user wants persistent artifacts, create one case directory containing:

- `<case>.context.md`
- `<case>.pain-points.md`
- `<case>.options.md`
- `<case>.validation-plan.md`
- `<case>.decision-log.md`

## Workflow

### 1) Bound the technical core

- Extract what the research actually does, for whom, under what conditions, and what remains unproven.
- Separate the underlying capability from the academic benchmark story.
- Note technical maturity, deployment dependencies, hardware or data requirements, regulatory constraints, reproducibility risk, and IP position if known.
- Refuse to jump into market-sizing theater until the technical claim is precise enough to be falsifiable.

### 2) Investigate pain before pitching solutions

- Identify 2-4 candidate industries, workflows, or operating contexts where the capability could matter.
- For each candidate, map the user, buyer, operator, budget owner, current workaround, cost of failure, cost of delay, and switching friction.
- Prefer concrete workflow pain over generic claims such as "the market is large" or "the sector needs innovation."
- Use `references/discovery-question-bank.md` when the problem framing is thin.

### 3) Form problem theses

- Write each thesis as `actor + painful job + current workaround + measurable consequence + why existing solutions underperform`.
- Kill vague theses that cannot be tied to a real workflow or budget.
- Rank candidate theses by severity, frequency, budget proximity, and credibility that this research changes the outcome.

### 4) Translate research into solution wedges

- Turn the research into a narrow sellable wedge that addresses one painful step.
- Separate enabling technology from the product or service a customer would actually buy.
- Consider whether the first offering should be software, workflow tooling, data service, instrument, component, service-enabled product, or partnership deliverable.
- Use `references/commercialization-patterns.md` when selecting viable commercialization patterns.

### 5) Compare commercialization paths

- Compare startup or spinout, outbound licensing, joint development or strategic partnership, service-enabled product, and tooling or component sales when relevant.
- Score each path on proof burden, time to value, capital intensity, channel difficulty, defensibility, IP leverage, and team or founder fit.
- Use `references/evaluation-rubric.md` to keep the comparison consistent.

### 6) Recommend a beachhead and sequence

- Choose the smallest credible initial market that creates learning, revenue, or adoption leverage.
- Present a sequence such as `initial wedge -> adjacent expansion -> longer-term platform story`.
- Make clear what must be true for the beachhead to work and what would break the plan.

### 7) Define validation work

- Convert uncertainty into experiments such as customer interviews, pilot designs, technical replication, cost-model tests, regulatory diligence, channel checks, and willingness-to-pay probes.
- Keep experiments cheap, time-bounded, and tied to a decision.
- Put the highest-value experiments in `<case>.validation-plan.md`.

### 8) Iterate methodically

- Move in passes rather than dumping one giant answer.
- After each pass, separate `sourced observations`, `inferences`, and `speculative ideas`.
- When the user wants collaborative ideation, present 2-3 concrete branches and explain what evidence would eliminate each one.

## Quality bar

- Start from customer pain and buying context, not from technical elegance.
- Treat adoption friction, distribution, pricing, and implementation burden as first-class.
- Avoid unsupported TAM claims unless market size truly changes the recommendation.
- Prefer specific, falsifiable hypotheses over visionary language.
- If current industry facts materially affect the answer and live research is available, verify them. Otherwise label them as assumptions.

## Resources

- `scripts/init_case_pack.py`: scaffold a repeatable commercialization working pack.
- `references/discovery-question-bank.md`: question sets for the technology, customer, workflow, economics, competition, regulatory, and go-to-market lenses.
- `references/commercialization-patterns.md`: common routes from academic capability to a sellable offering.
- `references/evaluation-rubric.md`: a scoring rubric for choosing a commercialization path.
