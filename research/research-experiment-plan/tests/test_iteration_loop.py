"""Tests for the iteration-loop scaffold and ledger validator."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
INIT = SCRIPTS / "init_iteration_loop.py"
VALIDATE = SCRIPTS / "validate_iteration_ledger.py"

HEADER = "commit\tmetric\tcost\tstatus\tdescription\n"


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, *args], capture_output=True, text=True, check=False, timeout=30)


class IterationLoopTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.ledger = self.root / "results.tsv"

    def write_ledger(self, *rows: str) -> None:
        self.ledger.write_text(HEADER + "".join(row + "\n" for row in rows), encoding="utf-8")

    def test_init_writes_program_ledger_notebook_and_queue(self) -> None:
        result = run(str(INIT), str(self.root / "loop"), "--name", "demo", "--metric", "val_bpb")
        self.assertEqual(result.returncode, 0, result.stderr)
        for name in ("program.md", "results.tsv", "experiments.md", "ideas.md"):
            self.assertTrue((self.root / "loop" / name).exists(), name)
        program = (self.root / "loop" / "program.md").read_text(encoding="utf-8")
        self.assertIn("## Exam (frozen", program)
        self.assertIn("val_bpb", program)
        self.assertEqual((self.root / "loop" / "results.tsv").read_text(encoding="utf-8"), HEADER)

    def test_init_refuses_to_overwrite_without_force(self) -> None:
        self.assertEqual(run(str(INIT), str(self.root)).returncode, 0)
        (self.root / "results.tsv").write_text(HEADER + "a1b2c3d\t1.0\t1.0\tkeep\tbaseline\n", encoding="utf-8")
        result = run(str(INIT), str(self.root))
        self.assertEqual(result.returncode, 1)
        self.assertIn("--force", result.stderr)
        self.assertIn("a1b2c3d", (self.root / "results.tsv").read_text(encoding="utf-8"))

    def test_valid_ledger_passes_and_summarizes_best(self) -> None:
        self.write_ledger(
            "a1b2c3d\t0.9979\t44.0\tkeep\tbaseline",
            "b2c3d4e\t0.9932\t44.2\tkeep\tincrease LR",
            "c3d4e5f\t1.0050\t44.0\tdiscard\tGeLU activation",
            "d4e5f6a\t0\t0\tcrash\tdouble width (OOM)",
        )
        result = run(str(VALIDATE), str(self.ledger), "--direction", "lower")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("best 0.9932 at b2c3d4e", result.stdout)
        self.assertIn("1 crashes", result.stdout)

    def test_keep_row_that_does_not_improve_is_rejected(self) -> None:
        self.write_ledger(
            "a1b2c3d\t0.9979\t44.0\tkeep\tbaseline",
            "b2c3d4e\t0.9990\t44.2\tkeep\tworse but logged as keep",
        )
        result = run(str(VALIDATE), str(self.ledger), "--direction", "lower")
        self.assertEqual(result.returncode, 1)
        self.assertIn("does not improve", result.stderr)

    def test_direction_higher_is_respected(self) -> None:
        self.write_ledger(
            "a1b2c3d\t0.50\t1.0\tkeep\tbaseline",
            "b2c3d4e\t0.62\t1.0\tkeep\tbetter prompt",
        )
        self.assertEqual(run(str(VALIDATE), str(self.ledger), "--direction", "higher").returncode, 0)
        self.assertEqual(run(str(VALIDATE), str(self.ledger), "--direction", "lower").returncode, 1)

    def test_malformed_rows_are_reported(self) -> None:
        self.write_ledger(
            "zzzzzzz\tnot-a-number\t44.0\tkept\tbaseline",
            "a1b2c3d\t0.9\t1.0\tcrash\tcrash with nonzero metric",
        )
        result = run(str(VALIDATE), str(self.ledger))
        self.assertEqual(result.returncode, 1)
        for fragment in ("not a hex hash", "is not a number", "status 'kept'", "crash rows must record metric 0"):
            self.assertIn(fragment, result.stderr)

    def test_first_row_must_be_baseline_keep(self) -> None:
        self.write_ledger("a1b2c3d\t0.9\t1.0\tdiscard\tnot a baseline")
        result = run(str(VALIDATE), str(self.ledger))
        self.assertEqual(result.returncode, 1)
        self.assertIn("baseline", result.stderr)

    def test_notebook_cross_check(self) -> None:
        self.write_ledger("a1b2c3d\t0.9979\t44.0\tkeep\tbaseline", "b2c3d4e\t0.9932\t44.2\tkeep\tincrease LR")
        notebook = self.root / "experiments.md"
        notebook.write_text("# nb\n\n## a1b2c3d keep\n- Changed: nothing\n\n## b2c3d4e discard\n- Changed: LR\n", encoding="utf-8")
        result = run(str(VALIDATE), str(self.ledger), "--notebook", str(notebook))
        self.assertEqual(result.returncode, 1)
        self.assertIn("notebook entry says discard, ledger says keep", result.stderr)
        notebook.write_text("# nb\n\n## a1b2c3d keep\n\n## b2c3d4e keep\n", encoding="utf-8")
        self.assertEqual(run(str(VALIDATE), str(self.ledger), "--notebook", str(notebook)).returncode, 0)


if __name__ == "__main__":
    unittest.main()
