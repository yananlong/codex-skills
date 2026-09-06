"""Regression tests for catalog freshness, using temporary repository fixtures."""

from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

from generate_skill_catalog import build_catalog  # noqa: E402
from validate_skill_catalog import validate_current, validate_shape  # noqa: E402


class SkillCatalogTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.skill = self.root / "examples" / "example-review"
        (self.skill / "agents").mkdir(parents=True)
        self.entrypoint = self.skill / "SKILL.md"
        self.entrypoint.write_text(
            "---\nname: example-review\ndescription: Review a bounded artifact.\n"
            "---\n\n# Example Review\n\nWrite `review.md`.\n",
            encoding="utf-8",
        )
        (self.skill / "agents" / "openai.yaml").write_text(
            'interface:\n  display_name: "Example Review"\n', encoding="utf-8"
        )
        self.catalog = build_catalog(self.root)

    def errors(self, catalog: dict | None = None) -> list[str]:
        value = self.catalog if catalog is None else catalog
        return validate_shape(self.root, value) + validate_current(self.root, value)

    def run_cli(self, value: object) -> subprocess.CompletedProcess[str]:
        (self.root / "skills-catalog.json").write_text(
            json.dumps(value), encoding="utf-8"
        )
        return subprocess.run(
            [sys.executable, str(SCRIPTS / "validate_skill_catalog.py"),
             "--root", str(self.root)],
            capture_output=True, text=True, check=False, timeout=10,
        )

    def test_fresh_catalog_passes(self) -> None:
        self.assertEqual(self.errors(), [])

    def test_changed_description_is_stale(self) -> None:
        self.entrypoint.write_text(
            self.entrypoint.read_text(encoding="utf-8").replace(
                "Review a bounded artifact.", "Review a bounded artifact and audit its evidence."
            ), encoding="utf-8",
        )
        self.assertTrue(self.errors())

    def test_changed_output_is_stale(self) -> None:
        with self.entrypoint.open("a", encoding="utf-8") as handle:
            handle.write("Also emit `handoff.json`.\n")
        self.assertTrue(self.errors())

    def test_changed_agent_metadata_is_stale(self) -> None:
        (self.skill / "agents" / "openai.yaml").write_text(
            'interface:\n  display_name: "Changed Review"\n', encoding="utf-8"
        )
        self.assertTrue(self.errors())

    def test_new_resource_is_stale(self) -> None:
        (self.skill / "references").mkdir()
        (self.skill / "references" / "contract.md").write_text("Contract\n", encoding="utf-8")
        self.assertTrue(self.errors())

    def test_removed_resource_is_stale(self) -> None:
        (self.skill / "agents" / "openai.yaml").unlink()
        self.assertTrue(self.errors())

    def test_changed_sidecar_input_is_stale(self) -> None:
        (self.skill / "catalog.json").write_text(
            json.dumps({"inputs": ["source-artifact"]}), encoding="utf-8"
        )
        self.assertTrue(self.errors())

    def test_changed_sidecar_extension_is_stale(self) -> None:
        sidecar = self.skill / "catalog.json"
        sidecar.write_text(json.dumps({"handoff_version": "1"}), encoding="utf-8")
        self.catalog = build_catalog(self.root)
        sidecar.write_text(json.dumps({"handoff_version": "2"}), encoding="utf-8")
        self.assertTrue(self.errors())

    def test_open_ended_source_metadata_remains_supported(self) -> None:
        (self.skill / "catalog.json").write_text(json.dumps({
            "domain": "future-domain", "primary_intent": "future-intent",
            "capabilities": ["future-capability"], "handoff_version": "1",
        }), encoding="utf-8")
        self.assertEqual(self.errors(build_catalog(self.root)), [])

    def test_stale_generated_record_fields_are_rejected(self) -> None:
        for field, replacement in {
            "name": "renamed-review", "domain": "wrong-domain",
            "description": "Old description", "primary_intent": "obsolete",
            "inputs": ["old-input"], "outputs": ["obsolete.json"],
            "capabilities": ["obsolete"], "related_skills": ["missing-skill"],
            "resources": {}, "agent_metadata": {}, "frontmatter": {},
        }.items():
            with self.subTest(field=field):
                stale = copy.deepcopy(self.catalog)
                stale["skills"][0][field] = replacement
                self.assertTrue(self.errors(stale), field)

    def test_stale_top_level_metadata_is_rejected(self) -> None:
        for field, replacement in {
            "catalog_version": 0, "domains": ["obsolete"],
            "generated_by": "old-generator", "open_catalog": False,
            "$schema": "old-schema.json", "notes": [],
        }.items():
            with self.subTest(field=field):
                stale = copy.deepcopy(self.catalog)
                stale[field] = replacement
                self.assertTrue(self.errors(stale), field)

    def test_boolean_count_is_not_an_integer_count(self) -> None:
        stale = copy.deepcopy(self.catalog)
        stale["skill_count"] = True
        self.assertTrue(self.errors(stale))

    def test_unbacked_extra_metadata_is_rejected(self) -> None:
        for target in ("root", "skill"):
            with self.subTest(target=target):
                stale = copy.deepcopy(self.catalog)
                node = stale if target == "root" else stale["skills"][0]
                node["obsolete_extension"] = "not in source"
                self.assertTrue(self.errors(stale))

    def test_missing_skill_is_rejected(self) -> None:
        stale = copy.deepcopy(self.catalog)
        stale["skills"] = []
        stale["skill_count"] = 0
        self.assertTrue(self.errors(stale))

    def test_deleted_skill_is_rejected(self) -> None:
        self.entrypoint.unlink()
        self.assertTrue(self.errors())

    def test_duplicate_record_is_rejected(self) -> None:
        stale = copy.deepcopy(self.catalog)
        stale["skills"].append(copy.deepcopy(stale["skills"][0]))
        stale["skill_count"] = 2
        self.assertTrue(self.errors(stale))

    def test_malformed_shapes_return_errors_without_crashing(self) -> None:
        variants = [None, {}, "bad", [None], [{"skill_file": []}]]
        for skills in variants:
            with self.subTest(skills=skills):
                stale = copy.deepcopy(self.catalog)
                stale["skills"] = skills
                self.assertTrue(validate_current(self.root, stale))

    def test_cli_reports_staleness_without_writing(self) -> None:
        self.entrypoint.write_text(
            self.entrypoint.read_text(encoding="utf-8") + "Emit `new.json`.\n",
            encoding="utf-8",
        )
        result = self.run_cli(self.catalog)
        self.assertEqual(result.returncode, 1)
        self.assertIn("stale", result.stderr.lower())
        self.assertNotIn("Traceback", result.stderr)
        self.assertEqual(
            json.loads((self.root / "skills-catalog.json").read_text(encoding="utf-8")),
            self.catalog,
        )

    def test_cli_malformed_skills_fails_cleanly(self) -> None:
        stale = copy.deepcopy(self.catalog)
        stale["skills"] = None
        result = self.run_cli(stale)
        self.assertEqual(result.returncode, 1)
        self.assertIn("must be a list", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_cli_fresh_catalog_passes(self) -> None:
        result = self.run_cli(self.catalog)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("valid and current", result.stdout)


if __name__ == "__main__":
    unittest.main()
