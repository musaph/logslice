"""Bucket log lines by time interval and produce ASCII histograms."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Iterable, Iterator, List, Optional, Tuple

from logslice.timestamp_parser import parse_timestamp

_INTERVALS: Dict[str, int] = {
    "second": 1,
    "minute": 60,
    "hour": 3600,
    "day": 86400,
}


@dataclass
class HistogramBucket:
    label: str
    count: int
    start: datetime


@dataclass
class Histogram:
    buckets: List[HistogramBucket] = field(default_factory=list)
    interval_seconds: int = 60
    total_lines: int = 0
    unparsed_lines: int = 0


def _floor_dt(dt: datetime, seconds: int) -> datetime:
    epoch = datetime(1970, 1, 1)
    total = int((dt - epoch).total_seconds())
    floored = (total // seconds) * seconds
    return epoch + timedelta(seconds=floored)


def _label(dt: datetime, seconds: int) -> str:
    if seconds < 60:
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    if seconds < 3600:
        return dt.strftime("%Y-%m-%d %H:%M")
    if seconds < 86400:
        return dt.strftime("%Y-%m-%d %H:00")
    return dt.strftime("%Y-%m-%d")


def compute_histogram(
    lines: Iterable[str],
    interval: str = "minute",
) -> Histogram:
    seconds = _INTERVALS.get(interval, 60)
    hist = Histogram(interval_seconds=seconds)
    buckets: Dict[datetime, int] = {}

    for line in lines:
        hist.total_lines += 1
        ts = parse_timestamp(line)
        if ts is None:
            hist.unparsed_lines += 1
            continue
        key = _floor_dt(ts, seconds)
        buckets[key] = buckets.get(key, 0) + 1

    for start in sorted(buckets):
        hist.buckets.append(
            HistogramBucket(
                label=_label(start, seconds),
                count=buckets[start],
                start=start,
            )
        )
    return hist


def format_histogram(hist: Histogram, bar_width: int = 40) -> Iterator[str]:
    if not hist.buckets:
        yield "(no timestamped lines found)"
        return
    max_count = max(b.count for b in hist.buckets)
    for bucket in hist.buckets:
        filled = int(bar_width * bucket.count / max_count) if max_count else 0
        bar = "#" * filled
        yield f"{bucket.label} | {bar:<{bar_width}} {bucket.count}"
    yield ""
    yield f"total lines : {hist.total_lines}"
    yield f"unparsed    : {hist.unparsed_lines}"
