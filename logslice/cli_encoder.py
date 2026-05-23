"""CLI entry point for log line transcoding.

Usage examples::

    logslice-encode --format json access.log
    cat app.log | logslice-encode --format logfmt
    logslice-encode --count app.log
"""
from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from logslice.log_encoder import count_decodable, transcode_lines
from logslice.reader import LogReadError, iter_lines


def build_encoder_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="logslice-encode",
        description="Re-encode log lines between plain, JSON, and logfmt formats.",
    )
    parser.add_argument(
        "file",
        nargs="?",
        default=None,
        help="Log file to read (default: stdin).",
    )
    parser.add_argument(
        "--format",
        choices=["json", "logfmt", "plain"],
        default="json",
        help="Target encoding format (default: json).",
    )
    parser.add_argument(
        "--count",
        action="store_true",
        help="Print the number of decodable (structured) lines and exit.",
    )
    return parser


def _stdin_lines() -> List[str]:
    return [line.rstrip("\n") for line in sys.stdin]


def run_encoder(
    args: argparse.Namespace,
    out=sys.stdout,
    err=sys.stderr,
) -> int:
    """Execute the encode command; return exit code."""
    if args.file:
        try:
            lines = list(iter_lines(args.file))
        except LogReadError as exc:
            print(f"error: {exc}", file=err)
            return 1
    else:
        lines = _stdin_lines()

    if args.count:
        print(count_decodable(lines), file=out)
        return 0

    for encoded in transcode_lines(lines, target_format=args.format):
        print(encoded, file=out)

    return 0


def main(argv: Optional[List[str]] = None) -> None:  # pragma: no cover
    parser = build_encoder_parser()
    args = parser.parse_args(argv)
    sys.exit(run_encoder(args))
