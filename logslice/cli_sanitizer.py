"""CLI entry point for log-sanitize: redact sensitive data from log streams."""

from __future__ import annotations

import argparse
import sys
from typing import Iterator, List

from logslice.log_sanitizer import SanitizeOptions, sanitize_lines

_BUILTIN_CHOICES = ["ipv4", "email", "token", "jwt", "credit_card"]


def build_sanitizer_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="logslice-sanitize",
        description="Redact sensitive patterns from log lines.",
    )
    parser.add_argument(
        "file",
        nargs="?",
        default="-",
        help="Log file to read (default: stdin).",
    )
    parser.add_argument(
        "--builtin",
        dest="builtins",
        metavar="PATTERN",
        choices=_BUILTIN_CHOICES,
        action="append",
        default=[],
        help=f"Built-in pattern to redact. Choices: {', '.join(_BUILTIN_CHOICES)}. May be repeated.",
    )
    parser.add_argument(
        "--pattern",
        dest="custom",
        metavar="REGEX",
        action="append",
        default=[],
        help="Custom regex pattern to redact. May be repeated.",
    )
    parser.add_argument(
        "--mask",
        default="***REDACTED***",
        help="Replacement string for redacted values (default: ***REDACTED***).",
    )
    parser.add_argument(
        "--count",
        action="store_true",
        help="Print total redaction count instead of sanitized lines.",
    )
    return parser


def _stdin_lines() -> Iterator[str]:
    for line in sys.stdin:
        yield line.rstrip("\n")


def run_sanitizer(argv: List[str] | None = None, *, stdout=None, stderr=None) -> int:
    if stdout is None:
        stdout = sys.stdout
    if stderr is None:
        stderr = sys.stderr

    parser = build_sanitizer_parser()
    args = parser.parse_args(argv)

    opts = SanitizeOptions(
        mask=args.mask,
        builtin_patterns=args.builtins,
        custom_patterns=args.custom,
    )

    try:
        if args.file == "-":
            lines = list(_stdin_lines())
        else:
            with open(args.file) as fh:
                lines = [l.rstrip("\n") for l in fh]
    except OSError as exc:
        stderr.write(f"error: {exc}\n")
        return 1

    results = list(sanitize_lines(lines, opts))

    if args.count:
        total = sum(r.redacted_count for r in results)
        stdout.write(f"{total}\n")
    else:
        for r in results:
            stdout.write(r.line + "\n")

    return 0


def main() -> None:  # pragma: no cover
    raise SystemExit(run_sanitizer())
