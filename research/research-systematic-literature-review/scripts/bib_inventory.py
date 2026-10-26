#!/usr/bin/env python3
"""Inventory a manuscript's citations against its BibTeX files.

Follow \\input, \\include, and \\subfile from a root .tex file, collect cited keys, read the .bib
files named by \\bibliography{} or \\addbibresource{} (or passed with --bib), and report resolved,
missing, and unused keys. Write a Markdown citation audit and a JSON list of corpus-manifest-shaped
records. Stdlib only. This checks citation consistency, not whether the bibliography is complete.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

CITE_RE = re.compile(r"\\([A-Za-z]*cite[A-Za-z]*)\*?")
NOT_CITATIONS = {"citestyle", "citesetup", "citename"}
INCLUDE_RE = re.compile(r"\\(input|include|subfile)(?![A-Za-z@])\s*(?:\{([^}]*)\}|([^\s{}\\%]+))")
BIBLIOGRAPHY_RE = re.compile(r"\\bibliography\s*\{([^}]*)\}")
ADDBIB_RE = re.compile(r"\\addbibresource\s*(?:\[[^\]]*\])?\s*\{([^}]*)\}")
NON_ENTRY_TYPES = {"comment", "preamble", "string"}
PUBLISHED_FIELDS = ("journal", "booktitle", "publisher", "school", "institution")
PREPRINT_MARKERS = re.compile(r"arxiv|corr|biorxiv|medrxiv|ssrn|preprint", re.I)


@dataclass
class Citation:
    key: str
    location: str


@dataclass
class BibEntry:
    key: str
    entry_type: str
    fields: dict[str, str]
    source: str


@dataclass
class Inventory:
    tex_files: list[str] = field(default_factory=list)
    bib_files: list[str] = field(default_factory=list)
    citations: list[Citation] = field(default_factory=list)
    nocite_all: bool = False
    entries: dict[str, BibEntry] = field(default_factory=dict)
    duplicates: dict[str, list[str]] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)


def strip_comments(text: str) -> str:
    return "\n".join(re.sub(r"(?<!\\)%.*", "", line) for line in text.splitlines())


def skip_space(text: str, pos: int) -> int:
    while pos < len(text) and text[pos].isspace():
        pos += 1
    return pos


def read_group(text: str, pos: int, open_char: str, close_char: str) -> tuple[str, int] | None:
    """Read a balanced group starting at text[pos] == open_char; return (inner, end_pos)."""
    if pos >= len(text) or text[pos] != open_char:
        return None
    depth = 0
    index = pos
    while index < len(text):
        char = text[index]
        if char == "\\":
            index += 2
            continue
        if char == open_char:
            depth += 1
        elif char == close_char:
            depth -= 1
            if depth == 0:
                return text[pos + 1:index], index + 1
        index += 1
    return None


def parse_citations(text: str, location: str) -> tuple[list[Citation], bool]:
    """Return citations in a comment-stripped TeX string and whether \\nocite{*} appeared."""
    citations: list[Citation] = []
    nocite_all = False
    for match in CITE_RE.finditer(text):
        command = match.group(1)
        if command.lower() in NOT_CITATIONS:
            continue
        multi = command.endswith("cites")
        pos = match.end()
        groups = 0
        while True:
            pos = skip_space(text, pos)
            if pos < len(text) and text[pos] in "[(":
                closing = "]" if text[pos] == "[" else ")"
                group = read_group(text, pos, text[pos], closing)
                if group is None:
                    break
                pos = group[1]
                continue
            group = read_group(text, pos, "{", "}")
            if group is None:
                break
            pos = group[1]
            groups += 1
            line = text.count("\n", 0, match.start()) + 1
            for key in group[0].split(","):
                key = key.strip()
                if not key:
                    continue
                if key == "*" and command == "nocite":
                    nocite_all = True
                    continue
                citations.append(Citation(key, f"{location}:{line}"))
            if not multi:
                break
    return citations, nocite_all


def resolve_tex(name: str, including: Path, root_dir: Path) -> Path | None:
    name = name.strip()
    candidates = [name] if name.endswith(".tex") else [name + ".tex", name]
    for base in (root_dir, including.parent):
        for candidate in candidates:
            path = (base / candidate).resolve()
            if path.is_file():
                return path
    return None


def collect_tex(root: Path, inventory: Inventory) -> list[str]:
    """Walk the include tree; return bibliography resource names in document order."""
    root_dir = root.resolve().parent
    bib_names: list[str] = []
    seen: set[Path] = set()

    def visit(path: Path) -> None:
        if path in seen:
            return
        seen.add(path)
        try:
            label = str(path.relative_to(root_dir))
        except ValueError:
            label = str(path)
        inventory.tex_files.append(label)
        text = strip_comments(path.read_text(encoding="utf-8", errors="replace"))
        citations, nocite_all = parse_citations(text, label)
        inventory.citations.extend(citations)
        inventory.nocite_all = inventory.nocite_all or nocite_all
        for match in BIBLIOGRAPHY_RE.finditer(text):
            bib_names.extend(part.strip() for part in match.group(1).split(",") if part.strip())
        for match in ADDBIB_RE.finditer(text):
            bib_names.append(match.group(1).strip())
        for match in INCLUDE_RE.finditer(text):
            target = match.group(2) if match.group(2) is not None else match.group(3)
            resolved = resolve_tex(target, path, root_dir)
            if resolved is None:
                line = text.count("\n", 0, match.start()) + 1
                inventory.warnings.append(f"{label}:{line}: \\{match.group(1)}{{{target}}} not found")
            else:
                visit(resolved)

    visit(root.resolve())
    return bib_names


def clean_value(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and ((value[0] == "{" and value[-1] == "}") or (value[0] == '"' and value[-1] == '"')):
        value = value[1:-1]
    value = value.replace("{", "").replace("}", "")
    return re.sub(r"\s+", " ", value).strip()


def parse_fields(body: str, macros: dict[str, str] | None = None) -> dict[str, str]:
    fields: dict[str, str] = {}
    pos = 0
    while pos < len(body):
        match = re.compile(r"\s*,?\s*([A-Za-z][\w:-]*)\s*=\s*").match(body, pos)
        if not match:
            break
        name = match.group(1).lower()
        pos = match.end()
        if pos < len(body) and body[pos] == "{":
            group = read_group(body, pos, "{", "}")
            if group is None:
                break
            raw, pos = "{" + group[0] + "}", group[1]
        elif pos < len(body) and body[pos] == '"':
            end = body.find('"', pos + 1)
            if end < 0:
                break
            raw, pos = body[pos:end + 1], end + 1
        else:
            bare = re.compile(r"[^,#]*").match(body, pos)
            raw, pos = bare.group(0).strip(), bare.end()
            if macros and raw.lower() in macros:
                raw = "{" + macros[raw.lower()] + "}"
        # String concatenation (a # b) is kept verbatim apart from braces.
        while True:
            concat = re.compile(r"\s*#\s*").match(body, pos)
            if not concat:
                break
            pos = concat.end()
            nxt = re.compile(r'"[^"]*"|\{[^{}]*\}|[^,\s#]+').match(body, pos)
            if not nxt:
                break
            raw += " " + nxt.group(0)
            pos = nxt.end()
        fields[name] = clean_value(raw)
    return fields


def parse_bib(path: Path, label: str, inventory: Inventory) -> None:
    text = path.read_text(encoding="utf-8", errors="replace")
    entry_re = re.compile(r"@\s*([A-Za-z]+)\s*([{(])")
    macros: dict[str, str] = {}
    pos = 0
    while True:
        match = entry_re.search(text, pos)
        if match is None:
            break
        entry_type = match.group(1).lower()
        opener = match.group(2)
        group = read_group(text, match.end() - 1, opener, "}" if opener == "{" else ")")
        if group is None:
            inventory.warnings.append(f"{label}: unterminated @{entry_type} entry near offset {match.start()}")
            pos = match.end()
            continue
        pos = group[1]
        if entry_type == "string":
            macros.update(parse_fields(group[0], macros))
            continue
        if entry_type in NON_ENTRY_TYPES:
            continue
        body = group[0]
        key, _, rest = body.partition(",")
        key = key.strip()
        if not key:
            inventory.warnings.append(f"{label}: @{entry_type} entry without a key near offset {match.start()}")
            continue
        entry = BibEntry(key=key, entry_type=entry_type, fields=parse_fields(rest, macros), source=label)
        if key in inventory.entries:
            inventory.duplicates.setdefault(key, [inventory.entries[key].source]).append(label)
            continue
        inventory.entries[key] = entry


def first_author(entry: BibEntry) -> str:
    authors = entry.fields.get("author") or entry.fields.get("editor") or ""
    if not authors:
        return ""
    first = re.split(r"\s+and\s+", authors, flags=re.I)[0].strip()
    if "," in first:
        return first.split(",", 1)[0].strip()
    return first.split()[-1] if first.split() else ""


def locator(entry: BibEntry) -> tuple[str, str]:
    """Return (display locator, canonical URL or empty)."""
    doi = entry.fields.get("doi", "").strip()
    if doi:
        doi = re.sub(r"^https?://(dx\.)?doi\.org/", "", doi, flags=re.I)
        return f"doi:{doi}", f"https://doi.org/{doi}"
    url = entry.fields.get("url", "").strip()
    if url:
        return url, url if re.match(r"^https?://", url, re.I) else ""
    eprint = entry.fields.get("eprint", "").strip()
    prefix = entry.fields.get("archiveprefix", entry.fields.get("eprinttype", "")).strip()
    if eprint:
        if not prefix or prefix.lower() == "arxiv":
            return f"arXiv:{eprint}", f"https://arxiv.org/abs/{eprint}"
        return f"{prefix}:{eprint}", ""
    return "", ""


def publication_status(entry: BibEntry) -> str:
    venue = " ".join(entry.fields.get(name, "") for name in PUBLISHED_FIELDS)
    has_eprint = bool(entry.fields.get("eprint")) or PREPRINT_MARKERS.search(
        " ".join([venue, entry.fields.get("archiveprefix", ""), entry.fields.get("howpublished", ""), entry.fields.get("note", "")])
    )
    if venue.strip() and not PREPRINT_MARKERS.search(venue):
        return "published"
    if has_eprint:
        return "preprint"
    if entry.entry_type in {"book", "phdthesis", "mastersthesis", "techreport"}:
        return "published"
    return "unknown"


def canonical_citation(entry: BibEntry) -> str:
    author = first_author(entry)
    year = entry.fields.get("year", "") or entry.fields.get("date", "")[:4]
    title = entry.fields.get("title", "")
    parts = [part for part in (f"{author} et al." if author and " and " in entry.fields.get("author", "") else author, f"({year})" if year else "", title) if part]
    return " ".join(parts) if parts else entry.key


def build_inventory(tex: Path, explicit_bibs: list[Path]) -> Inventory:
    inventory = Inventory()
    bib_names = collect_tex(tex, inventory)
    bib_paths: list[tuple[Path, str]] = []
    if explicit_bibs:
        bib_paths = [(path.resolve(), str(path)) for path in explicit_bibs]
    else:
        for name in bib_names:
            candidate = name if name.endswith(".bib") else name + ".bib"
            path = (tex.resolve().parent / candidate).resolve()
            bib_paths.append((path, candidate))
        if not bib_names:
            inventory.warnings.append("no \\bibliography{} or \\addbibresource{} found; pass --bib")
    for path, label in bib_paths:
        if not path.is_file():
            inventory.warnings.append(f"bibliography file not found: {label}")
            continue
        inventory.bib_files.append(label)
        parse_bib(path, label, inventory)
    return inventory


def summarize(inventory: Inventory) -> dict[str, Any]:
    first_location: dict[str, str] = {}
    counts: dict[str, int] = {}
    for citation in inventory.citations:
        first_location.setdefault(citation.key, citation.location)
        counts[citation.key] = counts.get(citation.key, 0) + 1
    cited = list(first_location)
    resolved = [key for key in cited if key in inventory.entries]
    missing = [key for key in cited if key not in inventory.entries]
    unused = [] if inventory.nocite_all else [key for key in inventory.entries if key not in first_location]
    lowered = {key.lower(): key for key in inventory.entries}
    case_hints = {key: lowered[key.lower()] for key in missing if key.lower() in lowered}
    return {
        "first_location": first_location,
        "counts": counts,
        "cited": cited,
        "resolved": resolved,
        "missing": missing,
        "unused": unused,
        "case_hints": case_hints,
    }


def record_for(entry: BibEntry, disposition: str, summary: dict[str, Any]) -> dict[str, Any]:
    display, url = locator(entry)
    return {
        "record_id": entry.key,
        "canonical_citation": canonical_citation(entry),
        "publication_url": url,
        "publication_status": publication_status(entry),
        "question_ids": [],
        "bib_key": entry.key,
        "bib_file": entry.source,
        "entry_type": entry.entry_type,
        "title": entry.fields.get("title", ""),
        "first_author": first_author(entry),
        "year": entry.fields.get("year", "") or entry.fields.get("date", "")[:4],
        "doi": entry.fields.get("doi", ""),
        "eprint": entry.fields.get("eprint", ""),
        "locator": display,
        "disposition": disposition,
        "first_cited_at": summary["first_location"].get(entry.key, ""),
        "citation_count": summary["counts"].get(entry.key, 0),
    }


def to_json(tex: Path, inventory: Inventory, summary: dict[str, Any]) -> dict[str, Any]:
    records = [record_for(inventory.entries[key], "resolved", summary) for key in summary["resolved"]]
    unused = [record_for(inventory.entries[key], "unused", summary) for key in summary["unused"]]
    return {
        "schema": "bib-inventory/1",
        "root_tex": str(tex),
        "tex_files": inventory.tex_files,
        "bib_files": inventory.bib_files,
        "nocite_all": inventory.nocite_all,
        "cited_keys": summary["cited"],
        "missing_keys": summary["missing"],
        "unused_keys": summary["unused"],
        "duplicate_keys": inventory.duplicates,
        "warnings": inventory.warnings,
        "note": (
            "records are corpus-manifest-shaped candidates for cited, resolved entries. question_ids are empty and "
            "publication_status 'unknown' or an empty publication_url must be resolved before the records enter a "
            "validated corpus manifest."
        ),
        "records": records,
        "unused_records": unused,
    }


def cell(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ").strip()


def to_markdown(tex: Path, inventory: Inventory, summary: dict[str, Any]) -> str:
    lines = [
        f"# Citation Audit: {tex.name}",
        "",
        "Generated by `bib_inventory.py`. This checks that cited keys resolve to bibliography entries; it does not "
        "check that the bibliography covers the relevant literature.",
        "",
        "## Summary",
        "",
        f"- TeX files scanned: {len(inventory.tex_files)} ({', '.join(inventory.tex_files)})",
        f"- Bibliography files: {', '.join(inventory.bib_files) or 'none found'}",
        f"- Distinct cited keys: {len(summary['cited'])}",
        f"- Resolved: {len(summary['resolved'])}",
        f"- Missing entries: {len(summary['missing'])}",
        f"- Unused entries: {len(summary['unused'])}" + (" (\\nocite{*} cites every entry)" if inventory.nocite_all else ""),
        f"- Duplicate keys across bib files: {len(inventory.duplicates)}",
        "",
        "## Citations",
        "",
        "| Key | Disposition | First author | Year | Title | DOI / URL / eprint | Bib file | First cited at | Notes |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    rows: list[tuple[str, str]] = [(key, "resolved") for key in summary["resolved"]]
    rows += [(key, "missing-entry") for key in summary["missing"]]
    rows += [(key, "unused") for key in summary["unused"]]
    for key, disposition in rows:
        entry = inventory.entries.get(key)
        notes: list[str] = []
        if key in summary["case_hints"]:
            notes.append(f"case differs from entry {summary['case_hints'][key]}")
        if key in inventory.duplicates:
            notes.append("duplicate in " + ", ".join(inventory.duplicates[key]))
        if entry is None:
            values = ["", "", "", "", "", summary["first_location"].get(key, "")]
        else:
            display, _url = locator(entry)
            if not display:
                notes.append("no DOI, URL, or eprint")
            values = [
                first_author(entry),
                entry.fields.get("year", "") or entry.fields.get("date", "")[:4],
                entry.fields.get("title", ""),
                display,
                entry.source,
                summary["first_location"].get(key, ""),
            ]
        lines.append("| " + " | ".join(cell(value) for value in [key, disposition, *values, "; ".join(notes)]) + " |")
    if inventory.warnings:
        lines += ["", "## Warnings", ""]
        lines += [f"- {warning}" for warning in inventory.warnings]
    return "\n".join(lines) + "\n"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--tex", required=True, type=Path, help="Root .tex file of the manuscript")
    parser.add_argument("--bib", action="append", type=Path, default=[], help="Bib file to use instead of \\bibliography{} (repeatable)")
    parser.add_argument("--out-md", type=Path, help="Write the Markdown audit here (for example citation-audit.md)")
    parser.add_argument("--out-json", type=Path, help="Write the JSON inventory with corpus-manifest-shaped records here")
    parser.add_argument("--fail-on-missing", action="store_true", help="Exit 1 when any cited key has no bib entry")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if not args.tex.is_file():
        print(f"Error: root .tex not found: {args.tex}", file=sys.stderr)
        return 2
    inventory = build_inventory(args.tex, args.bib)
    summary = summarize(inventory)
    if args.out_md:
        args.out_md.parent.mkdir(parents=True, exist_ok=True)
        args.out_md.write_text(to_markdown(args.tex, inventory, summary), encoding="utf-8")
        print(f"wrote {args.out_md}")
    if args.out_json:
        args.out_json.parent.mkdir(parents=True, exist_ok=True)
        args.out_json.write_text(json.dumps(to_json(args.tex, inventory, summary), indent=2) + "\n", encoding="utf-8")
        print(f"wrote {args.out_json}")
    print(
        f"cited {len(summary['cited'])}, resolved {len(summary['resolved'])}, missing {len(summary['missing'])}, "
        f"unused {len(summary['unused'])}, warnings {len(inventory.warnings)}"
    )
    for key in summary["missing"]:
        print(f"missing entry: {key} (first cited at {summary['first_location'][key]})")
    for warning in inventory.warnings:
        print(f"warning: {warning}")
    if args.fail_on_missing and summary["missing"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
