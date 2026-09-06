#!/usr/bin/env python3
"""Validate that the generated skill catalog matches skills on disk."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from generate_skill_catalog import build_catalog


REQUIRED_SKILL_FIELDS = {
    "name",
    "path",
    "skill_file",
    "domain",
    "description",
    "primary_intent",
    "capabilities",
    "inputs",
    "outputs",
    "related_skills",
    "resources",
}


def fail(message: str) -> int:
    print(f"[ERROR] {message}", file=sys.stderr)
    return 1


def load_catalog(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise SystemExit(fail(f"catalog not found: {path}"))
    except json.JSONDecodeError as exc:
        raise SystemExit(fail(f"invalid JSON in {path}: {exc}"))
    if not isinstance(data, dict):
        raise SystemExit(fail("catalog root must be a JSON object"))
    return data


def validate_shape(root: Path, catalog: dict) -> list[str]:
    errors: list[str] = []
    skills = catalog.get("skills")
    if not isinstance(skills, list):
        return ["catalog.skills must be a list"]
    names: set[str] = set()
    paths: set[str] = set()
    for index, skill in enumerate(skills):
        if not isinstance(skill, dict):
            errors.append(f"skills[{index}] must be an object")
            continue
        missing = sorted(REQUIRED_SKILL_FIELDS - set(skill))
        if missing:
            errors.append(f"{skill.get('name', f'skills[{index}]')} missing fields: {', '.join(missing)}")
        name = skill.get("name")
        path = skill.get("path")
        skill_file = skill.get("skill_file")
        if not isinstance(name, str) or not name:
            errors.append(f"skills[{index}] has invalid name")
        elif name in names:
            errors.append(f"duplicate skill name: {name}")
        else:
            names.add(name)
        if not isinstance(path, str) or not path:
            errors.append(f"{name or f'skills[{index}]'} has invalid path")
        elif path in paths:
            errors.append(f"duplicate skill path: {path}")
        else:
            paths.add(path)
        if not isinstance(skill_file, str) or not (root / skill_file).exists():
            errors.append(f"{name or f'skills[{index}]'} skill_file does not exist: {skill_file}")
        for list_field in ("capabilities", "inputs", "outputs", "related_skills"):
            if not isinstance(skill.get(list_field), list):
                errors.append(f"{name or f'skills[{index}]'} field {list_field} must be a list")
    return errors


def validate_current(root: Path, catalog: dict) -> list[str]:
    """Compare all generated metadata, not just skill membership.

    Records are matched by source path, so record ordering is immaterial.
    New domains, capabilities, and sidecar fields remain supported because
    the source generator, rather than a closed list of values, is authoritative.
    """
    shape_errors = validate_shape(root, catalog)
    if shape_errors:
        return shape_errors
    try:
        expected = build_catalog(root)
    except (OSError, ValueError, TypeError) as exc:
        return [f"cannot regenerate catalog for comparison: {exc}"]

    errors: list[str] = []
    expected_records = {skill["skill_file"]: skill for skill in expected["skills"]}
    actual_records = {skill["skill_file"]: skill for skill in catalog["skills"]}
    missing = sorted(expected_records.keys() - actual_records.keys())
    stale = sorted(actual_records.keys() - expected_records.keys())
    if missing:
        errors.append("catalog missing skills: " + ", ".join(missing))
    if stale:
        errors.append("catalog contains stale skills: " + ", ".join(stale))

    def changed_fields(actual: dict, fresh: dict, excluded: set[str]) -> list[str]:
        # JSON comparison preserves the distinction between true and 1, which
        # Python's ordinary equality would otherwise erase (including nested values).
        return [
            field
            for field in sorted((actual.keys() | fresh.keys()) - excluded)
            if field not in actual or field not in fresh
            or json.dumps(actual[field], sort_keys=True)
            != json.dumps(fresh[field], sort_keys=True)
        ]

    top_level = changed_fields(catalog, expected, {"skills"})
    if top_level:
        errors.append("catalog metadata is stale: " + ", ".join(top_level))
    for skill_file in sorted(expected_records.keys() & actual_records.keys()):
        changed = changed_fields(actual_records[skill_file], expected_records[skill_file], set())
        if changed:
            errors.append(f"{skill_file}: stale metadata fields: " + ", ".join(changed))
    if errors:
        errors.append("regenerate with scripts/generate_skill_catalog.py for this repository root")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Repository root")
    parser.add_argument("--catalog", default="skills-catalog.json", help="Catalog JSON path")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    catalog = load_catalog(root / args.catalog)
    errors = validate_current(root, catalog)
    if errors:
        for error in errors:
            print(f"[ERROR] {error}", file=sys.stderr)
        return 1
    print("[OK] skill catalog is valid and current.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
