#!/usr/bin/env python3
"""Generate an open, machine-readable catalog for the skill suite."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


CATALOG_VERSION = 1
DEFAULT_JSON_PATH = "skills-catalog.json"
DEFAULT_MD_PATH = "skills-catalog.md"
SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", "node_modules"}

CAPABILITY_RULES = [
    ("ideation", r"\b(ideation|brainstorm|candidate ideas?|generate[^.]*ideas?|find[^.]*ideas?|idea discovery|what idea|what to work on|choose what to work on)\b"),
    ("research-planning", r"\b(plan|planner|roadmap|agenda|milestone|scope|brief)\b"),
    ("stage-routing", r"\b(route|handoff|orchestrate|coordinate|workflow|pipeline)\b"),
    ("literature-review", r"\b(literature|survey|prisma|evidence synthesis|citation)\b"),
    ("novelty-review", r"\b(novelty|prior art|positioning|incremental)\b"),
    ("experiment-design", r"\b(experiment plan|baseline|ablation|control|evaluation goal)\b"),
    ("results-audit", r"\b(results|benchmark|statistical|confound|calibration|robustness)\b"),
    ("paper-review", r"\b(paper review|manuscript|critique|reviewer|peer review)\b"),
    ("paper-planning", r"\b(paper plan|outline|claims? to evidence|figures?)\b"),
    ("rebuttal", r"\b(rebuttal|author response|reviewer comments?|meta-review)\b"),
    ("zotero", r"\b(zotero|bibtex|csl-json|library|collection)\b"),
    ("document-memory", r"\b(memory pack|canonical facts|terminology|entity map)\b"),
    ("technical-writing", r"\b(revise|rewrite|prose|technical writing|flow|readability)\b"),
    ("commercialization", r"\b(commercial|market|buyer|budget|patent|diligence|licensing)\b"),
    ("pdf-processing", r"\b(pdf|bookmark|crop|rotate|assembler)\b"),
    ("notebook-generation", r"\b(notebook|jupyter|ipynb)\b"),
    ("multi-agent", r"\b(multi-agent|subagent|worker|orchestration)\b"),
    ("validation", r"\b(validate|validator|schema|audit|gate|check)\b"),
]

INTENT_RULES = [
    ("ideation", r"\b(ideation|brainstorm|candidate ideas?|generate[^.]*ideas?|find[^.]*ideas?|idea discovery|what idea|what to work on|choose what to work on)\b"),
    ("orchestration", r"\b(orchestrate|coordinate|pipeline|planner|handoff|route)\b"),
    ("review", r"\b(review|critique|red-team|audit|stress-test|adversarial)\b"),
    ("revision", r"\b(revise|rewrite|improve|humanize|polish)\b"),
    ("planning", r"\b(plan|roadmap|outline|agenda|experiment design|scope)\b"),
    ("execution", r"\b(sync|assemble|convert|generate|export|install|build)\b"),
    ("analysis", r"\b(analyze|analysis|synthesis|interpret|evaluate)\b"),
]

NAME_INTENT_RULES = [
    ("ideation", r"\bidea\b|\bideation\b"),
    ("orchestration", r"\bpipeline-planner\b|\bpipeline\b"),
    ("revision", r"\b(reviser|improver|humanizer)\b"),
    ("execution", r"\b(zotero|assembler|notebook|installer|sync)\b"),
    ("review", r"\b(review|auditor|diligence|rebuttal)\b"),
    ("planning", r"\b(plan|planner)\b"),
    ("analysis", r"\b(commercialize|memory-builder)\b"),
]

FILENAME_RE = re.compile(
    r"(?<![\w./-])([A-Za-z0-9_.-]+\.(?:md|json|yaml|yml|txt|csv|tsv|bib|ipynb|pdf|tex))(?![\w/-])"
)


def is_under_skipped_dir(path: Path) -> bool:
    return any(part in SKIP_DIRS for part in path.parts)


def parse_scalar(value: str) -> Any:
    value = value.strip()
    if not value:
        return ""
    if value in {"true", "false"}:
        return value == "true"
    if value in {"null", "~"}:
        return None
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [parse_scalar(part.strip()) for part in inner.split(",")]
    return value


def parse_simple_yaml(text: str) -> dict[str, Any]:
    """Parse the small YAML subset used by skill frontmatter and agent metadata."""
    result: dict[str, Any] = {}
    stack: list[tuple[int, dict[str, Any]]] = [(-1, result)]

    for raw_line in text.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        line = raw_line.strip()
        if ":" not in line or line.startswith("- "):
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]
        if value:
            parent[key] = parse_scalar(value)
        else:
            child: dict[str, Any] = {}
            parent[key] = child
            stack.append((indent, child))
    return result


def split_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---", 4)
    if end == -1:
        return {}, text
    frontmatter = text[4:end]
    body_start = text.find("\n", end + 4)
    body = "" if body_start == -1 else text[body_start + 1 :]
    return parse_simple_yaml(frontmatter), body


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def infer_capabilities(text: str) -> list[str]:
    lower_text = text.lower()
    values = [
        capability
        for capability, pattern in CAPABILITY_RULES
        if re.search(pattern, lower_text, re.IGNORECASE)
    ]
    return sorted(dict.fromkeys(values))


def infer_intent(name: str, text: str) -> str:
    for intent, pattern in NAME_INTENT_RULES:
        if re.search(pattern, name, re.IGNORECASE):
            return intent
    for intent, pattern in INTENT_RULES:
        if re.search(pattern, text, re.IGNORECASE):
            return intent
    return "specialized-workflow"


def extract_outputs(text: str) -> list[str]:
    values = [
        match.group(1)
        for match in FILENAME_RE.finditer(text)
        if not match.group(1).lower().startswith("skill.")
    ]
    return sorted(dict.fromkeys(values))


def positive_summary_text(name: str, description: str) -> str:
    sentences = re.split(r"(?<=[.!?])\s+", description)
    positive_sentences = [
        sentence
        for sentence in sentences
        if not re.search(r"\b(do not use|prefer\b|use after|route direct)\b", sentence, re.IGNORECASE)
    ]
    return "\n".join([name, *positive_sentences])


def find_related_skill_names(text: str, all_skill_names: set[str], current_name: str) -> list[str]:
    related = []
    lowered = text.lower()
    for name in sorted(all_skill_names):
        if name == current_name:
            continue
        if name.lower() in lowered:
            related.append(name)
    return related


def list_resource_files(skill_dir: Path, resource_dir: str) -> list[str]:
    root = skill_dir / resource_dir
    if not root.exists():
        return []
    return [
        path.relative_to(skill_dir).as_posix()
        for path in sorted(root.rglob("*"))
        if path.is_file() and not is_under_skipped_dir(path)
    ]


def skill_record(root: Path, skill_file: Path, all_skill_names: set[str]) -> dict[str, Any]:
    skill_dir = skill_file.parent
    text = skill_file.read_text(encoding="utf-8")
    frontmatter, body = split_frontmatter(text)
    name = str(frontmatter.get("name") or skill_dir.name)
    description = str(frontmatter.get("description") or "").strip()
    rel_dir = skill_dir.relative_to(root).as_posix()
    domain = rel_dir.split("/", 1)[0] if "/" in rel_dir else "uncategorized"
    agent_metadata = parse_simple_yaml((skill_dir / "agents" / "openai.yaml").read_text(encoding="utf-8")) if (skill_dir / "agents" / "openai.yaml").exists() else {}
    sidecar = read_json(skill_dir / "catalog.json")
    summary_text = positive_summary_text(name, description)
    searchable_text = "\n".join([name, description, body])

    record: dict[str, Any] = {
        "name": name,
        "path": rel_dir,
        "skill_file": f"{rel_dir}/SKILL.md",
        "domain": sidecar.get("domain", domain),
        "description": description,
        "primary_intent": sidecar.get("primary_intent", infer_intent(name, summary_text)),
        "capabilities": sorted(
            dict.fromkeys(sidecar.get("capabilities", []) + infer_capabilities(summary_text))
        ),
        "inputs": sidecar.get("inputs", []),
        "outputs": sorted(
            dict.fromkeys(sidecar["outputs"] if "outputs" in sidecar else extract_outputs(searchable_text))
        ),
        "related_skills": sorted(
            dict.fromkeys(
                sidecar.get("related_skills", [])
                + find_related_skill_names(searchable_text, all_skill_names, name)
            )
        ),
        "resources": {
            "agents": list_resource_files(skill_dir, "agents"),
            "references": list_resource_files(skill_dir, "references"),
            "scripts": list_resource_files(skill_dir, "scripts"),
            "assets": list_resource_files(skill_dir, "assets"),
            "prompts": list_resource_files(skill_dir, "prompts"),
        },
        "frontmatter": frontmatter,
        "agent_metadata": agent_metadata,
    }

    for key, value in sidecar.items():
        if key not in record:
            record[key] = value
    return record


def discover_skill_files(root: Path) -> list[Path]:
    return [
        path
        for path in sorted(root.rglob("SKILL.md"))
        if path.is_file() and not is_under_skipped_dir(path.relative_to(root))
    ]


def build_catalog(root: Path) -> dict[str, Any]:
    skill_files = discover_skill_files(root)
    names = set()
    parsed: list[tuple[Path, dict[str, Any], str]] = []
    for skill_file in skill_files:
        text = skill_file.read_text(encoding="utf-8")
        frontmatter, _ = split_frontmatter(text)
        name = str(frontmatter.get("name") or skill_file.parent.name)
        names.add(name)
        parsed.append((skill_file, frontmatter, name))

    skills = [skill_record(root, skill_file, names) for skill_file, _, _ in parsed]
    domains = sorted({skill["domain"] for skill in skills})
    return {
        "$schema": "./skills-catalog.schema.json",
        "catalog_version": CATALOG_VERSION,
        "generated_by": "scripts/generate_skill_catalog.py",
        "open_catalog": True,
        "notes": [
            "This catalog is generated from all SKILL.md files under the repository.",
            "Add new skills by adding a skill folder with SKILL.md; no central list edit is required.",
            "Optional per-skill catalog.json sidecars may add or override structured metadata.",
        ],
        "skill_count": len(skills),
        "domains": domains,
        "skills": skills,
    }


def write_markdown(catalog: dict[str, Any], path: Path) -> None:
    rows = [
        "# Skills Catalog",
        "",
        "Generated from `**/SKILL.md`. This is an open catalog: new skills are included by rerunning `scripts/generate_skill_catalog.py`.",
        "",
        f"- Skill count: {catalog['skill_count']}",
        f"- Domains: {', '.join(catalog['domains'])}",
        "",
        "| Domain | Skill | Primary intent | Capabilities | Path |",
        "|---|---|---|---|---|",
    ]
    for skill in catalog["skills"]:
        capabilities = ", ".join(skill["capabilities"][:6])
        if len(skill["capabilities"]) > 6:
            capabilities += ", ..."
        rows.append(
            "| {domain} | `{name}` | {intent} | {capabilities} | `{path}` |".format(
                domain=skill["domain"],
                name=skill["name"],
                intent=skill["primary_intent"],
                capabilities=capabilities,
                path=skill["path"],
            )
        )
    rows.extend(
        [
            "",
            "## Extension Points",
            "",
            "- Add a new skill folder with `SKILL.md`; the generator discovers it automatically.",
            "- Add optional `catalog.json` beside `SKILL.md` when inferred metadata needs correction or enrichment.",
            "- Do not treat `domain`, `primary_intent`, or `capabilities` as closed enums; downstream tools should tolerate new values.",
        ]
    )
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Repository root to scan")
    parser.add_argument("--json", default=DEFAULT_JSON_PATH, help="Catalog JSON output path")
    parser.add_argument("--markdown", default=DEFAULT_MD_PATH, help="Catalog Markdown output path")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    catalog = build_catalog(root)

    json_path = (root / args.json).resolve()
    md_path = (root / args.markdown).resolve()
    json_path.write_text(json.dumps(catalog, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(catalog, md_path)
    print(f"Wrote {json_path.relative_to(root)} and {md_path.relative_to(root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
