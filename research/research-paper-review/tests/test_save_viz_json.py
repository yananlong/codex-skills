#!/usr/bin/env python3
"""Runtime labelling in save_viz_json.py (no engine needed)."""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import save_viz_json  # noqa: E402


class SaveVizJsonRuntimeTests(unittest.TestCase):
    def test_default_runtime_is_agent_not_codex(self) -> None:
        with mock.patch.object(sys, "argv", ["save_viz_json.py", "review_dir"]):
            args, remainder = save_viz_json.parse_args()
        self.assertEqual(args.runtime, "agent")
        updated = save_viz_json._with_runtime_defaults(remainder, args.runtime)
        self.assertIn("openaireview__agent", updated)
        self.assertNotIn("openaireview__codex", updated)

    def test_runtime_argument_sets_key_label_and_model(self) -> None:
        with mock.patch.object(sys, "argv", ["save_viz_json.py", "rd", "--runtime", "claude"]):
            args, remainder = save_viz_json.parse_args()
        updated = save_viz_json._with_runtime_defaults(remainder, args.runtime)
        helper = save_viz_json._parse_helper_args(updated, args.runtime)
        self.assertEqual(helper.method_key, "openaireview__claude")
        self.assertEqual(helper.method_label, "OpenAIReview (claude)")

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            review_dir = root / "demo_review"
            review_dir.mkdir()
            (review_dir / "metadata.json").write_text(json.dumps({"slug": "demo"}), encoding="utf-8")
            output = root / "demo_skill.json"
            output.write_text(
                json.dumps({"methods": {"openaireview__claude": {"model": "placeholder"}}}),
                encoding="utf-8",
            )
            helper_args = argparse.Namespace(
                review_dir=str(review_dir),
                output_dir=str(root),
                slug_suffix="_skill",
                method_key="openaireview__claude",
            )
            save_viz_json._mark_viz_model(helper_args, "claude")
            data = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(data["methods"]["openaireview__claude"]["model"], "claude")


if __name__ == "__main__":
    unittest.main()
