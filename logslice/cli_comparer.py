"""CLI entry-point for log-comparer."""
from __future__ import annotations

import argparse
import sys
from typing import List

from logslice.log_comparer import compare_logs, format_compare_result
from logslice.reader import LogReadError, read_lines


def build_comparer_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="logslice-compare",
        description="Compare two log files and report similarity metrics.",
    )
    p.add_argument("file_a", help="First log file (baseline)")
    p.add_argument("file_b", help="Second log file (current)")
    p.add_argument(
        "--only-a",
        action="store_true",
        help="Print lines that appear only in FILE_A",
    )
    p.add_argument(
        "--only-b",
        action="store_true",
        help="Print lines that appear only in FILE_B",
    )
    p.add_argument(
        "--summary",
        action="store_true",
        default=True,
        help="Print similarity summary (default: on)",
    )
    return p


def run_comparer(args: argparse.Namespace, out=sys.stdout, err=sys.stderr) -> int:
    try:
        lines_a: List[str] = read_lines(args.file_a)
        lines_b: List[str] = read_lines(args.file_b)
    except LogReadError as exc:
        err.write(f"error: {exc}\n")
        return 1

    result = compare_logs(lines_a, lines_b)

    if args.only_a:
        for line in result.only_in_a:
            out.write(line + "\n")
        return 0

    if args.only_b:
        for line in result.only_in_b:
            out.write(line + "\n")
        return 0

    out.write(format_compare_result(result) + "\n")
    return 0


def main() -> None:  # pragma: no cover
    parser = build_comparer_parser()
    args = parser.parse_args()
    sys.exit(run_comparer(args))
