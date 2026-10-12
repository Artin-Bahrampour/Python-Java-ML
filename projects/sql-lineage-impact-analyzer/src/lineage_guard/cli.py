"""Command-line interface for SQL lineage analysis."""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
from collections.abc import Sequence
from pathlib import Path

from . import __version__
from .analyzer import analyze_directory
from .errors import LineageError
from .graph import build_impact
from .render import (
    render_impact_json,
    render_impact_text,
    render_lineage_json,
    render_lineage_text,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lineage-guard",
        description="Analyze SQL model dependencies and downstream change impact.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    commands = parser.add_subparsers(dest="command", required=True)

    analyze = commands.add_parser("analyze", help="build a model lineage report")
    _add_model_options(analyze)
    analyze.add_argument("--fail-on-cycles", action="store_true")

    impact = commands.add_parser("impact", help="list downstream models affected by a change")
    _add_model_options(impact)
    impact.add_argument(
        "--changed",
        action="append",
        required=True,
        metavar="MODEL",
        help="changed model name; repeat the option to compare multiple changes",
    )
    return parser


def _add_model_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--models-dir", type=Path, required=True)
    parser.add_argument("--dialect", default="postgres")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument(
        "--output",
        type=str,
        default="-",
        help="output file; '-' or omission writes to stdout",
    )


def _write_output(content: str, destination: str) -> None:
    if destination == "-":
        sys.stdout.write(content)
        return
    target = Path(destination)
    target.parent.mkdir(parents=True, exist_ok=True)
    temp_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=target.parent,
            prefix=f".{target.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temp_name = temporary.name
            temporary.write(content)
            temporary.flush()
            os.fsync(temporary.fileno())
        os.replace(temp_name, target)
    except OSError:
        if temp_name:
            try:
                os.unlink(temp_name)
            except OSError:
                pass
        raise


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        report = analyze_directory(args.models_dir, args.dialect)
        if args.command == "analyze":
            content = (
                render_lineage_json(report)
                if args.format == "json"
                else render_lineage_text(report)
            )
            _write_output(content, args.output)
            return 1 if args.fail_on_cycles and report.cycles else 0

        impact_report = build_impact(report, args.changed)
        content = (
            render_impact_json(impact_report)
            if args.format == "json"
            else render_impact_text(impact_report)
        )
        _write_output(content, args.output)
        return 0
    except (LineageError, OSError, ValueError) as exc:
        print(f"lineage-guard: error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
