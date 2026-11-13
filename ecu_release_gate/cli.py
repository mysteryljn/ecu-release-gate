import argparse
import sys
from pathlib import Path

from .core import InputError, evaluate
from .report import render


def main(argv=None):
    parser = argparse.ArgumentParser(description="Aggregate ECU release evidence reports into one CI gate")
    sub = parser.add_subparsers(dest="command")
    check = sub.add_parser("check")
    check.add_argument("manifest", type=Path)
    check.add_argument("--format", choices=("json", "markdown", "html"), default="json")
    check.add_argument("--output", type=Path)
    demo = sub.add_parser("demo")
    demo.add_argument("--format", choices=("json", "markdown", "html"), default="html")
    demo.add_argument("--output", type=Path, default=Path("release-gate.html"))
    args = parser.parse_args(argv)
    if args.command is None:
        parser.error("a command is required")
    try:
        if args.command == "demo":
            manifest = Path(__file__).parent / "fixtures" / "release.json"
            output = args.output
        else:
            manifest = args.manifest
            output = args.output
            if output and output.resolve() == manifest.resolve():
                raise InputError("output must differ from manifest")
        report = evaluate(manifest)
        content = render(report, args.format)
        if output:
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(content, encoding="utf-8")
        else:
            sys.stdout.write(content)
        return 0 if report["ok"] else 1
    except (OSError, UnicodeError, InputError, ValueError) as exc:
        print("error: " + str(exc), file=sys.stderr)
        return 2
