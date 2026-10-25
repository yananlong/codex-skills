#!/usr/bin/env python3
"""Create deterministic scaffolds for rebuttal planning and drafting."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


REVIEWS_RAW_TEMPLATE = """# Raw Reviews

Paste each review verbatim under its own level-2 heading named with the platform
reviewer handle (for example `## Reviewer xK3p`). Do not edit, summarize, or
reorder the pasted text: this file is the provenance source for every reviewer
quote, score, and claim used in the rebuttal.

## <reviewer handle>

<paste the full review text, scores, and confidence here>
"""

SCORE_MATRIX_HEADER = """| Reviewer | Platform ID | Score | Confidence | Stance | Core concern | AC-facing note |
| --- | --- | --- | --- | --- | --- | --- |
"""

SCORE_MATRIX_PLACEHOLDER = (
    "| <handle> | <platform reviewer ID> | | | Champion / Persuadable / Entrenched | | |\n"
)

FILE_TEMPLATES = {
    "review-analysis.md": """# Review Analysis

## Header

- Paper:
- Venue:
- Operating mode: standalone / orchestrated
- Artifact structure:
- Deadline:

## Score Matrix

{score_matrix}
## Shared Concerns

| Concern | Reviewers | Severity | Planned handling |
| --- | --- | --- | --- |
| | | Major-Blocking / Major-Addressable / Minor / Misunderstanding | |

## Decision View

- Main accept case:
- Main reject risk:
- Highest-leverage rebuttal targets:
""",
    "issue-board.md": """# Issue Board

Issue IDs use `EXT-<reviewer handle>-<n>` so they never collide with internal
review-loop or paper-review IDs. List matching internal issue IDs (for example from
`REVIEW_STATE.json` or `final_issues.json`) in `Internal issue IDs`.

| Issue ID | Reviewer | Internal issue IDs | Severity | Category | Strategy | Stance | Status | Shared with | Evidence source | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| EXT-<handle>-1 | <handle> | | Major-Blocking / Major-Addressable / Minor / Misunderstanding | | | Champion / Persuadable / Entrenched | open | | reviews-raw.md | |
""",
    "task-list.md": """# Task List

| Task ID | Issue IDs | Objective | Owner | Evidence source | Output artifact | Draft blocker | Affects | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T1 | | | | | | yes / no | manuscript / rebuttal / both | todo |
""",
    "rebuttal-working.md": """# Rebuttal Working Draft

## Header

- Venue:
- Format:
- Limit:
- Operating mode: standalone / orchestrated

## Global Summary

- 

## Reviewer Responses

### [Reviewer ID]

- Concern:
- Direct answer:
- Evidence:
- Implication:
- [INTERNAL] Source check:

## Open Risks

- 

## Final Checks

- Provenance gate:
- Commitment gate:
- Coverage gate:
- Length check:
""",
    "rebuttal-paste-ready.md": """# Paste-Ready Rebuttal

Remove headings or formatting not accepted by the venue before submission.
""",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target_dir", type=Path, help="Directory where the pack will be created.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing files.")
    parser.add_argument(
        "--reviews",
        type=Path,
        help="Markdown file of verbatim reviews, one '## <reviewer handle>' block each. "
        "Copied unchanged to reviews-raw.md; pre-fills one score-matrix row per block.",
    )
    return parser.parse_args()


def review_handles(text: str) -> list[str]:
    """Return the level-2 heading texts outside fenced code blocks, in order."""
    handles: list[str] = []
    fenced = False
    for line in text.splitlines():
        if line.startswith(("```", "~~~")):
            fenced = not fenced
            continue
        if not fenced and line.startswith("## "):
            handle = line[3:].strip()
            if handle:
                handles.append(handle)
    return handles


def short_handle(platform_id: str) -> str:
    """Turn 'Reviewer xK3p' into 'xK3p' for use in EXT-<handle>-<n> issue IDs."""
    text = re.sub(r"^(official\s+)?review(er)?\s*[:#-]?\s*", "", platform_id.strip(), flags=re.I)
    text = re.sub(r"[^A-Za-z0-9]+", "-", text or platform_id).strip("-")
    return text or "reviewer"


def score_matrix(handles: list[str]) -> str:
    if not handles:
        return SCORE_MATRIX_HEADER + SCORE_MATRIX_PLACEHOLDER
    rows = [
        f"| {short_handle(handle)} | {handle} | | | Champion / Persuadable / Entrenched | | |\n"
        for handle in handles
    ]
    return SCORE_MATRIX_HEADER + "".join(rows)


def main() -> None:
    args = parse_args()

    reviews_text = None
    handles: list[str] = []
    if args.reviews:
        if not args.reviews.is_file():
            raise SystemExit(f"reviews file not found: {args.reviews}")
        reviews_text = args.reviews.read_text(encoding="utf-8")
        handles = review_handles(reviews_text)
        if not handles:
            raise SystemExit(
                f"no '## <reviewer handle>' blocks found in {args.reviews}; "
                "put each pasted review under its own level-2 heading"
            )
        short = [short_handle(handle) for handle in handles]
        duplicates = sorted({name for name in short if short.count(name) > 1})
        if duplicates:
            raise SystemExit("duplicate reviewer handles in --reviews: " + ", ".join(duplicates))

    names = ["reviews-raw.md", *FILE_TEMPLATES]
    existing = [name for name in names if (args.target_dir / name).exists()]
    if existing and not args.force:
        raise SystemExit(
            "Refusing to overwrite existing files without --force: " + ", ".join(sorted(existing))
        )
    args.target_dir.mkdir(parents=True, exist_ok=True)

    raw_path = args.target_dir / "reviews-raw.md"
    raw_path.write_text(reviews_text if reviews_text is not None else REVIEWS_RAW_TEMPLATE, encoding="utf-8")
    print(f"created {raw_path}")

    for name, content in FILE_TEMPLATES.items():
        path = args.target_dir / name
        if name == "review-analysis.md":
            content = content.replace("{score_matrix}", score_matrix(handles))
        path.write_text(content, encoding="utf-8")
        print(f"created {path}")
    if handles:
        print(f"pre-filled {len(handles)} score-matrix rows: " + ", ".join(handles))


if __name__ == "__main__":
    main()
