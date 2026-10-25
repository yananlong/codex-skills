---
name: technical-writing-reviser
description: Revise technical writing into clear, audience-facing prose while preserving evidence, technical meaning, uncertainty, and scope, including planned multi-agent section or issue-cluster revision for substantial artifacts when workers are available. Use for academic manuscripts, industrial technical reports, whitepapers, evaluation summaries, methods/results/limitations prose, technical claims, contribution or decision framing, terminology conversion from internal shorthand to reader-facing language, and removing the habits that make text read as model-written (dash habits, deny-then-claim contrasts, signpost adverbs, significance inflation, participial tails, kickers, uniform rhythm). Use after critique from research-paper-review or research-review-loop when the task is to revise the artifact's prose and claims, not to re-review it, when a manuscript must be compressed to a page or word budget while preserving its claims, and on first drafts handed over by technical-writing-drafter. Do not use when there is no draft yet and the prose must be written from results, a literature review, a paper plan, or an issue board (technical-writing-drafter), or when the main task is generic prose flow, citation work, paper planning, novelty review, experiment design, market strategy, deciding what a rebuttal should concede (research-rebuttal), or writing unsupported claims.
---

# Technical Writing Reviser

## Overview

Revise technical text so an outside reader can understand the claim, method, result, limitation, design decision, or technical implication without first learning the author's internal shorthand. This skill revises prose that already exists. First drafts are written by `technical-writing-drafter` under its drafting contract, which applies the rules below at writing time, so a draft arriving from the drafter needs revision rather than a patch for habits the draft baked in. Prefer reader-facing technical prose that states what matters, what supports it, and what the reader should conclude, while keeping the original evidential and scope limits intact.

## Default Output

Return revised prose first unless the user asks for diagnosis, markup, or alternatives. Keep commentary brief: include only important terminology questions or evidence mismatches that materially affect the revision. Do not add disclaimers merely because a stronger claim could be imagined.

When the source is fragmentary, preserve the author's meaning and produce the most coherent technical version possible. Do not add invented transitions, citations, results, metrics, product claims, deployment facts, or motivation to make the passage feel complete.

## Keep the Scope Narrow

Treat this skill as a revision skill, not a planning, review, or evidence-generation skill. Improve wording, terminology, sentence shape, paragraph logic, claim framing, and limitation language, but do not invent citations, experiments, metrics, benchmarks, customer evidence, deployment details, product capabilities, novelty, or venue-specific requirements.

Preserve numbers, methods, caveats, uncertainty, negative results, and justified confidence. If a source claim exceeds its available support, weaken or flag that specific claim, but do not turn every bounded claim into a disclaimer about a stronger proposition the source never made. If the source's own evidence contradicts a sentence rather than under-supporting it, do not weaken the sentence into something still false. Flag it as an evidence conflict for the author.

Preserve the source format as well as the content. For LaTeX, Markdown, and other marked-up sources, keep macros, citation keys and their attachment to the clause they support, labels, cross-references, comments, and code spans intact. Read [references/register-and-format.md](references/register-and-format.md) before editing any LaTeX source or any manuscript outside empirical machine learning.

Use `technical-writing-drafter` when no draft exists and the prose must be written from results, audits, a literature review, a paper plan, or an issue board. Use `research-paper-plan` when the real need is manuscript structure, claim-to-evidence mapping, or figure planning. Use `research-paper-review` or `research-review-loop` when the real need is critique. Use `research-novelty-review` when the real need is positioning against prior work. Use `commercialize-academic-research` when the real need is buyer, budget, or commercialization analysis. Use `research-rebuttal` when the output is a response to reviewers rather than revised manuscript text. Use `prose-flow-improver` when the draft is also too choppy, list-heavy, or note-like. When both writing skills apply, this skill runs first and `prose-flow-improver` is one serial final pass counted in the same budget; its connective rules also bind this skill's workers, so no second orchestration is needed.

### Routing near misses

- "Make the results section read less like a wall of numbers": this skill if claims or connectives change, otherwise `prose-flow-improver`.
- "Reviewer 2 says the contribution is overclaimed; fix the intro": this skill for the manuscript text, `research-rebuttal` for the response.
- "Does our limitations section undersell the paper?": `research-review-loop` or `research-paper-review` for the judgment, then this skill for the text.
- "Restructure the intro so contributions map to sections": `research-paper-plan`. "Draft the methods section from the experiment plan" or "write the intro from the paper plan": `technical-writing-drafter`.
- "Draft the response to reviewer 2 from the issue board": `technical-writing-drafter`, with the paste-ready text returned to `research-rebuttal`. "Reviewer 2's response reads defensive, fix it": this skill.
- "Is our positioning against prior work defensible?": `research-novelty-review`. "Rewrite the related-work paragraph to state our difference clearly": this skill.
- "Cut related work by a third to fit the page limit": this skill, with the budget in the brief.
- "Turn these meeting notes into a paragraph", same facts already in sentences: `prose-flow-improver`. Notes that need claims, numbers, or citations introduced: `technical-writing-drafter`.
- "Rewrite the results section from scratch against the new audit": `technical-writing-drafter` (redraft from the ledger). "Fix the results section" with the text standing: this skill.
- "Fix typos and LaTeX warnings": neither writing skill.

## Calibrate the Revision

Choose the lightest revision that solves the problem. If the draft is already reader-facing technical prose, preserve sentence order and mainly tighten phrasing. If it reads like a lab note, engineering memo, internal status update, or sales-adjacent whitepaper draft, restructure paragraphs around claim, method, evidence, consequence, and limitation. If it is a pile of fragments, build coherent paragraphs but flag missing support only when the gap materially affects what the passage can claim.

Preserve authorial commitments and justified confidence. A rewrite may clarify "we test," "we find," "we argue," "the report shows," or "the system supports," but should not turn a preliminary observation into a result, a result into a mechanism, a prototype into a production capability, or a local finding into a general market or field-wide claim. Likewise, do not lower a supported claim merely because a more ambitious unsupported claim is conceivable.

## Rewrite Workflow

First identify the job of the passage: motivation, technical background, contribution framing, method, implementation summary, evaluation result, operational finding, recommendation, discussion, limitation, or transition. Rewrite toward the expectations of that section instead of applying one generic "technical tone" everywhere.

Then mark any internal language that will confuse an outside reader on first pass: project nicknames, code names, lab shorthand, implementation labels, and locally meaningful terms. Replace them with reader-facing terminology when the mapping is obvious, and preserve the meaning rather than the local wording.

Next identify the support level of each sentence. Separate what the text actually shows from why it matters, and keep that boundary visible in the rewrite. Use qualifiers when they are needed to keep a claim within the source's support, but do not add precautionary qualification to claims that are already appropriately scoped. For a formal statement such as a definition, proposition, theorem, or lemma, the support is its stated hypotheses. Do not add scope qualifiers or empirical hedges that restate or weaken them. For an argumentative claim, the support is the argument, so write "we argue" and make the premise visible rather than hedging the conclusion.

Finally tighten the prose into reader-facing technical form. Replace lab-log narration, internal memo phrasing, procedural diary language, and unsupported promotional language with sentences that foreground the technical object, method, evidence, result, decision, limitation, or implication. Join closely related sentences when a conjunction, relative clause, appositive, or subordinate clause makes the technical relationship clearer without changing the claim, and leave a sentence short when it carries one fact. Lean toward relative pronouns such as "that," "which," and "who" when they attach constraints, assumptions, mechanisms, or consequences to the specific technical object they modify. Make paragraphs do one clear job each and let their length follow the argument. End a paragraph on its evidence or on the consequence the reader needs, not on a flourish, and do not give every paragraph the same arc.

### Prefer Direct Positive Framing

State the supported proposition directly instead of first denying an adjacent stronger, weaker, or mistaken proposition. Do not invent a rejected interpretation merely to distinguish the author's actual claim from it.

Rewrite constructions such as "X is not A. X is B," "the point is not A but B," "this does not mean A," "we are not claiming A," "rather than A, this shows B," and "not merely A but B" as direct affirmative statements when A is not already salient in the source or necessary to the argument.

Use corrective negation only when the source is explicitly correcting a misconception, distinguishing genuinely confusable concepts, reporting an absence or exclusion that is itself a technical fact, stating a counterexample, converse failure, or impossibility result, answering a live objection raised by a named reviewer or position, or ruling out an alternative explanation. When the rejected proposition is doing no real argumentative work, lead with the supported proposition and omit the invented contrast.

Defensive narrowing is not only negation-shaped. Also watch for concessive priority clauses ("each component has close precedents, and ..."), self-minimizing scope labels ("the claim is deliberately narrow", "in a limited sense"), and scope restatements repeated at the opening and closing of one section. Keep the scope the evidence requires, state it once, and state it as what the work covers rather than as an apology.

Do not manufacture caution by naming claims the author supposedly is not making. Preserve genuine qualifications, but express the intended claim positively whenever its evidential boundary can be conveyed through precise scope, conditions, nouns, and verbs.

Read [references/claim-discipline.md](references/claim-discipline.md) when the draft mixes claims, interpretation, speculation, and missing evidence.

### Remove Machine-Prose Tells

Model-written prose carries habits readers now recognize: em dashes as the default joint, sentences that deny an invented position before stating the real one, signpost adverbs (Importantly, Notably, Crucially), significance adjectives (crucial, robust, nuanced, pivotal), participial tails that announce importance (", highlighting the need for"), tricolons where the content has two items, summary chains ("This suggests", "This means"), short kicker sentences closing paragraphs, paragraphs of identical shape, and bolded lead-ins. Each is a shaping habit, so remove it by writing what the sentence should be rather than by deleting a word: the measurement in place of the adjective, the fact in place of the announcing tail, one interpretation next to its evidence, a paragraph that ends on its evidence.

Run `python3 scripts/prose_tells.py <source>` before editing to get the baseline density, and `python3 scripts/prose_tells.py <revision> --baseline <source> --fail-if-worse` after. The scanner measures tells, not quality; read [references/machine-prose-tells.md](references/machine-prose-tells.md) for each tell's recipe and its legitimate uses, and do not strip terms of art, real contrasts, or real lists.

## Agent Orchestration

Default to a serial single-agent pass whenever the whole artifact fits comfortably in context, which covers a conference paper of up to roughly thirty pages. A serial pass still builds the revision brief below and still runs the merge audit on its own output. Fan out to workers only for longer artifacts, for several independent documents, or when the user asks for parallel revision. If this skill is itself running inside a subagent, run serially.

Ownership when skills chain: only the skill the user invoked spawns workers and sets one budget for the whole chain (quick: 1 pass; standard: up to 3; deep: 5 to 8), and a skill reached by handoff never spawns. When the user invoked a review skill that hands revision to this skill, this skill runs inside the review's budget as the owner of prose per issue cluster; when the user invoked this skill, it owns the budget, review stays diagnosis, and `prose-flow-improver` is one serial final pass inside the same budget. Record the budget and the passes used in the handoff note.

When workers are used, keep the plan small. Assign at most one worker per major section or reviewer-issue cluster, and make any cross-cutting pass (claim discipline, terminology, limitation language) comment-only: it returns findings to the parent and never edits text, so worker ownership stays disjoint. When `prose-flow-improver` also applies, it is one serial final pass counted in the budget, and its connective rules bind this skill's workers; there is never a second orchestration.

### Parent Brief Before Workers

The parent agent owns the global technical interpretation. Before assigning work, read the full artifact or enough surrounding context to identify the audience, purpose, stakes, terminology, claim boundaries, evidence limits, and any critique artifacts from `research-paper-review`, `research-review-loop`, or `adversarial-doc-review`.

Build a short revision brief before launching workers. Include:

- Audience and intended section role.
- Document-level thesis, contribution, decision, or recommendation.
- Key claims with source locations and support level.
- Important caveats, negative results, uncertainty, scope limits, and justified confidence that must survive revision.
- Terminology map for internal labels, symbols, acronyms, product names, and reader-facing replacements.
- Register and venue (empirical ML, ML theory, vision or systems, NLP or position paper, HCI or social science, technical report), inferred from the artifact or supplied by the user, with the conventions it implies for hedging, contrast, and terminology (see `references/register-and-format.md`).
- Source format and the elements that must survive byte-for-byte (macros, citation keys, labels, comments).
- Any page or word budget, and what may be cut to meet it.
- Known critique items or reviewer issues to resolve, taken through the critique intake below.
- For a draft from `technical-writing-drafter`: the ledger entries as the key claims with their support level and status, taken through the drafter handoff intake below.
- Claims that genuinely require verification when verification is part of the task.

Do not launch section workers until the brief is strong enough that another agent can revise locally without guessing the document's global meaning.

### Critique Intake

When the request follows a review, read the critique artifacts read-only: `final_issues.json` (quote, source section, impact rating) from `research-paper-review`, or `REVIEW_STATE.json` (open issues, required action, route effect, accepted risks) from `research-review-loop`, or the user's pasted reviewer comments.

Check staleness first. Compare the critique's recorded source head or date with the current source, and compare the paper identity it reviewed with the current title, abstract, and contribution list. List issues that predate a paper-identity change or a major revision as possibly stale and do not apply them silently.

Translate each issue into an edit, not a disclaimer. An issue whose effect is "blocks claim X" means the revision must not assert X; it does not license a sentence announcing that X is not claimed unless the reviewer explicitly asked for that statement or the venue requires a scope statement. An issue that narrows a claim means stating the narrower claim directly at the strength the evidence supports.

Record every issue-driven weakening in a short claim-change note (original wording, revised wording, the issue that forced it) so the owning review or planning stage can see the cumulative scope loss. Do not let several locally reasonable narrowings shrink the contribution without the author seeing the total.

### Drafter Handoff Intake

A draft from `technical-writing-drafter` arrives with its claim ledger, its approved outline, its brief, and the gate lines (numbers traced, citations resolved, tells density). Use them rather than re-deriving the claims:

- The ledger's `ready` and `careful` entries are the brief's key claims with their support level; a `careful` entry's limitation must still sit in the same passage after revision.
- `[EVIDENCE NEEDED: ...]` and `[CITATION NEEDED: ...]` markers are preserved as they stand. Never write around a marker or soften the sentence so the gap looks filled; the receiving review stage decides about gaps.
- Ledger source comments (`<!-- PC-3 -->`, `% PC-3`) are comments like any other: kept in place, stripped only when the author asks, and listed in the note when stripped.
- Compare the revised draft's tells density with the drafter's gate line as the baseline; a `--fail-if-worse` result is a failed revision.

### Revision Pass Plan

Build a concrete pass plan before spawning or running workers:

- one section or claim-cluster pass per major section, logical unit, or reviewer-issue cluster, grouping small or tightly coupled sections rather than creating trivial one-paragraph passes;
- at most one comment-only cross-cutting pass, chosen from the artifact's actual risks (claim discipline, terminology consistency, limitation language, notation, evidence-to-conclusion fit), and only when the parent's own merge audit would not cover it.

Do not run generic style passes that have no claim or reader-value target.

Each pass plan entry should include:

- `pass_id`
- `kind` (`section`, `issue_cluster`, or `cross_cutting`)
- assigned source text or file/line range
- relevant critique, evidence, or caveat notes
- one-sentence revision goal
- likely failure modes to avoid
- owned draft output target when workers can write files

### Worker Execution

Use one worker per planned pass when workers are available. Worker ownership must be disjoint: a worker revises only its assigned text or issue cluster and writes only to its owned output target when files are involved. Workers should draft revised prose, not directly edit the canonical document, unless the parent explicitly assigns a non-overlapping file or range and the environment can prevent conflicts.

Each worker prompt should:

- State that the worker writes only to its assigned output and that the parent alone edits the source.
- State the worker's assigned scope and owned output target.
- Provide the revision brief, audience, register, source-format rules, terminology map, claim constraints, and relevant critique notes.
- Require revised prose plus brief notes on any material claim-strength changes, preserved caveats, unresolved terminology, and missing support.
- Require an empty but explicit result if no safe revision is possible.

Workers must not invent citations, experiments, metrics, deployment facts, product claims, mechanisms, generalizations, or cross-section commitments. They may weaken a claim only when that claim exceeds the supplied support, and they must not introduce a stronger rejected alternative merely to disclaim it.

### Parent Merge And Audit

While workers run, the parent should do non-overlapping work only: check source coverage, refine merge criteria, inspect critique artifacts, or prepare the final document structure. Do not redo a worker's assigned pass before reviewing its output.

After all passes complete, merge in the parent. The parent must harmonize terminology, claim strength, tense, notation, contribution framing, limitation language, section transitions, and sentence rhythm across the whole artifact. Prefer the clearest supported rewrite over the most polished local sentence when those conflict, while preserving the source's justified confidence.

Run an adversarial final audit after merging:

- Check that every strengthened sentence is supported by the source, critique artifacts, or provided evidence.
- Check every weakened sentence the same way: name the support gap or critique item that requires the weakening, or restore the source wording.
- Compare the revised abstract, contribution list, and conclusion with the source versions. If the stated contribution became smaller, list the change for the author in the claim-change note rather than shipping it silently.
- Restore any source caveat, negative result, uncertainty, baseline condition, or scope limit that a local rewrite softened. A source caveat that carries scope (what the evidence does not cover) is kept and restated positively as scope plus consequence. Delete only rejected propositions that the source invented to sound cautious; this precedence resolves the apparent conflict with the negation scan below.
- For marked-up sources, compare the visible text before and after (comments stripped) and confirm that no macro, citation, label, or comment moved or vanished. For LaTeX, `scripts/latex_visible_diff.py before.tex after.tex` does this: it names every citation key, label, ref target, or user macro that disappeared, flags a comment-terminated line that was joined, and prints the visible-text diff.
- Run `scripts/prose_tells.py` on the revision against the source. No tell category may rise without a reason in the claim-change note, and the total density should fall. Then read the result as a reader would: a revision can score zero on the scanner and still be bland, choppy, or stripped of a real list, and that is a failed revision.
- Check for definitional drift, inconsistent terminology, unsupported causal language, and conclusions that no longer follow from the revised paragraph.
- Verify that cross-section transitions do not imply evidence, chronology, deployment status, or novelty that the source did not establish.
- Scan for corrective negation, anticipatory disclaimers, and objection-answering language that the source did not motivate. For each occurrence, ask whether the rejected interpretation is already salient or materially necessary. If not, delete the rejected proposition and state the supported proposition directly.
- Do not label source claims "unverified" merely because they are externally checkable. Verification belongs to a review or fact-checking task unless the user explicitly requested it as part of revision.

If the revision is file-based, preserve the user's requested output format and avoid generating a parallel report unless requested. If brief notes are useful, keep them focused on evidence gaps or terminology uncertainties that materially constrain the rewrite.

## Handle Terminology Carefully

Translate internal names only when the mapping is safe. A project nickname like "micro-archive" may become "a compact curated archive" if the meaning is clear from context. An implementation label like "control bucket B" may become "the stricter control condition" if the distinction is explicit in the source. A product or deployment label may become a neutral technical description only when the source supports that description.

When the intended meaning is uncertain, do not guess. Keep the original term, add a short neutral gloss if one is supported by the text, and ask for a terminology map or glossary. A wrong translation is worse than a visible internal label because it silently changes the claim.

Read [references/terminology-conversion.md](references/terminology-conversion.md) when the draft contains project-internal names, shorthand, or audience-hostile labels.

## Rewrite Toward Technical Prose

Prefer motivation over scene-setting, method or design over chronology, result over observation log, and limitation over apology. Replace sentences that narrate what the authors or team did in time order with sentences that explain what was done and why that choice matters.

Keep contribution and value framing specific and proportional to the evidence. State the artifact's contribution as what it provides, clarifies, tests, measures, supports, or argues, and preserve stronger framing when the source supports it rather than weakening it by default.

Use section-appropriate prose. Methods and technical approach sections should foreground design choices, controls, data, assumptions, architecture, and procedures. Results and evaluation sections should foreground findings at the scope supported by the evidence. Reports and whitepapers should distinguish measured behavior from interpretation, recommendation, and positioning. Limitations should state material constraints and their consequences without adding hypothetical objections.

Read [references/technical-writing-patterns.md](references/technical-writing-patterns.md) when the draft reads like a lab report, project memo, internal research note, engineering status update, or under-supported whitepaper. Read [references/rewrite-examples.md](references/rewrite-examples.md) when a concrete before-and-after pattern will help.

## Scripts

- `scripts/latex_visible_diff.py before.tex after.tex [--format json] [--allow-dropped-comments]`: the merge audit's survival check for LaTeX sources; exit 1 when a citation key, label, ref target, or user-defined macro present before is missing after, or when a `%`-terminated line was joined.
- `scripts/prose_tells.py`: count machine-prose tells per category with density per thousand words and located examples; `--baseline` compares a revision with its source, `--fail-if-worse` exits non-zero when the density rose, `--max-density N` exits non-zero when a new draft exceeds N per thousand words (the ceiling `technical-writing-drafter` applies before handoff), `--format json` for tooling. Handles Markdown and LaTeX by stripping comments, math, code, and citation commands first. It never rewrites.

## Final Pass

Check that the rewrite still says exactly what the source can support and preserves the source's supported strength. Make sure internal labels are either translated cleanly or left visible with a note of uncertainty.

Run the term-consistency and number-consistency checks in `references/technical-writing-patterns.md` on any revision that spans sections, and report mismatches rather than resolving them. Check that each paragraph has a single center and that the prose sounds like technical writing for informed outsiders rather than a note written for teammates or a claim written for persuasion without support. Avoid semicolons by default, using one only when it is cleaner than a period, conjunction, relative clause, or subordinate clause. Leave the draft more legible and more credible without making it either more or less certain than the evidence warrants.
