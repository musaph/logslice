"""cli_denoiser.py – CLI entry-point for the log denoiser.

Usage examples::

    logslice-denoise --threshold 10 app.log
    cat app.log | logslice-denoise --summarise
    logslice-denoise --stats app.log
"""
from __future__ import annotations

import argparse
import sys
from typing import Iterator

from logslice.log_denoiser import (
    compute_denoise_result,
    denoise,
    format_denoise_result,
)
from logslice.reader import LogReadError, iter_lines


def build_denoiser_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="logslice-denoise",
        description="Suppress repetitive log lines that exceed a pattern threshold.",
    )
    p.add_argument(
        "file",
        nargs="?",
        default=None,
        help="Log file to read (default: stdin).",
    )
    p.add_argument(
        "--threshold",
        type=int,
        default=5,
        metavar="N",
        help="Max occurrences of a normalised pattern before suppression (default: 5).",
    )
    p.add_argument(
        "--summarise",
        action="store_true",
        help="Append one summary line per suppressed pattern at the end.",
    )
    p.add_argument(
        "--stats",
        action="store_true",
        help="Print denoising statistics to stderr instead of filtered output.",
    )
    return p


def _stdin_lines() -> Iterator[str]:
    for line in sys.stdin:
        yield line.rstrip("\n")


def run_denoiser(args: argparse.Namespace, out=sys.stdout, err=sys.stderr) -> int:
    """Execute the denoiser command.  Returns an exit code."""
    try:
        if args.file:
            lines = list(iter_lines(args.file))
        else:
            lines = list(_stdin_lines())
    except LogReadError as exc:
        err.write(f"error: {exc}\n")
        return 1

    if args.stats:
        _, result = compute_denoise_result(lines, threshold=args.threshold)
        out.write(format_denoise_result(result) + "\n")
        return 0

    for line in denoise(lines, threshold=args.threshold, summarise=args.summarise):
        out.write(line + "\n")

    return 0


def main() -> None:  # pragma: no cover
    parser = build_denoiser_parser()
    args = parser.parse_args()
    sys.exit(run_denoiser(args))
