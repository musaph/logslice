"""Deduplication utilities for log lines."""
from __future__ import annotations

import hashlib
from collections import OrderedDict
from typing import Iterable, Iterator, Optional


def _line_key(line: str, ignore_timestamps: bool, timestamp_col_end: int = 0) -> str:
    """Return a stable key for *line*, optionally stripping a leading timestamp."""
    if ignore_timestamps and timestamp_col_end > 0:
        content = line[timestamp_col_end:].strip()
    else:
        content = line.strip()
    return hashlib.md5(content.encode("utf-8", errors="replace")).hexdigest()


def deduplicate(
    lines: Iterable[str],
    *,
    ignore_timestamps: bool = False,
    timestamp_col_end: int = 0,
    max_cache: Optional[int] = None,
) -> Iterator[str]:
    """Yield unique lines, preserving first-occurrence order.

    Args:
        lines: Input log lines.
        ignore_timestamps: When *True*, the leading timestamp portion
            (up to *timestamp_col_end* characters) is excluded from the
            uniqueness key so that identical messages at different times
            are still considered duplicates.
        timestamp_col_end: Character offset where the timestamp ends.
            Ignored when *ignore_timestamps* is *False*.
        max_cache: Maximum number of keys to keep in the seen-set.  When
            the cache is full the oldest entry is evicted (LRU-style).
            *None* means unlimited.
    """
    seen: "OrderedDict[str, None]" = OrderedDict()
    for line in lines:
        key = _line_key(line, ignore_timestamps, timestamp_col_end)
        if key in seen:
            if max_cache is not None:
                # Refresh recency
                seen.move_to_end(key)
            continue
        seen[key] = None
        if max_cache is not None and len(seen) > max_cache:
            seen.popitem(last=False)
        yield line


def count_duplicates(lines: Iterable[str], *, ignore_timestamps: bool = False, timestamp_col_end: int = 0) -> int:
    """Return the number of duplicate lines (total lines minus unique lines)."""
    seen: set[str] = set()
    total = 0
    for line in lines:
        total += 1
        key = _line_key(line, ignore_timestamps, timestamp_col_end)
        seen.add(key)
    return total - len(seen)
