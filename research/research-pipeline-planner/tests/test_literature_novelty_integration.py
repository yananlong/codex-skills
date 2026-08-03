#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

RESEARCH_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_MODULE = RESEARCH_ROOT / "research-novelty-review" / "tests" / "test_validate_novelty_pack.py"


def load_fixture_class():
    spec = importlib.util.spec_from_file_location("novelty_fixture_module", FIXTURE_MODULE)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load novelty fixture module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.NoveltyPackTests


class LiteratureNoveltyIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        fixture_class = load_fixture_class()
        self.fixture = fixture_class(methodName="test_rating_four_with_valid_bound_literature_passes")
        self.fixture.setUp()

    def tearDown(self) -> None:
        self.fixture.tearDown()

    def test_validated_literature_pack_supports_strong_novelty_positioning(self) -> None:
        cp = self.fixture.validate()
        self.assertIn("exact bound literature pack was revalidated", cp.stdout)

    def test_manifest_mutation_breaks_digest_bound_novelty_handoff(self) -> None:
        manifest_path = self.fixture.literature_paths()["corpus_manifest"]
        manifest = json.loads(manifest_path.read_text())
        manifest["corpus_version"] = 2
        manifest_path.write_text(json.dumps(manifest))
        cp = self.fixture.validate(expect=1)
        self.assertIn("corpus_manifest_sha256 does not match", cp.stdout)
        self.assertIn("corpus_version does not match", cp.stdout)

    def test_non_manifest_mutation_breaks_exact_pack_binding(self) -> None:
        report_path = self.fixture.literature_paths()["report"]
        report_path.write_text(report_path.read_text() + "\nChanged interpretation.\n")
        cp = self.fixture.validate(expect=1)
        self.assertIn("file_sha256.report does not match", cp.stdout)

    def test_unresolved_critical_question_blocks_rating_four(self) -> None:
        self.fixture.make_blocked_critical_question()
        cp = self.fixture.validate(expect=1)
        self.assertIn("novelty rating 4 cannot retain unresolved", cp.stdout)


if __name__ == "__main__":
    unittest.main()
