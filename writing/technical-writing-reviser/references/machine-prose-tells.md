# Machine-Prose Tells

Readers now recognize model-written prose by a small set of habits. Each habit is a shaping
problem, so the repair is a recipe for what the sentence should be, with the legitimate use named
so the recipe does not strip real content. Scan with `scripts/prose_tells.py` before and after a
revision; the audit requires the tell density not to rise, and a drafting or revision pass should
normally cut it.

The density that counts is per thousand words. Human technical prose in the owner's manuscripts
sits well under ten tells per thousand words on this scanner; model drafts commonly land between
thirty and eighty. The scanner marks approximate categories with `_possible`; read those before
acting.

## Dashes

Tell: em dashes used as the all-purpose joint, several to a paragraph, often in pairs that hold an
aside the sentence did not need.

Recipe: a comma for an aside, a period for a new thought, parentheses for a true parenthetical,
a colon for one specification. The policy is stated once in the drafter's `drafting-contract.md`:
one dash pair per page is a ceiling, not a target, and in LaTeX `---` is the same tell (the
scanner counts `---` and `--` in LaTeX sources).

Legitimate: a single interruption that changes the sentence's direction and that no other mark
can hold.

## Deny-then-claim contrast

Tell: "not X but Y", "not just X", "isn't about X, it's about Y", "rather than X, Y", "less about
X and more about Y", "the point is not X". The sentence invents a position in order to reject it.

Recipe: state Y with the precision that made X seem necessary. If X is a real position in the
literature or a reviewer's stated objection, name whose position it is and keep the contrast.
`claim-discipline.md` covers the evidential version of this habit.

Legitimate: correcting a named misconception, a counterexample, an absence that is itself the
technical fact, distinguishing two concepts that readers do confuse.

## Signpost adverbs

Tell: sentences opening with Importantly, Notably, Crucially, Interestingly, Fundamentally,
Ultimately, Essentially, Critically, Significantly, Overall, Taken together, In summary, In other
words, Put simply, That said, To be clear, At its core, More broadly. They announce importance
instead of demonstrating it, and they appear once per paragraph in model prose.

Recipe: delete the adverb and let the sentence carry its own weight. If the sentence does not
read as important without the adverb, the content is the problem. Moreover, Furthermore, and
Additionally are the same tell in a list of reasons; use "and", a new sentence, or an actual
ordering ("first", "second") when the order matters.

Legitimate: a transition the argument needs ("In contrast"), stated once; "Specifically" when the
next sentence narrows the previous one and the narrowing is the content.

## Significance inflation

Tell: crucial, pivotal, vital, robust, nuanced, comprehensive, holistic, seamless, leverage,
harness, unlock, navigate, landscape, tapestry, testament, underscore, delve, foster, bolster,
transformative, profound, myriad, multifaceted, intricate, realm, paradigm, groundbreaking,
cutting-edge, "plays a crucial role", "serves as a", "stands as a", "sheds light on", "paves the
way for", "a wide range of", "rapidly evolving", "in today's".

Recipe: replace the adjective with the measurement or the mechanism that made the writer reach for
it. "A robust method" becomes "the method's error stays within X under Y". "Plays a crucial role"
becomes what the component does. "Leverages" becomes "uses". A sentence that cannot be made
concrete this way was positioning, and is cut.

Legitimate: a term of art in the field ("robust statistics", "state of the art" as a comparison
class, "landscape" in loss-landscape analysis). Terms of art stay.

## Participial tails

Tell: a clause hung off the end of a sentence with a present participle that announces the
sentence's significance: ", highlighting the importance of X", ", underscoring the need for Y",
", suggesting that Z", ", enabling W", ", paving the way for V".

Recipe: end the sentence at the fact. If the significance is real and not yet stated, give it its
own sentence with its own evidence. If the participle introduces a causal or evidential claim
("suggesting", "demonstrating"), that claim needs the same support as any other, so write it as
a claim and check it.

Legitimate: a participial phrase that completes the action of the main clause with a concrete
result (", leaving the index half-built").

## Tricolons and balanced structure

Tell: three parallel items where the content has two or four, three adjectives in a row, three
short sentences in parallel, "X, Y, and Z" closing a paragraph. Also antithesis for its own sake
("fast where it matters, careful where it counts") and anaphora across consecutive sentences.

Recipe: count the real items and write that many. Parallel structure is for parallel content.

Legitimate: a list that has three members.

## Summary chains

Tell: sentences opening "This suggests", "This means", "This highlights", "This underscores",
"This matters because", one after another, each restating the previous sentence at a higher level
of abstraction without new evidence.

Recipe: one sentence of interpretation per piece of evidence, placed next to the evidence, with its
support level marked (`claim-discipline.md`). Delete restatements. A paragraph should not end by
summarizing itself.

## Kickers

Tell: a paragraph of long sentences closed by a short one that lands a point: "The results speak
for themselves." "That is the whole story." "It worked." Also the single-sentence paragraph used
as a drumbeat.

Recipe: end the paragraph on its last piece of evidence or on the consequence the reader needs,
in a sentence of ordinary length. Vary paragraph endings; a paragraph may end mid-argument when the
next paragraph continues it.

Legitimate: a short closing sentence once in a section, when the preceding sentences have earned
it.

## Uniform rhythm and the paragraph template

Tell: every paragraph runs three to four sentences of similar length and follows the same arc
(topic sentence, two supports, implication). The text reads as tiled.

Recipe: let paragraph length follow the argument. A one-sentence paragraph and a nine-sentence
paragraph are both fine when the content has that shape. Vary where the main point sits. Do not
end every paragraph with an implication.

## Meta-commentary and hedge stacks

Tell: "it is worth noting that", "it is important to note", "we note that", "as mentioned
above", "the key insight is", "here's the thing"; and "may potentially", "could possibly",
"seems to suggest", "arguably", "to some extent".

Recipe: delete the frame and state the point. One hedge per claim, chosen by the support level;
"may" and "potentially" together say nothing twice.

Legitimate: "Note that" before a genuine technical caveat in mathematical writing; a single hedge
that marks a real uncertainty.

## Rhetorical questions and conversational asides

Tell: "But what does this mean in practice?" "Why does this matter?" "Here's where it gets
interesting." Also "Let's", "we'll", and direct address in a manuscript.

Recipe: ask the question of yourself, then write the answer as a statement.

Legitimate: a research question stated as a question once, in the introduction, when the paper is
organized around it.

## Structure tells in documents

Tell: bulleted lists in place of paragraphs of argument; bolded lead-ins ("**Key insight:**");
headers in a two-page document; "First, ... Second, ... Finally, ..." signposting for three
sentences; a closing section that restates the opening.

Recipe: prose for argument, lists for genuinely list-shaped content (steps, options, inventories),
headers only when a reader will navigate by them. `prose-flow-improver` holds the list-versus-prose
rules.

## Tone

Tell: enthusiasm about the work ("exciting", "remarkable", "elegant" used of one's own method),
reassurance to the reader, praise of the question, closing offers of help, "I hope this helps".

Recipe: the register of a careful colleague: specific, calm, and at the strength the evidence
supports. Confidence shows in precision, not in adjectives.

## Procedure

1. Scan the source before editing and record the density per category; this is the baseline.
2. Revise under the skill's workflow. Where a tell appears, apply the recipe above; do not merely
   delete the word, since a deleted adjective usually leaves a sentence that still needs its
   measurement.
3. Scan the revision against the baseline (`--baseline source --fail-if-worse`). A revision that
   raises any category needs a reason in the claim-change note.
4. Read the `_possible` categories (tricolon, colon reveal, anaphora) by hand; they are leads.
5. Do not over-correct into choppiness, blandness, or stripped structure. The scanner measures
   tells, not quality. A text can score zero and be worse.
