"""CLI entry-point for the log profiler."""
from __future__ import annotations

import argparse
import sys
from typing import Iterator

from logslice.reader import iter_lines, LogReadError
from logslice.log_profiler import profile_lines, format_profile


def build_profiler_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="logslice-profile",
        description="Profile a log file: timestamp density, field richness, parse rate.",
    )
    p.add_argument("file", nargs="?", default="-", help="Log file (default: stdin)")
    p.add_argument(
        "--json",
        action="store_true",
        help="Emit results as a single JSON object",
    )
    return p


def _stdin_lines() -> Iterator[str]:
    for line in sys.stdin:
        yield line.rstrip("\n")


def run_profiler(args: argparse.Namespace, out=sys.stdout, err=sys.stderr) -> int:
    try:
        if args.file == "-":
            lines = list(_stdin_lines())
        else:
            lines = list(iter_lines(args.file))
    except LogReadError as exc:
        err.write(f"error: {exc}\n")
        return 1

    result = profile_lines(lines)

    if args.json:
        import json
        data = {
            "total_lines": result.total_lines,
            "lines_with_timestamp": result.lines_with_timestamp,
            "timestamp_density": round(result.timestamp_density, 6),
            "lines_with_fields": result.lines_with_fields,
            "field_density": round(result.field_density, 6),
            "unique_field_names": sorted(result.unique_field_names),
            "avg_fields_per_line": round(result.avg_fields_per_line, 4),
            "elapsed_seconds": round(result.elapsed_seconds, 6),
            "lines_per_second": round(result.lines_per_second, 2),
        }
        out.write(json.dumps(data) + "\n")
    else:
        for line in format_profile(result):
            out.write(line + "\n")
    return 0


def main() -> None:  # pragma: no cover
    parser = build_profiler_parser()
    args = parser.parse_args()
    sys.exit(run_profiler(args))
