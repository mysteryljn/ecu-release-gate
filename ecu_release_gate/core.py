import json
import os
from pathlib import Path


class InputError(ValueError):
    """Raised when a release manifest or evidence report is invalid."""


PASS_WORDS = {"ok", "pass", "passed", "success", "successful"}
FAIL_WORDS = {"fail", "failed", "error", "blocked", "failure"}


def _read_json(path):
    try:
        with Path(path).open(encoding="utf-8-sig") as stream:
            value = json.load(stream)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise InputError(f"{path}: {exc}") from exc
    if not isinstance(value, dict):
        raise InputError(f"{path}: report must be a JSON object")
    return value


def _status(report):
    """Extract a conservative pass/fail status from common tool reports."""
    if isinstance(report.get("ok"), bool):
        return report["ok"], "ok"
    if isinstance(report.get("passed"), bool):
        return report["passed"], "passed"
    if isinstance(report.get("gate_failed"), bool):
        return not report["gate_failed"], "gate_failed"
    status = report.get("status")
    if isinstance(status, str):
        normalized = status.strip().casefold()
        if normalized in PASS_WORDS:
            return True, "status"
        if normalized in FAIL_WORDS:
            return False, "status"
    raise InputError("report has no supported boolean or status field")


def _safe_report_path(root, value):
    if not isinstance(value, str) or not value.strip():
        raise InputError("check report path must be a non-empty string")
    candidate = Path(value)
    if candidate.is_absolute():
        raise InputError("check report path must be relative to the manifest")
    root = root.resolve()
    resolved = (root / candidate).resolve()
    try:
        root_key = os.path.normcase(os.path.abspath(str(root)))
        resolved_key = os.path.normcase(os.path.abspath(str(resolved)))
        if os.path.commonpath([root_key, resolved_key]) != root_key:
            raise ValueError
    except (OSError, ValueError) as exc:
        raise InputError("check report path escapes the manifest directory") from exc
    return resolved


def evaluate(manifest_path):
    manifest_path = Path(manifest_path)
    manifest = _read_json(manifest_path)
    release = manifest.get("release", manifest_path.stem)
    if not isinstance(release, str) or not release.strip():
        raise InputError("release must be a non-empty string")
    checks = manifest.get("checks")
    if not isinstance(checks, list) or not checks:
        raise InputError("checks must be a non-empty list")
    seen = set()
    results = []
    root = manifest_path.parent
    for index, check in enumerate(checks):
        if not isinstance(check, dict):
            raise InputError(f"checks[{index}] must be an object")
        name = check.get("name")
        if not isinstance(name, str) or not name.strip():
            raise InputError(f"checks[{index}].name must be a non-empty string")
        if name in seen:
            raise InputError(f"duplicate check name: {name}")
        seen.add(name)
        path = _safe_report_path(root, check.get("report"))
        try:
            report = _read_json(path)
            passed, source = _status(report)
            error = None
        except InputError as exc:
            passed, source, error = False, None, str(exc)
        results.append({"name": name, "report": os.path.relpath(str(path), str(root)).replace("\\", "/"),
                        "passed": passed, "status_field": source, "error": error})
    failed = [item for item in results if not item["passed"]]
    return {"release": release, "ok": not failed, "checks": results,
            "summary": {"total": len(results), "passed": len(results) - len(failed), "failed": len(failed)}}
