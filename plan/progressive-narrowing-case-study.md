# Progressive narrowing as a cross-stage research failure mode

## Purpose

This note extends the skill-quality and interoperability audit with a concrete, user-authorized case study from an active private research pull request. The private manuscript's substantive content is intentionally not reproduced here. Only the workflow pattern needed to evaluate the research skills is retained.

The case exposes a failure mode that is easy to miss when every stage is locally evidence-disciplined: **successive gates can each make a defensible decision to narrow a claim, while the cumulative sequence steadily removes the paper's distinctive contribution until later work must broaden the manuscript again**. Truthful qualification is necessary; a monotone ratchet toward the safest residual claim is not.

## Observed trajectory

The inspected research PR followed this sequence:

| Stage | Local disposition | Cumulative effect |
| --- | --- | --- |
| Initial manuscript | Mechanism-centered paper with a named theoretical contribution and a constructive artifact | Clear, ambitious paper identity, with several claims requiring stronger evidence or positioning. |
| First major comparator gate | `proceed with a narrowed contribution claim` | A comparator win and mixed evidence correctly removed an overgeneralized mechanism claim, leaving a smaller synthesis. |
| Constructive-value gate | `proceed with a narrowed constructive claim` | Earlier constructive artifacts were demoted and the surviving contribution became a smaller set of intervention distinctions. |
| Integration gate | pass | The manuscript was declared internally calibrated to the narrowed claims, even though the cumulative loss of contribution had not been treated as a separate gate failure. |
| Post-gate authoring | explicit broadening of title/abstract, introduction, theoretical framing, discussion, and conclusion | Later commits repaired defensive narrowing and restored a broader reader-facing thesis without reintroducing the unsupported claims. |

The key evidence is the sequence itself: two successive `proceed with narrowed ... claim` decisions were followed by an integration pass, and the next authoring commits explicitly broadened the manuscript and removed defensive narrowing. The local gates were not necessarily wrong about the evidence; the orchestration objective was incomplete.

## Diagnosis: the concession ratchet

The anti-pattern is:

```text
challenged claim
  -> remove unsupported portion
  -> local gate passes
  -> next stage treats the smaller claim as the new baseline
  -> another challenge removes another portion
  -> local gate passes again
  -> final integration optimizes prose around the safest residue
```

This produces a **concession ratchet** because losses are inherited as the new normal while the original contribution is no longer evaluated as a whole. Several mechanisms make the failure likely:

1. **Local correctness substitutes for project value.** A gate asks whether the revised claim is defensible, but not whether the remaining claim still carries the intended scientific or scholarly contribution.
2. **Narrowing is treated as resolution.** A predecessor failure marked accepted with narrowing may correctly retire an overclaim, yet the lost contribution is no longer represented as an active project-level consequence.
3. **Assurance class and semantic scope are conflated.** Evidence that is exploratory may justify keeping an ambitious claim explicitly exploratory, but a workflow can instead shrink the semantic claim until it feels confirmatory or unassailable.
4. **Paper identity is checked stepwise rather than cumulatively.** Several small revisions can collectively change the central object or contribution class even when no individual revision appears to be a pivot.
5. **Comparator wins are interpreted only subtractively.** A strong neighboring explanation should remove unjustified novelty, but can also sharpen a synthesis, boundary condition, mechanism distinction, negative result, or new empirical question. Treating overlap only as a reason to delete claims biases the process toward triviality.
6. **Integration validates consistency after attrition.** Once a narrowed set of claims is internally coherent, a final manuscript audit can pass without noticing that the paper became less useful, less interesting, or effectively different from the committed project.

## Corrective principle

A rigorous research workflow should optimize for the **strongest supportable contribution**, not the **smallest claim that survives criticism**. Negative evidence must change belief, but the response space should include strengthening evidence, lowering assurance without changing semantic scope, sharpening the comparator distinction, reporting a mixed or negative result, reframing the contribution, explicit pivoting, or stopping the paper. Narrowing is one legitimate action among these, not the default repair operation.

The distinction should be explicit:

| Change type | Meaning | Default treatment |
| --- | --- | --- |
| Precision | Same claim, clearer definitions or boundary | Continue normally. |
| Evidence qualification | Same semantic claim, weaker assurance or stronger uncertainty language | Continue while preserving evidence class. |
| Scope narrowing | Smaller population, condition, mechanism reach, or conclusion | Record scientific content lost and test contribution floor. |
| Contribution reframe | Central contribution changes type, for example mechanism -> synthesis or framework -> agenda | Require project-level review before downstream progression. |
| Identity drift | Central research object, minimum publishable claim, or paper-bearing route materially changes | Treat as a pivot/stop decision, even if accumulated through several small revisions. |

## Anti-ratchet contract

Before a stage recommends or accepts claim narrowing, the workflow should answer all of the following:

- What was the original or frozen claim?
- What exact evidence invalidates or weakens part of it?
- What is the strongest claim that the total evidence still supports?
- Can the original semantic claim remain as exploratory rather than being rewritten into a weaker proposition?
- Is there one decisive piece of additional evidence that would resolve the live uncertainty?
- Does the strongest comparator eliminate the contribution, or does it instead identify a boundary, mechanism difference, synthesis, or negative result worth retaining?
- What scientific content is lost by the proposed narrowing?
- Does the remaining contribution still satisfy the project's minimum publishable claim, intended decision role, or venue-level significance threshold?
- Have earlier narrowings accumulated so that the current paper is now a different paper?

A local stage must not answer the last two questions by inspecting only the current wording. The comparison baseline is the frozen paper commitment or, when no formal commitment exists, the earliest explicit central claim and contribution statement available in the tracked lineage.

## Results-auditor implication implemented in this PR

`research-results-auditor` now includes a semantic claim-scope trajectory pass before downstream handoff. The pass requires the auditor to distinguish precision, evidence qualification, semantic narrowing, contribution reframing, and identity drift; to record what was lost and what evidence could restore the stronger claim; to consider claim-preserving alternatives before recommending narrowing; and to escalate cumulative scope loss rather than allowing repeated `proceed with narrowed claim` decisions to become an automatic path to manuscript integration.

The current machine schema does not yet have a dedicated claim-trajectory object, so the skill records the material trajectory through existing limitations, predecessor-failure, and corrective-action fields. That is an explicit limitation: structural validation cannot currently prove that a paper's contribution survived cumulative narrowing.

## Cross-skill implications still open

### Research pipeline planner

Paper-identity control should be cumulative. A sequence of individually permissible refinements can add up to a contribution-class or paper-identity change, and the planner should detect that transition by comparing the current route against the frozen minimum publishable claim, not merely the previous work item.

### Research experiment plan

Decision gates should not have only `proceed`, `revise`, and `stop` semantics where `revise` naturally means `make the claim smaller`. A gate should preserve distinct actions for obtaining decisive evidence, lowering assurance, narrowing scope, reframing the contribution, recording a negative result, pivoting, or stopping.

### Research novelty review

Overlap with prior work should not create novelty-by-exclusion, where each neighboring concept causes another piece of the paper to be deleted until only a trivial residue remains. Novelty review should test the complete contribution bundle and explicitly consider synthesis, boundary-condition, mechanism, artifact, empirical, or negative-result contributions before recommending semantic narrowing.

### Research paper plan

The paper plan should compare the supportable claim set against the paper's contribution floor before converting audits into title, abstract, and section commitments. A manuscript that is perfectly consistent with a severely eroded claim set is not necessarily ready; the correct action may be to gather evidence, reframe transparently, pivot, or stop.

### Research review loop

Repeated issue closure through narrowing should trigger a cumulative-scope review. An issue can be locally closed because the overclaim disappeared while the project-level loss caused by that closure remains open.

## Regression scenario

A cross-skill regression fixture should encode the observed structure without depending on the private manuscript:

1. Start with a frozen central claim and a minimum publishable contribution.
2. Feed one valid negative/comparator result that weakens, but does not fully kill, the claim.
3. Record a local `proceed with narrowed claim` decision.
4. Feed a second valid result that narrows the constructive contribution again.
5. Attempt final paper integration.

The expected behavior is **not** to restore unsupported claims, and it is also **not** to pass merely because the remaining wording is safe. Before integration, the suite should surface cumulative contribution loss, compare the surviving claim against the frozen contribution floor, enumerate claim-preserving alternatives, and require an explicit project-level disposition if the paper identity or contribution class has changed.

A second regression should demonstrate the positive case: two evidence-driven qualifications that leave the central object, contribution class, and minimum publishable claim intact should proceed without a false scope-ratchet alarm.

## Quality criterion

The desired invariant is:

> Every downstream claim must be no stronger than its evidence, while the workflow must also make cumulative loss of scientific contribution visible rather than silently rewarding maximal defensiveness.

This keeps evidential discipline and research productivity aligned instead of treating them as opposites.
