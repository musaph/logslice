"""cli_redactor.py – CLI entry-point for the log-redactor feature."""
from __future__ import annotations

import argparse
import sys
from typing import List

from logslice.log_redactor import RedactOptions, redact_lines, count_redacted


def build_redactor_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    kwargs = dict(
        prog="logslice-redact",
        description="Redact sensitive fields or patterns from log lines.",
    )
    parser = parent.add_parser("redact", **kwargs) if parent else argparse.ArgumentParser(**kwargs)
    parser.add_argument("file", nargs="?", help="Log file to read (stdin if omitted)")
    parser.add_argument(
        "-f", "--field",
        dest="fields",
        action="append",
        default=[],
        metavar="FIELD",
        help="Field name to redact (repeatable; works with JSON and logfmt)",
    )
    parser.add_argument(
        "-p", "--pattern",
        dest="patterns",
        action="append",
        default=[],
        metavar="REGEX",
        help="Regex pattern whose matches are masked (repeatable)",
    )
    parser.add_argument(
        "--mask",
        default="***REDACTED***",
        help="Replacement string (default: ***REDACTED***)",
    )
    parser.add_argument(
        "--case-sensitive",
        action="store_true",
        default=False,
        help="Match field names and patterns case-sensitively",
    )
    parser.add_argument(
        "--count",
        action="store_true",
        default=False,
        help="Print the number of redacted lines instead of the redacted output",
    )
    return parser


def _stdin_lines() -> List[str]:
    return sys.stdin.readlines()


def run_redactor(args: argparse.Namespace, out=sys.stdout, err=sys.stderr) -> int:
    opts = RedactOptions(
        fields=args.fields,
        patterns=args.patterns,
        mask=args.mask,
        case_sensitive=args.case_sensitive,
    )

    if args.file:
        try:
            with open(args.file, "r", encoding="utf-8", errors="replace") as fh:
                lines = fh.readlines()
        except OSError as exc:
            err.write(f"error: {exc}\n")
            return 1
    else:
        lines = _stdin_lines()

    if args.count:
        out.write(f"{count_redacted(lines, opts)}\n")
        return 0

    for line in redact_lines(lines, opts):
        out.write(line + "\n")
    return 0


def main() -> None:  # pragma: no cover
    parser = build_redactor_parser()
    args = parser.parse_args()
    sys.exit(run_redactor(args))
