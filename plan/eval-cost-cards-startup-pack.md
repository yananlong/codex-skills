# Agentic AI Evaluation Cost Study Plan

Status: prose-polished planning draft  
Repository: `yananlong/eval-costs`  
Primary artifact: `plan/eval-cost-cards-startup-pack.md`  
Last major revision: 2026-06-09

## 0. Reframing

This project should be framed as a study of **the cost of doing AI evaluations**, not as a product named "Eval Cost Cards." A cost-reporting template may become one output, and it may eventually be absorbed into Every Eval Ever (EEE), Inspect, Eval Factsheets, or another documentation standard. The main contribution, however, is broader: to understand how evaluation artifacts report, omit, reconstruct, and normalize the resources required to produce AI evaluation scores, with special attention to agentic evaluations.

The guiding question is:

> How do AI evaluation papers, leaderboards, frameworks, and public eval datasets report-or fail to report-the resources required to produce their scores, and what would an auditable cost-reporting standard look like for agentic evaluations?

This framing is deliberately broader than asking how many dollars a benchmark costs. The research problem is that evaluation evidence is produced through a chain of resource-consuming activities: model calls, judge calls, tool calls, sandbox execution, retry handling, human review, failed runs, dataset maintenance, and infrastructure. These activities are often visible only in fragments. Papers may report scores but omit usage. Frameworks may record tokens but not human labor. Provider dashboards may show bills but not per-instance trajectories. Leaderboards may report cost summaries without enough metadata to reproduce them. A useful study should therefore ask what is reported, what can be reconstructed, what remains unknowable, and how these gaps affect scientific reproducibility, score comparison, and industry use.

EEE remains the preferred backbone. It already treats evaluation results as structured, queryable evidence rather than as static paper tables, and it records provenance, prompt templates, inference parameters, system states, aggregate JSON, detailed JSONL, and instance-level token usage. It also distinguishes `single_turn`, `multi_turn`, and `agentic` interaction types. These features make EEE a natural substrate for cost-adjacent metadata. At the same time, EEE should not be treated as a complete solution. Many cost components are not present in public records, and some data will require outreach to labs, leaderboard maintainers, framework developers, and companies. Independent reference runs may also be needed when public traces are too sparse.

## 1. Project naming and scope

The name should keep the research object broad and avoid prematurely productizing a reporting artifact. The repo name `eval-costs` works because it is neutral. The phrase "cost card" should remain only as a possible shorthand for one downstream standardization artifact, not as the identity of the work.

Possible titles include **Cost of Doing AI Evals**, **The Hidden Cost of AI Evaluation**, **Accounting for the Cost of Agentic AI Evaluation**, **How Much Evidence Can You Buy?**, **Cost Reporting and Reconstructability in AI Evaluation Artifacts**, **Beyond Scores**, and **From Token Counts to Evaluation Cost**. The strongest titles are those that foreground the empirical study rather than the proposed reporting module.

## 2. Thesis

The core thesis is that AI evaluation results are increasingly used as scientific, commercial, and governance evidence, but the resource cost of producing those results is rarely reported in a way that is auditable or comparable. Agentic evaluations make this gap especially important because a score may depend on long trajectories, tool use, retry loops, judge models, browser or computer use, sandbox execution, human adjudication, and failed attempts. A systematic audit, paired with reconstructability case studies, can reveal where reporting breaks down and define a minimal standard for future work.

This is a meta-scientific problem first. When benchmark scores guide papers, leaderboards, procurement decisions, safety cases, and model releases, readers need some account of the resources used to generate the evidence. That does not mean every paper must publish a full internal invoice. It does mean that the boundary of the reported evidence should be clear. A reader should be able to tell whether a score includes only candidate-model inference, whether judge-model calls were counted, whether failed runs were excluded, and whether human review or tool execution was material.

Agentic evaluation also differs from ordinary inference. In a single-turn benchmark, token usage may be a reasonable first-order proxy for cost. In an agentic benchmark, the same task can generate many calls, branch through different tools, fail and retry, spawn sub-agents, run tests, read files, browse websites, or wait on sandboxes. The final score alone hides these trajectories. Cost-aware reporting can therefore change not only budgeting but also interpretation: a high-scoring agent that reaches its score through very expensive failures may be less practical than a slightly lower-scoring agent with predictable resource use.

The proposed standard must fit existing infrastructure. It should be EEE-compatible and Inspect-compatible from the beginning, and it should learn from production observability systems such as Langfuse, Weave, and LangSmith. The goal is not to compete with those tools. The goal is to connect evaluation evidence, public datasets, framework logs, and cost-aware reporting in a way that researchers and maintainers can actually adopt.

## 3. Boundaries and non-goals

The first version of this project should not claim to estimate the true full operational cost of all AI evaluation. That would create false precision. The defensible first contribution is an empirical audit of reporting practices, a taxonomy of cost components, and a reconstructability analysis that distinguishes what is public, what is inferred, and what remains missing.

The project should also avoid several overclaims. It should not claim that cost-aware evaluation is new, because Green AI, HELM, efficiency studies, observability tools, and recent agent-efficiency papers already occupy nearby territory. It should not claim that EEE already solves cost reporting; EEE offers a strong substrate but not a complete cost ledger. It should not claim that market demand is proven simply because observability products track cost. Those products demonstrate adjacent workflow demand, but willingness to pay for eval-specific reporting still needs validation. The project should not claim patent defensibility without a real patent landscape. Finally, it should not reduce cost to tokens or treat public API pricing as ground truth. Tokens and public price tables are useful, but they are partial and time-sensitive proxies.

A good first paper would be modest and precise: it would show how evaluation artifacts currently report resource use, where public reconstruction fails, and what fields would make future agentic evaluations more auditable.

## 4. Research questions

The study should begin with descriptive questions before moving to standard design. The first question is prevalence: how often do AI evaluation papers, leaderboards, framework outputs, and public datasets report cost-related information at all? Relevant evidence includes token usage, wall time, working time, tool calls, compute hours, dollar estimates, energy, human labor, LLM judge usage, retries, and failed runs.

The second question is granularity. A cost statement can be attached to a call, turn, instance, trajectory, model, benchmark, leaderboard submission, result table, or end-to-end study. These levels are not interchangeable. A per-benchmark dollar estimate may be useful for budgeting but insufficient for diagnosing expensive failures or comparing agents.

The third question is component coverage. The key distinction is whether reported cost includes only candidate-model inference or also scoring, tools, agents, retries, sandboxes, infrastructure, and human work. Agentic evaluations are likely to be most misleading when only the visible model tokens are reported.

The fourth question is reconstructability. Given a public evaluation artifact, what can be reconstructed under transparent assumptions? The study should distinguish reported cost, reconstructable minimum cost, expanded reconstructable cost, and unknown cost. The unknown category is a feature, not a failure: it makes the boundary of the evidence visible.

The fifth question concerns time and pricing. Does an artifact report enough information to connect usage to a dated price table? This matters because model prices change, cached tokens may be priced differently, context windows can affect rates, batch or priority tiers can alter cost, and tool or container charges may be billed separately.

The sixth question is the agentic gap. Are agentic benchmarks more likely than single-turn or ordinary multi-turn evaluations to omit cost components that materially affect interpretation? A useful study should compare interaction types rather than assume that all evaluations have the same cost structure.

The seventh question is rank instability. Would cost-aware metrics change leaderboard interpretation? Candidate metrics include score per dollar, cost per successful task, score under a fixed budget, budget required to reach a threshold, and Pareto frontiers over score and cost.

The final question is standard design. What minimal reporting standard would make evaluation-cost claims auditable without making adoption too burdensome? The answer may be an EEE module, an Eval Factsheets extension, an Inspect converter, or a standalone template. It need not remain a permanent "card."

## 5. Definition: the cost of doing an eval

The cost of doing an evaluation is the resource consumed to produce an evaluation claim. The claim may be a benchmark score, leaderboard submission, safety case, paper result, model comparison, or audit report. This definition is broader than model inference cost because evaluation also involves scoring, validation, failure handling, data maintenance, and reproducibility work.

The study should distinguish four cost views. **Reported cost** is what the paper, leaderboard, dataset, or framework states. **Reconstructable cost** is what can be calculated from public metadata, traces, logs, and dated pricing assumptions. **Operational cost** is what the evaluator actually paid or consumed, including private pricing, internal compute, failed pilots, human labor, and infrastructure. **Decision-relevant cost** is the subset that changes a downstream decision, such as choosing a model, selecting a benchmark, budgeting a safety evaluation, or deciding whether an agentic benchmark is feasible.

The study will rarely observe true operational cost directly. It should therefore focus on reported cost, reconstructability, and missingness. This framing prevents the work from implying a precision it cannot support while still producing useful evidence.

## 6. Layered cost taxonomy

The taxonomy is the backbone of the study. It should appear in the audit rubric, extraction sheet, data schema, and any proposed standard. The table below gives a compact overview; the prose that follows explains why each layer matters.

| Layer | Short description | Unit |
|---|---|---|
| Model inference | Candidate calls | tokens, dollars |
| Agent execution | Control flow | turns, steps |
| Tools | External actions | calls, dollars |
| Environment | Runtime substrate | seconds, sessions |
| Scoring | Judges and graders | calls, tokens |
| Human labor | Manual work | hours, roles |
| Infrastructure | Compute and storage | VM/GPU hours |
| Run management | Pilots and failures | runs, retries |
| Data maintenance | Benchmark upkeep | hours, versions |
| Governance overhead | Reviews and approvals | hours, artifacts |

### 6.1 Model inference cost

Model inference is the baseline layer. It includes input tokens, output tokens, cached input tokens, reasoning tokens where exposed, model identifier, provider, service tier, endpoint, temperature, sampling configuration, context length, and price source. These fields are often the easiest to log and are therefore the most likely to appear in public artifacts.

For agentic systems, model inference is still not simple. Input tokens may dominate because the model repeatedly re-ingests context, tool outputs, code, browser state, and prior messages. A single `total_tokens` field may hide whether cost came from prompts, completions, reasoning traces, cached tokens, or tool-generated context. The study should therefore avoid treating aggregate token counts as a complete accounting unit.

### 6.2 Agent execution cost

Agent execution cost captures the scaffolding around model calls. It includes the number of turns, messages, planning steps, sub-agent calls, retry loops, failed calls, tool-selection calls, memory updates, context compaction steps, and early-stopping behavior.

This layer is crucial because two runs on the same task can consume very different resources. A successful short trajectory and an unsuccessful long trajectory have different scientific meanings even if the final score is binary. Agent execution fields help identify expensive failures, fragile strategies, and systems that succeed only by spending heavily.

### 6.3 Tool and environment cost

Tool and environment cost includes web search, browser actions, computer-use actions, shell commands, code execution, API calls, database calls, file search, container sessions, Docker execution, network egress, and storage. This layer is essential for browser agents, coding agents, cyber agents, data-analysis agents, and scientific agents.

These costs are often invisible in papers because they sit outside the model API call. They can nevertheless be central to the evaluation. A browser benchmark may be dominated by environment interaction, while a coding benchmark may depend on repeated test execution and sandbox behavior. A useful standard should therefore ask not only how many model tokens were used but also what the agent was allowed to do and what those actions consumed.

### 6.4 Scoring cost

Scoring cost includes exact-match scripts, unit tests, test suites, LLM judges, reward models, expert adjudication, rubric generation, calibration examples, and judge ensembles. LLM-as-judge pipelines create a second inference layer, and that layer should be reported separately from candidate-model use.

Separating candidate cost from scoring cost matters because the evaluator can be more expensive than the system under evaluation. A benchmark may appear cheap if only candidate inference is counted, but become costly once judging, adjudication, and retries are included. This distinction is also important for reproducibility because a published score may depend on a specific judge model, rubric, or adjudication protocol.

### 6.5 Human labor cost

Human labor includes benchmark construction, expert annotation, rubric writing, prompt design, manual adjudication, failure triage, leaderboard verification, private data cleaning, and outreach. This layer is hard to price and is therefore often omitted.

The standard does not need to force every lab to publish salary-adjusted dollar figures. A more realistic minimum is to report whether human labor was involved, which roles were involved, and whether approximate hours are available. If exact hours are sensitive or unavailable, the artifact should say so. A redacted or missingness flag is more honest than silent omission.

### 6.6 Infrastructure cost

Infrastructure cost includes GPU time, CPU time, cloud instance hours, local cluster time, storage, logging, observability, container orchestration, database usage, and region or data-residency constraints. For self-hosted models, token price may be the wrong abstraction. For API models, provider infrastructure is mostly hidden, but local tools and sandboxes can still impose meaningful cost.

This layer matters most when comparing API-based and self-hosted evaluations, or when evaluating agents that run code, browse the web, or operate inside virtual machines. It also matters for secure or regulated settings where regional processing, private networking, or data isolation can change the resource profile.

### 6.7 Run-management cost

Run-management cost includes pilot runs, prompt sweeps, ablations, failed submissions, repeated seeds, partial reruns, cache warmups, and debugging runs. It separates the cost of reproducing one final score from the cost of discovering, validating, and publishing that score.

This layer is likely underreported and difficult to reconstruct. It should still be represented because it is often decision-relevant. A lab deciding whether to adopt a benchmark needs to know not only the cost of one clean run, but also the likely cost of iteration, failure, and rerunning under changed model versions.

### 6.8 Maintenance and governance cost

Benchmarks require maintenance. They need versioning, contamination checks, task repairs, deprecation decisions, moderation, documentation, and public communication. For safety, cyber, medical, and legal evaluations, review and governance overhead can also be material.

The first study may not quantify this layer, but it should record whether artifacts acknowledge it. Maintenance and governance costs are part of the cost of sustaining evaluation evidence, even when they are not part of one model run.

## 7. Reporting status labels

Every cost component should receive a reporting status. Status labels are more important than a single total because they reveal the evidential boundary around the estimate.

| Status | Meaning |
|---|---|
| Measured | Directly logged |
| Estimated | Formula-based |
| Imputed | Assumption-filled |
| Self-reported | Author stated |
| Redacted | Known but hidden |
| Missing | Not reported |
| Not applicable | Truly irrelevant |

A cost estimate with explicit missingness is more useful than a precise-looking number with hidden omissions. The reporting standard should therefore make absence visible rather than treating unreported components as zero.

## 8. Systematic literature review plan

The systematic review should cover AI evaluation methodology and infrastructure, with emphasis on agentic AI evaluations, benchmark reproducibility, resource accounting, cost-aware evaluation, evaluation documentation, and observability. The research question is: what does current evidence show about the reporting, measurement, and reconstructability of the resource costs required to produce AI evaluation results, especially in agentic evaluations?

The technical exposition level should be standard. The study is empirical and methodological rather than mathematical. Cost-normalized metrics can be defined precisely later, but the first review should prioritize evidence extraction, publication status, reporting practices, and practical gaps.

The default date range should be 2016-06-09 through 2026-06-09. This range captures modern neural benchmark culture, Green AI, HELM-style broad evaluation, LLM-as-judge methods, production observability, and recent agentic benchmarks.

Sources should be included when they directly address at least one of the following: evaluation frameworks or datasets with usage-relevant metadata; benchmark papers or leaderboards for LLMs, multimodal systems, or agents; agentic evaluation papers with token, time, tool, or budget information; cost-aware or efficiency-aware evaluation methods; evaluation documentation frameworks; observability systems that track usage or cost; Green AI or environmental reporting work relevant to evaluation; and public pricing or billing documentation needed for reconstruction.

Sources should be excluded when they only discuss model training cost without implications for evaluation reporting. Pure product marketing should be excluded unless it documents concrete telemetry fields. Generic commentary about AI expense should be excluded unless it contains methods, data, or reporting implications. Legal and patent documents belong in the diligence track rather than the academic synthesis unless they directly affect commercialization strategy.

The review should label source class and publication status. Peer-reviewed papers and accepted venue records should anchor the academic evidence. arXiv preprints can be included when they capture emerging agentic-cost evidence, but the evidence table should not blur preprints with peer-reviewed work. Framework documentation, leaderboards, public datasets, vendor documentation, patent databases, and lab outreach each serve different purposes and should not be treated as interchangeable evidence.

Initial discovery should use queries such as `"AI evaluation" cost reporting benchmark`, `"LLM evaluation" token cost reporting`, `"agentic evaluation" cost tokens tool calls`, `"AI agents" token consumption SWE-bench`, `"LLM-as-judge" cost evaluation`, `"benchmark" "cost per success" "LLM"`, `"Green AI" reporting inference cost`, `"HELM" efficiency evaluation language models`, `"Eval Factsheets" AI evaluations`, `"Every Eval Ever" evaluation schema token_usage`, `"Inspect" evaluation cost limit token limit working time`, `"Langfuse" token cost tracking`, `"Weave" LLM cost tracking`, and `"LangSmith" tracing evaluation agents`.

Patent reconnaissance should be logged separately. Useful initial queries include `"large language model" "cost" "token" "evaluation" patent`, `"large language model" "cost-aware" routing patent`, `"LLM" "token usage" "evaluation" patent`, `"agent" "tool use" "cost" "large language model" patent`, and `"automated benchmark" "cost" "large language model" patent`.

Screening should use two stages. Title and abstract screening should classify each record as include, maybe, exclude, or duplicate. Full-text screening should record exact reasons. Preprints should be checked for published or accepted versions. OpenReview records should be preferred over arXiv only when they correspond to accepted full papers.

The extraction sheet should capture citation, URL, publication status, benchmark or framework, evaluation type, agentic status, cost components mentioned, cost components measured, cost components priced, pricing date, trace availability, human labor reporting, tool or environment reporting, scoring or judge reporting, missingness notes, relevance, and risk-of-bias notes.

Quality assessment should rate each source on transparency, directness, reproducibility, completeness, and conflict risk. A paper with strong agent-cost analysis but no public trajectories may be useful while still having limited reproducibility. A vendor doc may be reliable for its own telemetry fields but weak as evidence of market demand. A leaderboard may demonstrate reporting practice without proving operational cost.

## 9. Initial evidence map

This section is a scoping synthesis, not a completed PRISMA review.

EEE is the strongest public substrate for this project. It frames evaluation results as structured records and captures source provenance, model specification, evaluation library, metric configuration, generation configuration, detailed instance files, interaction type, and token usage. It also offers converters for Inspect, HELM, and lm-eval-harness. The implication is that EEE can host the public audit and any eventual reporting extension. The study should avoid unnecessary forking: EEE-compatible fields and reconstruction tests are the right starting point.

Inspect is the most important evaluation-framework reference because it supports agent, tool, sandbox, and model evaluation workflows. Its documentation discusses open-ended model conversations, agent evaluations with tool usage, total time, messages, tokens, cost, working time, and agent limits. The distinction between wall time and working time is especially valuable because it shows that raw elapsed time can be misleading when retries, rate limits, or shared resources are involved. Inspect logs can therefore serve both as a benchmark for good telemetry and as a substrate for independent reference runs.

Production observability tools show that cost telemetry is already operationally important. Langfuse tracks usage and costs for LLM generations and embeddings, supports arbitrary usage types, and can ingest or infer cost from model definitions. Weave tracks LLM costs from token usage and model pricing and supports custom cost schedules. LangSmith provides tracing, evaluation, and deployment workflows for LLM and agent applications. These tools do not prove demand for a new eval-cost product, but they show that the field already has concepts, data models, and potential integration paths.

Recent agentic-cost papers show why the problem is urgent. Work on SWE-bench trajectories reports that agentic coding tasks can consume far more tokens than ordinary code reasoning and that same-task token consumption can vary widely. AgencyBench, SWE-Effi, CostBench, and budget-constrained agent papers similarly treat resource use as central to evaluating agents. These sources support urgency but not full novelty. The proposed contribution is not the claim that agent costs matter; it is the empirical audit and reconstructability analysis across public evaluation artifacts.

Benchmark ecosystems provide the first empirical testbed. SWE-bench is already cost-aware at the leaderboard layer, while OSWorld and WebArena evaluate agents in realistic environments where tool and environment cost are central. GAIA, AppWorld, Cybench, InterCode, HAL-style benchmarks, and agentharm are additional candidates through EEE and linked papers or leaderboards. The first corpus should include both coding and non-coding agents, because coding benchmarks are data-rich but may bias the study.

The documentation and Green AI literature provide the closest academic neighbors. Green AI argued for reporting efficiency and financial price tags. Strubell et al. quantified financial and environmental costs in NLP training. Counting Carbon studied emissions reporting. Efficiency Misnomer warned that incomplete efficiency reporting can mislead conclusions. HELM offered a multi-metric evaluation framework including efficiency, and Eval Factsheets proposes structured documentation for evaluations. The study should position itself as an extension of this literature: it focuses on the cost of producing evaluation evidence, especially agentic evidence.

Provider pricing complexity makes reconstruction fragile. Public price tables vary by model, endpoint, service tier, context length, cached-token treatment, batch or priority processing, and separate tool or container charges. All dollar estimates must therefore record provider, model, endpoint, service tier, pricing source URL, pricing effective date, cache treatment, and omitted charges. A reconstructed public price is not the evaluator's actual invoice.

## 10. Study design

The project should be organized as four linked empirical studies, with a fifth adoption track if commercialization remains relevant.

### Study A: Cross-sectional audit of cost reporting

The first study should measure how often and how well AI evaluation artifacts report the resources required to produce scores. The units of analysis may include a paper result, leaderboard row, public dataset record, framework output, benchmark submission, or evaluation report. The initial corpus should combine EEE records, agentic benchmark papers and leaderboards, HELM/lm-eval/Inspect-compatible outputs, SWE-bench, OSWorld, WebArena, GAIA, AppWorld, Cybench, InterCode, agentharm, HAL-style agent benchmarks, LLM-as-judge evaluation papers, and available safety or cyber evaluation reports.

A practical first sample would include 100 to 200 artifacts, with deliberate oversampling of agentic evaluations and a comparison group of single-turn and non-agentic multi-turn evaluations. The main outputs should be prevalence of cost reporting, prevalence by component, reporting quality score, missingness heatmap, agentic versus non-agentic gaps, and differences between papers, leaderboards, datasets, and framework logs.

### Study B: Reconstructability audit

The second study should ask which costs can be reconstructed from public metadata. For each artifact, the analysis should produce several views: reported cost, minimum reconstructable cost, expanded reconstructable cost, and unknown or redacted cost. Minimum reconstructable cost usually includes candidate-model token cost only. Expanded cost may include judge calls, tool calls, container cost, and storage when metadata exists. Unknown cost should be reported explicitly rather than silently omitted.

The goal is not to produce a false total. A typical conclusion might say that a public artifact supports candidate-model token reconstruction but not judge cost, failed runs, container time, or human review. That kind of statement is useful because it tells readers what the public evidence can and cannot support.

### Study C: Lab outreach and independent reference runs

The third study should fill missing data and test the proposed taxonomy against real workflows. EEE will not contain every cost field. Some labs may have logs but no public cost summaries. Some leaderboards may have per-submission metadata but no public traces. Some papers may have budget information in private lab notebooks. Lab outreach and independent reference runs should therefore be part of the research design rather than an afterthought.

The outreach channel should ask maintainers and authors for narrow, low-burden telemetry. The request should focus on usage fields rather than private invoices, and it should allow redaction. The independent-run channel should rerun selected evaluations with full instrumentation. These runs do not need to reproduce state-of-the-art scores. Their purpose is to validate the taxonomy and identify which fields are difficult to capture.

Candidate reference runs include a small SWE-bench Lite or SWE-bench Verified subset, a small OSWorld subset, a WebArena task subset, a GAIA or AppWorld subset, a non-agentic benchmark baseline, and an LLM-as-judge evaluation pipeline. The minimum instrumentation should capture candidate-model tokens, judge-model tokens, tool calls, web or search calls, shell or container calls, wall time, working time, retries, failures, scoring time, pricing source, and human notes. Failed and partial runs should be preserved because they are cost evidence.

### Study D: Cost-aware leaderboard interpretation

The fourth study should examine whether cost reporting changes interpretation. Candidate metrics include score per dollar, cost per successful instance, cost per solved task, score under a fixed budget, budget required for a score threshold, Pareto frontier of score versus cost, expensive failure rate, judge cost fraction, tool cost fraction, and cost variance across repeated runs.

These metrics should supplement, not replace, raw performance. Cost-normalized metrics can be gamed if they reward cheap failure. The right presentation is joint: score, cost, uncertainty, and missingness should appear together.

### Study E: Adoption and commercialization interviews

A fifth track should test adoption and commercial relevance. Interviewees should include benchmark maintainers, evaluation framework maintainers, academic labs, AI safety institutes, enterprise AI platform teams, model providers, observability vendors, and procurement or governance teams.

The interviews should ask what cost data teams already log, what they would share publicly, which fields are sensitive, what would be too burdensome, what would help procurement or governance, whether EEE integration would increase adoption, whether dollar estimates are necessary, and what reporting granularity is acceptable. These interviews are needed because market relevance cannot be inferred from observability-tool existence alone.

## 11. Audit rubric

Each artifact should receive a score from 0 to 3 across several dimensions. The rubric should remain simple enough for reliable coding while preserving prose notes for complex cases.

| Dimension | 0 | 1 | 2 | 3 |
|---|---|---|---|---|
| Tokens | none | aggregate | per model | per instance |
| Time | none | vague | wall time | working + wall |
| Tools | none | mentioned | counted | priced |
| Judge | none | mentioned | counted | priced |
| Retries | none | policy | counted | logged |
| Failures | none | excluded | counted | analyzed |
| Human labor | none | mentioned | role-level | hours |
| Pricing | none | dollars only | source | dated source |
| Missingness | none | caveat | component list | status flags |
| Reproducibility | none | partial | code/logs | full trace |

The numeric score should not replace qualitative judgment. A paper may score well on token reporting while still omitting judge cost or human adjudication. The coding guide should therefore require a short note for every artifact that explains the main interpretive limitation.

## 12. Data model and possible EEE extension

The study may produce a cost-reporting module, but the module should be treated as a research output rather than the whole project. It should be optional, EEE-compatible, and separable from the empirical claims. Neutral names such as `cost_report`, `resource_report`, `eval_resource_usage`, `cost_trace`, or `resource_accounting` are preferable to branding the artifact as a "cost card."

An aggregate-level record should include schema version, currency, pricing source URL, pricing effective date, cost method, provider, service tier, candidate-model cost, judge-model cost, tool cost, environment cost, infrastructure cost, human labor cost, run-management cost, total reported cost, missing components, redacted components, and confidence. The schema should allow nulls and status flags because many components will be unknown.

An instance-level record should capture candidate input tokens, candidate output tokens, cached tokens, reasoning tokens where available, judge input and output tokens, model-call counts, judge-call counts, tool-call counts, retries, failed calls, wall time, working time, environment sessions, and cost status. The schema should not require exact dollars at the instance level; usage-only reporting may be enough, with dated price reconstruction performed downstream.

A minimal schema sketch is useful for implementation, but the philosophy is more important: the reporting module should make missingness visible, separate candidate cost from scoring cost, and avoid treating unreported components as zero.

## 13. Lab outreach packet

The outreach packet should be designed for low friction. The minimum request should ask for benchmark name, model or agent name, evaluation date, number of instances, candidate-model token usage, judge-model token usage if any, number of tool calls, wall time, retry policy, whether failed runs are included, whether human review was used, and whether a pricing source is available.

The optional request can ask for per-instance traces, tool-specific counts, container or sandbox time, error logs, repeated-seed runs, pilot-versus-final distinction, cache behavior, service tier, region or data-residency constraints, and human hours by role. These fields will not always be available, but asking for them establishes the future norm.

The outreach should explicitly allow redaction. Labs should be able to withhold exact dollars, private discounts, proprietary prompts, individual reviewer names, private data, and sensitive tool outputs. Usage counts and status flags may be enough for the study. The tone should be collaborative rather than punitive: the goal is to build a field norm where cost evidence has receipts.

## 14. Market and commercialization diligence

The strongest market signal is workflow convergence. Public evaluation infrastructure needs reproducibility and comparability. Production observability platforms already track usage and cost. Enterprises and safety teams increasingly need defensible evaluation evidence. These facts suggest that the study is commercially relevant, but they do not yet prove a monetizable product.

The likely wedge is not a standalone observability platform. The stronger path is an open study, public dataset, EEE-compatible reporting module, adapter layer, and optional audit service. Credibility should come before monetization. A dashboard or enterprise product should be built only after interviews or pilot audits show real demand.

The market evidence has different confidence levels. EEE's suitability as a substrate is high-confidence because it is visible in public project materials and data structure. Inspect's cost-adjacent logging is high-confidence because it is documented. The existence of cost telemetry in Langfuse, Weave, and LangSmith is also high-confidence. The claim that agentic cost is high and variable is medium-confidence because much of the most relevant evidence is recent and preprint-heavy. Buyer demand and patent defensibility remain low-confidence until interviews and a real patent landscape are completed.

Likely academic users include benchmark maintainers, meta-evaluation researchers, AI safety researchers, agent benchmark authors, reproducibility reviewers, and labs with limited compute budgets. Likely industry users include AI platform teams, AI FinOps teams, enterprise evaluation teams, governance and risk teams, procurement teams, model providers, observability vendors, and safety institutes. Public-sector users may include AI evaluation institutes, standards bodies, regulators using evaluation evidence, and grant or procurement reviewers.

The substitutes are provider dashboards, spreadsheets, Inspect logs, Langfuse, Weave, LangSmith, leaderboards, and narrative notes in papers. These are not direct competitors at the early stage. Provider dashboards show what one account paid. Observability tools show application traces. Papers and leaderboards show scores. The proposed study connects these worlds by asking whether a public evaluation claim can be audited and reconstructed.

Commercial hypotheses should remain explicit. Benchmark maintainers may adopt cost reporting if it is easy and does not require private invoices. Enterprise teams may value eval-cost reporting when comparing model vendors or agent frameworks. AI safety and governance teams may value it because evaluation claims are becoming part of assurance cases. Observability vendors may prefer integration over competition. Academic labs may value budget planning for expensive agentic evaluations. Each of these is a hypothesis that requires interviews or pilots.

The patent posture is unresolved. A preliminary public-web reconnaissance did not identify a clean blocking family specific to cost reporting for AI evaluation artifacts, but this is not a freedom-to-operate conclusion. A real patent landscape should search Google Patents, USPTO, WIPO/PCT, EPO, and major assignees using terms such as LLM cost attribution, token usage accounting, agent trace cost, evaluation provenance, budget-aware agent evaluation, cost-aware model routing, tool-use cost accounting, benchmark cost estimation, evaluation trace compression, and agent observability.

If patentable opportunities exist, they are likely to be concrete methods rather than the broad study idea. Candidate areas include trace compression for cost reconstruction, automated missingness detection, cost attribution across nested agent/tool/judge calls, budget-aware evaluation scheduling, cross-provider price normalization, and reproducible cost ranges under changing price schedules. For now, the stronger defensibility is dataset quality, community adoption, integrations, and trust.

## 15. Evidence ledger

The current evidence base supports the project direction but not every commercialization claim. The ledger below should be expanded into a separate source log.

| Claim | Type | Confidence | Missing proof |
|---|---|---:|---|
| EEE is a good substrate | Source-backed | High | Field audit |
| Reporting is fragmented | Hypothesis | Medium | Audit data |
| Agentic evals need richer layers | Source-backed | High | More domains |
| Industry tracks usage cost | Source-backed | High | Buyer interviews |
| Monetization exists | Hypothesis | Low | Pilots |
| Patent defensibility is weak | Inference | Low | Patent search |
| Independent runs are needed | Inference | High | Budget plan |

The weakest claims are the market and IP claims. They should stay labeled as hypotheses until interviews, pilots, and patent searching produce stronger evidence.

## 16. Execution plan

Phase 0 should repair the scope and planning structure. The conceptual project should be renamed from "Cost Cards" to an agentic evaluation cost study, while keeping the existing file path for continuity. The repo should add a source log, extraction template, outreach template, reference-run checklist, and decision gates. The exit criterion is simple: all planning documents should agree that the main deliverable is a study, not a card product.

Phase 1 should conduct the scoping review and corpus design. Over two to three weeks, the team should build a search log, screen 100 to 200 candidate sources, build an evidence table, classify publication status, identify benchmark families, define cost-reporting dimensions, and construct an artifact sampling frame. The exit criterion is a corpus strong enough to justify a systematic audit.

Phase 2 should run the EEE-first public audit. Over three to six weeks, the team should pull EEE records, map available fields to the cost taxonomy, identify benchmarks with token usage, identify agentic interaction types, trace linked source artifacts, sample papers and leaderboards for manual coding, and produce a missingness heatmap. The exit criterion is the first empirical result table.

Phase 3 should build reconstructability prototypes. Over four to eight weeks, the team should implement a pricing-table abstraction, build a minimum-cost estimator, add an expanded-cost estimator, test both on EEE and Inspect-style logs, report unknown components, and validate calculations by hand. The exit criterion is a reproducible cost reconstruction notebook.

Phase 4 should combine lab outreach and reference runs. Over six to twelve weeks, the team should contact benchmark maintainers, request minimal telemetry, run small instrumented evaluations, compare public metadata with obtained and self-run metadata, and revise the schema and rubric. The exit criterion is at least two case studies with richer cost data.

Phase 5 should produce the paper and public release. Over eight to sixteen weeks, the team should write the manuscript, release the dataset, release code, publish the schema proposal, share the work with EEE and Inspect maintainers, and decide whether a dashboard or commercialization follow-on is justified. The exit criterion is a submission-ready manuscript and a public-facing repository.

## 17. Proposed repository structure

The repository should keep planning, review, audit, schema, run, and diligence artifacts separate. A proposed structure is:

```text
eval-costs/
  plan/
    eval-cost-cards-startup-pack.md
    source-log.md
    outreach-plan.md
    decision-gates.md
  literature-review/
    protocol.md
    search-log.md
    screening-log.md
    evidence-table.md
    synthesis.md
  audit/
    rubric.md
    extraction-template.csv
    artifact-sampling-frame.csv
    coding-guide.md
  data/
    raw/
    interim/
    processed/
  notebooks/
    eee-field-audit.ipynb
    reconstructability-prototype.ipynb
    leaderboard-cost-frontiers.ipynb
  schema/
    resource-report.schema.json
    examples/
  runs/
    inspect-reference-run/
    swebench-lite-subset/
    osworld-subset/
  diligence/
    market-map.md
    patent-recon.md
    evidence-ledger.md
  paper/
    outline.md
    figures.md
```

The `.gitignore` should keep raw data, credentials, local logs, and large traces out of the repository unless they are intentionally published.

## 18. Decision gates

The first gate asks whether the gap is real. The project should proceed only if the audit shows meaningful missingness across public evaluation artifacts. If most artifacts already report cost sufficiently, the work should be reframed as a synthesis rather than an audit.

The second gate asks whether EEE is enough. If EEE fields and linked artifacts support useful reconstruction, the project should remain EEE-first. If EEE lacks enough relevant agentic records or if linked artifacts are inaccessible, the study should widen its corpus and treat EEE as one source among several.

The third gate asks whether independent runs are feasible. If small reference runs can capture the taxonomy within a reasonable budget, they should be included. If they are too expensive, the project should lean more heavily on outreach, public traces, and lightweight baselines.

The fourth gate asks whether the proposed standard is adoptable. If maintainers find the reporting burden acceptable, the project can develop an EEE-compatible module. If they find it too heavy, the module should be reduced to a smaller minimum viable schema.

The fifth gate asks whether there is commercial pull. Commercialization should proceed only after interviews or pilot audits show real demand. A dashboard should not be built before this evidence exists.

## 19. Risks and mitigations

The largest risk is false precision. Dollar estimates can look exact even when they omit private discounts, failed runs, judge calls, human review, or infrastructure. The mitigation is to report ranges, methods, pricing dates, status labels, and missing components.

A second risk is token reductionism. If the study becomes only token counting, it will miss the distinctive cost structure of agentic evaluation. The mitigation is to keep the layered taxonomy central and to require tool, environment, scoring, retry, and human-labor fields where applicable.

A third risk is benchmark bias. Coding agents may dominate the corpus because their data and leaderboards are more accessible. The mitigation is to include non-coding agent benchmarks such as browser, OS, web, science, cyber, and general-assistant tasks.

Private pricing opacity is also unavoidable. Public price reconstruction may differ from actual invoices, especially under enterprise discounts, batch pricing, regional processing, or internal compute. The mitigation is to distinguish public reconstruction from operational cost and to preserve pricing-source metadata.

Lab nonresponse is likely. Authors and maintainers may not have telemetry, may be unable to share it, or may consider it sensitive. The mitigation is to allow redaction, ask for usage counts rather than invoices, and run small reference evaluations where outreach fails.

Cost-normalized metrics can also create incentives for cheap failure. The mitigation is to report raw score and cost jointly, show Pareto frontiers, and explicitly warn against treating score-per-dollar as a replacement for task success.

Finally, the planning documents may drift as the project evolves. The mitigation is to maintain a source log, decision gates, and status notes so that the repository records why the scope changed.

## 20. Immediate next actions

The next step is to turn this plan into working scaffolding. The repository should add `plan/source-log.md`, `audit/rubric.md`, `audit/extraction-template.csv`, `literature-review/protocol.md`, and `diligence/patent-recon.md`. The team should then create a small EEE field-audit script, build a list of 100 candidate artifacts, draft the lab outreach email, and choose the first reference-run target.

These actions should be sequenced so that the empirical audit starts before any dashboard or product work. The research claim needs evidence before the commercialization path can be evaluated.

## 21. Source log seed

This is only a seed log, not a full review log. The full project should keep exact query strings, retrieval dates, source classes, and screening decisions in separate files.

| Query | Purpose | Status |
|---|---|---|
| Every Eval Ever schema | EEE fields | useful |
| Inspect cost limit working time | Eval telemetry | useful |
| Langfuse token cost tracking | Industry telemetry | useful |
| Weave LLM cost tracking | Industry telemetry | useful |
| SWE-bench cost leaderboard | Benchmark practice | useful |
| AI agents token consumption | Agent cost | useful |
| Green AI cost reporting | Prior art | useful |
| Eval Factsheets | Documentation | useful |
| LLM cost patents | IP recon | weak |
| Agent tool cost patents | IP recon | weak |

Seed sources include Every Eval Ever, the EEE datastore, Inspect setting limits and eval logs, Langfuse, W&B Weave, LangSmith, SWE-bench, OSWorld, WebArena, Green AI, Strubell et al. on NLP energy and policy, Counting Carbon, Efficiency Misnomer, HELM, Eval Factsheets, How Do AI Agents Spend Your Money?, AgencyBench, SWE-Effi, CostBench, Budget-Constrained Agentic LLMs, and current provider pricing documentation such as OpenAI API pricing.

## 22. Bottom line

The study should start as a meta-evaluation and reporting project. Its core task is to audit how evaluation artifacts report the cost of producing scores, measure what is missing, reconstruct what can be reconstructed, and propose a lightweight EEE-compatible reporting module for the parts that matter most in agentic evaluation.

A cost card may eventually be one output, but the study should not be centered on that artifact. The central deliverable is evidence: a systematic audit, a taxonomy, a reconstructability analysis, and a practical path for labs and benchmark maintainers to report cost without exposing sensitive operational details.
