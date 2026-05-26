"""log_slicer.py – Extract a numbered slice (window) of lines from a log stream."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Iterator


@dataclass(frozen=True)
class SliceResult:
    """Outcome of a slice operation."""
    lines: list[str]
    start_index: int   # 0-based, inclusive
    end_index: int     # 0-based, exclusive
    total_seen: int

    @property
    def count(self) -> int:
        return len(self.lines)


def slice_lines(
    source: Iterable[str],
    start: int,
    end: int | None = None,
    *,
    step: int = 1,
) -> Iterator[str]:
    """Yield lines whose 0-based index falls within [start, end) stepping by *step*.

    Args:
        source: Any iterable of log lines.
        start:  First line index to include (0-based).
        end:    One past the last line index to include.  ``None`` means read
                to the end of the stream.
        step:   Only yield every *step*-th matched line (default 1 = all).

    Raises:
        ValueError: If *start* is negative, *step* < 1, or *end* <= *start*.
    """
    if start < 0:
        raise ValueError(f"start must be >= 0, got {start}")
    if step < 1:
        raise ValueError(f"step must be >= 1, got {step}")
    if end is not None and end <= start:
        raise ValueError(f"end ({end}) must be greater than start ({start})")

    match_count = 0
    for idx, line in enumerate(source):
        if end is not None and idx >= end:
            break
        if idx < start:
            continue
        if (match_count % step) == 0:
            yield line
        match_count += 1


def compute_slice_result(
    source: Iterable[str],
    start: int,
    end: int | None = None,
    *,
    step: int = 1,
) -> SliceResult:
    """Collect *slice_lines* into a :class:`SliceResult`."""
    lines_list = list(source)
    total = len(lines_list)
    sliced = list(slice_lines(iter(lines_list), start, end, step=step))
    effective_end = end if end is not None else total
    return SliceResult(
        lines=sliced,
        start_index=start,
        end_index=min(effective_end, total),
        total_seen=total,
    )


def format_slice_result(result: SliceResult) -> str:
    """Return a human-readable summary of a :class:`SliceResult`."""
    return (
        f"lines {result.start_index}–{result.end_index - 1} "
        f"({result.count} returned of {result.total_seen} total)"
    )
