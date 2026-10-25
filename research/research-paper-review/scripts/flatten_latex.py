#!/usr/bin/env python3
"""Flatten a LaTeX source tree into one reviewable body with a source map.

Detects the root file, inlines \\input, \\include, and \\subfile recursively,
drops the preamble, takes the title from \\title{}, and lists .tex files that the
root never reaches so they can be excluded from review. Stdlib only.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

INPUT_RE = re.compile(r"\\(input|include|subfile)\s*(?:\{([^}]*)\}|\s+([^\s{}\\%]+))")
DOCCLASS_RE = re.compile(r"\\documentclass\b")
BEGIN_DOC_RE = re.compile(r"\\begin\s*\{document\}")
END_DOC_RE = re.compile(r"\\end\s*\{document\}")


def strip_comment(line: str) -> str:
    """Remove a LaTeX comment (unescaped %) from one line."""
    for match in re.finditer(r"%", line):
        idx = match.start()
        backslashes = len(line[:idx]) - len(line[:idx].rstrip("\\"))
        if backslashes % 2 == 0:
            return line[:idx]
    return line


def read_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8", errors="replace").splitlines()


def resolve_input(name: str, including: Path, root_dir: Path) -> Path | None:
    name = name.strip()
    if not name:
        return None
    for base in (root_dir, including.parent):
        candidate = (base / name)
        for option in (candidate, candidate.with_name(candidate.name + ".tex")):
            if option.is_file():
                return option.resolve()
    return None


def referenced_names(path: Path) -> list[str]:
    names: list[str] = []
    for line in read_lines(path):
        for match in INPUT_RE.finditer(strip_comment(line)):
            names.append(match.group(2) or match.group(3) or "")
    return names


def find_root(source_dir: Path) -> Path:
    tex_files = sorted(p.resolve() for p in source_dir.rglob("*.tex") if p.is_file())
    candidates = [
        p for p in tex_files if any(DOCCLASS_RE.search(strip_comment(line)) for line in read_lines(p))
    ]
    referenced: set[Path] = set()
    for path in tex_files:
        for name in referenced_names(path):
            target = resolve_input(name, path, source_dir.resolve())
            if target is not None:
                referenced.add(target)
    roots = [p for p in candidates if p not in referenced]
    if len(roots) == 1:
        return roots[0]
    named_main = [p for p in roots if p.name == "main.tex"]
    if len(named_main) == 1:
        return named_main[0]
    if not roots:
        raise SystemExit(f"no root .tex file with \\documentclass found under {source_dir}")
    listing = ", ".join(str(p.relative_to(source_dir.resolve())) for p in roots)
    raise SystemExit(f"several candidate root files under {source_dir}: {listing}; pass the root .tex file")


class Flattener:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.root_dir = self.root.parent
        self.lines: list[str] = []
        self.source_map: dict[str, str] = {}
        self.reached: set[Path] = {self.root}
        self.missing: list[str] = []
        self.preamble: list[str] = []

    def rel(self, path: Path) -> str:
        try:
            return str(path.relative_to(self.root_dir))
        except ValueError:
            return str(path)

    def emit(self, text: str, path: Path, line_no: int) -> None:
        if not text.strip():
            if self.lines and self.lines[-1] == "":
                return
            text = ""
        self.lines.append(text.rstrip())
        self.source_map[str(len(self.lines))] = f"{self.rel(path)}:{line_no}"

    def walk(self, path: Path, lines: list[tuple[int, str]], stack: tuple[Path, ...], collect: bool) -> None:
        for line_no, raw in lines:
            line = strip_comment(raw)
            if raw.strip() and not line.strip():
                continue  # comment-only line
            pos = 0
            for match in INPUT_RE.finditer(line):
                before = line[pos:match.start()]
                if collect and before.strip():
                    self.emit(before, path, line_no)
                name = match.group(2) or match.group(3) or ""
                target = resolve_input(name, path, self.root_dir)
                if target is None:
                    self.missing.append(f"{self.rel(path)}:{line_no}: {name}")
                    if collect:
                        self.emit(match.group(0), path, line_no)
                elif target in stack:
                    self.missing.append(f"{self.rel(path)}:{line_no}: cyclic input {name}")
                else:
                    self.reached.add(target)
                    child = list(enumerate(read_lines(target), start=1))
                    self.walk(target, child, stack + (target,), collect)
                pos = match.end()
            rest = line[pos:]
            if collect:
                if pos == 0 or rest.strip():
                    self.emit(rest, path, line_no)
            else:
                self.preamble.append(rest)

    def run(self) -> None:
        numbered = list(enumerate(read_lines(self.root), start=1))
        begin = next((i for i, (_, text) in enumerate(numbered) if BEGIN_DOC_RE.search(strip_comment(text))), None)
        if begin is None:
            preamble, body = [], numbered
        else:
            preamble = numbered[:begin]
            first_no, first_text = numbered[begin]
            after = BEGIN_DOC_RE.split(strip_comment(first_text), maxsplit=1)[1]
            body = ([(first_no, after)] if after.strip() else []) + numbered[begin + 1 :]
        self.walk(self.root, preamble, (self.root,), collect=False)
        end = next((i for i, (_, text) in enumerate(body) if END_DOC_RE.search(strip_comment(text))), None)
        if end is not None:
            body = body[:end]
        self.walk(self.root, body, (self.root,), collect=True)
        while self.lines and self.lines[-1] == "":
            self.source_map.pop(str(len(self.lines)), None)
            self.lines.pop()


def balanced_argument(text: str, start: int) -> str | None:
    if start >= len(text) or text[start] != "{":
        return None
    depth = 0
    for idx in range(start, len(text)):
        if text[idx] == "{" and (idx == 0 or text[idx - 1] != "\\"):
            depth += 1
        elif text[idx] == "}" and text[idx - 1] != "\\":
            depth -= 1
            if depth == 0:
                return text[start + 1 : idx]
    return None


def extract_title(text: str) -> str | None:
    match = re.search(r"\\title\s*(\[[^\]]*\])?\s*", text)
    if not match:
        return None
    raw = balanced_argument(text, match.end())
    if raw is None:
        return None
    while True:
        thanks = re.search(r"\\thanks\s*", raw)
        if not thanks:
            break
        arg = balanced_argument(raw, thanks.end())
        raw = raw[: thanks.start()] + raw[thanks.end() + (len(arg) + 2 if arg is not None else 0) :]
    raw = raw.replace("\\\\", " ")
    raw = re.sub(r"\\[a-zA-Z]+\*?\s*\{([^{}]*)\}", r"\1", raw)
    raw = re.sub(r"\\[a-zA-Z]+\*?", "", raw)
    raw = raw.replace("{", "").replace("}", "")
    return " ".join(raw.split()) or None


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")[:60] or "paper"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("source", type=Path, help="Root .tex file, or a source directory to detect it in.")
    parser.add_argument("--output-dir", type=Path, required=True, help="Review directory to write into.")
    parser.add_argument("--full-text-name", default="full_text.md", help="Flattened body file name.")
    parser.add_argument("--force", action="store_true", help="Overwrite an existing flattened body.")
    args = parser.parse_args()

    source = args.source.expanduser().resolve()
    if source.is_dir():
        root = find_root(source)
        tree_dir = source
    elif source.is_file():
        root = source
        tree_dir = source.parent
    else:
        raise SystemExit(f"source not found: {source}")

    flattener = Flattener(root)
    flattener.run()

    all_tex = sorted(p.resolve() for p in tree_dir.rglob("*.tex") if p.is_file())
    excluded = [flattener.rel(p) for p in all_tex if p not in flattener.reached]
    included = sorted(flattener.rel(p) for p in flattener.reached)
    title = extract_title("\n".join(flattener.preamble)) or extract_title("\n".join(flattener.lines))

    out = args.output_dir.expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)
    full_text = out / args.full_text_name
    if full_text.exists() and not args.force:
        raise SystemExit(f"Refusing to overwrite {full_text} without --force")
    full_text.write_text("\n".join(flattener.lines) + "\n", encoding="utf-8")

    source_map_path = out / "latex_source_map.json"
    report = {
        "root": flattener.rel(root),
        "root_path": str(root),
        "title": title,
        "flattened_file": args.full_text_name,
        "included_files": included,
        "excluded_unreferenced_tex": excluded,
        "missing_inputs": flattener.missing,
        "source_map": flattener.source_map,
    }
    source_map_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    metadata_path = out / "metadata.json"
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        metadata = {}
    if not isinstance(metadata, dict):
        metadata = {}
    current_title = str(metadata.get("title") or "")
    if title and (not current_title or current_title.lstrip().startswith("\\")):
        metadata["title"] = title
    metadata.setdefault("slug", slugify(title or root.stem))
    metadata.setdefault("source", str(root))
    metadata["latex_root"] = str(root)
    metadata["latex_source_map"] = source_map_path.name
    metadata["excluded_tex_files"] = excluded
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

    print(f"root: {report['root']}")
    print(f"title: {title or '(no \\title found)'}")
    print(f"wrote {full_text} ({len(flattener.lines)} lines) and {source_map_path}")
    print(f"included: {', '.join(included)}")
    print(f"excluded (unreferenced): {', '.join(excluded) if excluded else 'none'}")
    if flattener.missing:
        print("missing inputs:", file=sys.stderr)
        for item in flattener.missing:
            print(f"  {item}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
