#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INIT = ROOT / "scripts" / "init_rebuttal_pack.py"

REVIEWS = """Pasted from the platform.

## Reviewer aB12
Summary: synthetic review text.
Rating: 0

## Reviewer Cd34
Summary: synthetic review text.

```text
## not a reviewer heading (inside a code block)
```
"""


class InitRebuttalPackTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def run_init(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(INIT), *args], capture_output=True, text=True, check=False
        )

    def test_reviews_option_copies_verbatim_and_prefills_score_matrix(self) -> None:
        reviews = self.root / "reviews.md"
        reviews.write_text(REVIEWS, encoding="utf-8")
        pack = self.root / "rebuttal"
        result = self.run_init(str(pack), "--reviews", str(reviews))
        self.assertEqual(result.returncode, 0, result.stderr)

        self.assertEqual((pack / "reviews-raw.md").read_text(encoding="utf-8"), REVIEWS)
        analysis = (pack / "review-analysis.md").read_text(encoding="utf-8")
        self.assertIn("| Reviewer | Platform ID | Score | Confidence |", analysis)
        self.assertIn("| aB12 | Reviewer aB12 |", analysis)
        self.assertIn("| Cd34 | Reviewer Cd34 |", analysis)
        self.assertNotIn("not a reviewer heading", analysis)
        self.assertNotIn("<handle>", analysis)

        board = (pack / "issue-board.md").read_text(encoding="utf-8")
        self.assertIn("EXT-<handle>-1", board)
        self.assertIn("Internal issue IDs", board)
        self.assertNotIn("| R1-1 |", board)

    def test_default_pack_includes_reviews_raw_template(self) -> None:
        pack = self.root / "rebuttal"
        result = self.run_init(str(pack))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("## <reviewer handle>", (pack / "reviews-raw.md").read_text(encoding="utf-8"))
        analysis = (pack / "review-analysis.md").read_text(encoding="utf-8")
        self.assertIn("| <handle> | <platform reviewer ID> |", analysis)

    def test_reviews_without_blocks_fails_without_writing(self) -> None:
        reviews = self.root / "reviews.md"
        reviews.write_text("one unstructured paste\n", encoding="utf-8")
        pack = self.root / "rebuttal"
        result = self.run_init(str(pack), "--reviews", str(reviews))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("## <reviewer handle>", result.stderr)
        self.assertFalse(pack.exists())


if __name__ == "__main__":
    unittest.main()
