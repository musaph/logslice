"""CLI entry-point for the line truncator."""
from __future__ import annotations

import argparse
import sys
from typing import Iterable, Iterator

from logslice.truncator import truncate_lines, count_truncated
from logslice.reader import iter_lines, LogReadError


def build_truncator_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="logslice-truncate",
        description="Truncate long log lines to a maximum width.",
    )
    p.add_argument("file", nargs="?", help="Log file to read (default: stdin).")
    p.add_argument(
        "-w",
        "--width",
        type=int,
        default=120,
        metavar="N",
        help="Maximum line width in characters (default: 120).",
    )
    p.add_argument(
        "--suffix",
        default="…",
        help="Suffix appended to truncated lines (default: '…').",
    )
    p.add_argument(
        "--count",
        action="store_true",
        help="Print the number of truncated lines instead of the lines themselves.",
    )
    return p


def _stdin_lines() -> Iterator[str]:
    for line in sys.stdin:
        yield line.rstrip("\n")


def run_truncator(argv: list[str] | None = None, *, stdout=None, stderr=None) -> int:
    if stdout is None:
        stdout = sys.stdout
    if stderr is None:
        stderr = sys.stderr

    parser = build_truncator_parser()
    args = parser.parse_args(argv)

    try:
        if args.file:
            source: Iterable[str] = iter_lines(args.file)
        else:
            source = _stdin_lines()

        lines = list(source)
    except LogReadError as exc:
        stderr.write(f"error: {exc}\n")
        return 1

    if args.count:
        n = count_truncated(iter(lines), max_width=args.width)
        stdout.write(f"{n}\n")
    else:
        for line in truncate_lines(iter(lines), max_width=args.width, suffix=args.suffix):
            stdout.write(line + "\n")

    return 0


def main() -> None:  # pragma: no cover
    sys.exit(run_truncator())
