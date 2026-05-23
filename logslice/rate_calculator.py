"""Log event rate calculation utilities.

Computes per-second, per-minute, and per-hour event rates from
a sequence of timestamped log lines.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Optional

from logslice.timestamp_parser import parse_timestamp


@dataclass
class RateStats:
    """Aggregated rate information for a log stream."""

    total_events: int
    span_seconds: float
    events_per_second: float
    events_per_minute: float
    events_per_hour: float
    earliest: Optional[datetime]
    latest: Optional[datetime]


def _collect_timestamps(lines: Iterable[str]) -> list[datetime]:
    """Return sorted list of parsed timestamps from *lines*."""
    timestamps: list[datetime] = []
    for line in lines:
        ts = parse_timestamp(line)
        if ts is not None:
            timestamps.append(ts)
    timestamps.sort()
    return timestamps


def compute_rate(lines: Iterable[str]) -> RateStats:
    """Compute event-rate statistics for *lines*.

    Lines without a detectable timestamp are counted but excluded from
    the time-span calculation.
    """
    all_lines = list(lines)
    total = len(all_lines)
    timestamps = _collect_timestamps(all_lines)

    if len(timestamps) < 2:
        return RateStats(
            total_events=total,
            span_seconds=0.0,
            events_per_second=0.0,
            events_per_minute=0.0,
            events_per_hour=0.0,
            earliest=timestamps[0] if timestamps else None,
            latest=timestamps[-1] if timestamps else None,
        )

    earliest = timestamps[0]
    latest = timestamps[-1]
    span = (latest - earliest).total_seconds()

    if span <= 0:
        eps = 0.0
    else:
        eps = total / span

    return RateStats(
        total_events=total,
        span_seconds=span,
        events_per_second=eps,
        events_per_minute=eps * 60,
        events_per_hour=eps * 3600,
        earliest=earliest,
        latest=latest,
    )


def format_rate(stats: RateStats) -> str:
    """Return a human-readable summary of *stats*."""
    lines = [
        f"Total events : {stats.total_events}",
        f"Span         : {stats.span_seconds:.1f}s",
        f"Rate/sec     : {stats.events_per_second:.3f}",
        f"Rate/min     : {stats.events_per_minute:.3f}",
        f"Rate/hour    : {stats.events_per_hour:.3f}",
    ]
    if stats.earliest:
        lines.append(f"Earliest     : {stats.earliest.isoformat()}")  
    if stats.latest:
        lines.append(f"Latest       : {stats.latest.isoformat()}")
    return "\n".join(lines)
