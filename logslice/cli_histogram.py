"""CLI entry-point for log histogram generation."""
from __future__ import annotations

import argparse
import sys
from typing import Iterator, List, Optional

from logslice.log_histogram import compute_histogram, format_histogram
from logslice.reader import LogReadError, iter_lines

_INTERVALS = ["second", "minute", "hour", "day"]


def build_histogram_parser(parent: Optional[argparse.ArgumentParser] = None) -> argparse.ArgumentParser:
    p = parent or argparse.ArgumentParser(
        prog="logslice-histogram",
        description="Bucket log lines by time and render an ASCII histogram.",
    )
    p.add_argument(
        "file",
        nargs="?",
        default=None,
        help="Log file to read (plain or gzip). Reads stdin if omitted.",
    )
    p.add_argument(
        "--interval",
        choices=_INTERVALS,
        default="minute",
        metavar="INTERVAL",
        help="Time bucket size: second, minute (default), hour, day.",
    )
    p.add_argument(
        "--bar-width",
        type=int,
        default=40,
        dest="bar_width",
        metavar="N",
        help="Maximum bar width in characters (default 40).",
    )
    return p


def _stdin_lines() -> Iterator[str]:
    for line in sys.stdin:
        yield line.rstrip("\n")


def run_histogram(args: argparse.Namespace) -> int:
    try:
        if args.file:
            lines: Iterator[str] = iter_lines(args.file)
        else:
            lines = _stdin_lines()

        hist = compute_histogram(lines, interval=args.interval)
        for row in format_histogram(hist, bar_width=args.bar_width):
            print(row)
        return 0
    except LogReadError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


def main() -> None:  # pragma: no cover
    parser = build_histogram_parser()
    sys.exit(run_histogram(parser.parse_args()))


if __name__ == "__main__":  # pragma: no cover
    main()
