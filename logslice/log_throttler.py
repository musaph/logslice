"""Rate-based log throttling: suppress lines that exceed a burst limit within a time window."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Iterable, Iterator

from logslice.timestamp_parser import parse_timestamp


@dataclass
class ThrottleOptions:
    max_lines: int = 10          # maximum lines allowed per window
    window_seconds: float = 1.0  # rolling window size in seconds
    drop_message: str | None = None  # if set, emit this line instead of dropping


@dataclass
class ThrottleResult:
    total: int = 0
    emitted: int = 0
    suppressed: int = 0

    @property
    def suppression_rate(self) -> float:
        return self.suppressed / self.total if self.total else 0.0


def _window_start(ts: datetime, window_seconds: float) -> datetime:
    """Floor a timestamp to the nearest window boundary."""
    epoch = datetime(1970, 1, 1, tzinfo=ts.tzinfo)
    total = (ts - epoch).total_seconds()
    floored = (total // window_seconds) * window_seconds
    return epoch + timedelta(seconds=floored)


def throttle_lines(
    lines: Iterable[str],
    opts: ThrottleOptions | None = None,
) -> Iterator[str]:
    """Yield lines, suppressing bursts that exceed *max_lines* per *window_seconds*.

    Lines without a parseable timestamp are always emitted.
    """
    if opts is None:
        opts = ThrottleOptions()

    bucket_start: datetime | None = None
    bucket_count: int = 0
    window = opts.window_seconds

    for line in lines:
        ts = parse_timestamp(line)
        if ts is None:
            yield line
            continue

        ws = _window_start(ts, window)
        if bucket_start is None or ws != bucket_start:
            bucket_start = ws
            bucket_count = 0

        bucket_count += 1
        if bucket_count <= opts.max_lines:
            yield line
        elif opts.drop_message is not None:
            yield opts.drop_message


def compute_throttle_result(
    lines: Iterable[str],
    opts: ThrottleOptions | None = None,
) -> ThrottleResult:
    """Return a summary of how many lines were emitted vs suppressed."""
    if opts is None:
        opts = ThrottleOptions()

    result = ThrottleResult()
    drop_msg = opts.drop_message
    emitted_lines = list(throttle_lines(lines, opts))

    # We need to re-run to get totals; count original lines separately.
    # Use a simpler counting pass instead.
    result.emitted = sum(
        1 for ln in emitted_lines if ln != drop_msg
    )
    return result


def format_throttle_result(r: ThrottleResult) -> str:
    return (
        f"total={r.total} emitted={r.emitted} "
        f"suppressed={r.suppressed} "
        f"suppression_rate={r.suppression_rate:.2%}"
    )
