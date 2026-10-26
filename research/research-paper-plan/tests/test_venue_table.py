#!/usr/bin/env python3
"""D14: one dated venue table shared with research-rebuttal."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "venue_table.py"
TABLE = ROOT / "references" / "venues.json"


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(SCRIPT), *args], text=True, capture_output=True)


class VenueTableTests(unittest.TestCase):
    def test_shipped_table_is_valid_and_dated(self) -> None:
        cp = run("--today", "2026-10-26", "check")
        self.assertEqual(cp.returncode, 0, cp.stdout + cp.stderr)
        rows = json.loads(TABLE.read_text(encoding="utf-8"))["venues"]
        self.assertTrue(all(row["verified_on"] and row["sources"] for row in rows))

    def test_old_rows_are_flagged_stale(self) -> None:
        cp = run("--today", "2027-06-01", "show", "icml-2025")
        self.assertIn("STALE", cp.stdout)
        cp = run("--today", "2026-10-26", "show", "icml-2025")
        self.assertNotIn("STALE", cp.stdout)

    def test_unverified_and_inferred_rows_are_flagged(self) -> None:
        self.assertIn("UNVERIFIED", run("--today", "2026-10-26", "show", "webconf-2025-research").stdout)
        self.assertIn("INFERRED", run("--today", "2026-10-26", "show", "sigir-2025").stdout)

    def test_diff_lists_changed_fields_for_porting(self) -> None:
        cp = run("--today", "2026-10-26", "diff", "cvpr-2025", "icml-2025")
        self.assertEqual(cp.returncode, 0, cp.stderr)
        self.assertIn("Porting cvpr-2025 -> icml-2025", cp.stdout)
        self.assertIn("response_limit:", cp.stdout)
        self.assertIn("unit=chars, value=5000, scope=per_review", cp.stdout)

    def test_limit_prints_unit_value_scope_or_exits_3(self) -> None:
        cp = run("--today", "2026-10-26", "limit", "icml-2025")
        self.assertEqual((cp.returncode, cp.stdout.strip()), (0, "chars 5000 per_review"))
        self.assertEqual(run("--today", "2026-10-26", "limit", "neurips-2025").returncode, 3)

    def test_unknown_venue_names_the_known_ids(self) -> None:
        cp = run("show", "nowhere-2030")
        self.assertNotEqual(cp.returncode, 0)
        self.assertIn("Known venue_id values", cp.stderr)

    def test_check_rejects_rows_without_a_date_or_source(self) -> None:
        data = json.loads(TABLE.read_text(encoding="utf-8"))
        data["venues"][0]["verified_on"] = "sometime"
        data["venues"][1]["sources"] = []
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "venues.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            cp = run("--table", str(path), "check")
        self.assertEqual(cp.returncode, 1)
        self.assertIn("verified_on must be an ISO date", cp.stdout)
        self.assertIn("sources must list at least one source URL", cp.stdout)


if __name__ == "__main__":
    unittest.main()
