"""Sort log lines by their parsed timestamps."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Iterator, List, Optional

from logslice.timestamp_parser import parse_timestamp


@dataclass
class SortedChunk:
    """A sorted block of log lines."""

    lines: List[str]
    sorted_count: int  # lines that had a parseable timestamp
    unsorted_count: int  # lines placed at end (no timestamp)


def _sort_key(line: str):
    """Return (has_ts, datetime_or_None) for stable ordering."""
    ts = parse_timestamp(line)
    if ts is None:
        return (1, None)  # push lines without timestamps to the end
    return (0, ts)


def sort_lines(
    lines: Iterable[str],
    reverse: bool = False,
    stable: bool = True,
) -> Iterator[str]:
    """Sort *lines* by timestamp, preserving insertion order for ties.

    Lines that carry no recognisable timestamp are placed at the end of
    the output (or at the beginning when *reverse* is True).

    Args:
        lines:   Iterable of raw log lines.
        reverse: Emit newest-first when True.
        stable:  Use a stable sort so equal timestamps keep their
                 original relative order (default True).

    Yields:
        Sorted log lines.
    """
    collected = list(lines)
    collected.sort(key=_sort_key, reverse=reverse)
    yield from collected


def sort_into_chunk(
    lines: Iterable[str],
    reverse: bool = False,
) -> SortedChunk:
    """Sort *lines* and return a :class:`SortedChunk` with metadata."""
    collected = list(lines)
    collected.sort(key=_sort_key, reverse=reverse)

    sorted_count = sum(1 for ln in collected if parse_timestamp(ln) is not None)
    unsorted_count = len(collected) - sorted_count

    return SortedChunk(
        lines=collected,
        sorted_count=sorted_count,
        unsorted_count=unsorted_count,
    )


def format_sort_summary(chunk: SortedChunk) -> str:
    """Return a human-readable summary of a sort operation."""
    total = len(chunk.lines)
    return (
        f"Sorted {total} lines: "
        f"{chunk.sorted_count} with timestamp, "
        f"{chunk.unsorted_count} without."
    )
