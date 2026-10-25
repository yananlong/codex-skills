#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "count_limits.sh"


class CountLimitsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def write(self, name: str, text: str) -> Path:
        path = self.root / name
        path.write_text(text, encoding="utf-8")
        return path

    def run_script(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["bash", str(SCRIPT), *args],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_plain_text_under_limit_counts_raw_characters(self) -> None:
        text = "We thank the reviewer. The ablation is in Section 4 (naive vs. tuned).\n"
        path = self.write("plain.md", text)
        result = self.run_script(str(path), "--chars", "--limit", "5000")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(f"Count: {len(text)} characters (raw)", result.stdout)
        self.assertIn("OK: Within limit", result.stdout)

    def test_markup_heavy_response_over_raw_limit_fails(self) -> None:
        line = "**Point.** See `cfg_x` and $\\alpha_i$ in \\cite{ref} <b>here</b>.\n"
        text = line * 40
        path = self.write("markup.md", text)
        limit = len(text) - 200
        result = self.run_script(str(path), "--chars", "--limit", str(limit))
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn(f"Count: {len(text)} characters (raw)", result.stdout)
        self.assertIn("WARNING: Exceeds limit", result.stdout)

        estimate = self.run_script(str(path), "--chars", "--strip-markup")
        self.assertEqual(estimate.returncode, 0, estimate.stdout + estimate.stderr)
        self.assertIn("estimate", estimate.stdout)

    def test_multi_response_file_fails_when_one_section_exceeds(self) -> None:
        text = (
            "Shared preface line.\n"
            "## Reviewer Alpha\n" + ("short reply. " * 5) + "\n"
            "## Reviewer Beta\n" + ("long reply sentence. " * 30) + "\n"
            "## Reviewer Gamma\n" + ("ok. " * 5) + "\n"
        )
        path = self.write("responses.md", text)
        result = self.run_script(str(path), "--limit", "300")
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("Per-section counts", result.stdout)
        beta = [line for line in result.stdout.splitlines() if "Reviewer Beta" in line]
        alpha = [line for line in result.stdout.splitlines() if "Reviewer Alpha" in line]
        gamma = [line for line in result.stdout.splitlines() if "Reviewer Gamma" in line]
        self.assertEqual(len(beta), 1)
        self.assertIn("OVER LIMIT", beta[0])
        self.assertTrue(alpha and alpha[0].endswith("ok"), result.stdout)
        self.assertTrue(gamma and gamma[0].endswith("ok"), result.stdout)

    def test_single_response_with_subsections_is_counted_whole(self) -> None:
        block = "sentence of reply. " * 60  # about 1140 chars each
        text = (
            "## Reviewer xK3p\n"
            "### W1\n" + block + "\n"
            "### W2\n" + block + "\n"
            "### W3\n" + block + "\n"
        )
        path = self.write("one-response.md", text)
        result = self.run_script(str(path), "--chars", "--limit", "2000")
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertNotIn("Per-section counts", result.stdout)
        self.assertIn("WARNING: Exceeds limit", result.stdout)
        forced = self.run_script(str(path), "--chars", "--limit", "2000", "--per-section")
        self.assertEqual(forced.returncode, 0, forced.stdout + forced.stderr)
        self.assertIn("Per-section counts", forced.stdout)

    def test_limit_without_value_is_a_usage_error(self) -> None:
        path = self.write("plain.md", "text\n")
        result = self.run_script(str(path), "--limit")
        self.assertEqual(result.returncode, 1)
        self.assertNotIn("unbound variable", result.stderr)
        self.assertIn("--limit requires", result.stderr)

    def test_pages_mode_reports_unverifiable(self) -> None:
        path = self.write("plain.md", "text\n")
        result = self.run_script(str(path), "--pages", "--limit", "1")
        self.assertEqual(result.returncode, 3, result.stdout + result.stderr)
        self.assertIn("cannot be verified from text", result.stdout)
        self.assertIn("venue", result.stdout)


if __name__ == "__main__":
    unittest.main()
