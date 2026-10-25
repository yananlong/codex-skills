#!/usr/bin/env python3
"""Scan prose for machine-writing tells and report density per category.

The scanner never rewrites. It counts patterns that make text read as model-written (dash
habits, deny-then-claim contrasts, signpost adverbs, significance inflation, participial tails,
tricolons, paragraph kickers, uniform rhythm, meta-commentary, hedge stacks, bolded lead-ins) and
reports counts, density per thousand words, and located examples, so a revision can be checked
against its source. Pass --baseline to compare a revision with the original.

Markdown and LaTeX are handled: comments, math, citation and reference commands, and code fences
are removed before scanning so the counts describe the visible prose.
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from dataclasses import dataclass, field
from pathlib import Path

INFLATION_WORDS = [
    "crucial", "pivotal", "vital", "robust", "nuanced", "comprehensive", "holistic", "seamless",
    "seamlessly", "leverage", "leverages", "leveraged", "leveraging", "harness", "harnesses", "unlock",
    "unlocks", "navigate", "navigating", "landscape", "tapestry", "testament", "underscore", "underscores",
    "underscoring", "delve", "delves", "delving", "foster", "fosters", "bolster", "bolsters",
    "transformative", "profound", "myriad", "multifaceted", "intricate", "realm", "paradigm",
    "game-changer", "cutting-edge", "groundbreaking", "revolutionize", "revolutionizes", "elevate",
    "elevates", "empower", "empowers", "streamline", "streamlines", "synergy", "synergies", "ever-evolving",
    "rapidly evolving", "sheds light", "shed light", "paves the way", "pave the way", "plays a crucial role",
    "plays a key role", "plays a vital role", "plays an important role", "serves as a", "stands as a",
    "represents a significant", "marks a significant", "a wide range of", "in today's",
]

SIGNPOSTS = [
    "importantly", "notably", "crucially", "interestingly", "specifically", "fundamentally", "ultimately",
    "essentially", "critically", "significantly", "overall", "taken together", "in summary", "in other words",
    "put simply", "simply put", "that said", "to be clear", "in short", "at its core", "in essence",
    "more broadly", "in practice", "in particular", "moreover", "furthermore", "additionally",
]

META = [
    r"it is worth noting", r"it's worth noting", r"it is important to note", r"it's important to note",
    r"it should be noted", r"it is interesting to note", r"we note that", r"as mentioned (?:above|earlier|before)",
    r"as discussed (?:above|earlier)", r"needless to say", r"it goes without saying", r"the key (?:point|insight|takeaway) (?:here )?is",
    r"what this means is", r"here's the thing", r"the bottom line",
]

HEDGE_STACKS = [
    r"may potentially", r"could potentially", r"could possibly", r"might possibly", r"seems? to suggest",
    r"appears? to (?:indicate|suggest)", r"arguably", r"to some extent", r"in some sense", r"it is possible that \w+ may",
]

SYCOPHANCY = [
    r"great question", r"i hope this helps", r"happy to help", r"\bcertainly[,!]", r"\babsolutely[,!]", r"of course[,!]",
    r"you're (?:absolutely )?right", r"feel free to",
]

TAIL_VERBS = (
    "highlighting|underscoring|suggesting|reflecting|demonstrating|ensuring|enabling|allowing|making|showing|"
    "emphasizing|reinforcing|signaling|signalling|raising|paving|offering|providing|illustrating|indicating|"
    "revealing|pointing|marking|setting|opening|laying|cementing|positioning|contributing|leading"
)
CONTRAST_RE = re.compile(
    r"\b(?:not (?:just|merely|simply|only) \w|isn't (?:just|merely|simply|only|about)|is not (?:just|merely|simply|only|about)|"
    r"aren't (?:just|merely)|are not (?:just|merely)|rather than|it's not that|it is not that|this is not (?:to say|about)|"
    r"the (?:point|goal|question|issue|problem) (?:is not|isn't)|less about \w+ and more about|not because .{3,60}? but because)",
    re.I,
)
THIS_OPENER_RE = re.compile(
    r"^(?:This|That|These) (?:suggests|means|indicates|highlights|underscores|shows|demonstrates|reflects|matters|"
    r"is not|isn't|is where|is why|is what|reveals|points|implies|ensures|allows|makes|represents|raises|marks)\b"
)
TRICOLON_RE = re.compile(r"\b(\w+), (\w+), (?:and|or) (\w+)\b")
PARTICIPIAL_TAIL_RE = re.compile(r", (?:thereby |thus |ultimately |further )?(" + TAIL_VERBS + r") [^,;]*$")
COLON_REVEAL_RE = re.compile(r"[a-z]: [a-z]")
BOLD_LEADIN_RE = re.compile(r"^\s*(?:[-*]\s+)?\*\*[^*]{1,60}\*\*[:.]?\s")
SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z\"'(])")
WORD_RE = re.compile(r"[A-Za-z][A-Za-z'-]*")


@dataclass
class Finding:
    category: str
    line: int
    text: str


@dataclass
class Report:
    words: int = 0
    counts: dict[str, int] = field(default_factory=dict)
    findings: list[Finding] = field(default_factory=list)

    def add(self, category: str, line: int, text: str) -> None:
        self.counts[category] = self.counts.get(category, 0) + 1
        self.findings.append(Finding(category, line, text.strip()[:160]))

    def density(self) -> dict[str, float]:
        per_k = max(self.words, 1) / 1000.0
        return {k: round(v / per_k, 2) for k, v in sorted(self.counts.items())}

    def total_density(self) -> float:
        return round(sum(self.counts.values()) / max(self.words, 1) * 1000, 2)


LATEX_HINT = re.compile(r"\\(?:documentclass|begin|section|subsection|cite|ref|textbf|emph|label|%)")


def _keep_lines(replacement: str):
    """Replace a multi-line match while keeping its newlines, so line numbers stay right."""

    def repl(match: re.Match) -> str:
        return replacement + "\n" * match.group(0).count("\n")

    return repl


def strip_markup(text: str) -> str:
    """Remove comments, math, code, and non-prose commands so counts describe visible prose."""
    text = re.sub(r"```.*?```", _keep_lines(" "), text, flags=re.S)
    text = re.sub(r"`[^`\n]*`", " CODE ", text)
    if LATEX_HINT.search(text):
        # Only LaTeX treats % as a comment; in Markdown "12% of runs" keeps its sentence.
        text = re.sub(r"(?m)(?<!\\)%.*$", "", text)
    text = re.sub(r"\$\$.*?\$\$", _keep_lines(" MATH "), text, flags=re.S)
    text = re.sub(r"(?<!\\)\$[^$\n]*\$", " MATH ", text)
    text = re.sub(r"\\begin\{(equation|align|figure|table|tabular|algorithm|lstlisting|verbatim)\*?\}.*?\\end\{\1\*?\}", _keep_lines(" "), text, flags=re.S)
    text = re.sub(r"\\(?:cite[tp]?\*?|citep|citet|ref|Cref|cref|eqref|label|includegraphics|input|include|bibliography|footnote)(?:\[[^\]]*\])?\{[^}]*\}", " ", text)
    text = re.sub(r"\\(?:emph|textbf|textit|texttt|underline)\{([^}]*)\}", r"\1", text)
    text = re.sub(r"\\[A-Za-z]+\*?(?:\[[^\]]*\])?(?:\{[^}]*\})?", " ", text)
    text = re.sub(r"[{}]", "", text)
    text = re.sub(r"(?m)^#{1,6}\s+", "", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    return text


def paragraphs(text: str) -> list[tuple[int, str]]:
    result = []
    start = 1
    buffer: list[str] = []
    for index, line in enumerate(text.splitlines(), start=1):
        if line.strip():
            if not buffer:
                start = index
            buffer.append(line.strip())
        elif buffer:
            result.append((start, " ".join(buffer)))
            buffer = []
    if buffer:
        result.append((start, " ".join(buffer)))
    return result


def sentences(paragraph: str) -> list[str]:
    return [s for s in SENTENCE_SPLIT_RE.split(paragraph) if s.strip()]


def scan(text: str) -> Report:
    report = Report()
    cleaned = strip_markup(text)
    report.words = len(WORD_RE.findall(cleaned))
    lowered_lines = cleaned.splitlines()

    for number, raw in enumerate(text.splitlines(), start=1):
        if BOLD_LEADIN_RE.match(raw):
            report.add("bold_leadin", number, raw)

    for number, line in enumerate(lowered_lines, start=1):
        low = line.lower()
        for _ in re.finditer(r"\u2014|\u2013| -- ", line):
            report.add("dash", number, line)
        for word in INFLATION_WORDS:
            for _ in re.finditer(r"\b" + re.escape(word) + r"\b", low):
                report.add("inflation", number, line)
        for pattern in META:
            if re.search(pattern, low):
                report.add("meta_commentary", number, line)
        for pattern in HEDGE_STACKS:
            if re.search(pattern, low):
                report.add("hedge_stack", number, line)
        for pattern in SYCOPHANCY:
            if re.search(pattern, low):
                report.add("sycophancy", number, line)
        for _ in CONTRAST_RE.finditer(line):
            report.add("contrast_negation", number, line)

    for start, paragraph in paragraphs(cleaned):
        sents = sentences(paragraph)
        for sentence in sents:
            first = sentence.split(",")[0].strip().lower()
            if first in SIGNPOSTS or first.rstrip(",") in SIGNPOSTS:
                report.add("signpost_adverb", start, sentence)
            elif sentence.lower().startswith(tuple(s + "," for s in SIGNPOSTS)):
                report.add("signpost_adverb", start, sentence)
            if THIS_OPENER_RE.match(sentence):
                report.add("this_opener", start, sentence)
            if PARTICIPIAL_TAIL_RE.search(sentence.rstrip(".!?")):
                report.add("participial_tail", start, sentence)
            if TRICOLON_RE.search(sentence):
                report.add("tricolon_possible", start, sentence)
            if sentence.rstrip().endswith("?"):
                report.add("rhetorical_question", start, sentence)
            if COLON_REVEAL_RE.search(sentence) and not sentence.rstrip().endswith(":"):
                report.add("colon_reveal_possible", start, sentence)
        if len(sents) >= 3:
            last_words = len(WORD_RE.findall(sents[-1]))
            mean_words = statistics.mean(len(WORD_RE.findall(s)) for s in sents[:-1])
            if last_words <= 6 and mean_words >= 10:
                report.add("kicker", start, sents[-1])
        if len(sents) >= 4:
            lengths = [len(WORD_RE.findall(s)) for s in sents]
            if statistics.mean(lengths) > 0 and statistics.pstdev(lengths) / statistics.mean(lengths) < 0.18:
                report.add("uniform_rhythm", start, f"{len(sents)} sentences of about {round(statistics.mean(lengths))} words each")
        openers = [s.split(" ")[0] for s in sents]
        run = 1
        for a, b in zip(openers, openers[1:]):
            run = run + 1 if a == b else 1
            if run == 3:
                report.add("anaphora_possible", start, f"three consecutive sentences open with '{a}'")
    return report


def format_text(report: Report, path: str, examples: int) -> str:
    lines = [f"{path}: {report.words} words, {sum(report.counts.values())} tells, {report.total_density()} per 1k words"]
    for category, density in report.density().items():
        lines.append(f"  {category:24s} {report.counts[category]:4d}  ({density} per 1k)")
        shown = [f for f in report.findings if f.category == category][:examples]
        for finding in shown:
            lines.append(f"      line {finding.line}: {finding.text}")
    return "\n".join(lines)


def compare(baseline: Report, revised: Report) -> list[str]:
    lines = [f"baseline {baseline.total_density()} per 1k -> revised {revised.total_density()} per 1k"]
    categories = sorted(set(baseline.counts) | set(revised.counts))
    for category in categories:
        before = baseline.counts.get(category, 0)
        after = revised.counts.get(category, 0)
        marker = "WORSE" if after > before else ("same" if after == before else "better")
        lines.append(f"  {category:24s} {before:4d} -> {after:4d}  {marker}")
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("path", type=Path, help="Markdown, LaTeX, or plain-text file to scan")
    parser.add_argument("--baseline", type=Path, help="Original text to compare against (the revision is PATH)")
    parser.add_argument("--examples", type=int, default=3, help="Examples to show per category")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--fail-if-worse", action="store_true", help="Exit 1 when total density rose against the baseline")
    parser.add_argument("--max-density", type=float, help="Exit 1 when total density per 1k words exceeds this value (for new drafts with no baseline)")
    args = parser.parse_args()

    try:
        revised = scan(args.path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"[ERROR] not found: {args.path}", file=sys.stderr)
        return 2
    baseline = None
    if args.baseline:
        try:
            baseline = scan(args.baseline.read_text(encoding="utf-8"))
        except FileNotFoundError:
            print(f"[ERROR] not found: {args.baseline}", file=sys.stderr)
            return 2

    if args.format == "json":
        payload = {
            "path": str(args.path), "words": revised.words, "counts": revised.counts,
            "density_per_1k": revised.density(), "total_density_per_1k": revised.total_density(),
            "findings": [finding.__dict__ for finding in revised.findings],
        }
        if baseline:
            payload["baseline"] = {"path": str(args.baseline), "words": baseline.words, "counts": baseline.counts,
                                   "total_density_per_1k": baseline.total_density()}
        print(json.dumps(payload, indent=2))
    else:
        print(format_text(revised, str(args.path), args.examples))
        if baseline:
            print("\n".join(compare(baseline, revised)))

    failed = False
    if args.fail_if_worse and baseline and revised.total_density() > baseline.total_density():
        print("[FAIL] the revision has a higher tell density than the baseline", file=sys.stderr)
        failed = True
    if args.max_density is not None and revised.total_density() > args.max_density:
        print(f"[FAIL] tell density {revised.total_density()} per 1k words exceeds the limit of {args.max_density}", file=sys.stderr)
        failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
