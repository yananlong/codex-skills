#!/usr/bin/env python3
"""Create deterministic scaffolds for paper planning."""

from __future__ import annotations

import argparse
from pathlib import Path


FILE_TEMPLATES = {
    "paper-plan.md": """# Paper Plan

## Header

- Working title:
- One-sentence contribution:
- Operating mode: standalone / orchestrated
- Target venue:
- Page budget:

## Structure

1. Problem framing and stakes
2. Related work and positioning
3. Method, protocol, or artifact
4. Evidence and main results
5. Failure modes, limitations, and threats to validity
6. Conclusion

## Section Notes

- Which sections carry the main claim:
- Which sections carry supporting evidence:
- Which sections must stay short because the evidence is still thin:
""",
    "claims-evidence-matrix.md": """# Claims-Evidence Matrix

| Claim | Status | Evidence artifact | Planned section | Figure or table | Limitation or caveat |
| --- | --- | --- | --- | --- | --- |
| | supported / partial / blocked | | | | |
""",
    "figure-plan.md": """# Figure Plan

| Exhibit | Purpose | Claim supported | Priority | Notes |
| --- | --- | --- | --- | --- |
| | | | mandatory / helpful / cut | |
""",
    "citation-plan.md": """# Citation Plan

| Claim or section | Citation need | Source status | Notes |
| --- | --- | --- | --- |
| | motivation / novelty / method / benchmark | verified / verify | |
""",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target_dir", type=Path, help="Directory where the pack will be created.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing files.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.target_dir.mkdir(parents=True, exist_ok=True)

    existing = [name for name in FILE_TEMPLATES if (args.target_dir / name).exists()]
    if existing and not args.force:
        raise SystemExit(
            "Refusing to overwrite existing files without --force: " + ", ".join(sorted(existing))
        )

    for name, content in FILE_TEMPLATES.items():
        path = args.target_dir / name
        path.write_text(content, encoding="utf-8")
        print(f"created {path}")


if __name__ == "__main__":
    main()
