"""CLI entry point for the log-templater feature.

Usage:
    logslice-template --template "{level} | {msg}" [FILE]
    cat app.log | logslice-template --template "{level} | {msg}"
"""
from __future__ import annotations

import argparse
import sys
from typing import Iterator

from logslice.log_templater import TemplateOptions, compute_render_result, render_lines
from logslice.reader import LogReadError, iter_lines


def build_templater_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="logslice-template",
        description="Reformat log lines using a field-interpolation template.",
    )
    p.add_argument(
        "file",
        nargs="?",
        default=None,
        help="Log file to read (default: stdin).",
    )
    p.add_argument(
        "--template",
        required=True,
        metavar="TPL",
        help="Template string, e.g. '{level} | {msg}'.",
    )
    p.add_argument(
        "--fallback",
        default="",
        metavar="TEXT",
        help="Text to emit for lines whose fields cannot fill the template.",
    )
    p.add_argument(
        "--skip-unmatched",
        action="store_true",
        help="Silently drop lines that cannot be rendered.",
    )
    p.add_argument(
        "--stats",
        action="store_true",
        help="Print a render summary to stderr instead of rendered lines.",
    )
    return p


def _stdin_lines() -> Iterator[str]:
    for line in sys.stdin:
        yield line.rstrip("\n")


def run_templater(args: argparse.Namespace, out=sys.stdout, err=sys.stderr) -> int:
    opts = TemplateOptions(
        template=args.template,
        fallback=args.fallback,
        skip_unmatched=args.skip_unmatched,
    )

    try:
        source = iter_lines(args.file) if args.file else _stdin_lines()
    except LogReadError as exc:
        err.write(f"error: {exc}\n")
        return 1

    if args.stats:
        lines = list(source)
        from logslice.log_templater import compute_render_result, format_render_result
        result = compute_render_result(lines, opts)
        err.write(format_render_result(result) + "\n")
        for line in result.rendered:
            out.write(line + "\n")
    else:
        for line in render_lines(source, opts):
            out.write(line + "\n")

    return 0


def main() -> None:  # pragma: no cover
    parser = build_templater_parser()
    args = parser.parse_args()
    sys.exit(run_templater(args))
