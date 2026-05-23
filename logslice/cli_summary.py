"""CLI entry-point: logslice-summary — print a summary of a log file."""
from __future__ import annotations

import argparse
import sys
from typing import List

from logslice.reader import iter_lines, LogReadError
from logslice.log_summary import summarise, format_summary


def build_summary_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="logslice-summary",
        description="Print a statistical summary of a log file.",
    )
    p.add_argument(
        "file",
        nargs="?",
        default="-",
        help="Log file to read (default: stdin).",
    )
    p.add_argument(
        "--no-levels",
        action="store_true",
        help="Omit per-level breakdown from output.",
    )
    return p


def _stdin_lines() -> List[str]:
    return [line.rstrip("\n") for line in sys.stdin]


def run_summary(args: argparse.Namespace, out=sys.stdout, err=sys.stderr) -> int:
    try:
        if args.file == "-":
            lines = _stdin_lines()
        else:
            lines = list(iter_lines(args.file))
    except LogReadError as exc:
        err.write(f"error: {exc}\n")
        return 1

    summary = summarise(lines)

    if args.no_levels:
        summary.level_counts = {}

    for row in format_summary(summary):
        out.write(row + "\n")

    return 0


def main() -> None:  # pragma: no cover
    parser = build_summary_parser()
    args = parser.parse_args()
    sys.exit(run_summary(args))


if __name__ == "__main__":  # pragma: no cover
    main()
