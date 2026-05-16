"""Command-line interface for logslice."""

import argparse
import sys
from datetime import datetime
from typing import Optional

from logslice import get_version
from logslice.reader import read_lines, LogReadError
from logslice.timestamp_parser import parse_timestamp
from logslice.line_filter import filter_lines_by_range, filter_lines_by_keyword
from logslice.output_formatter import FormatOptions, format_lines, lines_to_string


def _parse_dt(value: str) -> datetime:
    """Parse a datetime string from CLI argument."""
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    raise argparse.ArgumentTypeError(
        f"Cannot parse datetime: {value!r}. "
        "Expected formats: YYYY-MM-DDTHH:MM:SS, YYYY-MM-DD HH:MM:SS, YYYY-MM-DD"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="logslice",
        description="Fast log filtering and time-range slicing utility.",
    )
    parser.add_argument("file", help="Log file to process (plain or gzip).")
    parser.add_argument("--start", type=_parse_dt, metavar="DATETIME",
                        help="Include lines with timestamp >= START.")
    parser.add_argument("--end", type=_parse_dt, metavar="DATETIME",
                        help="Include lines with timestamp <= END.")
    parser.add_argument("--keyword", "-k", metavar="PATTERN",
                        help="Filter lines matching keyword/pattern.")
    parser.add_argument("--ignore-case", "-i", action="store_true",
                        help="Case-insensitive keyword matching.")
    parser.add_argument("--line-numbers", "-n", action="store_true",
                        help="Prepend line numbers to output.")
    parser.add_argument("--highlight", action="store_true",
                        help="Highlight matched keyword in output.")
    parser.add_argument("--version", action="version",
                        version=f"logslice {get_version()}")
    return parser


def run(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        lines = read_lines(args.file)
    except LogReadError as exc:
        print(f"logslice: error: {exc}", file=sys.stderr)
        return 1

    if args.start or args.end:
        lines = list(filter_lines_by_range(
            lines,
            start=args.start,
            end=args.end,
            parse_fn=parse_timestamp,
        ))

    if args.keyword:
        lines = list(filter_lines_by_keyword(
            lines,
            pattern=args.keyword,
            ignore_case=args.ignore_case,
        ))

    opts = FormatOptions(
        line_numbers=args.line_numbers,
        highlight=args.keyword if args.highlight else None,
        ignore_case=args.ignore_case,
    )
    output = lines_to_string(format_lines(lines, opts))
    if output:
        print(output)
    return 0


def main():
    sys.exit(run())
