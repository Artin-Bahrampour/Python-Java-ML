"""Command-line entry point."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Sequence

from . import __version__
from .compare import compare_specs
from .errors import OACGError
from .report import write_report
from .spec_loader import load_spec

EXIT_COMPATIBLE = 0
EXIT_BREAKING = 1
EXIT_INPUT_ERROR = 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="oacg",
        description="Detect likely breaking changes between two OpenAPI 3.0/3.1 specifications.",
        epilog="Exit codes: 0=compatible, 1=breaking changes found, 2=input or execution error.",
    )
    parser.add_argument("baseline", help="Path to the released/baseline OpenAPI JSON or YAML file")
    parser.add_argument("candidate", help="Path to the proposed OpenAPI JSON or YAML file")
    parser.add_argument("--report", type=Path, help="Write a machine-readable JSON report to this path")
    parser.add_argument("--fail-on-warning", action="store_true", help="Return exit code 1 when warnings are present")
    parser.add_argument("--quiet", action="store_true", help="Print only the final status line")
    parser.add_argument("--version", action="version", version=f"oacg {__version__}")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(message)s")
    try:
        baseline = load_spec(args.baseline)
        candidate = load_spec(args.candidate)
        report = compare_specs(baseline, candidate, str(args.baseline), str(args.candidate))
        if args.report:
            write_report(report, args.report)
    except OACGError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return EXIT_INPUT_ERROR
    except OSError as exc:
        print(f"ERROR: cannot write report: {exc}", file=sys.stderr)
        return EXIT_INPUT_ERROR

    if not args.quiet:
        for finding in report.findings:
            print(f"[{finding.severity.upper()}] {finding.rule_id} {finding.location}: {finding.message}")
    if not report.compatible:
        status = "BREAKING CHANGES FOUND"
    elif args.fail_on_warning and report.warning_count:
        status = "WARNINGS FAILED BUILD"
    else:
        status = "COMPATIBLE"
    print(f"{status}: {report.breaking_count} breaking, {report.warning_count} warning(s), {len(report.findings)} total finding(s)")

    if not report.compatible or (args.fail_on_warning and report.warning_count):
        return EXIT_BREAKING
    return EXIT_COMPATIBLE


if __name__ == "__main__":
    raise SystemExit(main())
