#!/usr/bin/env python3
"""Find review artifacts in any known layout, report the latest round, and name the next one.

Review artifacts live in many layouts: first-pass bundles under review_results/<slug>_review/,
review-loop rounds in review-loop/round-N/, dated or labelled round folders, a bare
REVIEW_STATE.json, bundles nested inside a round, and rebuttal issue boards. This script finds them
under a root, says which layout each one uses, groups them by the folder that holds a review's
rounds (its home), and picks the latest round by state round number, folder round number, folder
date, and modification time, in that order.

New rounds have one canonical location: an integer round-<N>/ folder directly inside the review's
workspace. For a review started now the workspace is review_results/<slug>_review/, which also holds
the first-pass bundle. An existing review keeps its home and continues there with integer folders.

The canonical copy lives in research-paper-review/scripts/; byte-identical copies ship with
research-review-loop and research-rebuttal (scripts/tests/test_shared_modules.py checks them).
Read-only: it never moves or writes review files.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

ARTIFACT_FILES = ("REVIEW_STATE.json", "final_issues.json", "review_summary.json", "issue-board.md")
SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", ".openaireview-venv", "site-packages"}
CANONICAL_ROOT = "review_results"
ROUND_INT = re.compile(r"^round[-_]?(\d+)$", re.I)
ROUND_ANY_INT = re.compile(r"round[-_]?(\d+)(?!\d|-\d\d-)", re.I)
TRAILING_INT = re.compile(r"[-_](\d+)$")
DATE = re.compile(r"(\d{4}-\d{2}-\d{2})")
REVIEW_PARENTS = {"review-loop", "reviews", "review", "rounds", CANONICAL_ROOT}

LAYOUTS = {
    "canonical_workspace": "first-pass bundle at review_results/<slug>_review/",
    "canonical_round": "integer round-<N>/ inside a review_results/<slug>_review/ workspace",
    "numbered_round": "integer round-<N>/ elsewhere (review-loop/, reviews/review-loop/, review/, review_results/)",
    "dated_round": "round folder named by date, such as round-<YYYY-MM-DD>[-label] or <date>_round-<n>_<label>",
    "labelled_round": "round folder with a label instead of a number, such as <label>-<n> or <label>-review",
    "flat_state": "REVIEW_STATE.json directly in a review folder, with no round folder",
    "nested_bundle": "first-pass bundle inside a round folder (round-<N>/paper-review/)",
    "bundle": "first-pass bundle outside review_results/",
    "issue_board": "rebuttal issue-board.md",
}


@dataclass
class ReviewUnit:
    path: str
    layout: str
    home: str
    files: list[str]
    round_number: int | None = None
    round_date: str | None = None
    mtime: float = 0.0
    notes: list[str] = field(default_factory=list)

    def sort_key(self) -> tuple:
        return (
            self.round_number if self.round_number is not None else -1,
            self.round_date or "",
            self.mtime,
        )


def _state_round(path: Path) -> int | None:
    try:
        data = json.loads((path / "REVIEW_STATE.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    value = data.get("round") if isinstance(data, dict) else None
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    return None


def _name_round(name: str) -> int | None:
    match = ROUND_INT.match(name) or ROUND_ANY_INT.search(name)
    if match:
        return int(match.group(1))
    match = TRAILING_INT.search(name)
    if match and not DATE.search(name[-10:]):
        return int(match.group(1))
    return None


def _is_round_name(name: str) -> bool:
    return bool(re.search(r"round", name, re.I))


def _classify(directory: Path, files: list[str]) -> tuple[str, Path]:
    name, parent = directory.name, directory.parent
    has_state = "REVIEW_STATE.json" in files
    has_bundle = "final_issues.json" in files and not has_state
    if files == ["issue-board.md"] or ("issue-board.md" in files and not has_state and "final_issues.json" not in files):
        return "issue_board", directory
    if has_bundle and _is_round_name(parent.name):
        return "nested_bundle", parent.parent
    if has_bundle and parent.name == CANONICAL_ROOT and name.endswith("_review"):
        return "canonical_workspace", directory
    if ROUND_INT.match(name):
        if parent.parent.name == CANONICAL_ROOT and parent.name.endswith("_review"):
            return "canonical_round", parent
        return "numbered_round", parent
    if _is_round_name(name) and DATE.search(name):
        return "dated_round", parent
    if has_state and not _is_round_name(name) and name in REVIEW_PARENTS:
        return "flat_state", directory
    if has_state or _is_round_name(name) or "review_summary.json" in files:
        if parent.name in REVIEW_PARENTS or _is_round_name(name) or TRAILING_INT.search(name):
            return "labelled_round", parent
        return "flat_state", directory
    return "bundle", directory


def find_units(root: Path, max_depth: int = 10) -> list[ReviewUnit]:
    root = root.expanduser().resolve()
    units: list[ReviewUnit] = []
    base_depth = len(root.parts)
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".openaireview"))
        if len(Path(dirpath).parts) - base_depth >= max_depth:
            dirnames[:] = []
        present = [name for name in ARTIFACT_FILES if name in filenames]
        if not present:
            continue
        directory = Path(dirpath)
        layout, home = _classify(directory, present)
        unit = ReviewUnit(
            path=str(directory),
            layout=layout,
            home=str(home),
            files=present,
            mtime=max((directory / name).stat().st_mtime for name in present),
        )
        if layout not in ("canonical_workspace", "bundle", "issue_board"):
            state_round = _state_round(directory) if "REVIEW_STATE.json" in present else None
            round_dir = directory.parent if layout == "nested_bundle" else directory
            name_round = _name_round(round_dir.name)
            unit.round_number = state_round if state_round is not None else name_round
            if state_round is not None and name_round is not None and state_round != name_round:
                unit.notes.append(f"state round {state_round} differs from folder round {name_round}")
            date = DATE.search(round_dir.name)
            unit.round_date = date.group(1) if date else None
        units.append(unit)
    return units


def homes(units: list[ReviewUnit]) -> dict[str, list[ReviewUnit]]:
    grouped: dict[str, list[ReviewUnit]] = {}
    for unit in units:
        grouped.setdefault(unit.home, []).append(unit)
    return grouped


def latest_round(units: list[ReviewUnit]) -> ReviewUnit | None:
    rounds = [unit for unit in units if unit.layout not in ("canonical_workspace", "bundle", "issue_board")]
    return max(rounds, key=lambda unit: unit.sort_key()) if rounds else None


def latest_bundle(units: list[ReviewUnit]) -> ReviewUnit | None:
    bundles = [unit for unit in units if "final_issues.json" in unit.files and "REVIEW_STATE.json" not in unit.files]
    return max(bundles, key=lambda unit: (unit.layout == "canonical_workspace", unit.mtime)) if bundles else None


def next_round_dir(home: Path, units: list[ReviewUnit]) -> Path:
    """The canonical next round: an integer round-<N>/ inside the review's home."""
    numbers = [unit.round_number for unit in units if unit.round_number is not None]
    rounds = [unit for unit in units if unit.layout not in ("canonical_workspace", "bundle", "issue_board")]
    next_number = (max(numbers) + 1) if numbers else len(rounds) + 1
    return Path(home) / f"round-{next_number}"


def canonical_workspace(root: Path, slug: str) -> Path:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", slug):
        raise SystemExit(f"slug must use letters, numbers, dot, underscore, or hyphen: {slug}")
    return root.expanduser().resolve() / CANONICAL_ROOT / f"{slug}_review"


def home_for(path: Path, root: Path | None = None) -> tuple[Path, list[ReviewUnit]]:
    """The home of the review that holds `path` (a round folder, state file, or bundle)."""
    path = path.expanduser().resolve()
    if path.is_file():
        path = path.parent
    search_root = root.expanduser().resolve() if root else path.parent.parent
    units = find_units(search_root)
    for unit in units:
        if Path(unit.path) == path or Path(unit.home) == path:
            home = Path(unit.home)
            return home, [other for other in units if Path(other.home) == home]
    return path, []


def _describe(home: str, group: list[ReviewUnit]) -> dict:
    newest = latest_round(group)
    bundle = latest_bundle(group)
    return {
        "home": home,
        "layouts": sorted({unit.layout for unit in group}),
        "round_count": len([u for u in group if u.layout not in ("canonical_workspace", "bundle", "issue_board")]),
        "latest_round": asdict(newest) if newest else None,
        "latest_bundle": asdict(bundle) if bundle else None,
        "next_round": str(next_round_dir(Path(home), group)),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", type=Path, default=Path("."), help="Directory to search (default: current).")
    parser.add_argument("--review-dir", type=Path, help="Report only the review whose home holds this path.")
    parser.add_argument("--slug", help="With --next-round and no existing review: start review_results/<slug>_review/.")
    parser.add_argument("--next-round", action="store_true", help="Print only the path for the next round.")
    parser.add_argument("--json", action="store_true", help="Print a JSON report.")
    args = parser.parse_args()

    root = args.root.expanduser().resolve()
    if args.review_dir:
        home, group = home_for(args.review_dir, root)
        grouped = {str(home): group} if group else {}
    else:
        grouped = homes(find_units(root))

    if args.next_round:
        if len(grouped) == 1:
            (home, group), = grouped.items()
            print(next_round_dir(Path(home), group))
            return 0
        if not grouped and args.slug:
            print(canonical_workspace(root, args.slug) / "round-1")
            return 0
        if not grouped:
            print("error: no review found; pass --slug to start review_results/<slug>_review/", file=sys.stderr)
            return 2
        print("error: several reviews found; pass --review-dir to choose one:", file=sys.stderr)
        for home in sorted(grouped):
            print(f"  {home}", file=sys.stderr)
        return 2

    report = [_describe(home, group) for home, group in sorted(grouped.items())]
    if args.json:
        print(json.dumps({"root": str(root), "reviews": report}, indent=2))
        return 0
    if not report:
        print(f"No review artifacts under {root}.")
        return 0
    for entry in report:
        print(f"Review home: {entry['home']}")
        print(f"  layouts: {', '.join(entry['layouts'])}")
        newest = entry["latest_round"]
        if newest:
            label = f"round {newest['round_number']}" if newest["round_number"] is not None else "unnumbered round"
            print(f"  latest round: {newest['path']} ({label}, {newest['layout']}; files: {', '.join(newest['files'])})")
            for note in newest["notes"]:
                print(f"  note: {note}")
        if entry["latest_bundle"]:
            print(f"  first-pass bundle: {entry['latest_bundle']['path']} ({entry['latest_bundle']['layout']})")
        print(f"  next round: {entry['next_round']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
