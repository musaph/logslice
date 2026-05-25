"""CLI entry-point for log-line classification."""
from __future__ import annotations

import argparse
import sys
from typing import Iterator

from logslice.log_classifier import (
    ClassifyRule,
    classify_lines,
    compute_classify_summary,
    format_classify_summary,
    DEFAULT_CATEGORY,
)
from logslice.reader import iter_lines, LogReadError


def build_classifier_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="logslice-classify",
        description="Classify log lines by pattern rules.",
    )
    p.add_argument("file", nargs="?", help="Log file to read (default: stdin)")
    p.add_argument(
        "-r",
        "--rule",
        dest="rules",
        metavar="CATEGORY:PATTERN",
        action="append",
        default=[],
        help="Rule in the form CATEGORY:PATTERN (repeatable)",
    )
    p.add_argument(
        "--case-sensitive",
        action="store_true",
        default=False,
        help="Make pattern matching case-sensitive",
    )
    p.add_argument(
        "--summary",
        action="store_true",
        default=False,
        help="Print a classification summary instead of classified lines",
    )
    p.add_argument(
        "--category",
        default=None,
        help="Only output lines belonging to this category",
    )
    return p


def _stdin_lines() -> Iterator[str]:
    for line in sys.stdin:
        yield line.rstrip("\n")


def _parse_rules(raw: list[str], case_sensitive: bool) -> list[ClassifyRule]:
    rules: list[ClassifyRule] = []
    for entry in raw:
        if ":" not in entry:
            raise ValueError(f"Rule must be CATEGORY:PATTERN, got: {entry!r}")
        category, _, pattern = entry.partition(":")
        rules.append(
            ClassifyRule(
                category=category.strip(),
                pattern=pattern.strip(),
                case_sensitive=case_sensitive,
            )
        )
    return rules


def run_classifier(args: argparse.Namespace, out=sys.stdout, err=sys.stderr) -> int:
    try:
        rules = _parse_rules(args.rules, args.case_sensitive)
    except ValueError as exc:
        err.write(f"error: {exc}\n")
        return 1

    try:
        if args.file:
            source = iter_lines(args.file)
        else:
            source = _stdin_lines()
        classified = list(classify_lines(source, rules))
    except LogReadError as exc:
        err.write(f"error: {exc}\n")
        return 1

    if args.summary:
        out.write(format_classify_summary(compute_classify_summary(classified)) + "\n")
        return 0

    for cl in classified:
        if args.category and cl.category != args.category:
            continue
        out.write(f"[{cl.category}] {cl.line}\n")
    return 0


def main() -> None:  # pragma: no cover
    sys.exit(run_classifier(build_classifier_parser().parse_args()))
