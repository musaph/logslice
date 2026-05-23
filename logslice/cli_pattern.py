"""CLI entry-point for regex-based pattern filtering."""
from __future__ import annotations

import argparse
import sys
from typing import Iterator, List

from logslice.pattern_filter import count_pattern_matches, filter_by_pattern
from logslice.reader import LogReadError, iter_lines


def build_pattern_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="logslice-pattern",
        description="Filter log lines by a regular expression.",
    )
    p.add_argument("pattern", help="Regular expression to match against each line.")
    p.add_argument("file", nargs="?", help="Log file path (stdin if omitted).")
    p.add_argument("-v", "--invert", action="store_true", help="Invert match (exclude matching lines).")
    p.add_argument("-c", "--count", action="store_true", help="Print count of matching lines instead of lines.")
    p.add_argument("-s", "--case-sensitive", action="store_true", help="Enable case-sensitive matching.")
    return p


def _stdin_lines() -> Iterator[str]:
    for line in sys.stdin:
        yield line.rstrip("\n")


def run_pattern(argv: List[str] | None = None) -> int:
    parser = build_pattern_parser()
    args = parser.parse_args(argv)

    ignore_case = not args.case_sensitive

    try:
        if args.file:
            lines = iter_lines(args.file)
        else:
            lines = _stdin_lines()
    except LogReadError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.count:
        # Materialise to count; acceptable for CLI use.
        n = count_pattern_matches(lines, args.pattern, ignore_case=ignore_case)
        print(n)
        return 0

    matched_any = False
    for line in filter_by_pattern(lines, args.pattern, ignore_case=ignore_case, invert=args.invert):
        print(line)
        matched_any = True

    return 0 if matched_any or args.invert else 0


def main() -> None:  # pragma: no cover
    sys.exit(run_pattern())


if __name__ == "__main__":  # pragma: no cover
    main()
