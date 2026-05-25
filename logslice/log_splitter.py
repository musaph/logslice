"""Split a log stream into named segments based on delimiter patterns."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable, Iterator, List, Optional


@dataclass
class LogSegment:
    """A named segment of log lines."""

    name: str
    lines: List[str] = field(default_factory=list)

    @property
    def line_count(self) -> int:
        return len(self.lines)


def split_by_delimiter(
    lines: Iterable[str],
    pattern: str,
    *,
    case_sensitive: bool = False,
    include_delimiter: bool = True,
    default_name: str = "segment",
) -> Iterator[LogSegment]:
    """Yield LogSegments split wherever *pattern* matches a line.

    The matching line is treated as the start of a new segment.  Lines
    before the first match are grouped into a segment named ``<default_name>-0``.
    """
    flags = 0 if case_sensitive else re.IGNORECASE
    rx = re.compile(pattern, flags)

    segment_index = 0
    current: LogSegment = LogSegment(name=f"{default_name}-{segment_index}")

    for line in lines:
        if rx.search(line):
            if current.lines:
                yield current
                segment_index += 1
            current = LogSegment(name=f"{default_name}-{segment_index}")
            if include_delimiter:
                current.lines.append(line)
        else:
            current.lines.append(line)

    if current.lines:
        yield current


def split_by_line_count(
    lines: Iterable[str],
    chunk_size: int,
    *,
    default_name: str = "segment",
) -> Iterator[LogSegment]:
    """Yield LogSegments each containing at most *chunk_size* lines."""
    if chunk_size < 1:
        raise ValueError("chunk_size must be >= 1")

    index = 0
    current: List[str] = []
    for line in lines:
        current.append(line)
        if len(current) >= chunk_size:
            yield LogSegment(name=f"{default_name}-{index}", lines=current)
            index += 1
            current = []

    if current:
        yield LogSegment(name=f"{default_name}-{index}", lines=current)


def format_segment_summary(segments: List[LogSegment]) -> str:
    """Return a human-readable summary table for a list of segments."""
    if not segments:
        return "No segments."
    lines = [f"{'Segment':<30}  {'Lines':>6}"]
    lines.append("-" * 40)
    for seg in segments:
        lines.append(f"{seg.name:<30}  {seg.line_count:>6}")
    lines.append("-" * 40)
    lines.append(f"{'Total':<30}  {sum(s.line_count for s in segments):>6}")
    return "\n".join(lines)
