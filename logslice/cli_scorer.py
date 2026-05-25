"""CLI entry-point for relevance scoring of log lines."""
from __future__ import annotations

import argparse
import sys
from typing import Iterator, List

from logslice.log_scorer import ScoreOptions, format_scored_line, score_lines, top_n
from logslice.reader import LogReadError, iter_lines


def build_scorer_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="logslice-score",
        description="Score log lines by keyword relevance.",
    )
    p.add_argument("file", nargs="?", help="Log file (stdin if omitted)")
    p.add_argument(
        "-w",
        "--weight",
        metavar="TERM:SCORE",
        action="append",
        dest="weights",
        default=[],
        help="Keyword and numeric weight, e.g. error:2.0 (repeatable)",
    )
    p.add_argument(
        "--min-score",
        type=float,
        default=0.0,
        help="Minimum score threshold (default: 0.0)",
    )
    p.add_argument(
        "--top",
        type=int,
        default=0,
        metavar="N",
        help="Show only the top-N highest-scoring lines",
    )
    p.add_argument(
        "--case-sensitive",
        action="store_true",
        default=False,
    )
    p.add_argument(
        "--hide-terms",
        action="store_true",
        default=False,
    )
    return p


def _stdin_lines() -> Iterator[str]:
    yield from sys.stdin


def _parse_weights(raw: List[str]) -> dict[str, float]:
    weights: dict[str, float] = {}
    for item in raw:
        if ":" not in item:
            weights[item] = 1.0
        else:
            term, _, val = item.rpartition(":")
            try:
                weights[term] = float(val)
            except ValueError:
                weights[item] = 1.0
    return weights


def run_scorer(args: argparse.Namespace, *, out=sys.stdout) -> int:
    weights = _parse_weights(args.weights)
    if not weights:
        out.write("error: at least one --weight TERM:SCORE is required\n")
        return 1

    opts = ScoreOptions(
        weights=weights,
        case_sensitive=args.case_sensitive,
        min_score=args.min_score,
    )

    try:
        if args.file:
            lines = list(iter_lines(args.file))
        else:
            lines = list(_stdin_lines())
    except LogReadError as exc:
        out.write(f"error: {exc}\n")
        return 1

    if args.top > 0:
        results = top_n(lines, opts, args.top)
    else:
        results = list(score_lines(lines, opts))

    for sl in results:
        out.write(format_scored_line(sl, show_terms=not args.hide_terms) + "\n")
    return 0


def main() -> None:  # pragma: no cover
    parser = build_scorer_parser()
    sys.exit(run_scorer(parser.parse_args()))
