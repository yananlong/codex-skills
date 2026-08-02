#!/usr/bin/env python3
"""Create deterministic machine-readable and narrative result-audit scaffolds."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def audit_template(paper_id: str, identity_version: int) -> dict:
    return {
        "schema_version": "1.0",
        "paper_id": paper_id,
        "identity_version": identity_version,
        "status": "draft",
        "audits": [],
    }


NARRATIVE_TEMPLATE = """# Results Audit

`results-audit.json` is the canonical machine-readable audit record. This Markdown file is the explanatory view and must not contradict the JSON verdicts.

## Audit Summary

- Paper ID:
- Identity version:
- Audit status: draft / complete / superseded
- Overall caveat: repository validation establishes declared consistency only; it does not establish executor isolation, external immutability, scientific validity, or independent verification.

## Audit Records

Add one section per JSON audit record using the exact heading `## Audit <audit_id>` and include the exact bounded verdict.

### Example structure

## Audit A1

- Claim ID:
- Bounded verdict: inconclusive
- Attained assurance class: none
- Audited claim effect: inconclusive
- Source run IDs:
- Evidence artifacts:
- Strongest evidence against the preferred interpretation:
- Limitations:
- Minimum corrective action:
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target_dir", type=Path)
    parser.add_argument("--paper-id", default="")
    parser.add_argument("--identity-version", type=int, default=1)
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.identity_version < 1:
        raise SystemExit("--identity-version must be positive")
    args.target_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        args.target_dir / "results-audit.json": json.dumps(
            audit_template(args.paper_id, args.identity_version), indent=2, sort_keys=True
        ) + "\n",
        args.target_dir / "results-audit.md": NARRATIVE_TEMPLATE,
    }
    existing = [str(path) for path in paths if path.exists()]
    if existing and not args.force:
        raise SystemExit("Refusing to overwrite existing files without --force: " + ", ".join(existing))
    for path, content in paths.items():
        path.write_text(content, encoding="utf-8")
        print(f"created {path}")


if __name__ == "__main__":
    main()
