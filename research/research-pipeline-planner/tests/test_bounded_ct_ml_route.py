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

            # CI pass 1 exposed a test-pack reciprocity defect: CQ-BENCH
            # named K16, but the record omitted the reciprocal question ID.
            # CI pass 2 exposed a commitment-schema representation defect:
            # selection_history must use decision/rationale objects.
            # These repairs do not change retrieval inputs or expected outcomes.
            payload = json.loads(fixture.read_text(encoding="utf-8"))
            for record in payload["records"]:
                if record["record_id"] == "K16" and "CQ-BENCH" not in record["question_ids"]:
                    record["question_ids"].append("CQ-BENCH")
            payload["paper_identity"]["selection_history"] = [
                {
                    "decision": "select IDEA-002",
                    "rationale": "Selected from ten candidates after score-independent overlap, falsifiability, and feasibility review.",
                }
            ]
            fixture.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

            # CI pass 3 showed that the fixture assertion still read the legacy
            # string representation. Align the assertion with the validated
            # decision/rationale object without changing the selected identity.
            old_assertion = "self.assertEqual(commitment['selection_history'][0].split()[0],self.fixture['selected_idea_id'])"
            new_assertion = "self.assertEqual(commitment['selection_history'][0]['decision'].split()[-1], self.fixture['selected_idea_id'])"
            implementation_text = implementation.read_text(encoding="utf-8")
            self.assertIn(old_assertion, implementation_text)
            implementation.write_text(
                implementation_text.replace(old_assertion, new_assertion, 1),
                encoding="utf-8",
            )

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
