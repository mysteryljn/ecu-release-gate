import html
import json


def render(report, format="json"):
    if format == "json":
        return json.dumps(report, indent=2, ensure_ascii=True, allow_nan=False) + "\n"
    if format == "markdown":
        lines = ["# ECU release gate", "", "Release: `%s`" % report["release"],
                 "", "Decision: **%s**" % ("PASS" if report["ok"] else "FAIL"), "",
                 "| Check | Report | Result | Error |", "|---|---|---|---|"]
        for item in report["checks"]:
            values = [item["name"], item["report"], "PASS" if item["passed"] else "FAIL", item["error"] or ""]
            lines.append("| " + " | ".join(str(value).replace("|", "\\|").replace("\n", " ") for value in values) + " |")
        return "\n".join(lines) + "\n"
    if format != "html":
        raise ValueError("format must be json, markdown or html")
    esc = lambda value: html.escape(str(value), quote=True)
    rows = []
    for item in report["checks"]:
        rows.append("<tr><td>" + esc(item["name"]) + "</td><td>" + esc(item["report"]) +
                    "</td><td>" + ("PASS" if item["passed"] else "FAIL") + "</td><td>" +
                    esc(item["error"] or "") + "</td></tr>")
    return ("<!doctype html><meta charset='utf-8'><title>ECU release gate</title>"
            "<style>body{font:16px system-ui;margin:2rem;color:#172b4d}table{border-collapse:collapse;width:100%}"
            "td,th{padding:.5rem;border:1px solid #ccd}th{background:#edf2f7}</style>"
            "<h1>ECU release gate</h1><p>Release: <strong>" + esc(report["release"]) +
            "</strong> · Decision: <strong>" + ("PASS" if report["ok"] else "FAIL") +
            "</strong></p><table><tr><th>Check</th><th>Report</th><th>Result</th><th>Error</th></tr>" +
            "".join(rows) + "</table>\n")
