#!/usr/bin/env python3
r"""Compare a LaTeX source before and after a revision for what must survive byte-for-byte.

The reviser's merge audit asks: did any macro, citation key, label, cross-reference, or
comment move or vanish, and did a line ending in a % comment get joined with the next? This
script answers with counts and names, and prints the visible-text diff (comments stripped,
whitespace normalised) so the author can read what actually changed.

Usage:
    latex_visible_diff.py before.tex after.tex [--format text|json] [--allow-dropped-comments]

Exit 1 when a citation key, label, ref target, or user-defined macro name present before is
missing after, or when the number of comment-terminated lines fell (a joined line loses its
provenance comment) unless --allow-dropped-comments is given.
"""

from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
from collections import Counter
from pathlib import Path

CITE_RE = re.compile(r"\\[Cc]ite\w*\*?(?:\[[^\]]*\]){0,2}\{([^}]*)\}|\\(?:parencite|textcite|autocite|footcite)\w*(?:\[[^\]]*\]){0,2}\{([^}]*)\}")
LABEL_RE = re.compile(r"\\label\{([^}]*)\}")
REF_RE = re.compile(r"\\(?:[Cc]ref|ref|eqref|autoref|pageref|nameref)\*?\{([^}]*)\}")
MACRO_RE = re.compile(r"\\([A-Za-z]+)\*?")
STANDARD_MACROS = {"begin", "end", "section", "subsection", "subsubsection", "paragraph", "emph", "textbf", "textit", "texttt", "item", "label", "ref", "cite", "citep", "citet", "footnote", "caption", "centering", "includegraphics", "hline", "toprule", "midrule", "bottomrule", "left", "right", "frac", "sum", "alpha", "beta", "gamma", "delta", "mathbf", "mathrm", "text", "cref", "Cref", "eqref", "input", "include", "documentclass", "usepackage", "newcommand", "renewcommand", "maketitle", "title", "author", "date", "abstract", "and", "noindent", "vspace", "hspace", "textwidth", "linewidth", "small", "large", "Large", "scriptsize", "footnotesize", "par"}


def strip_comments(text: str) -> tuple[str, int]:
    lines = []
    comment_terminated = 0
    for line in text.splitlines():
        stripped = re.sub(r"(?<!\\)%.*$", "", line)
        if stripped != line:
            comment_terminated += 1
        lines.append(stripped)
    return "\n".join(lines), comment_terminated


def inventory(text: str) -> dict:
    body, comment_lines = strip_comments(text)
    cites: Counter[str] = Counter()
    for match in CITE_RE.finditer(body):
        for key in (match.group(1) or match.group(2) or "").split(","):
            if key.strip():
                cites[key.strip()] += 1
    labels = Counter(LABEL_RE.findall(body))
    refs: Counter[str] = Counter()
    for group in REF_RE.findall(body):
        for key in group.split(","):
            if key.strip():
                refs[key.strip()] += 1
    macros = Counter(name for name in MACRO_RE.findall(body) if name not in STANDARD_MACROS)
    visible = re.sub(r"\s+", " ", body).strip()
    return {"cites": cites, "labels": labels, "refs": refs, "macros": macros, "comment_lines": comment_lines, "visible": visible}


def missing(before: Counter, after: Counter) -> list[str]:
    return sorted(name for name, count in before.items() if after.get(name, 0) < count)


def compare(before_text: str, after_text: str, allow_dropped_comments: bool) -> dict:
    b, a = inventory(before_text), inventory(after_text)
    problems: list[str] = []
    for kind in ("cites", "labels", "refs", "macros"):
        for name in missing(b[kind], a[kind]):
            problems.append(f"{kind[:-1] if kind != 'cites' else 'citation key'} {name!r} appears {b[kind][name]} time(s) before and {a[kind].get(name, 0)} after")
    if a["comment_lines"] < b["comment_lines"] and not allow_dropped_comments:
        problems.append(f"comment-terminated lines fell from {b['comment_lines']} to {a['comment_lines']}: a line ending in % was joined or its comment dropped")
    before_words = b["visible"].split()
    after_words = a["visible"].split()
    diff = list(difflib.unified_diff(before_words, after_words, lineterm="", n=3, fromfile="before", tofile="after"))
    ratio = difflib.SequenceMatcher(None, before_words, after_words).ratio()
    return {
        "problems": problems,
        "visible_similarity": round(ratio, 4),
        "words_before": len(before_words),
        "words_after": len(after_words),
        "diff": diff[2:],
        "counts_before": {k: sum(b[k].values()) for k in ("cites", "labels", "refs", "macros")} | {"comment_lines": b["comment_lines"]},
        "counts_after": {k: sum(a[k].values()) for k in ("cites", "labels", "refs", "macros")} | {"comment_lines": a["comment_lines"]},
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("before", type=Path)
    parser.add_argument("after", type=Path)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--allow-dropped-comments", action="store_true")
    parser.add_argument("--max-diff-lines", type=int, default=80)
    args = parser.parse_args(argv)
    try:
        report = compare(args.before.read_text(encoding="utf-8"), args.after.read_text(encoding="utf-8"), args.allow_dropped_comments)
    except (OSError, UnicodeDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(
            f"visible text: {report['words_before']} -> {report['words_after']} words, similarity {report['visible_similarity']}; "
            f"before {report['counts_before']}; after {report['counts_after']}"
        )
        for problem in report["problems"]:
            print(f"  PROBLEM: {problem}")
        for line in report["diff"][: args.max_diff_lines]:
            print(f"  {line}")
        if len(report["diff"]) > args.max_diff_lines:
            print(f"  ... {len(report['diff']) - args.max_diff_lines} more diff lines")
    return 1 if report["problems"] else 0


if __name__ == "__main__":
    sys.exit(main())
