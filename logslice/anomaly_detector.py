"""Simple anomaly detection for log streams based on rate deviation."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from statistics import mean, stdev
from typing import Iterable, Iterator, List, Optional, Tuple

from logslice.timestamp_parser import parse_timestamp


@dataclass
class AnomalyResult:
    line: str
    line_number: int
    timestamp: Optional[datetime]
    z_score: float
    bucket_count: int
    mean_count: float
    stddev: float


def _bucket_lines(
    lines: Iterable[str],
    bucket_seconds: int = 60,
) -> Tuple[List[Tuple[datetime, int]], List[Tuple[int, str, Optional[datetime]]]]:
    """Group lines into time buckets; return (bucket_counts, indexed_lines)."""
    buckets: dict[int, int] = {}
    indexed: List[Tuple[int, str, Optional[datetime]]] = []

    for idx, line in enumerate(lines, start=1):
        ts = parse_timestamp(line)
        indexed.append((idx, line, ts))
        if ts is not None:
            key = int(ts.timestamp()) // bucket_seconds
            buckets[key] = buckets.get(key, 0) + 1

    sorted_buckets = sorted(buckets.items())
    return sorted_buckets, indexed


def detect_anomalies(
    lines: Iterable[str],
    bucket_seconds: int = 60,
    z_threshold: float = 2.0,
) -> Iterator[AnomalyResult]:
    """Yield lines whose bucket has an anomalously high log rate.

    Args:
        lines: Iterable of raw log lines.
        bucket_seconds: Width of each time bucket in seconds.
        z_threshold: Minimum z-score to flag a bucket as anomalous.
    """
    sorted_buckets, indexed = _bucket_lines(lines, bucket_seconds)

    if len(sorted_buckets) < 2:
        return

    counts = [c for _, c in sorted_buckets]
    mu = mean(counts)
    sigma = stdev(counts)

    if sigma == 0:
        return

    anomalous_keys: set[int] = set()
    for key, count in sorted_buckets:
        z = (count - mu) / sigma
        if z >= z_threshold:
            anomalous_keys.add(key)

    for line_no, line, ts in indexed:
        if ts is None:
            continue
        key = int(ts.timestamp()) // bucket_seconds
        if key in anomalous_keys:
            count = dict(sorted_buckets)[key]
            z = (count - mu) / sigma
            yield AnomalyResult(
                line=line,
                line_number=line_no,
                timestamp=ts,
                z_score=round(z, 4),
                bucket_count=count,
                mean_count=round(mu, 4),
                stddev=round(sigma, 4),
            )


def format_anomaly(result: AnomalyResult) -> str:
    """Return a human-readable summary line for an anomaly result."""
    ts_str = result.timestamp.isoformat() if result.timestamp else "unknown"
    return (
        f"[ANOMALY] line={result.line_number} ts={ts_str} "
        f"z={result.z_score:.2f} bucket={result.bucket_count} "
        f"mean={result.mean_count:.2f} stddev={result.stddev:.2f}\n"
        f"  {result.line.rstrip()}"
    )
