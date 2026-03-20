#!/usr/bin/env python3
"""Initialize a standard memory pack for a document corpus."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


MEMORY_TEMPLATE = """# {title} Memory

## Scope

- Memory name: `{slug}`
- Created: [TODO]
- Corpus summary: [TODO]
- Intended use: [TODO]

## Canonical Facts

[TODO: durable facts that should survive across sessions]

## Terminology and Conventions

[TODO: definitions, naming conventions, notation, acronyms]

## Entities and Relationships

[TODO: people, systems, files, datasets, modules, and how they relate]

## Workflows and Decision Rules

[TODO: reusable procedures, heuristics, or decision criteria]

## Constraints and Non-Goals

[TODO: hard constraints, assumptions, and explicit non-goals]

## Change Watchlist

[TODO: volatile items that may need refresh]
"""


SOURCE_MAP_TEMPLATE = """# {title} Source Map

## Source Inventory

| Source | Type | Authority | Version/Date | Coverage | Notes |
| --- | --- | --- | --- | --- | --- |
| [TODO] | [TODO] | [TODO] | [TODO] | [TODO] | [TODO] |

## Canonical Sources

[TODO: identify the documents that should win when conflicts arise]

## Coverage Gaps

[TODO: note missing or referenced-but-unavailable materials]
"""


OPEN_QUESTIONS_TEMPLATE = """# {title} Open Questions

## Contradictions

- [TODO]

## Missing Information

- [TODO]

## Follow-Up Reads

- [TODO]
"""


def normalize_name(raw_name: str) -> str:
    slug = raw_name.strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = re.sub(r"-{2,}", "-", slug).strip("-")
    if not slug:
        raise ValueError("memory name must contain at least one alphanumeric character")
    return slug


def title_case(slug: str) -> str:
    return " ".join(part.capitalize() for part in slug.split("-"))


def write_file(path: Path, contents: str, overwrite: bool) -> None:
    if path.exists() and not overwrite:
        raise FileExistsError(f"refusing to overwrite existing file: {path}")
    path.write_text(contents, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a standard memory pack directory and Markdown files."
    )
    parser.add_argument("memory_name", help="Name for the memory pack")
    parser.add_argument(
        "--path",
        required=True,
        help="Parent directory where the memory pack directory should be created",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow overwriting an existing memory pack directory contents",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    slug = normalize_name(args.memory_name)
    title = title_case(slug)

    base_dir = Path(args.path).expanduser().resolve()
    pack_dir = base_dir / slug
    pack_dir.mkdir(parents=True, exist_ok=True)

    files = {
        pack_dir / f"{slug}.memory.md": MEMORY_TEMPLATE.format(title=title, slug=slug),
        pack_dir / f"{slug}.source-map.md": SOURCE_MAP_TEMPLATE.format(title=title),
        pack_dir / f"{slug}.open-questions.md": OPEN_QUESTIONS_TEMPLATE.format(title=title),
    }

    try:
        for file_path, contents in files.items():
            write_file(file_path, contents, overwrite=args.overwrite)
    except (FileExistsError, OSError, ValueError) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    print(f"[OK] Created memory pack: {pack_dir}")
    for file_path in files:
        print(f"[OK] Wrote {file_path.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
