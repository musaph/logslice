"""Line counting utilities with optional grouping by level or time bucket."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Iterable, Iterator

from logslice.level_filter import detect_level
from logslice.timestamp_parser import parse_timestamp


@dataclass
class CountResult:
    total: int = 0
    by_level: Counter = field(default_factory=Counter)
    by_minute: Counter = field(default_factory=Counter)


def count_lines(lines: Iterable[str]) -> int:
    """Return the total number of lines in *lines*."""
    return sum(1 for _ in lines)


def count_by_level(lines: Iterable[str]) -> Counter:
    """Return a Counter mapping log level -> line count.

    Lines with no detectable level are counted under the key ``'UNKNOWN'``.
    """
    counts: Counter = Counter()
    for line in lines:
        level = detect_level(line) or "UNKNOWN"
        counts[level] += 1
    return counts


def count_by_minute(lines: Iterable[str]) -> Counter:
    """Return a Counter mapping 'YYYY-MM-DD HH:MM' bucket -> line count.

    Lines whose timestamp cannot be parsed are silently skipped.
    """
    counts: Counter = Counter()
    for line in lines:
        ts = parse_timestamp(line)
        if ts is not None:
            bucket = ts.strftime("%Y-%m-%d %H:%M")
            counts[bucket] += 1
    return counts


def compute_count_result(lines: Iterable[str]) -> CountResult:
    """Compute total, per-level, and per-minute counts in a single pass."""
    result = CountResult()
    for line in lines:
        result.total += 1
        level = detect_level(line) or "UNKNOWN"
        result.by_level[level] += 1
        ts = parse_timestamp(line)
        if ts is not None:
            bucket = ts.strftime("%Y-%m-%d %H:%M")
            result.by_minute[bucket] += 1
    return result


def format_count_result(result: CountResult) -> Iterator[str]:
    """Yield human-readable summary lines for a :class:`CountResult`."""
    yield f"Total lines : {result.total}"
    if result.by_level:
        yield "By level:"
        for lvl, cnt in sorted(result.by_level.items()):
            yield f"  {lvl:<10} {cnt}"
    if result.by_minute:
        yield "By minute (first 10):"
        for bucket, cnt in sorted(result.by_minute.items())[:10]:
            yield f"  {bucket}  {cnt}"
