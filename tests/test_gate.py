import json
import tempfile
import unittest
from pathlib import Path

from ecu_release_gate.core import InputError, evaluate
from ecu_release_gate.report import render
from ecu_release_gate.cli import main


class GateTests(unittest.TestCase):
    def write_manifest(self, root, checks, release="1.0"):
        (root / "manifest.json").write_text(json.dumps({"release": release, "checks": checks}), encoding="utf-8")

    def test_accepts_common_pass_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name, report in (("a", {"ok": True}), ("b", {"passed": True}), ("c", {"status": "success"}), ("d", {"gate_failed": False})):
                (root / (name + ".json")).write_text(json.dumps(report), encoding="utf-8")
            self.write_manifest(root, [{"name": name, "report": name + ".json"} for name in "abcd"])
            result = evaluate(root / "manifest.json")
            self.assertTrue(result["ok"])
            self.assertEqual(result["summary"], {"total": 4, "passed": 4, "failed": 0})

    def test_failure_field_fails_gate(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "bad.json").write_text('{"ok": false}', encoding="utf-8")
            self.write_manifest(root, [{"name": "bad", "report": "bad.json"}])
            result = evaluate(root / "manifest.json")
            self.assertFalse(result["ok"])
            self.assertEqual(result["summary"]["failed"], 1)

    def test_missing_report_is_a_failed_check(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_manifest(root, [{"name": "missing", "report": "missing.json"}])
            result = evaluate(root / "manifest.json")
            self.assertFalse(result["ok"])
            self.assertIn("missing.json", result["checks"][0]["error"])

    def test_invalid_report_status_is_failed_check(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "unknown.json").write_text('{"value": 1}', encoding="utf-8")
            self.write_manifest(root, [{"name": "unknown", "report": "unknown.json"}])
            self.assertFalse(evaluate(root / "manifest.json")["ok"])

    def test_traversal_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_manifest(root, [{"name": "escape", "report": "../outside.json"}])
            with self.assertRaisesRegex(InputError, "escapes"):
                evaluate(root / "manifest.json")

    def test_absolute_report_path_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_manifest(root, [{"name": "absolute", "report": str(root / "x.json")}])
            with self.assertRaisesRegex(InputError, "relative"):
                evaluate(root / "manifest.json")

    def test_duplicate_names_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "ok.json").write_text('{"ok":true}', encoding="utf-8")
            self.write_manifest(root, [{"name": "same", "report": "ok.json"}, {"name": "same", "report": "ok.json"}])
            with self.assertRaisesRegex(InputError, "duplicate"):
                evaluate(root / "manifest.json")

    def test_empty_checks_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_manifest(root, [])
            with self.assertRaisesRegex(InputError, "non-empty"):
                evaluate(root / "manifest.json")

    def test_html_escapes_external_values(self):
        report = {"release": "<release>", "ok": False, "checks": [{"name": "<x>", "report": "a&b", "passed": False, "error": "<bad>"}]}
        output = render(report, "html")
        self.assertIn("&lt;release&gt;", output)
        self.assertIn("&lt;bad&gt;", output)

    def test_cli_demo_and_status(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "report.html"
            self.assertEqual(main(["demo", "--output", str(output)]), 0)
            self.assertTrue(output.is_file())


if __name__ == "__main__":
    unittest.main()
