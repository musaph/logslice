"""CLI entry-point for the log-tagger feature."""
from __future__ import annotations

import argparse
import json
import sys
from typing import Iterator, List

from logslice.log_tagger import TagRule, count_by_tag, tag_lines
from logslice.reader import LogReadError, iter_lines


def build_tagger_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="logslice-tag",
        description="Tag log lines with labels based on keyword/pattern rules.",
    )
    p.add_argument("file", nargs="?", help="Log file to read (stdin if omitted)")
    p.add_argument(
        "-r", "--rule",
        metavar="TAG:PATTERN",
        action="append",
        dest="rules",
        default=[],
        help="Tag rule in the form TAG:PATTERN (repeatable)",
    )
    p.add_argument(
        "--rules-file",
        metavar="FILE",
        help="JSON file containing a list of {tag, pattern} objects",
    )
    p.add_argument(
        "--tagged-only",
        action="store_true",
        help="Only output lines that match at least one rule",
    )
    p.add_argument(
        "--stats",
        action="store_true",
        help="Print tag counts to stderr instead of formatted lines",
    )
    p.add_argument(
        "--case-sensitive",
        action="store_true",
        help="Make all inline rules case-sensitive",
    )
    return p


def _stdin_lines() -> Iterator[str]:
    for line in sys.stdin:
        yield line.rstrip("\n")


def _build_rules(args: argparse.Namespace) -> List[TagRule]:
    rules: List[TagRule] = []
    for raw in args.rules:
        if ":" not in raw:
            raise ValueError(f"Rule must be TAG:PATTERN, got: {raw!r}")
        tag, _, pattern = raw.partition(":")
        rules.append(TagRule(tag=tag.strip(), pattern=pattern.strip(),
                             case_sensitive=args.case_sensitive))
    if args.rules_file:
        with open(args.rules_file, encoding="utf-8") as fh:
            raw_list = json.load(fh)
        rules.extend(
            TagRule(
                tag=item["tag"],
                pattern=item["pattern"],
                case_sensitive=item.get("case_sensitive", args.case_sensitive),
            )
            for item in raw_list
        )
    return rules


def run_tagger(args: argparse.Namespace, out=sys.stdout, err=sys.stderr) -> int:
    try:
        rules = _build_rules(args)
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        err.write(f"error: {exc}\n")
        return 1

    try:
        source = iter_lines(args.file) if args.file else _stdin_lines()
        tagged = list(tag_lines(source, rules, tagged_only=args.tagged_only))
    except LogReadError as exc:
        err.write(f"error: {exc}\n")
        return 1

    if args.stats:
        counts = count_by_tag(tagged)
        for tag, n in sorted(counts.items()):
            err.write(f"{tag}: {n}\n")
    else:
        for tl in tagged:
            out.write(tl.formatted() + "\n")
    return 0


def main() -> None:  # pragma: no cover
    parser = build_tagger_parser()
    sys.exit(run_tagger(parser.parse_args()))
