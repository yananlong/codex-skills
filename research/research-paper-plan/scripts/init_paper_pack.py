#!/usr/bin/env python3
"""Create deterministic scaffolds for evidence-bound paper planning."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


PAPER_PLAN = """# Paper Plan

## Header

- Paper ID:
- Identity version: 1
- Plan status: draft / complete
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

## Evidence Boundary

`claim-evidence-bindings.json` is the canonical machine-readable authority for manuscript claim support and action. The Markdown plans are human-readable views and must not promote a claim beyond its linked audit evidence.
"""

MATRIX = """# Claims-Evidence Matrix

`claim-evidence-bindings.json` is canonical. Keep one row per JSON claim using the exact paper claim ID.

| Paper claim ID | Claim | Type | Evidence mode | Support status | Manuscript action | Required assurance | Source claim IDs | Audit IDs | Planned sections | Exhibit IDs | Citation need IDs | Limitation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
"""

FIGURE_PLAN = """# Figure Plan

| Exhibit ID | Purpose | Paper claim IDs | Priority | Status | Notes |
| --- | --- | --- | --- | --- | --- |
"""

CITATION_PLAN = """# Citation Plan

| Citation need ID | Paper claim IDs | Citation need | Source status | Notes |
| --- | --- | --- | --- | --- |
"""


def binding_template(paper_id: str, identity_version: int) -> dict:
    return {
        "schema_version": "1.0",
        "paper_id": paper_id,
        "identity_version": identity_version,
        "status": "draft",
        "claims": [],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target_dir", type=Path, help="Directory where the pack will be created.")
    parser.add_argument("--paper-id", default="")
    parser.add_argument("--identity-version", type=int, default=1)
    parser.add_argument("--force", action="store_true", help="Overwrite existing files.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.identity_version < 1:
        raise SystemExit("--identity-version must be positive")
    args.target_dir.mkdir(parents=True, exist_ok=True)
    files = {
        "paper-plan.md": PAPER_PLAN,
        "claims-evidence-matrix.md": MATRIX,
        "claim-evidence-bindings.json": json.dumps(
            binding_template(args.paper_id, args.identity_version), indent=2, sort_keys=True
        ) + "\n",
        "figure-plan.md": FIGURE_PLAN,
        "citation-plan.md": CITATION_PLAN,
    }
    existing = [name for name in files if (args.target_dir / name).exists()]
    if existing and not args.force:
        raise SystemExit(
            "Refusing to overwrite existing files without --force: " + ", ".join(sorted(existing))
        )
    for name, content in files.items():
        path = args.target_dir / name
        path.write_text(content, encoding="utf-8")
        print(f"created {path}")


if __name__ == "__main__":
    main()
