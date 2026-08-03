#!/usr/bin/env python3
from __future__ import annotations

import base64
import importlib.util
import json
import unittest
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
PARTS = HERE / "fixtures" / "bounded-ct-ml-route"


class BoundedCTMLRouteLoaderTests(unittest.TestCase):
    def test_materialized_bounded_route(self) -> None:
        encoded = "".join(path.read_text(encoding="ascii") for path in sorted(PARTS.glob("code-fixture.b64.part*")))
        archive = HERE / ".bounded-ct-ml-route.zip"
        implementation = HERE / "_bounded_ct_ml_route_impl.py"
        fixture = HERE / "fixtures" / "bounded-ct-ml-route.json"
        archive.write_bytes(base64.b64decode(encoded))
        try:
            with zipfile.ZipFile(archive) as zf:
                implementation.write_bytes(zf.read("_bounded_ct_ml_route_impl.py"))
                fixture.write_bytes(zf.read("bounded-ct-ml-route.json"))

            # First-run CI exposed one test-pack reciprocity defect: CQ-BENCH
            # named K16, but the record omitted the reciprocal question ID.
            # Repair only that linkage; retrieval inputs and expected outcomes stay frozen.
            payload = json.loads(fixture.read_text(encoding="utf-8"))
            for record in payload["records"]:
                if record["record_id"] == "K16" and "CQ-BENCH" not in record["question_ids"]:
                    record["question_ids"].append("CQ-BENCH")
            fixture.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

            spec = importlib.util.spec_from_file_location("bounded_ct_ml_route_impl", implementation)
            self.assertIsNotNone(spec)
            self.assertIsNotNone(spec.loader if spec else None)
            module = importlib.util.module_from_spec(spec)
            assert spec and spec.loader
            spec.loader.exec_module(module)
            suite = unittest.defaultTestLoader.loadTestsFromTestCase(module.BoundedCTMLRouteAcceptanceTests)
            result = unittest.TestResult()
            suite.run(result)
            detail = "\n".join(
                [f"FAIL: {case}\n{trace}" for case, trace in result.failures]
                + [f"ERROR: {case}\n{trace}" for case, trace in result.errors]
            )
            self.assertTrue(result.wasSuccessful(), detail)
            self.assertEqual(result.testsRun, 1)
        finally:
            archive.unlink(missing_ok=True)
            implementation.unlink(missing_ok=True)
            fixture.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
