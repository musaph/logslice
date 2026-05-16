"""Log statistics: count lines, match rates, and timestamp span."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Iterable, Optional

from logslice.timestamp_parser import parse_timestamp


@dataclass
class LogStats:
    """Summary statistics for a collection of log lines."""

    total_lines: int = 0
    lines_with_timestamp: int = 0
    earliest: Optional[datetime] = None
    latest: Optional[datetime] = None
    keyword_matches: int = 0
    keywords: list[str] = field(default_factory=list)

    @property
    def timestamp_coverage(self) -> float:
        """Fraction of lines that contain a parseable timestamp (0.0–1.0)."""
        if self.total_lines == 0:
            return 0.0
        return self.lines_with_timestamp / self.total_lines

    @property
    def span_seconds(self) -> Optional[float]:
        """Total time span in seconds, or None if fewer than two timestamps."""
        if self.earliest is None or self.latest is None:
            return None
        return (self.latest - self.earliest).total_seconds()


def compute_stats(
    lines: Iterable[str],
    keywords: Optional[list[str]] = None,
) -> LogStats:
    """Compute statistics over *lines*.

    Parameters
    ----------
    lines:
        Iterable of log line strings (newlines already stripped is fine).
    keywords:
        Optional list of keyword strings; matching is case-insensitive.

    Returns
    -------
    LogStats
        Populated statistics object.
    """
    keywords = keywords or []
    stats = LogStats(keywords=list(keywords))

    for line in lines:
        stats.total_lines += 1

        ts = parse_timestamp(line)
        if ts is not None:
            stats.lines_with_timestamp += 1
            if stats.earliest is None or ts < stats.earliest:
                stats.earliest = ts
            if stats.latest is None or ts > stats.latest:
                stats.latest = ts

        lower = line.lower()
        if any(kw.lower() in lower for kw in keywords):
            stats.keyword_matches += 1

    return stats


def format_stats(stats: LogStats) -> str:
    """Return a human-readable summary string for *stats*."""
    lines = [
        f"Total lines      : {stats.total_lines}",
        f"With timestamp   : {stats.lines_with_timestamp} ({stats.timestamp_coverage:.1%})",
        f"Earliest         : {stats.earliest or 'n/a'}",
        f"Latest           : {stats.latest or 'n/a'}",
        f"Span (seconds)   : {stats.span_seconds if stats.span_seconds is not None else 'n/a'}",
    ]
    if stats.keywords:
        lines.append(
            f"Keyword matches  : {stats.keyword_matches} (keywords: {', '.join(stats.keywords)})"
        )
    return "\n".join(lines)
