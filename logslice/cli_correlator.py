"""CLI entry-point for log-line correlation."""
from __future__ import annotations

import argparse
import sys
from typing import Iterator, List

from logslice.log_correlator import (
    correlate,
    format_correlation_summary,
    iter_correlated_lines,
)
from logslice.reader import LogReadError, read_lines


def build_correlator_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="logslice-correlate",
        description="Group log lines by a shared structured field.",
    )
    p.add_argument("file", nargs="?", help="Log file to read (default: stdin)")
    p.add_argument(
        "-f", "--field",
        required=True,
        metavar="FIELD",
        help="Structured field name to correlate on (e.g. request_id)",
    )
    p.add_argument(
        "-m", "--min-group",
        type=int,
        default=1,
        metavar="N",
        help="Minimum lines per group (smaller groups go to unmatched)",
    )
    p.add_argument(
        "--summary",
        action="store_true",
        help="Print a summary instead of the correlated lines",
    )
    p.add_argument(
        "--unmatched",
        action="store_true",
        help="Print only unmatched lines",
    )
    return p


def _stdin_lines() -> Iterator[str]:
    for line in sys.stdin:
        yield line.rstrip("\n")


def run_correlator(args: argparse.Namespace, out=sys.stdout, err=sys.stderr) -> int:
    try:
        if args.file:
            raw: List[str] = read_lines(args.file)
        else:
            raw = list(_stdin_lines())
    except LogReadError as exc:
        err.write(f"error: {exc}\n")
        return 1

    result = correlate(raw, args.field, min_group_size=args.min_group)

    if args.summary:
        out.write(format_correlation_summary(result) + "\n")
        return 0

    if args.unmatched:
        for line in result.unmatched:
            out.write(line + "\n")
        return 0

    for line in iter_correlated_lines(result):
        out.write(line + "\n")
    return 0


def main() -> None:  # pragma: no cover
    parser = build_correlator_parser()
    args = parser.parse_args()
    sys.exit(run_correlator(args))
