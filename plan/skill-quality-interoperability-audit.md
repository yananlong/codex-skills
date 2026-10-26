# Individual skill quality and interoperability audit

Review date: 2026-09-06. Baseline: [`955fcc435e651834b03768c136dca6b16ccbae08`](https://github.com/yananlong/codex-skills/tree/955fcc435e651834b03768c136dca6b16ccbae08).

## Scope and evidence boundary

This audit examines all 20 cataloged skill entrypoints across commercialization, documents, research, and writing, treating the instructions as source material rather than invoking any skill. The review also inspected the catalog generator and validator, research-assurance workflow, memory initializer, diligence validator, and novelty literature-binding contract and import boundary. Every individual assessment below identifies the reviewed entrypoint and a concrete next acceptance test.

The assessment distinguishes reproduced utility defects, source-confirmed contract inconsistencies, and recommendations whose runtime consequences remain untested. The two catalog utilities used for local testing were reconstructed from the pinned GitHub contents and matched their Git blob hashes. This was not a full local checkout, and the existing research suite, external services, notebook execution, PDF tools, packaged installations, and model-driven workflows were not executed. Reading every entrypoint is not an exhaustive review of every script, reference, schema, or dependency.

Quality is assessed through trigger precision, bounded responsibilities, input/output clarity, evidence discipline, failure behavior, portability, and verification. Interoperability is assessed through producer/consumer agreement, artifact identity, path resolution, schema/profile compatibility, dependencies, preservation of negative evidence, and regression coverage. Qualitative judgments below are design assessments, not measured model-performance scores.

## Overall assessment

The research core has unusually explicit evidence discipline. Experiment planning, results auditing, and paper planning distinguish execution completion from scientific success, retain negative evidence, bind claims to scoped artifacts, and explain why structural validation cannot establish scientific truth. Those properties should survive any simplification.

The weakest interfaces sit around that core: catalog metadata can falsely appear current, lexical metadata is mistaken for an interface description, independently packaged skills depend on adjacent directories, and some consumers still look in obsolete default locations. The collection is more coherent as a checked-out research suite than as independently installable components. Better interoperability requires executable boundary contracts and distribution tests, not more repeated instructions or a mandatory orchestration layer for every small task.

This PR fixes catalog freshness validation, adds 20 regression tests, and adds catalog CI for all pull requests and pushes to `main`. Other findings are deliberately documented rather than silently represented as repaired.

## Prioritized findings

### QI-01: Catalog validation does not establish freshness

**Priority: high. Evidence: reproduced. Status: fixed in this PR.**

At the baseline, [`validate_current`](https://github.com/yananlong/codex-skills/blob/955fcc435e651834b03768c136dca6b16ccbae08/scripts/validate_skill_catalog.py) compares only skill-file membership and count against regeneration. A catalog with stale descriptions, inputs, outputs, relationships, agent metadata, resources, capabilities, or version metadata can still receive the message that the catalog is valid and current. Malformed `skills` values can also crash the comparison rather than produce a validation error.

The fix compares generated top-level metadata and every generated record field, matching records by source path. Source-defined extensions remain legal, including unfamiliar domains and capability names, while unbacked catalog-only fields are stale. Validation remains read-only, reports affected fields, and fails cleanly on malformed shapes. The accompanying temporary-repository tests reproduce the old failures and pass after the fix. This establishes metadata agreement with the generator, not semantic correctness of the generator's inferences.

### QI-02: Generated metadata is an index, not an executable interface

**Priority: high. Evidence: source-confirmed. Status: open.**

[`extract_outputs`](../scripts/generate_skill_catalog.py) scans filenames throughout the entrypoint rather than distinguishing produced artifacts from consumed inputs, examples, and supporting references. The published [catalog](../skills-catalog.json) contains outputs such as `.context.md`, `.memory.md`, and `.handoff-to-commercialization.json`, losing the parameter name in `<case>` or `<memory_name>`. The inspected commercialization and memory entries also have empty structured inputs despite explicit required inputs in prose. Lexical `related_skills` cannot distinguish a required dependency, optional supplier, consumer, or exclusion route.

Introduce explicit, versioned artifact contracts for tracked interfaces, retaining lexical inference only as labeled discovery metadata. Preserve templates such as `<case>.source-log.md`, distinguish optional and required artifacts, and describe relationship direction. Sidecars can override outputs today, but capabilities are merged with inferred capabilities, so a sidecar cannot remove an incorrect inference. Document that difference or support an explicit replacement policy. Acceptance requires a fixture where consumed files never become declared outputs and placeholder-bearing paths survive intact.

### QI-03: Standalone packaging does not close dependencies

**Priority: high. Evidence: source-confirmed import boundary. Status: open.**

The [research-assurance workflow](../.github/workflows/research-assurance.yml) creates separate skill archives. The [novelty validator](../research/research-novelty-review/scripts/validate_novelty_pack.py) unconditionally imports `review_pack_coverage` from the neighboring systematic-literature-review directory before argument parsing. A novelty-only installation without that sibling cannot even reach its help or structural-validation path. This is a dependency failure implied by the import, not a claim that an isolated installation was executed during this audit.

Declare required companion packages and resolve them during installation, or delay optional imports until the linked profile needs them and provide an actionable dependency error. Add isolated-unzip smoke tests outside the repository layout, including a negative missing-dependency case. Keep standalone project mode distinct from standalone installation: allowing a user to omit a suite root does not make a package self-contained.

### QI-04: Review consumers retain incompatible default paths

**Priority: high. Evidence: source-confirmed. Status: open.**

[Paper review](../research/research-paper-review/SKILL.md) uses `review_results/<slug>_review/`, while [review-loop](../research/research-review-loop/SKILL.md) and the [rebuttal safety gate](../research/research-rebuttal/SKILL.md) still refer to `paper-review/final_issues.json` in several places. Following those existence checks literally can skip an available internal diagnosis. The newer provenance and explicit-path instructions mitigate this problem but do not remove the contradictory defaults.

Resolve artifacts from explicit input first and the recorded artifact index or metadata next, preserving imported paths and latest-round provenance. Treat legacy defaults only as documented fallbacks. Test native, imported OpenAIReview, hybrid round directories, noncanonical explicit paths, and multiple ambiguous workspaces. A missing artifact and an unresolved location must remain different outcomes.

### QI-05: Literature-context and linked-novelty modes need an explicit bridge

**Priority: medium. Evidence: source-confirmed mode ambiguity. Status: open.**

[Paper review](../research/research-paper-review/SKILL.md) and [systematic literature review](../research/research-systematic-literature-review/SKILL.md) agree on a four-file lightweight paper-context exchange. The [novelty assurance contract](../research/research-novelty-review/references/literature-assurance-contract.md) requires seven bound full-review artifacts when `literature_assurance.mode` is `linked`. Both formats can be valid for their intended modes, so this is not evidence that every four-file handoff is broken.

State explicitly when the four-file exchange supports a bounded standalone judgment and when a seven-file assurance pack must be produced before linked validation or stronger positioning. Never manufacture the missing assurance files or reinterpret lightweight context as full assurance. Acceptance should exercise both routes and reject an attempted four-file-to-linked promotion with a clear explanation.

### QI-06: Commercialization has a producer without an explicit consumer contract

**Priority: medium. Evidence: source-confirmed. Status: open.**

[Market/patent diligence](../commercialization/market-patent-diligence/SKILL.md) produces `<case>.handoff-to-commercialization.json` and names commercialization as its downstream decision-maker, but [commercialization](../commercialization/commercialize-academic-research/SKILL.md) does not name that supplier in its sibling relationships or define intake of the handoff. The diligence workflow also mentions an unprefixed handoff filename despite the prefixed output and validator contract.

Add reciprocal intake with schema version, research asset, geographic scope, retrieval dates, source pointers, confidence, unresolved assumptions, and decision questions. Keep legal-status signals and purchase evidence separate from scientific novelty. Test reuse of a completed diligence pack without repeating its searches or silently dropping its limitations.

### QI-07: Diligence validation needs type safety and a completion boundary

**Priority: medium. Evidence: source inspection. Status: open.**

The [diligence validator](../commercialization/market-patent-diligence/scripts/validate_diligence_pack.py) checks required handoff keys before checking that decoded JSON is an object, then calls `.get`. A JSON array or null therefore reaches invalid operations. Required fields are checked for presence, not substantive values or source linkage. The success message correctly says structure is valid, so this should not be misreported as a scientific-validity claim.

Reject wrong root and field types gracefully, preserve a permissive scaffold profile, and add a distinct completed-handoff profile that rejects placeholders and missing provenance. Test valid scaffolds, completed packs, null, arrays, malformed dates, missing sources, and unknown next-skill names. Any known-skill check should remain compatible with new catalog entries.

### QI-08: Memory creation and updating have conflicting semantics

**Priority: medium. Evidence: source-confirmed. Status: open.**

[Memory-builder instructions](../documents/document-memory-builder/SKILL.md) prohibit overwriting without explicit permission but later instruct in-place updating when overwrite is disabled. The [initializer](../documents/document-memory-builder/scripts/init_memory_pack.py) refuses existing files, and sequential writes can create earlier files before a collision at a later file. This leaves creation, missing-file repair, content refresh, and destructive reset insufficiently separated.

Define those four operations explicitly, preserving source history and unresolved questions during refresh. Preflight collisions before creation or stage writes transactionally. Tests should cover existing complete packs, partially existing packs, refresh without reset, denied overwrite, and preservation of an earlier source map after failure.

### QI-09: CI depth is uneven across the collection

**Priority: medium. Evidence: source-confirmed workflow scope. Status: partially addressed.**

The baseline research-assurance workflow has substantial integration coverage for experiment execution, literature-to-novelty, result-audit-to-paper binding, commitment, and prospective evaluation. Its path filters cover nine skill directories, leaving eleven other skills and the root catalog tooling outside those triggers. This is a statement about that workflow, not proof that the excluded skills have no tests anywhere.

The new catalog workflow runs without a closed skill-path allowlist and checks utility regressions plus the committed catalog. It does not execute all skill workflows. Next add a discovered-skill inventory check, representative non-research smoke tests, and isolated package checks, retaining heavier scientific-contract tests as their own tier.

### QI-10: Execution cost and shared ownership need tighter boundaries

**Priority: medium. Evidence: design recommendation. Status: open.**

Paper review and both writing skills prescribe multi-pass worker plans, while technical writing can also call prose-flow revision. Nesting those defaults risks redundant work. Paper review's suggestion that a thorough review usually yields 15-30 issues can also become an unintended issue quota, despite otherwise strong quote-verification and consolidation rules.

Choose one parent plan, treat worker count as a budget rather than a quality proxy, and make cross-cutting passes comment-only until the parent merge. Judge adequacy by risk coverage and evidence, not issue count. Evaluate short, long, already-clean, and high-risk documents, measuring preservation, false positives, and execution cost separately.

## Individual skill assessments

### 1. commercialize-academic-research

[Entrypoint](../commercialization/commercialize-academic-research/SKILL.md). **Strong decision framing, incomplete supplier intake.** Requiring a bounded asset, separating user and buyer, comparing commercialization routes, and demanding evidence-linked validation tests counter common commercialization errors. The distinction between sourced facts and assumptions is useful, as are conditions against unsupported startup and pilot recommendations.

The key repair is QI-06: accept diligence output explicitly rather than rediscovering market facts. Keep scientific audit findings separate from willingness-to-pay evidence. Acceptance: consume one diligence pack, retain source dates and weak links, compare at least two plausible routes, and show which missing evidence changes the decision.

### 2. market-patent-diligence

[Entrypoint](../commercialization/market-patent-diligence/SKILL.md). **Clear evidence scope, weak machine boundary.** Distinguishing patent signals from legal conclusions and demand is appropriate, while jurisdiction, family, ownership, and retrieval context make the search reproducible. The downstream roles are more explicit than in the commercialization consumer.

Unify the handoff filename, validate object and field types, and introduce a completed-pack profile without making scaffolds unusable. Acceptance: source-backed and assumption-only findings remain distinguishable after handoff, and malformed or placeholder-only JSON never masquerades as a completed diligence result.

### 3. adversarial-doc-review

[Entrypoint](../documents/adversarial-doc-review/SKILL.md). **Strong assurance reasoning, broad routing surface.** The property-versus-label checks and bounded verdicts are particularly valuable, and the treatment of unresolved predecessor failures avoids cosmetic closure. However, the broad review trigger can overlap paper review and review-loop without an equally explicit reverse-routing rule in this entrypoint.

Clarify non-paper versus initial-paper versus tracked-review ownership, make unavailable browsing a disclosed limitation rather than a repeated permission loop, and define a writable report destination for URL or read-only inputs. Acceptance: the same manuscript, policy document, and revised research artifact each reach the appropriate owner without recursive routing.

### 4. document-memory-builder

[Entrypoint](../documents/document-memory-builder/SKILL.md). **Good source authority and uncertainty preservation, ambiguous update safety.** Canonical-source precedence, conflict retention, section-aware reading, and separation of volatile facts suit durable reuse. Those benefits depend on reliable refresh semantics, which currently conflict with overwrite rules and initialization behavior.

Repair QI-08 and state that memory is a lossy, source-linked view rather than a substitute for canonical evidence or machine state. Acceptance: a refresh retains unresolved conflicts and prior provenance, retires contradicted facts explicitly, and cannot reset the existing pack accidentally.

### 5. exposition-to-notebook

[Entrypoint](../documents/exposition-to-notebook/SKILL.md). **Useful computable-core workflow, incomplete execution provenance.** Definitions, shapes, assumptions, modular functions, seeded examples, and restart-and-run-all checks form a solid notebook baseline. CPU-only offline defaults and synthetic data reduce unnecessary setup.

The term product-ready is stronger than the listed minimal checks alone establish. Add an execution record with environment, dependency versions, timeout, source mapping, and observed failures, distinguishing synthetic demonstrations from empirical findings. Acceptance: execute a notebook in a fresh kernel and hand its actual result artifacts to results auditing without promoting demonstration data into evidence.

### 6. pdf-book-assembler

[Entrypoint](../documents/pdf-book-assembler/SKILL.md). **Focused page-level scope, under-specified transformation handoff.** Explicit order, selection rules, bookmark targets, and `page_map` are strong foundations for reproducible assembly. The constraints appropriately distinguish assembly from forms and object-level editing.

Clarify when proportional cropping belongs to the trimmer instead, and preserve page mappings for later reviews and source citations. Orientation changes, signatures, annotations, and crop effects need explicit preservation or warning policies. Acceptance: assemble mixed source selections, verify bookmarks against output pages, and carry the source-to-output page map through any subsequent trim.

### 7. proportional-pdf-trimmer

[Entrypoint](../documents/proportional-pdf-trimmer/SKILL.md). **Precise geometry and unusually explicit visual QA.** Required user proportion, linear-margin semantics, shared aspect ratio, CropBox-aware comparison, numerical tolerance, and signature sensitivity create a well-bounded contract. Conservative failure on incompatible geometry is preferable to hidden scaling.

The phrase largest common source page size should be reconciled with the later baseline definition, which must fit every page and is therefore constrained by the smaller compatible pages. Keep the diagnostic report internally when provenance matters, even when only the final PDF is delivered. Acceptance: same-ratio mixed-size, rotated, blank, faint-mark, and full-bleed cases, followed by source-linked visual comparison.

### 8. research-experiment-plan

[Entrypoint](../research/research-experiment-plan/SKILL.md). **One of the strongest stage contracts.** Frozen claims, anti-claims, non-vacuity, failure accounting, explicit gates, and execution declarations provide a concrete bridge to implementation. Keeping technical completion distinct from the scientific gate is essential.

Preserve those controls while making profile and companion-dependency requirements explicit outside the full checkout. The default of three seeds should remain a budget heuristic, not an assertion of adequate statistical power. Acceptance: a completed negative experiment remains a valid completed run but does not activate a success-gated dependent block.

### 9. research-idea-discovery

[Entrypoint](../research/research-idea-discovery/SKILL.md). **Strong filtering and selection-history discipline, one avoidable cardinality rule.** Source basis, disconfirmation, rejected ideas, and exploratory labeling reduce polished-but-unfounded recommendations. The next-stage boundary is clear.

Selecting one to three ideas is allowed, yet the filtering section requires revisiting scope when fewer than three survive. Permit one defensible candidate when the constraints genuinely support only one, without lowering the quality threshold. Acceptance: a constrained corpus with one testable candidate produces a narrow novelty-review handoff, preserving rejected alternatives rather than generating filler.

### 10. research-novelty-review

[Entrypoint](../research/research-novelty-review/SKILL.md). **Strong bounded positioning, fragile dependency and mode edges.** Separating novelty, impact, empirical validity, and actual reviewer independence is sound. Exact literature bindings and conditional rating gates are more meaningful than a generic novelty score.

Address isolated installation in QI-03 and the lightweight-versus-linked distinction in QI-05. Acceptance: structural use works with its declared dependencies, linked mode checks all seven exact artifacts, and an incomplete context exchange cannot authorize a linked rating merely because the report is persuasive.

### 11. research-paper-plan

[Entrypoint](../research/research-paper-plan/SKILL.md). **Strong claim-to-evidence authority.** Canonical JSON, scoped audit bindings, explicit negative-audit accounting, allowed status/action pairs, and reciprocal exhibit/citation links constrain rhetorical overreach. Theoretical and citation evidence are not forced into an empirical-only model.

Make downstream writing consume these bindings read-only and return proposed claim changes for renewed audit rather than changing the authority silently. Acceptance: a partially supported claim is qualified, a same-scope negative audit cannot disappear, and a prose revision cannot strengthen an assertion beyond the linked assurance.

### 12. research-paper-review

[Entrypoint](../research/research-paper-review/SKILL.md). **Rich review workflow, high instruction and execution overhead.** Full-paper understanding, separate pass outputs, quote checking, provenance families, native-model operation, and explicit serial fallback are well designed. Existing imported bundles are preserved rather than forcibly relocated.

Resolve QI-04 and QI-05, remove issue-count pressure, and tie pass count to the artifact's actual risk. The lengthy entrypoint repeats several mode and ownership rules, creating drift risk. Acceptance: a clean short paper receives no invented findings, while a contextualized review records whether external evidence is lightweight or fully assurance-bound.

### 13. research-pipeline-planner

[Entrypoint](../research/research-pipeline-planner/SKILL.md). **Strong orchestration boundaries, central dependency hotspot.** Single-writer state, event replay, frozen work items, explicit pivot authorization, and preservation of negative outcomes make this the suite's control center. The instruction correctly disclaims independent verification and isolation when only local continuity checks exist.

Keep direct one-stage work lightweight and avoid making every skill depend on the planner's whole implementation. Reduce duplicated contract prose by referencing stable versioned boundaries. Acceptance: interruption/replay, failed scientific gates, and unapproved identity changes retain their distinct states without rewriting predecessor history.

### 14. research-rebuttal

[Entrypoint](../research/research-rebuttal/SKILL.md). **Good response discipline, weaker tracked evidence interchange.** Concrete reviews are required, venue constraints are checked, and provenance, commitment, and coverage gates prohibit fabricated experiments and unsupported claims of manuscript changes.

Repair review-path resolution and bind responses to stable issue IDs, actual result artifacts, and specific manuscript revisions. Treat rough page equivalents from a text counter as estimates, not verification of a venue's final PDF page limit. Acceptance: an unresolved major issue remains visible and no response describes a planned experiment or edit as already completed.

### 15. research-results-auditor

[Entrypoint](../research/research-results-auditor/SKILL.md). **Strong scientific-direction and assurance separation.** Exact claim scope, eligible-run accounting, explicit exclusions, predecessor-failure disposition, and JSON/narrative consistency support trustworthy downstream use. Confirmatory evidence can correctly contradict the claim.

Ensure consumers revalidate the same source-mode and assurance profile rather than accepting an attractive verdict string alone. Acceptance: a favorable selected run cannot hide an eligible negative run, retry lineage cannot count as independent replication, and an audit for another scope or paper identity cannot support the manuscript claim.

### 16. research-review-loop

[Entrypoint](../research/research-review-loop/SKILL.md). **Strong issue continuity, remaining location ambiguity.** Preserving prior rounds, imported quotes and ratings, accepted risks, and material assurance failures prevents superficial resolution. The provenance-family compatibility is a good migration policy.

Remove hardcoded legacy review paths and specify a deterministic latest-round resolver, including ambiguity handling and unchanged source IDs. Acceptance: import a canonical paper-review bundle, preserve its identifiers through two rounds, and reject closing a major issue solely because wording or a self-attested field changed.

### 17. research-systematic-literature-review

[Entrypoint](../research/research-systematic-literature-review/SKILL.md). **Strong profile-aware discovery discipline.** Coverage questions, seed recovery, citation searching, corpus freeze, amendments, and explicit assurance limits are stronger than counting papers or producing a PRISMA diagram alone. Domain adapters avoid forcing every field into a biomedical ontology.

Clarify the lightweight context exchange versus full assurance artifacts and package shared coverage code as an explicit dependency. Acceptance: a late novelty-critical omission triggers search repair and an amendment, while a rapid scan remains a rapid scan regardless of how polished the report becomes.

### 18. research-zotero

[Entrypoint](../research/research-zotero/SKILL.md). **Clear corpus ownership, adapter acceptance tests needed.** Narrow library scope, account-based default resolution, raw item preservation, and separate citation exports provide useful inputs to several consumers. Saved references are correctly treated as candidates rather than automatically included evidence.

Define how an MCP-sourced library maps to the same normalized artifact contract as script-based access. Prefer environment or connector credentials over putting secrets in command arguments. Pagination, retry behavior, and snapshot consistency require helper-level testing before reliability claims. Acceptance: equivalent API and connector fixtures preserve library identity, filters, item metadata, and explicit partial-sync status.

### 19. prose-flow-improver

[Entrypoint](../writing/prose-flow-improver/SKILL.md). **Good preservation rules, potentially excessive orchestration.** The instruction appropriately protects lists, tables, procedural formats, filenames, numbers, and caveats, while treating prose flow as a distinct task from factual revision.

Use one shared parent plan when combined with technical revision, and prevent cross-cutting workers from competing with chunk writers. Sentence joining should remain subordinate to readability rather than become a mechanical length preference. Acceptance: adversarial before/after fixtures retain every constraint, preserve required list structure, and introduce neither dangling subjects nor new factual claims.

### 20. technical-writing-reviser

[Entrypoint](../writing/technical-writing-reviser/SKILL.md). **Strong claim preservation, missing explicit authority handback.** The separation of revision from planning and evidence creation is clear. Preserving justified confidence while preventing unsupported strengthening is more useful than indiscriminate caution, and terminology translation is appropriately conditional.

Consume paper bindings and review issues as immutable inputs, recording material proposed claim changes for the owning stage rather than treating a rewrite as new evidence. Coordinate prose-flow work under the same parent. Acceptance: a revision retains numbers, scope, negative results, and supported confidence, while an evidence conflict is surfaced instead of rhetorically resolved.

## Interoperability acceptance matrix

These are proposed tests, not additional results claimed by this audit.

| Boundary | Information that must survive | Required rejection or qualification |
|---|---|---|
| Zotero to literature/ideation | Library identity, filters, raw records, source date | Partial sync or unscreened candidates cannot imply complete coverage. |
| Ideation to novelty | Selected claim, rejected alternatives, source basis, selection history | An untestable or outcome-selected idea cannot gain confirmatory status. |
| Lightweight literature context to novelty | Context paths, scope, access limits, mode | Four context files cannot impersonate a seven-file linked assurance pack. |
| Novelty to experiment planning | Narrow claim, overlap threats, evidence class | A high novelty rating cannot certify empirical validity. |
| Experiment execution to results audit | Claim/block/run identity, lineage, all outcomes, verified gate | Completion cannot substitute for scientific success. |
| Results audit to paper planning | Scope, assurance, negative runs/audits, evidence paths | Wrong-scope or cherry-picked positive evidence cannot authorize assertion. |
| Paper review to review-loop/rebuttal | Resolved workspace, issue IDs, quotes, ratings, latest-round provenance | An obsolete default path cannot silently skip diagnosis. |
| Paper plan/review to writing | Canonical bindings, issue IDs, caveats, proposed changes | A prose edit cannot upgrade evidence or close a technical issue alone. |
| Diligence to commercialization | Asset, jurisdiction, source dates, uncertainty, handoff version | Patent signals cannot become legal conclusions or buying evidence. |
| PDF assembly to trimming/review | Source/output page map, orientation, geometry, warnings | Cropping cannot silently invalidate source locators or clip content. |
| Memory to any stage | Source authority, versions, unresolved conflicts, volatile flags | A compressed memory view cannot replace canonical state or evidence. |

## Validation performed and follow-up order

The new suite runs with `python -m unittest discover -s scripts/tests -p 'test_skill_catalog.py' -v`. All 20 test methods passed locally after the validator change, including subcases for generated fields and malformed shapes. Running the same suite against the baseline validator first produced expected failures and errors. The modified validator and tests also passed `py_compile`.

The local tests use temporary miniature repositories and the exact baseline generator, not stubbed generator return values. They cover fresh catalogs, stale descriptions and outputs, agent changes, added/removed resources, sidecar inputs and extensions, open-ended source metadata, stale record and top-level fields, boolean-versus-integer counts, extra unsupported metadata, missing/deleted/duplicate skills, malformed shapes, CLI exit behavior, and read-only validation. They do not validate Markdown catalog rendering or prove that inferred inputs, outputs, and relationships are semantically correct.

The new CI workflow checks the committed catalog against the full checkout. Full-checkout freshness and hosted CI are separate from the local fixture result, and any hosted outcome should be read from the PR checks rather than inferred from this report. Existing skill integration tests and all proposed acceptance-matrix cases remain outside this audit's executed scope.

Next prioritize dependency-closed packaging and shared review-path resolution, then explicitly version the literature and commercialization handoffs. Follow with safe memory refresh, diligence completion validation, non-research smoke coverage, and budget-aware model evaluations. Prefer small boundary-specific changes with negative tests over rewriting all 20 entrypoints at once.
