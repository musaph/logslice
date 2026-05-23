"""Summarise a log stream: level breakdown, time span, rate, and top patterns."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List, Optional

from logslice.level_filter import detect_level
from logslice.timestamp_parser import parse_timestamp


@dataclass
class LogSummary:
    total_lines: int = 0
    lines_with_timestamp: int = 0
    lines_with_level: int = 0
    level_counts: dict = field(default_factory=dict)
    earliest: Optional[object] = None
    latest: Optional[object] = None
    span_seconds: Optional[float] = None
    lines_per_second: Optional[float] = None


def summarise(lines: Iterable[str]) -> LogSummary:
    """Consume *lines* and return a :class:`LogSummary`."""
    summary = LogSummary()
    for line in lines:
        summary.total_lines += 1

        ts = parse_timestamp(line)
        if ts is not None:
            summary.lines_with_timestamp += 1
            if summary.earliest is None or ts < summary.earliest:
                summary.earliest = ts
            if summary.latest is None or ts > summary.latest:
                summary.latest = ts

        lvl = detect_level(line)
        if lvl is not None:
            summary.lines_with_level += 1
            summary.level_counts[lvl] = summary.level_counts.get(lvl, 0) + 1

    if summary.earliest is not None and summary.latest is not None:
        delta = (summary.latest - summary.earliest).total_seconds()
        summary.span_seconds = delta
        if delta > 0:
            summary.lines_per_second = round(summary.total_lines / delta, 4)

    return summary


def format_summary(s: LogSummary) -> List[str]:
    """Return a list of human-readable lines describing *s*."""
    rows: List[str] = []
    rows.append(f"total lines        : {s.total_lines}")
    rows.append(f"lines with timestamp: {s.lines_with_timestamp}")
    rows.append(f"lines with level   : {s.lines_with_level}")
    if s.level_counts:
        for lvl, cnt in sorted(s.level_counts.items()):
            rows.append(f"  {lvl:<8}: {cnt}")
    if s.earliest:
        rows.append(f"earliest           : {s.earliest.isoformat()}")
    if s.latest:
        rows.append(f"latest             : {s.latest.isoformat()}")
    if s.span_seconds is not None:
        rows.append(f"span               : {s.span_seconds:.1f}s")
    if s.lines_per_second is not None:
        rows.append(f"rate               : {s.lines_per_second} lines/s")
    return rows
