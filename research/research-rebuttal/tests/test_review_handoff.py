#!/usr/bin/env python3
"""The rebuttal skill reads its issue board and the internal review through the shared modules."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import resolve_review_artifacts as resolver  # noqa: E402
from review_schema import load_issues  # noqa: E402


class ReviewHandoffTests(unittest.TestCase):
    def test_board_and_internal_review_share_one_schema(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pack = root / "rebuttal"
            cp = subprocess.run([sys.executable, str(SCRIPTS / "init_rebuttal_pack.py"), str(pack)], capture_output=True, text=True)
            self.assertEqual(cp.returncode, 0, cp.stderr)
            layout, issues, _ = load_issues(pack / "issue-board.md")
            self.assertEqual((layout, issues), ("rebuttal_issue_board", []))
            board = (pack / "issue-board.md").read_text()
            board += "| EXT-a-1 | a | R1 | major | baseline | add_evidence | concede | open | | results/b.json | Missing baseline |\n"
            (pack / "issue-board.md").write_text(board)
            _, issues, _ = load_issues(pack / "issue-board.md")
            self.assertEqual([issue["prior_issue_ids"] for issue in issues], [["R1"]])

            state = {"version": "1.0", "target": "t", "round": 3, "status": "open", "summary": "s", "source_artifacts": [],
                     "open_issues": [{"id": "R1", "title": "Baseline gap", "severity": "major", "status": "open"}],
                     "resolved_issues": [], "accepted_risks": []}
            loop = root / "review-loop" / "round-3"
            loop.mkdir(parents=True)
            (loop / "REVIEW_STATE.json").write_text(json.dumps(state))
            units = resolver.find_units(root)
            newest = resolver.latest_round(units)
            self.assertEqual(Path(newest.path), loop)
            _, internal, _ = load_issues(Path(newest.path))
            self.assertEqual(internal[0]["id"], issues[0]["prior_issue_ids"][0])


if __name__ == "__main__":
    unittest.main()
