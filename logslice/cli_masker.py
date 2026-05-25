"""cli_masker.py – CLI for masking field values in log lines."""
from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from logslice.log_masker import MaskOptions, compute_mask_result
from logslice.reader import LogReadError, iter_lines


def build_masker_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="logslice-mask",
        description="Mask field values in structured log lines.",
    )
    p.add_argument("file", nargs="?", help="Log file (stdin if omitted)")
    p.add_argument(
        "-f",
        "--field",
        dest="fields",
        metavar="FIELD",
        action="append",
        default=[],
        help="Field name to mask (repeatable)",
    )
    p.add_argument(
        "--mask",
        default="***",
        help="Replacement token (default: ***)",
    )
    p.add_argument(
        "--case-sensitive",
        action="store_true",
        default=False,
        help="Match field names case-sensitively",
    )
    p.add_argument(
        "--stats",
        action="store_true",
        default=False,
        help="Print masking statistics to stderr",
    )
    return p


def _stdin_lines():
    for line in sys.stdin:
        yield line


def run_masker(argv: Optional[List[str]] = None) -> int:
    parser = build_masker_parser()
    args = parser.parse_args(argv)

    opts = MaskOptions(
        fields=args.fields,
        mask=args.mask,
        case_sensitive=args.case_sensitive,
    )

    try:
        if args.file:
            raw = list(iter_lines(args.file))
        else:
            raw = list(_stdin_lines())
    except LogReadError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    out_lines, changed = compute_mask_result(raw, opts)

    for line in out_lines:
        print(line)

    if args.stats:
        total = len(out_lines)
        print(
            f"masked: {changed}/{total} lines",
            file=sys.stderr,
        )

    return 0


def main() -> None:  # pragma: no cover
    sys.exit(run_masker())
