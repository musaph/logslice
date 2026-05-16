"""merger.py — Merge and interleave multiple log streams in timestamp order.

Provides utilities for combining log lines from several sources (files,
iterators) into a single chronologically-sorted stream.  Lines that carry
no parseable timestamp are emitted immediately after the preceding
timestamped line from the same source, preserving local ordering.
"""

from __future__ import annotations

import heapq
from dataclasses import dataclass, field
from datetime import datetime
from typing import Iterable, Iterator, List, Optional, Tuple

from logslice.timestamp_parser import parse_timestamp


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

@dataclass(order=True)
class _Entry:
    """Heap entry that orders log lines by timestamp then by source index."""

    timestamp: datetime
    source_index: int
    line: str = field(compare=False)


def _iter_with_timestamps(
    lines: Iterable[str],
    source_index: int,
) -> Iterator[Tuple[Optional[datetime], int, str]]:
    """Yield *(timestamp, source_index, line)* tuples for every line.

    When a line has no timestamp the timestamp from the most recent
    timestamped line in the same source is reused so that context lines
    stay close to their anchor.
    """
    last_ts: Optional[datetime] = None
    for line in lines:
        ts = parse_timestamp(line)
        if ts is not None:
            last_ts = ts
        yield (last_ts, source_index, line)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def merge_logs(
    sources: List[Iterable[str]],
) -> Iterator[str]:
    """Merge multiple log line iterables into one timestamp-ordered stream.

    Lines are ordered by their parsed timestamp.  When two lines share the
    same timestamp the source index (position in *sources*) acts as a
    tiebreaker, preserving stable ordering across repeated calls.

    Lines with no detectable timestamp (and no preceding timestamped line
    in their source) are emitted first, before any timestamped content.

    Parameters
    ----------
    sources:
        A list of iterables, each yielding log lines (strings).  Each
        element represents one log source (e.g. a file).

    Yields
    ------
    str
        Log lines in merged timestamp order.
    """
    # Collect lines that have no timestamp anchor at all so they can be
    # flushed before the heap-ordered section.
    pre_heap: List[str] = []
    heap: List[_Entry] = []

    for source_index, source in enumerate(sources):
        for ts, idx, line in _iter_with_timestamps(source, source_index):
            if ts is None:
                pre_heap.append(line)
            else:
                heapq.heappush(heap, _Entry(timestamp=ts, source_index=idx, line=line))

    yield from pre_heap

    while heap:
        entry = heapq.heappop(heap)
        yield entry.line


def merge_log_files(paths: List[str], encoding: str = "utf-8") -> Iterator[str]:
    """Convenience wrapper that opens *paths* and merges their contents.

    Parameters
    ----------
    paths:
        Filesystem paths to plain-text log files.
    encoding:
        Text encoding used when opening each file.

    Yields
    ------
    str
        Merged log lines in timestamp order.
    """
    handles = [open(p, encoding=encoding) for p in paths]  # noqa: WPS515
    try:
        # Read all lines eagerly per file so handles can be closed promptly.
        sources = [list(h) for h in handles]
    finally:
        for h in handles:
            h.close()

    # Strip trailing newlines to match the convention used by iter_lines.
    stripped = [[line.rstrip("\n") for line in src] for src in sources]
    yield from merge_logs(stripped)
