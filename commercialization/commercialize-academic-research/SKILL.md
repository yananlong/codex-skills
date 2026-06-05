---
name: commercialize-academic-research
description: Run evidence-gated commercialization analysis for academic research by translating a bounded research asset into workflow pain, current workarounds, buyer and budget logic, commercialization paths, risk-retirement tests, and kill/pivot/continue decisions. Use when Codex needs to evaluate market pull for a paper, prototype, dataset, device, algorithm, lab result, or platform technology; distinguish user, buyer, operator, procurement, and budget roles; compare startup, licensing, partnership, service, or component routes; identify beachhead wedges; build validation sprints; or red-team unsupported commercialization claims.
---

# Commercialize Academic Research

## Quick start

1. Require a bounded `research_asset` before doing substantive commercialization work. If missing, ask for the paper, abstract, prototype summary, deck, technical memo, or lab notes.
2. Default to `fast triage` unless the user asks for a full case pack, deep analysis, red-team review, validation sprint, or source-grounded market scan.
3. Use this required chain before recommending anything: `research claim -> workflow pain -> current workaround -> buyer/budget -> why now -> evidence -> weak link -> validation test`.
4. Choose the evidence posture early: `user-facts-only`, `light desk research`, or `source-grounded diligence`. If current industry, regulatory, reimbursement, funding, pricing, or competitive facts materially affect the answer and live research is available, verify them and cite sources; if not available, label them as assumptions.
5. Initialize a working pack with `python3 scripts/init_case_pack.py <case-name> --path <output-dir>` when the user wants persistent artifacts.
6. For persistent packs, maintain `<case>.source-log.md` and validate the pack with `python3 scripts/validate_case_pack.py <case-dir>` before returning it.
7. Compare at least two plausible commercialization paths before recommending one; do not default to startup formation.
8. End every pass with assumptions, evidence strength, weak links, cheapest next tests, and a `kill / pivot / continue` decision.

## Modes

### Fast triage

Use by default for quick commercialization judgment. Produce a 1-2 page chat answer with the required analysis chain, evidence table, path comparison, and top tests. Use live sources only for facts that would materially change the recommendation.

### Deep case

Use when the user asks for a fuller strategy pass. Include segment ranking, stakeholder map, hypothesis ledger, readiness scoring, path sequencing, domain-adapter checks, and a risk-retirement plan.

### Source-grounded market scan

Use when the recommendation depends on changing market, regulatory, reimbursement, funding, procurement, or competitive facts. Log sources, search queries, retrieval dates, source type, and what each source supports. Keep this bounded; do not silently turn it into a full systematic literature review.

### Red-team pass

Use when reviewing a proposed commercialization plan. Lead with unsupported claims, role confusion, generic advice, fake validation, and decisive missing evidence.

### Validation sprint

Use when the user wants a 2-6 week test plan. Turn the weakest assumptions into customer discovery, technical, pricing, procurement, regulatory, partner, or funding-readiness tests.

## Relationship to sibling skills

- `research-systematic-literature-review` owns systematic evidence synthesis. Invoke it or consume its artifacts when commercialization depends on efficacy, safety, SOTA, clinical, benchmark, or published-evidence claims beyond the provided asset.
- `research-novelty-review` owns adversarial prior-art and positioning decisions. Use it when commercial value depends on whether the technical contribution is truly differentiated.
- `research-results-auditor` owns validity checks for experiment outputs. Use it before treating benchmark, ablation, clinical, or statistical results as commercialization evidence.
- `research-experiment-plan` owns decisive technical validation design. Use it when the main weak link is a technical claim rather than customer, budget, or channel risk.
- `research-zotero` can supply a curated corpus for literature-heavy diligence, but saved references are not proof of inclusion or commercial relevance.

## Input contract

### Required

- `research_asset`: a paper, abstract, prototype description, device spec, dataset, algorithm summary, lab result, or other bounded technical artifact.

### Optional inputs with defaults

- `goal`: default `identify the best commercialization path`.
- `geography`: default `global, noting region-specific constraints only when material`.
- `time_horizon`: default `12-24 months to first commercial traction`.
- `mode_preference`: default `open across startup, licensing, partnership, and service models`.
- `customer_scope`: default `explore 2-4 plausible customer segments before narrowing`.
- `evidence_depth`: default `light desk research only when material facts may change the decision`.
- `source_scope`: default `official, primary, customer/procurement, peer-reviewed, and credible industry sources before generic commentary`.
- `funding_context`: default `consider non-dilutive and translational funding only when it changes path sequencing or validation feasibility`.
- `domain_adapter`: default `infer from the research asset; otherwise use the generic rubric`.
- `evidence_standard`: default `separate sourced facts from user-provided facts from inferences from speculative ideas`.
- `risk_tolerance`: default `moderate: favor credible beachheads over distant platform visions`.

## Hard-stop and failover rules

- Stop immediately if `research_asset` is missing.
- Do not present market size, reimbursement, regulatory status, procurement rules, or current competitor claims as facts without sources when live research is available.
- If live research is unavailable and current facts matter, continue only if the user accepts an assumption-led pass or if the asset itself contains enough evidence for the requested decision.
- Do not recommend a pilot unless buyer, budget or conversion commitment, success metric, timeline, data/integration access, adoption owner, and decision after the pilot are explicit.
- Do not recommend startup formation unless repeatable wedge, buyer access, differentiated product, team/operator fit, and financing path are credible.

## Default output contract

When the user wants persistent artifacts, create one case directory containing:

- `<case>.context.md`
- `<case>.source-log.md`
- `<case>.evidence-ledger.md`
- `<case>.pain-points.md`
- `<case>.options.md`
- `<case>.validation-plan.md`
- `<case>.decision-log.md`

## Required answer shape

Use this shape unless the user requests otherwise:

1. `Commercialization read`: state the likely best path and confidence.
2. `Evidence posture`: state whether the answer used user facts only, light desk research, source-grounded diligence, or sibling-skill evidence.
3. `Analysis chain`: fill `research claim -> workflow pain -> current workaround -> buyer/budget -> why now -> evidence -> weak link -> validation test`.
4. `Commercialization Evidence Table`: include `Claim | Evidence type | Confidence | Missing proof | Cheapest next test | Decision informed`.
5. `Stakeholder and budget map`: distinguish user, economic buyer, budget owner, procurement/compliance, operator, beneficiary, and champion when relevant.
6. `Path comparison`: score at least two of startup/spinout, licensing, joint development, service-enabled product, tooling/component sale, data/evaluation asset, or funding-first translational path.
7. `Risk-retirement plan`: prioritize tests by decision value and cost.
8. `Decision`: recommend `continue`, `pivot`, or `kill/defer`, with what would change the decision.

## Workflow

### 1) Bound the technical core

- Extract what the research actually does, for whom, under what conditions, and what remains unproven.
- Separate the underlying capability from the academic benchmark story.
- Note TRL, MRL if physical/manufactured, deployment dependencies, hardware or data requirements, regulatory constraints, reproducibility risk, and IP/FTO position if known.
- Refuse to jump into market-sizing theater until the technical claim is precise enough to be falsifiable.

### 2) Establish evidence posture and source plan

- Decide which claims can be answered from the user-provided asset and which require external evidence.
- For source-grounded work, log query strings, source types, retrieval dates, and supported claims in `<case>.source-log.md` or in chat.
- Prefer official program pages, regulator guidance, reimbursement/procurement documentation, customer-visible pricing, technical standards, peer-reviewed evidence, patent/TTO records, and credible industry reports over generic blog summaries.
- Separate facts, source-backed observations, user-provided facts, inferences, and speculative ideas.
- Use `research-systematic-literature-review` instead of ad hoc searching when the decision depends on a body of published research rather than a few market or regulatory facts.

### 3) Investigate pain before pitching solutions

- Identify 2-4 candidate industries, workflows, or operating contexts where the capability could matter.
- For each candidate, map the user, economic buyer, budget owner, procurement/compliance gate, operator, beneficiary, champion, current workaround, cost of failure, cost of delay, and switching friction.
- Prefer concrete workflow pain over generic claims such as "the market is large" or "the sector needs innovation."
- Use `references/discovery-question-bank.md` when the problem framing is thin.

### 4) Form problem theses

- Write each thesis as `actor + painful job + current workaround + measurable consequence + buyer/budget + why existing solutions underperform`.
- Kill vague theses that cannot be tied to a real workflow or budget.
- Rank candidate theses by severity, frequency, budget proximity, and credibility that this research changes the outcome.

### 5) Translate research into solution wedges

- Turn the research into a narrow sellable wedge that addresses one painful step.
- Separate enabling technology from the product or service a customer would actually buy.
- Consider whether the first offering should be software, workflow tooling, data service, instrument, component, service-enabled product, sponsored development, or partnership deliverable.
- Use `references/commercialization-patterns.md` when selecting viable commercialization patterns.
- Make the sequence explicit: `initial wedge -> proof milestone -> adjacent expansion -> possible platform`, and suppress platform narratives until the wedge has evidence.

### 6) Compare commercialization paths

- Compare startup or spinout, outbound licensing, joint development or strategic partnership, service-enabled product, tooling or component sales, data/evaluation assets, and funding-first translational routes when relevant.
- Score each path on TRL/MRL/ARL, budget proximity, buyer access, proof burden, channel difficulty, value quantifiability, defensibility, IP leverage, regulatory/procurement burden, capital intensity, and founder/operator fit.
- Use `references/evaluation-rubric.md` to keep the comparison consistent.

### 7) Apply domain adapter

- Use `references/domain-adapters.md` when the asset falls into a specialized domain such as health/biomed, AI/software/data, climate/energy, materials/manufacturing, robotics/hardware, or public-sector/education.
- Apply only the adapter checks that affect the decision; do not dump generic domain advice into the answer.
- If the domain adapter reveals a blocking evidence requirement, promote it to the hypothesis ledger and validation plan.

### 8) Recommend a beachhead and sequence

- Choose the smallest credible initial market that creates learning, revenue, or adoption leverage.
- Present a sequence such as `initial wedge -> proof milestone -> adjacent expansion -> longer-term platform story`.
- Make clear what must be true for the beachhead to work and what would break the plan.

### 9) Maintain a hypothesis ledger

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
| Funding/translational path |  |  |  |  |  |  |

### 10) Define validation work

- Convert uncertainty into experiments such as customer interviews, pilot designs, technical replication, cost-model tests, regulatory diligence, channel checks, funding-path checks, and willingness-to-pay probes.
- Keep experiments cheap, time-bounded, and tied to a decision. A pilot is not valid unless it has a buyer, success metric, timeline, data access, adoption owner, and paid/next-step conversion criterion.
- Put the highest-value experiments in `<case>.validation-plan.md`.

### 11) Iterate methodically

- Move in passes rather than dumping one giant answer.
- After each pass, separate `sourced observations`, `user-provided facts`, `inferences`, and `speculative ideas`.
- When the user wants collaborative ideation, present 2-3 concrete branches and explain what evidence would eliminate each one.
- Validate persistent case packs with `scripts/validate_case_pack.py` before returning them.

## Anti-pattern checks

Before finalizing, remove or flag:

- TAM theater: market size claims that do not change the next decision or lack sourcing.
- Startup defaulting: recommending a spinout without buyer access, repeatable wedge, team fit, and financing logic.
- Academic novelty as value: assuming benchmark improvement, publication, or patentability equals customer demand.
- Fake interview validation: counting compliments, hypotheticals, surveys, or expert opinions as buying evidence.
- Free pilot purgatory: proposing pilots without paid conversion logic or a buyer-owned success metric.
- Premature platform narrative: describing broad platform potential before proving a narrow workflow wedge.
- Role confusion: conflating user, buyer, procurement, operator, regulator, partner, or beneficiary.
- Unsupported industry facts: presenting changing market, regulatory, reimbursement, funding, or competitive facts without verification or labels.
- Literature overreach: treating a single paper, benchmark, or preprint as market proof without customer, workflow, and buyer evidence.

## Quality bar

- Start from customer pain and buying context, not from technical elegance.
- Treat adoption friction, distribution, pricing, implementation burden, and funding feasibility as first-class.
- Avoid unsupported TAM claims unless market size truly changes the recommendation.
- Prefer specific, falsifiable hypotheses over visionary language.
- Preserve uncertainty: every major recommendation needs evidence type, confidence, missing proof, and next test.
- Use official, primary, or directly decision-relevant sources for time-sensitive facts whenever possible.
- If current industry facts materially affect the answer and live research is unavailable, label them as assumptions or defer the fact-dependent recommendation.

## Resources

- `scripts/init_case_pack.py`: scaffold a repeatable commercialization working pack.
- `scripts/validate_case_pack.py`: validate required case-pack files, sections, source logging, and decision fields.
- `references/discovery-question-bank.md`: I-Corps-style discovery, stakeholder, workaround, pricing, and interview-integrity questions.
- `references/commercialization-patterns.md`: routes from academic capability to sellable offerings, including TTO/licensing and wedge selection checks.
- `references/evaluation-rubric.md`: readiness and path scoring using TRL/MRL/ARL, budget, channel, value, defensibility, and fit dimensions.
- `references/domain-adapters.md`: domain-specific commercialization checks for health, AI/software/data, energy, materials, robotics, and public-sector contexts.
- `references/diligence-checklists.md`: concise checklists for TTO/licensing, regulated/health, pricing/WTP, validation sprints, and adversarial review.
