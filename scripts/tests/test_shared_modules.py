#!/usr/bin/env python3
"""Shared modules ship as byte-identical copies so each skill validates when installed alone."""
from __future__ import annotations

import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SHARED = {
    "claim_trajectory.py": (
        "research/research-pipeline-planner/scripts",
        [
            "research/research-experiment-plan/scripts",
            "research/research-results-auditor/scripts",
            "research/research-novelty-review/scripts",
        ],
    ),
    "domain-adapters.md": (
        "research/research-pipeline-planner/references",
        [
            "research/research-experiment-plan/references",
            "research/research-results-auditor/references",
            "research/research-novelty-review/references",
            "research/research-paper-plan/references",
            "research/research-review-loop/references",
        ],
    ),
    "venues.json": ("research/research-paper-plan/references", ["research/research-rebuttal/references"]),
    "venue_table.py": ("research/research-paper-plan/scripts", ["research/research-rebuttal/scripts"]),
}


class SharedModuleTests(unittest.TestCase):
    def test_copies_match_the_canonical_module(self) -> None:
        for name, (canonical_dir, copy_dirs) in SHARED.items():
            canonical = (REPO / canonical_dir / name).read_bytes()
            for copy_dir in copy_dirs:
                with self.subTest(module=name, copy=copy_dir):
                    copy = REPO / copy_dir / name
                    self.assertTrue(copy.is_file(), f"missing copy: {copy}")
                    self.assertEqual(
                        copy.read_bytes(), canonical,
                        f"{copy} differs from {canonical_dir}/{name}; edit the canonical copy and copy it over",
                    )


if __name__ == "__main__":
    unittest.main()
