# Bounded CT-ML Route Acceptance Test

## Evaluation class

This is a public, bounded-corpus, self-reviewed development acceptance test of the integrated route:

`research-idea-discovery → research-pipeline-planner → research-systematic-literature-review → research-novelty-review`

It evaluates known-item recall, causal search repair, cross-stage identity continuity, adverse-overlap retention, and novelty calibration. It does not estimate unseen recall, comprehensive field coverage, independent reviewer agreement, or research-suite effectiveness outside the declared corpus.

## Frozen corpus

The test uses repository metadata from three pinned README snapshots:

- `bgavran/Category_Theory_Machine_Learning@78180832afd6870211b5ca05702879ab98e0ab2f`
- `madnight/awesome-category-theory@57af40ed428c84df0e2d37e16d76ee17dbb61824`
- `jules-hedges/awesome-applied-category-theory@a5afc837d0eff94bf607bd01f9c295288866f32f`

Outbound links are limited to title and abstract inspection after repository retrieval. Full-text retrieval, unconstrained web search, citation-graph expansion, author expansion, and new repositories are outside this run.

## Recall result

The frozen denominator contains 18 public quasi-gold records, including 11 critical records.

| Measure | Initial | After repair |
| --- | ---: | ---: |
| Overall known-item recall | 15/18 = 0.8333 | 18/18 = 1.0000 |
| Critical-item recall | 9/11 = 0.8182 | 11/11 = 1.0000 |

The initial plan missed:

- `K15`: *A Category-theoretical Meta-analysis of Definitions of Disentanglement*;
- `K17`: *Position: Topological Deep Learning is the New Frontier for Relational Learning*;
- `K18`: *Neural Sheaf Diffusion: A Topological Perspective on Heterophily and Oversmoothing in GNNs*.

The misses were not repaired by manual title insertion:

- `R1` diagnosed that the benchmark query omitted **meta-analysis**, **definitions**, and **disentanglement** vocabulary.
- `R2` diagnosed that requiring explicitly categorical terminology suppressed adjacent **topological**, **sheaf**, **heterophily**, and **oversmoothing** boundary work.

These repairs changed the substantive route. `K15` killed the generic category-theoretic taxonomy idea, while `K17` and `K18` forced a distinction between explicitly categorical commitments and adjacent structure-aware methods.

## Ideation result

Ten candidates are generated through multiple lenses. The route preserves direct-overlap rejections and successor ideas rather than presenting only the winner.

Selected idea:

> **Categorical Commitment Audit Benchmark** — create a reproducible corpus and ablation protocol that distinguishes operational categorical commitments from descriptive categorical framing in machine-learning papers.

The idea is selected because it has:

- a falsifiable operational/descriptive distinction;
- matched structure-preserving and structure-breaking interventions;
- a useful negative result if categorical framing proves non-operational;
- a bounded minimum validation;
- explicit kill criteria.

A generic category-theoretic disentanglement ontology is rejected because `K15` visibly preempts it.

## Planning result

The integration test initializes a real harness-backed research pack, preserves paper ID `ct-ml-categorical-commitment-audit`, and executes exactly three sequential work items:

1. `WI-IDEATION`
2. `WI-SLR`
3. `WI-NOVELTY`

Each stage is submitted as a structured episode and self-review is disclosed during planner verification. Only one work item may be active. The SLR depends on completed ideation, and novelty depends on the repaired and validated SLR.

## SLR result

The generated bounded-systematic pack contains:

- protocol;
- exact query and repair log;
- seed-recovery ledger;
- recall audit;
- schema 1.1 corpus manifest with reciprocal coverage links;
- screening and PRISMA accounting;
- 18-row evidence table;
- bounded synthesis and adversarial stress test.

The assurance verdict is `adequate-for-bounded-claims`. It explicitly excludes comprehensive or priority claims.

## Novelty result

The novelty review is digest-bound to the exact seven-file SLR pack and reruns the upstream validator.

Final ratings:

| Rating | Value |
| --- | ---: |
| Novelty | 3/5 |
| Impact positioning | 3/5 |
| Decision confidence | 3/5 |

Narrow surviving position:

> A bounded benchmark and diagnostic protocol that annotates whether sampled ML claims depend on explicit categorical commitments and tests those commitments with matched structure-breaking ablations.

Strong novelty is withheld because the corpus is public, bounded, metadata-heavy, and self-reviewed. Existing surveys, the categorical-deep-learning position paper, and the category-theoretic disentanglement meta-analysis create material overlap.

## Secondary stress routes

The fixture also checks:

- CT-NLP boundary separation among categorical compositional semantics, quantum NLP, categorical NLP/ML overlap, formal-language work, and adjacent non-categorical NLP;
- CT-FOUNDATIONS source-type separation among historical primary scholarship, secondary synthesis, pedagogy, software, community resources, and practitioner/promotional claims;
- prohibition on backfilling modern ML claims into historical category-theory sources.

## Acceptance interpretation

The test passes only when:

- the initial critical misses remain observable;
- causal repairs recover all frozen critical records;
- every stage pack validates;
- the planner preserves one identity and sequential dependencies;
- adverse records survive all handoffs;
- novelty remains narrowly rated at 3;
- no hidden or general effectiveness claim is made.

A passing result is bounded functional evidence that the suite can detect and repair this frozen low-recall failure while preserving downstream epistemic constraints. Repeated use of this fixture makes it a regression test, not held-out evidence.
