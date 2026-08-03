#!/usr/bin/env python3
from __future__ import annotations

import base64
import importlib.util
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
