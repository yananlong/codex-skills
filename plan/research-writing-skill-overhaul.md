# Research and Writing Skill Overhaul: Stress-Test Findings and Program

Date: 2026-10-25. Scope: the eleven `research/*` skills and the two `writing/*` skills.

## Method and evidence boundary

Five independent reviewers each took one cluster of skills and stress-tested it against the
owner's recent research repositories rather than against the suite's own fixtures:

| Cluster | Skills | Material |
| --- | --- | --- |
| orchestration | research-pipeline-planner | bnp_ai_evals, frontier_plateau, llm_triangulation, normality_milieu (four real harness suites) |
| discovery | research-idea-discovery, research-systematic-literature-review, research-novelty-review, research-zotero | bnp_ai_evals novelty review, normality_milieu literature context, sedimented_use and normality_milieu manuscripts' bib files, three real ideation packs |
| experiments | research-experiment-plan, research-results-auditor | bnp_ai_evals and frontier_plateau experiment plans, results trees and audits; llm_triangulation plans |
| paper | research-paper-plan, research-paper-review, research-review-loop, research-rebuttal | two real first-pass review bundles, 47 review-loop states, four paper-plan packs, three LaTeX manuscript trees |
| writing | technical-writing-reviser, prose-flow-improver | passages from four manuscripts across ML theory, ML empirical, vision, and HCI/philosophy registers |

Every shipped script was run on scratch copies of the real artifacts. Steps that only a model
performs were walked through against concrete requests. Each finding is tagged in the source
reports as verified (observed) or judged (reading). This document consolidates 59 findings; the
per-cluster reports with test cases live outside the repository because they reference private
material. Nothing here quotes manuscript text or results.

The method has limits. Walkthroughs estimate what a model would do; token costs for multi-agent
paths are estimates, not measurements; and no live Zotero, arXiv, or model-backed run was made.

## What the real projects showed

Eight themes recur across clusters. They matter more than any single finding.

1. **Validators fail on real artifacts and pass on empty ones.** None of the four real harness
   suites passes the planner's pack validator. Neither real first-pass review bundle passes the
   review-bundle validator. Neither real experiment plan passes the experiment-pack validator.
   None of the four real paper-plan packs passes linked validation. Meanwhile an untouched novelty
   scaffold, an empty experiment pack, an empty audit draft, a nonexistent evidence path with an
   all-zero digest, and a rating-5 novelty decision with no prior-art rows all pass. The owner has
   responded by forking validators, adding quarantine profiles, and hand-writing fields the schemas
   reject. A validator that mature projects abandon protects nothing.

2. **The narrowing ratchet has no machine anchor anywhere.** Every cluster found the same gap from
   its own side. The planner accepts a chain of four successive claim narrowings. The novelty skill
   asks only for the narrowest defensible positioning. The auditor's new trajectory pass (PR #25)
   has no schema field. The experiment-plan gate vocabulary makes "smaller claim" the only
   non-terminal repair. The reviser's critique intake turns "blocks claim X" into disclaimers.
   Three projects independently invented a contribution-floor field that the commitment schema
   rejects, and two projects hand-built the retain/narrow/omit table the auditor lacks.

3. **There is no lightweight path.** "Sanity-check these numbers", "find prior art I am missing
   in this draft", "what should I do next", and "review this revised draft" each land on the
   heaviest workflow: a 4 KB audit JSON with invented IDs, a seven-file linked novelty pack, a
   harness initialisation offer, or a fresh ten-pass first review. The skills say "standalone"
   but the output contracts and validators do not.

4. **Multi-agent defaults are disproportionate and contradict their own references.** A routine
   "review then revise" request costs 21 to 32 agent passes if each skill takes its default, and
   in practice every real run recorded a serial fallback. Cross-cutting passes contradict the
   disjoint-ownership rule. No skill owns the pass budget when skills chain.

5. **Handoffs do not line up on disk.** The owner's repos have at least six review layouts; the
   default paths in review-loop, rebuttal, and the planner's review-stage contract match none
   of them. The literature context bundle has no bridge to the linked novelty pack. The planner
   and experiment-plan validators parse run-blocks differently. The rebuttal and review-loop
   issue IDs collide. Five rating dialects coexist in one project.

6. **LaTeX source trees are the owner's medium, and no skill handles them.** Past review
   extractions took `\documentclass` as the title. Half the `.tex` files in one manuscript tree
   are unreachable from `main.tex`. One manuscript routes every number through slot macros with
   line-ending provenance comments; a naive sentence-joining rewrite deletes most of the
   paragraph from the PDF. No skill reads the per-manuscript `.bib` files all projects use.

7. **Register and domain are hard-coded to empirical ML.** The reviser hedges theorems and would
   neutralise a position paper's coined terms. The auditor's checklist has no Bayesian or
   LLM-judge items; the owner's MCMC standards live in a repo `AGENTS.md`. A single-project
   adapter (TabMol DDI/OOD) ships in six skills with no selection rule, and no adapter exists for
   LLM evaluation, Bayesian measurement, recomputation audits, theory, or conceptual work.

8. **Runtime-specific packaging.** Ninety mentions of one vendor's runtime in the paper-review
   skill, an unpinned engine installed into the skill directory, `agents/openai.yaml` sidecars
   that other runtimes ignore, and viz output labelled with the wrong runtime. The owner now
   works mostly from a different runtime.

## Program

### Phase 1: mechanical fixes with regression tests (this branch)

Each item below is a defect with verified evidence, a bounded fix, and a regression test that
fails on the previous code. All of them landed in this branch.

Writing skills (done in this branch):
- Formal and argumentative support types in claim discipline; theorem hypotheses are the scope, no empirical hedges on proved statements (writing F-1).
- Critique intake with staleness check and claim-change note; "blocks claim X" means do not assert X, not write a disclaimer (writing F-2).
- Symmetric merge audit: weakened sentences need named support; abstract/contributions/conclusion compared for shrinkage; precedence between caveat restoration and negation deletion; concessive-narrowing patterns added to the scan (writing F-3).
- Connectives are claims in technical prose; prose-flow examples no longer invent "because" or deny-then-claim framing; reviser runs first when both apply (writing F-4).
- Source-format safety for LaTeX and Markdown in both skills (writing F-5).
- Register profiles and coined-term protection, new `references/register-and-format.md` (writing F-6).
- Serial default when the artifact fits in context; comment-only cross-cutting passes; one orchestration when skills chain (writing F-7).
- Graded overclaim example, evidence-conflict rule, specific limitation example (writing F-8).
- Length-budget trigger, rebuttal routing, near-miss routing table (writing F-9).
- Catalog sidecars for both writing skills; the generator now lets an explicit sidecar list replace lexical inference (writing F-10, QI-02).
- Runtime-neutral wording; serial when running inside a subagent (writing F-11).
- Drafting has an owner. Earlier workflows drafted manuscript sections, rebuttal responses, and reports inside the research skills with no writing discipline, and the writing skills, being revision-only, could only patch the result. A companion skill, `technical-writing-drafter`, now owns first drafts. It starts from the supporting artifacts (`inventory_artifacts.py`), derives the claim list from bindings, audits, claim maps, evidence tables, and issue boards (`build_claim_ledger.py`), writes a one-page brief, drafts evidence-bearing sections before framing sections, traces every number in the draft to a source (`check_draft_numbers.py`), and gates on tells before handing to the reviser, all under a one-page `references/drafting-contract.md` (claims listed with support before writing, visible `[EVIDENCE NEEDED]` markers, register and format rules, the tells recipes, and a `prose_tells.py --max-density 20` gate on the draft). Paper-plan hands its bound claims to that mode instead of to an unowned "drafting" stage, rebuttal's response prose is drafted under it, review-loop routes wording problems to it, and every other prose-producing skill (paper review, auditor narrative, novelty and literature reports, idea selection, experiment-plan narrative, the planner's brief and episodes) names the contract at its output boundary.
- Machine-prose tells: a shared catalogue with a recipe and the legitimate use for each habit (dashes, deny-then-claim contrasts, signpost adverbs, significance inflation, participial tails, tricolons, summary chains, kickers, uniform rhythm, meta-commentary, hedge stacks, bolded lead-ins, tone), a stdlib scanner that reports density per thousand words and compares a revision with its source, a workflow step and an audit requirement in both writing skills, and removal of the two rules in our own skills that prescribed the pattern ("end with the implication" and "2 to 4 sentences per paragraph").

Discovery skills:
- Novelty validator runs standalone; sibling import is lazy with a clear error; CI installs the skill alone and runs it (discovery F-3, QI-03).
- Zotero fetch honours `Total-Results`, paginates fully by default, records `partial`; export terminates; API key never written to disk; HTTP errors are specific (discovery F-7).
- Scaffolds initialise ratings to null; completed packs reject null ratings and TODO cells (discovery F-4).
- `bib_inventory.py`: cited keys vs bib entries from a LaTeX tree, with a citation-audit table and corpus-manifest-shaped records; a manuscript citation-audit path in the literature-review skill (discovery F-8).
- Retired ABANDON/REFRAME/PROCEED labels replaced; both narrowest-defensible and strongest-supportable positioning asked for; integration paths fixed; theory and conceptual domain adapters added (discovery F-6 text, F-11, F-12).

Paper skills:
- `count_limits.sh` counts raw characters per response and fails on any over-limit section (paper F-8).
- Review-bundle validator is provenance-family aware and resolves sibling round folders (paper F-1).
- `init_review_loop.py --from-state` continues a loop without renumbering or dropping issues; empty required fields fail loudly (paper F-3).
- Rebuttal pack keeps the raw pasted reviews and uses `EXT-<handle>-<n>` IDs (paper F-11).
- Runtime-neutral wording; viz runtime label from an argument; LaTeX source accepted and flattened with a source map (paper F-12, F-7). On the real bundles the family-aware validator now passes both first-pass reviews and fails one imported round for the eleven issues whose quotes were lost, which is the loud failure the owner wanted.
- Paper-plan description names the lightweight outline path and venue porting (paper F-13 part).

Experiments and planner:
- `status` and `experiment-lineage` are read-only and refuse a root without an event log (orchestration F-3).
- `--force` refuses to discard event history without an explicit flag; brief and decision log are never deleted; `--adopt` imports an existing project (orchestration F-2).
- Commitment validator and transitions ledger agree on `identity_anchors`, `state`, and D3 authorization targets (orchestration F-5).
- Audit narrative template no longer parses as a real audit; empty audit lists report "draft"; exploratory experiment-pack profile rejects placeholders (experiments F-9).
- `validate_results_audit.py --root` checks evidence paths and digests against files (experiments F-3).
- Lightweight sanity-check path in the auditor; `paper_id` optional for exploratory standalone audits; trigger descriptions carry negative examples (experiments F-7, F-12).
- Planner quick start split into standalone and orchestrated; hard stops scoped by mode (orchestration F-9).
- Experiment-pack validator accepts versioned claim and run-block envelopes and ignores history tables under tracker headings (experiments F-5, validator side only: the init script still writes bare arrays because the paper-plan and planner-runtime loaders require them; see D2 and D15).

Repository:
- Research CI compiles every skill script, discovers every `tests/` folder, and packages every research skill without tests (QI-09).
- PR #25's catalog-freshness validator and results-auditor trajectory text are included.

### Phase 2: design decisions for the owner

These need a decision before code. Each is sketched in the cluster reports with a proposed
schema or rule; the decision is which shape to adopt, since several skills must share it.

| # | Decision | Skills | Source findings |
| --- | --- | --- | --- |
| D1 | One claim-trajectory object (`change_class`, `content_lost`, `alternatives_considered`, `restoring_evidence`) shared by the commitment's `selection_history`, the auditor, novelty decisions, and the reviser's claim-change note; a `contribution_floor` with a non-vacuity outcome in the commitment; a validator rule that two or more narrowings trigger a project-level review | planner, auditor, novelty, experiment-plan, reviser | orch F-4, exp F-4, exp F-8, disc F-6, writing F-2, PR #25 case study |
| D2 | One decision vocabulary (technical outcome, gate result, verifier decision, route action, evidence-class action) in `suite-contract.md`, with `decision_if_unproven` and gate "Revise" cells carrying an action enum plus free text | planner, experiment-plan, auditor | orch F-8, exp F-8 |
| D3 | Pack validation treats approved digests as historical facts (`superseded` / `drifted`), allows withheld artifacts, drops the empty-directory requirement | planner | orch F-1 (blocker) |
| D4 | Runtime subcommands for pivot request, pivot decision, and commitment edits so identity changes enter the hash chain | planner | orch F-6 |
| D5 | A supervised harness profile and a technical attempt budget that does not consume the scientific one | planner | orch F-7 |
| D6 | Audit schema additions: `standalone_runs`, `measurements` (estimate, interval, diagnostics, judge identity, multiplicity), `audit_kind`, evidence `source` enum extension, `abstained_diagnostics_failed` disposition | auditor, paper-plan | exp F-1, F-2, F-11 |
| D7 | Run `kind` for unplanned, precursor, diagnostic, and retry runs; `check_plan_drift.py` | experiment-plan, auditor | exp F-6 |
| D8 | Novelty rating gates in structural mode (cap at 3 unless linked or validated context mode); `literature_assurance.mode: context`; `promote` and `--link` helpers; schema migration for pre-1.1 decisions | novelty, literature-review | disc F-1 (blocker), F-2, QI-05 |
| D9 | Ideation schema for route-level re-ideation: evidence class, predecessor failures, switching cost, identity change, per-idea next skill including paper-review and stop | idea-discovery | disc F-5 |
| D10 | One review-issue schema and summary schema, one `review_schema.py` normaliser, one conversion table; `validate_review_state.py` | paper-review, review-loop, rebuttal, planner | paper F-2 |
| D11 | `resolve_review_artifacts.py` replacing every literal `paper-review/...` default; one canonical location for new rounds | planner, review-loop, rebuttal, paper-review | paper F-4, orch F-8, QI-04 |
| D12 | Ownership rule for multi-agent work: only the skill the user invoked spawns workers; the parent sets a budget (quick 1, standard 3, deep 5 to 8); review owns diagnosis, the reviser owns prose per issue cluster, prose-flow is a final pass | paper-review, review-loop, reviser, prose-flow | paper F-5, writing F-7, QI-10 |
| D13 | Remove the upstream engine from the default path: keep the validator and a stdlib consolidator, move OCR/viz/provider review to an optional reference with a pinned install outside the skill directory | paper-review | paper F-6 |
| D14 | One venue table with verified-on dates (page limits, mandatory sections, response limits) shared by rebuttal and paper-plan; venue porting as a diff of two rows | rebuttal, paper-plan | paper F-9 |
| D15 | Paper-plan bindings to gates and value slots; `--report` mode; `--work-items` optional for standalone audits; never invent audit links | paper-plan | paper F-10 |
| D16 | One shared `research/references/domain-adapters.md` (llm-evaluation, bayesian-measurement, recomputation-audit, theory, conceptual, tabmol) with a selection rule, replacing six copies | all research | exp F-10, disc F-11, orch F-11 |
| D17 | Move prospective-evaluation machinery to repo-level `evals/`; exclude from skill packages | planner | orch F-11 |
| D18 | Search-log columns that web-search models can fill honestly (`results_inspected`, `tool`, `spot-checked`), one query per row, dated novelty logs | literature-review, novelty | disc F-9 |
| D19 | Stage gates move into the owning sibling SKILL.md; `stage-gates.md` becomes an index | planner and all stage skills | orch F-8 |
| D20 | Decided: `technical-writing-reviser` keeps its name and stays revision-only. A companion skill, `technical-writing-drafter`, owns first drafts and kickstarts writing from the supporting artifacts (audits, tables, literature reviews, paper plans, issue boards) with an artifact inventory, a derived claim ledger, a brief, and number-tracing and tells gates before handoff to the reviser | drafter, reviser, prose-flow, all prose-producing skills | landed |

Recommended order: D3 and D8 first (the two blockers), then D1 and D2 together (they define the
shared vocabulary that D6, D7, D9 depend on), then D10 and D11 together (one issue schema and one
resolver unblock the whole paper cluster), then D12 and D13, then the rest.

### Phase 3: polish

Trigger near-miss lines in every description (all clusters list them), catalog sidecars for every
research skill, runtime-neutral `agents/` metadata, and removing the remaining project-specific
debris.

## Borrowed designs

`borrowed-ideas.md` records the public skill designs read for this overhaul (the autoresearch loop
and its forks, Anthropic's skill-creator, Superpowers, the agentskills.io specification, and four
research-writing skills) and where each borrowing landed. It fixes the designs for D10 (review
evidence notes), D15 (numeric-evidence selectors as value slots), and D18 (claim cards and fetch
status in the search log), and adds an iteration-loop mode to the experiment-plan skill, route
tables to the two largest skills, trigger-evaluation sets under `evals/`, and three style rules for
how the remaining skill text should be rewritten.

## Acceptance tests for the overhaul

The existing suites are green and fast but exercise none of the defects above. The overhaul is
complete when CI carries real-shape fixtures (structure only, synthetic content) for:

- a nested harness suite with later-edited approved artifacts, a gitignored artifact, extension fields, and a `commitment-transitions.json` ledger that validates (D3, D4, orch F-5);
- a four-step narrowing chain that the planner, auditor, and novelty validators each flag at step two (D1);
- the two real review-bundle families and a sibling-round hybrid layout that validate, continue a loop, and feed a rebuttal pack without hand editing (paper F-1, F-3, F-4);
- a standalone exploratory audit that validates without `paper_id`, with runs, seeds, and one measurement (D6, exp F-7);
- a novelty decision at rating 5 with no prior-art rows that fails in every mode (D8);
- a three-file LaTeX tree with slot macros and provenance comments that flattens with a source map and survives a reviser pass with identical visible text (paper F-7, writing F-5);
- the standalone novelty install running from its own archive (done).

## What to keep

The reviewers were asked what should survive. The hash-chained event log and byte-stable replay;
the separation of technical outcome, verifier decision, gate result, and scientific disposition;
gate-conditioned activation; the commitment concepts (paper identity, minimum publishable claim,
pivot triggers, kill conditions), which all six real commitments adopt; the honest-boundary
language in shorter form; summary-first review with disjoint pass outputs and quote
verification; the reviser's positive-framing guidance on clean input; prose-flow's
list-preservation rules; and the fast test suites as a base for the real-shape fixtures above.
