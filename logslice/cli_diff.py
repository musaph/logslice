"""cli_diff.py – CLI entry-point for log-diff feature."""
from __future__ import annotations

import argparse
import sys
from typing import List

from logslice.log_differ import diff_logs, format_diff, iter_diff_lines
from logslice.reader import LogReadError, read_lines


def build_diff_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="logslice-diff",
        description="Compare two log files and report added/removed lines.",
    )
    p.add_argument("baseline", help="Baseline log file (plain or .gz)")
    p.add_argument("current", help="Current log file to compare against baseline")
    p.add_argument(
        "--show-diff",
        action="store_true",
        default=False,
        help="Print each added/removed/common line prefixed with +/-/space",
    )
    p.add_argument(
        "--added-only",
        action="store_true",
        default=False,
        help="Print only lines present in current but not baseline",
    )
    p.add_argument(
        "--removed-only",
        action="store_true",
        default=False,
        help="Print only lines present in baseline but not current",
    )
    return p


def run_diff(args: argparse.Namespace, out=sys.stdout, err=sys.stderr) -> int:
    """Execute the diff command; return exit code."""
    try:
        baseline_lines: List[str] = read_lines(args.baseline)
        current_lines: List[str] = read_lines(args.current)
    except LogReadError as exc:
        err.write(f"error: {exc}\n")
        return 1

    result = diff_logs(baseline_lines, current_lines)

    if args.added_only:
        for line in result.added:
            out.write(line + "\n")
        return 0

    if args.removed_only:
        for line in result.removed:
            out.write(line + "\n")
        return 0

    if args.show_diff:
        for line in iter_diff_lines(result):
            out.write(line + "\n")
        return 0

    out.write(format_diff(result) + "\n")
    return 0


def main() -> None:  # pragma: no cover
    parser = build_diff_parser()
    args = parser.parse_args()
    sys.exit(run_diff(args))
