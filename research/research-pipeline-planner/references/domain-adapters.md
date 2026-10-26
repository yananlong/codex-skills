# Domain Adapters

A domain adapter lists the checks a stage adds when the project's evidence has a particular shape. The generic contracts in each skill still apply; an adapter only adds the threats that are typical for its kind of evidence.

This file is shared. The canonical copy lives in `research-pipeline-planner/references/`, and identical copies ship with `research-experiment-plan`, `research-results-auditor`, `research-novelty-review`, `research-paper-plan`, and `research-review-loop`. `scripts/tests/test_shared_modules.py` at the repository root fails when a copy drifts, so edit the canonical copy and copy it over.

`research-systematic-literature-review` keeps its own screening adapters in its `references/domain-adapters.md` (bias rubrics for judging other people's papers). Where an adapter below has a counterpart there, the counterpart is named.

## Selection rule

1. Pick the adapter that matches the evidence the central claim rests on, which may differ from the paper's topic. A paper about LLMs whose central evidence is a proof uses `theory`; a paper about measurement whose central evidence is a re-derivation of published numbers uses `recomputation-audit`.
2. Use at most one primary adapter and one secondary adapter. The secondary adapter covers a supporting evidence line, such as the judge model in a Bayesian measurement study. When three or more seem to apply, the claim set is probably too broad; take that to the planner before adding adapters.
3. When none fits, use no adapter and say so. A poorly fitting adapter adds checks that do not bear on the claim.
4. Record the choice where the stage records its scope: the research brief for the planner, the plan header for experiment plans, the limitations or narrative of an audit, the novelty memo, the paper plan's scope section, and the review report. Write the adapter IDs, for example `adapters: bayesian-measurement (primary), llm-evaluation (secondary)`.
5. Revisit the choice when the commitment's identity changes (D3 or D4): a pivot often changes what the central evidence is.

## `llm-evaluation`

Use when the central evidence is measured behavior of language models on tasks, benchmarks, or judged outputs.

- Plan and experiment: pin every model by provider, name, version, and access date; fix decoding settings and seeds; budget runs for prompt-template sensitivity; state how contamination of the benchmark into training data will be checked or bounded.
- Audit: record judges in `measurements[].judge` with identity, version, and whether they were blinded to the condition; report the number of model and task comparisons with the correction applied; check that aggregate scores agree with per-item or per-category results; treat API nondeterminism as a diagnostic and rerun when it could change the verdict.
- Novelty: test the objection that the work is a new benchmark run, a new prompt, or a rerun of a known evaluation on newer models.
- Paper: report model versions with access dates, prompts or their location, judge identity, and the date range of the evaluation; keep claims about "models" scoped to the models tested.
- Review: attack contamination, judge bias toward its own model family, cherry-picked prompts, and conclusions drawn from one decoding setting.

## `bayesian-measurement`

Use when the central evidence is a posterior from a measurement model: item response, latent variable, hierarchical, or mixture models of a construct.

- Plan and experiment: state the estimand on the latent scale and how it maps to the claim; fix priors before fitting and plan a prior-sensitivity run; plan identifiability checks (simulation-based recovery on synthetic data with known parameters).
- Audit: record convergence diagnostics (split R-hat, bulk and tail effective sample size, divergent transitions) and posterior predictive checks as `measurements[].diagnostics`; report credible intervals with their level; when diagnostics fail, abstain with `abstained_diagnostics_failed` before arguing from the posterior; check measurement invariance before comparing groups.
- Novelty: test the objection that the model is a standard IRT or hierarchical model applied to a new dataset.
- Paper: report priors, the sensitivity result, diagnostics, and posterior predictive checks; distinguish what the model assumes from what the data show.
- Review: attack identifiability, prior dominance in sparse cells, invariance assumptions, and point summaries of skewed posteriors.

## `recomputation-audit`

Use when the central evidence is a re-derivation of reported numbers from stored outputs, released data, or released code, whether the original work is the project's own or a third party's.

- Plan and experiment: list every number to be recomputed and its source; record digests of the inputs before recomputing; pin the software environment; set the match criterion in advance (exact, or within a stated tolerance and why).
- Audit: set `audit_kind` to `recomputation` and list the re-derived outputs as evidence with source `recomputation`; separate the numbers recomputed from the numbers taken on trust; report each mismatch with its size and the most likely cause, and keep the original value alongside the recomputed one.
- Novelty: a recomputation is a contribution only when the mismatch or its cause is new; test whether the discrepancy is already reported in errata, issues, or follow-up work.
- Paper: report the match rate, the tolerance, the environment, and where the inputs came from; describe mismatches without speculating about intent.
- Review: attack input provenance, version drift between the original and the recomputation environment, and tolerances chosen after seeing the results.

## `theory`

Use when the central evidence is definitions, theorems, proofs, or formal constructions. Literature-review counterpart: `theoretical-mathematical`.

- Plan and experiment: list the theorems to be proved with their standing assumptions; plan a search for counterexamples at the boundaries of each assumption; treat simulations as illustrations of a proved result, never as its evidence.
- Audit: record the status of each result (proved, proof sketch only, conjectured) and whether the proof was checked, by whom, or formalized; record failed proof attempts and found counterexamples as evidence against the claim.
- Novelty: trace each result to known theorems under other names and notations, including special cases of older results and reductions to standard constructions; search adjacent formal literatures in their own vocabulary.
- Paper: state every assumption where the result is stated; mark which results are new and which are restated.
- Review: attack hidden assumptions, gaps between the stated and the proved result, and claims that rest on unproved lemmas.

## `conceptual`

Use when the central evidence is arguments, distinctions, and frameworks. Literature-review counterpart: `conceptual-interdisciplinary`.

- Plan and experiment: state the thesis in one sentence and the distinctions it introduces; name the strongest opposing positions to be answered; decide which claims will be operationalized and tested and which stay conceptual.
- Audit: separate the conceptual claims from empirical claims the argument borrows, and audit the borrowed claims against their sources; check that each key term is used in one sense throughout.
- Novelty: trace each named concept across fields, including earlier uses under other names; search each contributing discipline in its own venues.
- Paper: define terms before using them; answer the strongest objection to the thesis, including one from outside the home field.
- Review: attack equivocation, straw opponents, and empirical claims presented as conceptual ones.

## `tabmol`

Use for the DDI-as-OOD framework agenda: drug-drug interaction prediction treated as a pairwise out-of-distribution problem.

- Plan: treat the contribution as a framework and protocol, without a new model. Make the deliverables explicit: a pairwise OOD threat model, a split and leakage audit spec, shift-severity quantification, a reporting table and statistical test plan, and a failure-mode catalog. Decide which OOD regimes are in scope (one new drug, both new, scaffold shift, mechanism or class shift, temporal shift), whether non-edges are negatives or unlabeled, how temporal censoring and discovery bias are handled, and what evidence makes the framework general beyond DDI. Put the threat model in `research-brief.md`, split definitions and audit outputs in the task board and artifact index, and record every narrowing of the framework claim in the decision log.
- Experiment: the decisive matrix should show which pairwise regimes are evaluated, whether censoring or missingness explains an observed drop, whether the handling of negative or unlabeled pairs changes the conclusion, whether framework claims survive across more than one split family, and whether statistical uncertainty and classwise behavior agree with the headline result.
- Audit: check that each split corresponds to a defined pairwise regime; whether drift could come from label mix or missingness instead of OOD difficulty; whether negatives are defensible or should be unlabeled; whether top-k, calibration, and classwise behavior matter more than one aggregate score; and whether the result supports a framework claim or only a dataset-specific observation.
- Novelty: test the objections that the work is only scaffold, temporal, and inductive splits with better packaging; a DDI benchmark paper instead of a general pairwise OOD framework; or a result about DrugBank missingness instead of robustness. Pressure-test whether the novelty is the pairwise OOD taxonomy, the split and leakage audit spec, shift-severity quantification, the reporting and testing standard, or a reusable framework instantiated on DDI.
- Paper: center the manuscript on the framework contribution, the pairwise regimes and what each approximates, split audits, censoring-aware interpretation, metric design, why the framework generalizes beyond DDI, and limitations around negative labels, discovery bias, and deployment claims.
- Review: attack novelty overreach (a framework, or another split?), temporal censoring (could apparent drift be discovery bias?), regime ambiguity (does OOD mean one new drug, both new drugs, unseen pairs, or unseen scaffolds?), label semantics (are missing edges negatives without justification?), and metric mismatch (do aggregates hide imbalance, calibration, or regime-specific failures?). Ask what artifact proves the framework contribution, what a skeptical reviewer attacks first, and which claim to narrow if the evidence stays weak.
