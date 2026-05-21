---
name: commercialize-academic-research
description: Run evidence-gated commercialization analysis for academic research by translating a bounded research asset into workflow pain, current workarounds, buyer and budget logic, commercialization paths, risk-retirement tests, and kill/pivot/continue decisions. Use when Codex needs to evaluate market pull for a paper, prototype, dataset, device, algorithm, lab result, or platform technology; distinguish user, buyer, operator, procurement, and budget roles; compare startup, licensing, partnership, service, or component routes; identify beachhead wedges; build validation sprints; or red-team unsupported commercialization claims.
---

# Commercialize Academic Research

## Quick start

1. Require a bounded `research_asset` before doing substantive commercialization work. If missing, ask for the paper, abstract, prototype summary, deck, technical memo, or lab notes.
2. Default to `fast triage` unless the user asks for a full case pack, deep analysis, red-team review, or validation sprint.
3. Use this required chain before recommending anything: `research claim -> workflow pain -> current workaround -> buyer/budget -> why now -> evidence -> weak link -> validation test`.
4. Initialize a working pack with `python3 scripts/init_case_pack.py <case-name> --path <output-dir>` when the user wants persistent artifacts.
5. Compare at least two plausible commercialization paths before recommending one; do not default to startup formation.
6. End every pass with assumptions, evidence strength, weak links, cheapest next tests, and a `kill / pivot / continue` decision.

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

## Output modes

- `fast triage` default: 1-2 page chat answer with the required analysis chain, evidence table, path comparison, and top tests.
- `deep case`: fuller strategy pass with segment ranking, stakeholder map, hypothesis ledger, readiness scoring, path sequencing, and risk-retirement plan.
- `red-team pass`: adversarial review of a proposed commercialization plan; lead with unsupported claims, role confusion, generic advice, and decisive missing evidence.
- `validation sprint`: 2-6 week test plan that turns the weakest assumptions into customer discovery, technical, pricing, procurement, regulatory, or partner tests.

## Default output contract

When the user wants persistent artifacts, create one case directory containing:

- `<case>.context.md`
- `<case>.evidence-ledger.md`
- `<case>.pain-points.md`
- `<case>.options.md`
- `<case>.validation-plan.md`
- `<case>.decision-log.md`

## Required answer shape

Use this shape unless the user requests otherwise:

1. `Commercialization read`: state the likely best path and confidence.
2. `Analysis chain`: fill `research claim -> workflow pain -> current workaround -> buyer/budget -> why now -> evidence -> weak link -> validation test`.
3. `Commercialization Evidence Table`: include `Claim | Evidence type | Confidence | Missing proof | Cheapest next test | Decision informed`.
4. `Stakeholder and budget map`: distinguish user, economic buyer, budget owner, procurement/compliance, operator, and beneficiary when relevant.
5. `Path comparison`: score at least two of startup/spinout, licensing, joint development, service-enabled product, tooling/component sale, or data/evaluation asset.
6. `Risk-retirement plan`: prioritize tests by decision value and cost.
7. `Decision`: recommend `continue`, `pivot`, or `kill/defer`, with what would change the decision.

## Workflow

### 1) Bound the technical core

- Extract what the research actually does, for whom, under what conditions, and what remains unproven.
- Separate the underlying capability from the academic benchmark story.
- Note TRL, MRL if physical/manufactured, deployment dependencies, hardware or data requirements, regulatory constraints, reproducibility risk, and IP/FTO position if known.
- Refuse to jump into market-sizing theater until the technical claim is precise enough to be falsifiable.

### 2) Investigate pain before pitching solutions

- Identify 2-4 candidate industries, workflows, or operating contexts where the capability could matter.
- For each candidate, map the user, economic buyer, budget owner, procurement/compliance gate, operator, beneficiary, current workaround, cost of failure, cost of delay, and switching friction.
- Prefer concrete workflow pain over generic claims such as "the market is large" or "the sector needs innovation."
- Use `references/discovery-question-bank.md` when the problem framing is thin.

### 3) Form problem theses

- Write each thesis as `actor + painful job + current workaround + measurable consequence + buyer/budget + why existing solutions underperform`.
- Kill vague theses that cannot be tied to a real workflow or budget.
- Rank candidate theses by severity, frequency, budget proximity, and credibility that this research changes the outcome.

### 4) Translate research into solution wedges

- Turn the research into a narrow sellable wedge that addresses one painful step.
- Separate enabling technology from the product or service a customer would actually buy.
- Consider whether the first offering should be software, workflow tooling, data service, instrument, component, service-enabled product, or partnership deliverable.
- Use `references/commercialization-patterns.md` when selecting viable commercialization patterns.
- Make the sequence explicit: `initial wedge -> proof milestone -> adjacent expansion -> possible platform`, and suppress platform narratives until the wedge has evidence.

### 5) Compare commercialization paths

- Compare startup or spinout, outbound licensing, joint development or strategic partnership, service-enabled product, and tooling or component sales when relevant.
- Score each path on TRL/MRL/ARL, budget proximity, buyer access, proof burden, channel difficulty, value quantifiability, defensibility, IP leverage, regulatory/procurement burden, and founder/operator fit.
- Use `references/evaluation-rubric.md` to keep the comparison consistent.

### 6) Recommend a beachhead and sequence

- Choose the smallest credible initial market that creates learning, revenue, or adoption leverage.
- Present a sequence such as `initial wedge -> adjacent expansion -> longer-term platform story`.
- Make clear what must be true for the beachhead to work and what would break the plan.

### 7) Maintain a hypothesis ledger

Track these hypotheses explicitly in chat for deep/red-team/validation modes and in `<case>.evidence-ledger.md` for persistent packs:

| Hypothesis | Current belief | Evidence | Confidence | Weak link | Cheapest next test | Decision |
| --- | --- | --- | --- | --- | --- | --- |
| Customer segment |  |  |  |  |  |  |
| Job/pain severity |  |  |  |  |  |  |
| Current workaround |  |  |  |  |  |  |
| Buyer/budget |  |  |  |  |  |  |
| Willingness to pay |  |  |  |  |  |  |
| Channel/access |  |  |  |  |  |  |
| Deployment blocker |  |  |  |  |  |  |
| IP/FTO |  |  |  |  |  |  |
| Regulatory/procurement |  |  |  |  |  |  |

### 8) Define validation work

- Convert uncertainty into experiments such as customer interviews, pilot designs, technical replication, cost-model tests, regulatory diligence, channel checks, and willingness-to-pay probes.
- Keep experiments cheap, time-bounded, and tied to a decision. A pilot is not valid unless it has a buyer, success metric, timeline, data access, adoption owner, and paid/next-step conversion criterion.
- Put the highest-value experiments in `<case>.validation-plan.md`.

### 9) Iterate methodically

- Move in passes rather than dumping one giant answer.
- After each pass, separate `sourced observations`, `user-provided facts`, `inferences`, and `speculative ideas`.
- When the user wants collaborative ideation, present 2-3 concrete branches and explain what evidence would eliminate each one.

## Anti-pattern checks

Before finalizing, remove or flag:

- TAM theater: market size claims that do not change the next decision or lack sourcing.
- Startup defaulting: recommending a spinout without buyer access, repeatable wedge, team fit, and financing logic.
- Academic novelty as value: assuming benchmark improvement, publication, or patentability equals customer demand.
- Fake interview validation: counting compliments, hypotheticals, surveys, or expert opinions as buying evidence.
- Free pilot purgatory: proposing pilots without paid conversion logic or a buyer-owned success metric.
- Premature platform narrative: describing broad platform potential before proving a narrow workflow wedge.
- Role confusion: conflating user, buyer, procurement, operator, regulator, partner, or beneficiary.
- Unsupported industry facts: presenting changing market, regulatory, reimbursement, or competitive facts without verification or labels.

## Quality bar

- Start from customer pain and buying context, not from technical elegance.
- Treat adoption friction, distribution, pricing, and implementation burden as first-class.
- Avoid unsupported TAM claims unless market size truly changes the recommendation.
- Prefer specific, falsifiable hypotheses over visionary language.
- Preserve uncertainty: every major recommendation needs evidence type, confidence, missing proof, and next test.
- If current industry facts materially affect the answer and live research is available, verify them. Otherwise label them as assumptions.

## Resources

- `scripts/init_case_pack.py`: scaffold a repeatable commercialization working pack.
- `references/discovery-question-bank.md`: I-Corps-style discovery, stakeholder, workaround, pricing, and interview-integrity questions.
- `references/commercialization-patterns.md`: routes from academic capability to sellable offerings, including TTO/licensing and wedge selection checks.
- `references/evaluation-rubric.md`: readiness and path scoring using TRL/MRL/ARL, budget, channel, value, defensibility, and fit dimensions.
- `references/diligence-checklists.md`: concise checklists for TTO/licensing, regulated/health, pricing/WTP, validation sprints, and adversarial review.
