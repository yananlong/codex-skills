# Register and Source Format

## Purpose

Use this reference before revising a manuscript or report whose discipline, venue, or source format differs from plain empirical machine-learning prose in Markdown. The reviser's defaults are tuned to empirical ML writing. Applied unchanged to a theory paper, a position paper, or a LaTeX source tree, they weaken correct statements, erase defined concepts, or corrupt the build.

Infer the register from the artifact (venue style files, section names, density of theorems or arguments, citation style) and state the inferred register in the revision brief. When the user names a venue or register, use that. Never invent venue requirements such as page limits, section orders, or formatting rules that the user did not supply.

## Register Profiles

Empirical ML or evaluation paper (ICLR, ICML, NeurIPS, ACL findings-style):
Contribution bullets are conventional. Hedging follows the evidence ladder in `claim-discipline.md`. Contrastive negation is rare and usually defensive, so the salience test applies strictly. Standard vocabulary is the subfield's.

ML or CS theory paper:
Theorem, lemma, proposition, and definition statements are the support. Their hypotheses already carry the scope, so empirical hedges such as "suggests" or "under the evaluated conditions" are wrong and must not be added. Negation is often substantive: counterexamples, impossibility results, converse failures, and "does not depend on" statements are technical content. Proof sketches may say "we show" without qualification. Informal glosses of a theorem are interpretation and are calibrated like any interpretation.

Vision or systems paper (CVPR, ECCV, MLSys):
Method and architecture prose foregrounds components, training regime, and compute. Terminology is dense and conventional; convert internal labels but keep established component names. Results prose is number-heavy, so citation and macro attachment matter.

NLP or ACL-style paper, including position papers:
Position papers argue. The support for a thesis sentence is the argument, so write "we argue" and make the premise visible rather than hedging the conclusion. Rejected positions from the literature are legitimately salient, so contrastive negation that distinguishes the thesis from a named position stays.

HCI, social science, humanities, or philosophy:
Argumentative registers use contrastive framing several times more often than empirical ML prose, and much of it distinguishes the author's position from real alternatives. Apply the salience test to positions in the literature, not only to propositions in the source. Coined or defined terms often carry the thesis. Keep them and gloss them on first use. Do not restructure around claim, method, evidence, and limitation unless the section is reporting a study.

Technical report or whitepaper:
Separate measured behavior from positioning. Decision relevance is part of the content, so state it at the supported strength.

## Coined and Defined Terms

A term that the source introduces with a definition, uses in its title or contribution list, or that is standard in the source discipline is a concept, not an internal label. Keep it. If the target audience may not know it, add a one-time gloss. Replacing such a term with a neutral paraphrase changes the paper's contribution.

## Source Formats

LaTeX:
- Never join a line that ends in an unescaped `%` comment with the line after it. Text moved across such a comment disappears from the PDF.
- Keep every macro call (`\cite*`, `\ref`, `\Cref`, `\label`, `\footnote`, and project macros such as result or provenance slots) byte-identical and attached to the same clause it modified in the source.
- Do not edit text inside math, labels, comments, or verbatim environments.
- When joining or splitting sentences, move citation groups with the claim they support. A citation attached to the wrong clause is a changed claim.
- After editing a source file, compare the visible text (comments stripped) before and after, and compile when a build is available.

Markdown and plain text:
- Preserve code spans, links, footnote markers, and reference-style definitions.
- Keep heading levels and list structure unless the task is to change them.

Word or rich text exported to plain text:
- Expect footnotes and tracked changes to appear inline. Ask for the clean source rather than guessing which text is live.

## Length Budgets

When the user gives a page or word budget, compression is part of the task. Cut by removing restated scope, duplicated transitions, and background that the venue's readers already hold, before shortening evidence or claims. Report what was removed when it includes a claim, a caveat, or a result.
