"""cli_watchdog.py — CLI entry-point for the log watchdog feature."""
from __future__ import annotations

import argparse
import sys
from typing import Iterator

from logslice.log_watchdog import WatchdogOptions, compute_watchdog_result, format_watchdog_result
from logslice.reader import LogReadError, iter_lines


def build_watchdog_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # type: ignore[name-defined]
    kwargs = dict(
        prog="logslice-watchdog",
        description="Scan a log file and alert when lines match a pattern.",
    )
    parser = parent.add_parser("watchdog", **kwargs) if parent else argparse.ArgumentParser(**kwargs)
    parser.add_argument("file", nargs="?", help="Log file to scan (stdin if omitted)")
    parser.add_argument(
        "-p", "--pattern",
        dest="patterns",
        action="append",
        default=[],
        metavar="PATTERN",
        help="Pattern to watch for (repeatable)",
    )
    parser.add_argument(
        "--case-sensitive",
        action="store_true",
        default=False,
        help="Enable case-sensitive matching",
    )
    parser.add_argument(
        "--max-alerts",
        type=int,
        default=0,
        metavar="N",
        help="Stop after N alerts (0 = unlimited)",
    )
    parser.add_argument(
        "--stop-on-first",
        action="store_true",
        default=False,
        help="Stop after the very first alert",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        default=False,
        help="Print a summary instead of individual alerts",
    )
    return parser


def _stdin_lines() -> Iterator[str]:
    yield from sys.stdin


def run_watchdog(args: argparse.Namespace, out=sys.stdout, err=sys.stderr) -> int:
    options = WatchdogOptions(
        patterns=args.patterns,
        case_sensitive=args.case_sensitive,
        max_alerts=args.max_alerts,
        stop_on_first=args.stop_on_first,
    )

    try:
        lines = list(iter_lines(args.file)) if args.file else list(_stdin_lines())
    except LogReadError as exc:
        err.write(f"error: {exc}\n")
        return 1

    result = compute_watchdog_result(lines, options)

    if args.summary:
        out.write(format_watchdog_result(result) + "\n")
    else:
        for alert in result.alerts:
            out.write(str(alert) + "\n")

    return 0


def main() -> None:  # pragma: no cover
    parser = build_watchdog_parser()
    args = parser.parse_args()
    sys.exit(run_watchdog(args))
