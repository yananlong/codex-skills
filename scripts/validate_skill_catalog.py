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
    expected = build_catalog(root)
    errors: list[str] = []
    expected_paths = {skill["skill_file"] for skill in expected["skills"]}
    actual_paths = {skill.get("skill_file") for skill in catalog.get("skills", []) if isinstance(skill, dict)}
    missing = sorted(expected_paths - actual_paths)
    stale = sorted(actual_paths - expected_paths)
    if missing:
        errors.append("catalog missing skills: " + ", ".join(missing))
    if stale:
        errors.append("catalog contains stale skills: " + ", ".join(stale))
    if catalog.get("skill_count") != len(catalog.get("skills", [])):
        errors.append("skill_count does not match number of skills")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Repository root")
    parser.add_argument("--catalog", default="skills-catalog.json", help="Catalog JSON path")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    catalog = load_catalog(root / args.catalog)
    errors = validate_shape(root, catalog) + validate_current(root, catalog)
    if errors:
        for error in errors:
            print(f"[ERROR] {error}", file=sys.stderr)
        return 1
    print("[OK] skill catalog is valid and current.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
