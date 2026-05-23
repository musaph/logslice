"""CLI for managing log read-position bookmarks."""
from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from logslice.log_bookmark import (
    delete_bookmark,
    get_bookmark,
    list_bookmarks,
    set_bookmark,
)

_DEFAULT_STORE = ".logslice_bookmarks.json"


def build_bookmark_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="logslice-bookmark",
        description="Save and restore read positions in log files.",
    )
    parser.add_argument(
        "--store",
        default=_DEFAULT_STORE,
        help="Path to bookmark store file (default: %(default)s)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # set
    p_set = sub.add_parser("set", help="Create or update a bookmark")
    p_set.add_argument("key", help="Bookmark name")
    p_set.add_argument("file", help="Log file path")
    p_set.add_argument("offset", type=int, help="Byte offset")
    p_set.add_argument("line_number", type=int, help="Line number (1-based)")
    p_set.add_argument("--label", default=None, help="Optional description")

    # get
    p_get = sub.add_parser("get", help="Print a bookmark by key")
    p_get.add_argument("key", help="Bookmark name")

    # delete
    p_del = sub.add_parser("delete", help="Remove a bookmark")
    p_del.add_argument("key", help="Bookmark name")

    # list
    sub.add_parser("list", help="List all bookmarks")

    return parser


def run_bookmark(argv: Optional[List[str]] = None, out=sys.stdout, err=sys.stderr) -> int:
    parser = build_bookmark_parser()
    args = parser.parse_args(argv)

    if args.command == "set":
        bm = set_bookmark(
            args.store, args.key, args.file, args.offset, args.line_number, args.label
        )
        label_part = f" ({bm.label})" if bm.label else ""
        out.write(f"Bookmark '{args.key}' set: {bm.path}:{bm.offset}{label_part}\n")
        return 0

    if args.command == "get":
        bm = get_bookmark(args.store, args.key)
        if bm is None:
            err.write(f"No bookmark found for key '{args.key}'\n")
            return 1
        label_part = f" label={bm.label}" if bm.label else ""
        out.write(f"{args.key}: {bm.path} offset={bm.offset} line={bm.line_number}{label_part}\n")
        return 0

    if args.command == "delete":
        found = delete_bookmark(args.store, args.key)
        if not found:
            err.write(f"No bookmark found for key '{args.key}'\n")
            return 1
        out.write(f"Bookmark '{args.key}' deleted.\n")
        return 0

    if args.command == "list":
        bms = list_bookmarks(args.store)
        if not bms:
            out.write("No bookmarks stored.\n")
        for bm in bms:
            label_part = f" ({bm.label})" if bm.label else ""
            out.write(f"{bm.path}  offset={bm.offset}  line={bm.line_number}{label_part}\n")
        return 0

    return 1  # unreachable


def main() -> None:  # pragma: no cover
    sys.exit(run_bookmark())
