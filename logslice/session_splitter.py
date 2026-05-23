"""Split a log stream into sessions based on inactivity gaps."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Iterable, Iterator, List

from logslice.timestamp_parser import parse_timestamp

_DEFAULT_GAP_SECONDS = 300  # 5 minutes


@dataclass
class Session:
    """A contiguous group of log lines separated by no large time gap."""

    lines: List[str] = field(default_factory=list)
    start: datetime | None = None
    end: datetime | None = None

    @property
    def line_count(self) -> int:
        return len(self.lines)

    @property
    def span_seconds(self) -> float | None:
        if self.start is None or self.end is None:
            return None
        return (self.end - self.start).total_seconds()


def split_into_sessions(
    lines: Iterable[str],
    gap_seconds: float = _DEFAULT_GAP_SECONDS,
) -> Iterator[Session]:
    """Yield Session objects split wherever consecutive timestamps differ by
    more than *gap_seconds*.

    Lines without a parseable timestamp are appended to the current session
    without affecting the gap calculation.
    """
    gap = timedelta(seconds=gap_seconds)
    current: Session = Session()
    last_ts: datetime | None = None

    for line in lines:
        ts = parse_timestamp(line)

        if ts is not None and last_ts is not None:
            if ts - last_ts > gap:
                if current.lines:
                    yield current
                current = Session()

        current.lines.append(line)

        if ts is not None:
            if current.start is None:
                current.start = ts
            current.end = ts
            last_ts = ts

    if current.lines:
        yield current


def format_session_summary(sessions: List[Session]) -> str:
    """Return a human-readable summary table for a list of sessions."""
    if not sessions:
        return "No sessions found."

    rows = []
    for idx, s in enumerate(sessions, start=1):
        start_str = s.start.strftime("%Y-%m-%d %H:%M:%S") if s.start else "unknown"
        end_str = s.end.strftime("%Y-%m-%d %H:%M:%S") if s.end else "unknown"
        span = f"{s.span_seconds:.1f}s" if s.span_seconds is not None else "n/a"
        rows.append(
            f"Session {idx:>3}: {start_str} -> {end_str}  "
            f"lines={s.line_count:<6} span={span}"
        )
    return "\n".join(rows)
