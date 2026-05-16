"""Command-line interface for logslice."""
from __future__ import annotations

import argparse
import sys
from datetime import datetime
from typing import List, Optional

from logslice.reader import LogReadError, read_lines
from logslice.line_filter import filter_lines_by_range, filter_lines_by_keyword
from logslice.output_formatter import FormatOptions, format_lines, lines_to_string
from logslice.sampler import sample_head, sample_tail, sample_every_nth
from logslice.deduplicator import deduplicate

_DT_FORMATS = ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"]


def _parse_dt(value: str) -> datetime:
    for fmt in _DT_FORMATS:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    raise argparse.ArgumentTypeError(f"Cannot parse datetime: {value!r}")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="logslice",
        description="Fast log filtering and time-range slicing utility.",
    )
    p.add_argument("file", help="Log file to process (.log or .gz)")
    p.add_argument("--start", metavar="DATETIME", type=_parse_dt, help="Include lines at or after this time")
    p.add_argument("--end", metavar="DATETIME", type=_parse_dt, help="Include lines at or before this time")
    p.add_argument("--keyword", metavar="PATTERN", help="Only include lines matching this keyword/regex")
    p.add_argument("--head", metavar="N", type=int, help="Keep only the first N lines")
    p.add_argument("--tail", metavar="N", type=int, help="Keep only the last N lines")
    p.add_argument("--nth", metavar="N", type=int, help="Keep every Nth line")
    p.add_argument("--dedup", action="store_true", help="Remove duplicate lines")
    p.add_argument(
        "--dedup-ignore-ts",
        action="store_true",
        dest="dedup_ignore_ts",
        help="When deduplicating, ignore leading timestamp (requires --ts-width)",
    )
    p.add_argument("--ts-width", metavar="N", type=int, default=0, dest="ts_width", help="Timestamp column width for --dedup-ignore-ts")
    p.add_argument("--line-numbers", action="store_true", dest="line_numbers", help="Prepend line numbers to output")
    p.add_argument("--highlight", metavar="PATTERN", help="Highlight matching text in output")
    p.add_argument("--version", action="version", version=f"logslice {_version()}")
    return p


def _version() -> str:
    try:
        from logslice import get_version
        return get_version()
    except Exception:
        return "unknown"


def run(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        raw = read_lines(args.file)
    except LogReadError as exc:
        print(f"logslice: error: {exc}", file=sys.stderr)
        return 1

    lines = list(raw)

    if args.start or args.end:
        lines = list(filter_lines_by_range(lines, start=args.start, end=args.end))

    if args.keyword:
        lines = list(filter_lines_by_keyword(lines, pattern=args.keyword))

    if args.dedup:
        lines = list(deduplicate(lines, ignore_timestamps=args.dedup_ignore_ts, timestamp_col_end=args.ts_width))

    if args.head is not None:
        lines = list(sample_head(lines, args.head))
    elif args.tail is not None:
        lines = list(sample_tail(lines, args.tail))
    elif args.nth is not None:
        lines = list(sample_every_nth(lines, args.nth))

    opts = FormatOptions(
        line_numbers=args.line_numbers,
        highlight_pattern=args.highlight,
    )
    print(lines_to_string(format_lines(lines, opts)))
    return 0


def main() -> None:  # pragma: no cover
    sys.exit(run())
