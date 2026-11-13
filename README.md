# ecu-release-gate

Turn separate ECU release reports into one reviewable CI decision. The gate reads a small manifest that points at JSON reports produced by firmware, memory, SBOM and security tools, then emits JSON, Markdown or self-contained HTML with one exit code.

```bash
python -m pip install "ecu-release-gate @ git+https://github.com/mysteryljn/ecu-release-gate.git"
ecu-release-gate check release.json --format html --output release-gate.html
```

Manifest example:

```json
{"release":"ecu-1.2.0","checks":[
  {"name":"firmware-image","report":"image.json"},
  {"name":"memory-budget","report":"size.json"},
  {"name":"sbom-policy","report":"sbom.json"},
  {"name":"security-findings","report":"sarif.json"}
]}
```

The aggregator recognizes the common `ok`, `passed`, `gate_failed` and textual `status` fields. It never re-parses firmware, SBOM or SARIF formats, never executes a build, and rejects absolute or escaping report paths. A report with an unsupported status fails closed. It is a release evidence gate, not a safety or security certification tool.

## Development

`python -m unittest discover -s tests -v` runs the offline suite. `python -m ecu_release_gate demo --output report.html` uses the bundled synthetic reports.

MIT License.
