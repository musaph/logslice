"""CLI entry point for log-tracer: trace a field value across log lines."""
from __future__ import annotations

import argparse
import sys
from typing import Iterator

from logslice.log_tracer import compute_trace_result, format_trace_result
from logslice.reader import LogReadError, iter_lines


def build_tracer_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="logslice-trace",
        description="Trace a field value across log lines.",
    )
    p.add_argument("file", nargs="?", help="Log file (omit to read stdin)")
    p.add_argument("--field", required=True, help="Field name to match on")
    p.add_argument("--value", required=True, help="Field value to trace")
    p.add_argument(
        "--case-sensitive",
        action="store_true",
        default=False,
        help="Use case-sensitive matching (default: case-insensitive)",
    )
    p.add_argument(
        "--count",
        action="store_true",
        default=False,
        help="Print only the number of matching lines",
    )
    return p


def _stdin_lines() -> Iterator[str]:
    for line in sys.stdin:
        yield line


def run_tracer(argv: list[str] | None = None, *, out=None) -> int:
    if out is None:
        out = sys.stdout
    parser = build_tracer_parser()
    args = parser.parse_args(argv)

    try:
        if args.file:
            lines = iter_lines(args.file)
        else:
            lines = _stdin_lines()
        result = compute_trace_result(
            lines,
            args.field,
            args.value,
            case_sensitive=args.case_sensitive,
        )
    except LogReadError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.count:
        print(result.count, file=out)
    else:
        print(format_trace_result(result), file=out)
    return 0


def main() -> None:  # pragma: no cover
    sys.exit(run_tracer())
