"""Utilities for splitting a log stream into fixed-size or fixed-line-count chunks."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Iterator, List


@dataclass
class LogChunk:
    """A contiguous slice of log lines."""

    index: int  # zero-based chunk number
    lines: List[str] = field(default_factory=list)

    @property
    def line_count(self) -> int:
        return len(self.lines)

    @property
    def byte_size(self) -> int:
        return sum(len(line.encode()) for line in self.lines)


def split_by_lines(
    lines: Iterable[str],
    chunk_size: int,
) -> Iterator[LogChunk]:
    """Yield LogChunks each containing at most *chunk_size* lines.

    Args:
        lines: Source log lines (newlines already stripped or not).
        chunk_size: Maximum number of lines per chunk.  Must be >= 1.

    Yields:
        LogChunk instances in order.
    """
    if chunk_size < 1:
        raise ValueError(f"chunk_size must be >= 1, got {chunk_size}")

    current: List[str] = []
    index = 0
    for line in lines:
        current.append(line)
        if len(current) >= chunk_size:
            yield LogChunk(index=index, lines=current)
            index += 1
            current = []
    if current:
        yield LogChunk(index=index, lines=current)


def split_by_bytes(
    lines: Iterable[str],
    max_bytes: int,
) -> Iterator[LogChunk]:
    """Yield LogChunks whose encoded byte size stays below *max_bytes*.

    A single line that exceeds *max_bytes* is placed in its own chunk.

    Args:
        lines: Source log lines.
        max_bytes: Soft byte ceiling per chunk.  Must be >= 1.

    Yields:
        LogChunk instances in order.
    """
    if max_bytes < 1:
        raise ValueError(f"max_bytes must be >= 1, got {max_bytes}")

    current: List[str] = []
    current_bytes = 0
    index = 0
    for line in lines:
        line_bytes = len(line.encode())
        if current and current_bytes + line_bytes > max_bytes:
            yield LogChunk(index=index, lines=current)
            index += 1
            current = []
            current_bytes = 0
        current.append(line)
        current_bytes += line_bytes
    if current:
        yield LogChunk(index=index, lines=current)


def format_chunk_summary(chunk: LogChunk) -> str:
    """Return a human-readable one-line summary for *chunk*."""
    return (
        f"chunk {chunk.index}: {chunk.line_count} lines, "
        f"{chunk.byte_size} bytes"
    )
