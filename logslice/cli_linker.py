"""cli_linker.py – CLI front-end for log_linker."""
from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from logslice.log_linker import format_link_result, link_logs
from logslice.reader import LogReadError, iter_lines


def build_linker_parser(parent: Optional[argparse._SubParsersAction] = None) -> argparse.ArgumentParser:  # noqa: SLF001
    kwargs = dict(
        prog="logslice-link",
        description="Correlate log lines across files by a shared field value.",
    )
    parser = parent.add_parser("link", **kwargs) if parent else argparse.ArgumentParser(**kwargs)
    parser.add_argument("files", nargs="+", metavar="FILE", help="Log files to link (use '-' for stdin).")
    parser.add_argument("-f", "--field", required=True, metavar="FIELD", help="Field name to link on (e.g. trace_id).")
    parser.add_argument("--case-sensitive", action="store_true", default=False, help="Match field names case-sensitively.")
    parser.add_argument("--show-unmatched", action="store_true", default=False, help="Also print lines with no matching field.")
    parser.add_argument("--min-group-size", type=int, default=1, metavar="N", help="Only show groups with at least N lines.")
    return parser


def _stdin_lines():
    for line in sys.stdin:
        yield line


def run_linker(args: argparse.Namespace, out=sys.stdout, err=sys.stderr) -> int:
    sources = []
    for path in args.files:
        if path == "-":
            sources.append(("-", list(_stdin_lines())))
        else:
            try:
                sources.append((path, list(iter_lines(path))))
            except LogReadError as exc:
                err.write(f"error: {exc}\n")
                return 1

    result = link_logs(sources, link_field=args.field, case_sensitive=args.case_sensitive)

    min_size: int = args.min_group_size
    filtered = [g for g in result.groups if g.line_count() >= min_size]
    from logslice.log_linker import LinkResult  # local import to avoid circular
    filtered_result = LinkResult(groups=filtered, unmatched=result.unmatched)

    for line in format_link_result(filtered_result, show_unmatched=args.show_unmatched):
        out.write(line + "\n")

    return 0


def main(argv: Optional[List[str]] = None) -> None:
    parser = build_linker_parser()
    args = parser.parse_args(argv)
    sys.exit(run_linker(args))


if __name__ == "__main__":  # pragma: no cover
    main()
