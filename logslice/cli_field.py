"""CLI helpers for field-extraction sub-commands."""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from logslice.field_extractor import extract_field_column, filter_by_field
from logslice.reader import LogReadError, iter_lines


def build_field_parser(parent: Optional[argparse.ArgumentParser] = None) -> argparse.ArgumentParser:
    """Return an :class:`ArgumentParser` for the ``field`` sub-commands."""
    parser = parent or argparse.ArgumentParser(
        prog="logslice-field",
        description="Extract or filter structured log fields.",
    )
    sub = parser.add_subparsers(dest="field_cmd", required=True)

    # --- filter sub-command ---
    flt = sub.add_parser("filter", help="Keep lines where FIELD equals VALUE.")
    flt.add_argument("file", help="Log file path (use '-' for stdin).")
    flt.add_argument("field", help="Field name to match.")
    flt.add_argument("value", help="Expected field value.")
    flt.add_argument(
        "--ignore-case", "-i", action="store_true", help="Case-insensitive comparison."
    )

    # --- column sub-command ---
    col = sub.add_parser("column", help="Print a single field value per line.")
    col.add_argument("file", help="Log file path (use '-' for stdin).")
    col.add_argument("field", help="Field name to extract.")
    col.add_argument(
        "--default", default="", metavar="STR", help="Value when field is absent."
    )

    return parser


def run_field(args: argparse.Namespace, out=sys.stdout, err=sys.stderr) -> int:
    """Execute the chosen field sub-command; return an exit code."""
    try:
        source = None if args.file == "-" else args.file
        lines: List[str] = list(iter_lines(source) if source else _stdin_lines())
    except LogReadError as exc:
        err.write(f"error: {exc}\n")
        return 1

    if args.field_cmd == "filter":
        results = filter_by_field(
            lines,
            args.field,
            args.value,
            case_sensitive=not args.ignore_case,
        )
        for line in results:
            out.write(line + "\n")

    elif args.field_cmd == "column":
        for value in extract_field_column(lines, args.field, default=args.default):
            out.write(value + "\n")

    return 0


def _stdin_lines() -> List[str]:
    return [line.rstrip("\n") for line in sys.stdin]


def main(argv=None) -> None:  # pragma: no cover
    parser = build_field_parser()
    args = parser.parse_args(argv)
    sys.exit(run_field(args))
