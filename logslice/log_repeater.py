"""Detect and report repeated consecutive log lines."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Iterator


@dataclass
class RepeatGroup:
    """A run of identical (or normalised-identical) consecutive lines."""
    line: str
    count: int
    first_lineno: int  # 1-based


@dataclass
class RepeatResult:
    groups: list[RepeatGroup] = field(default_factory=list)
    total_lines: int = 0
    suppressed_lines: int = 0


def suppression_rate(result: RepeatResult) -> float:
    """Fraction of lines that were suppressed (0.0 – 1.0)."""
    if result.total_lines == 0:
        return 0.0
    return result.suppressed_lines / result.total_lines


def detect_repeats(
    lines: Iterable[str],
    min_repeat: int = 2,
) -> Iterator[RepeatGroup]:
    """Yield RepeatGroup for every run of *min_repeat* or more identical lines."""
    current: str | None = None
    run_count = 0
    run_start = 1

    for lineno, line in enumerate(lines, start=1):
        stripped = line.rstrip("\n")
        if stripped == current:
            run_count += 1
        else:
            if current is not None and run_count >= min_repeat:
                yield RepeatGroup(line=current, count=run_count, first_lineno=run_start)
            current = stripped
            run_count = 1
            run_start = lineno

    if current is not None and run_count >= min_repeat:
        yield RepeatGroup(line=current, count=run_count, first_lineno=run_start)


def collapse_repeats(
    lines: Iterable[str],
    min_repeat: int = 2,
    marker: str = "[repeated {n} times]",
) -> Iterator[str]:
    """Yield lines with consecutive runs collapsed to one line + marker."""
    current: str | None = None
    run_count = 0

    for line in lines:
        stripped = line.rstrip("\n")
        if stripped == current:
            run_count += 1
        else:
            if current is not None:
                yield current
                if run_count >= min_repeat:
                    yield marker.format(n=run_count)
            current = stripped
            run_count = 1

    if current is not None:
        yield current
        if run_count >= min_repeat:
            yield marker.format(n=run_count)


def compute_repeat_result(
    lines: Iterable[str],
    min_repeat: int = 2,
) -> RepeatResult:
    """Collect full RepeatResult statistics for *lines*."""
    all_lines = list(lines)
    groups = list(detect_repeats(iter(all_lines), min_repeat=min_repeat))
    suppressed = sum(g.count - 1 for g in groups)
    return RepeatResult(
        groups=groups,
        total_lines=len(all_lines),
        suppressed_lines=suppressed,
    )


def format_repeat_summary(result: RepeatResult) -> str:
    """Return a human-readable summary string."""
    rate = suppression_rate(result) * 100
    lines = [
        f"total lines   : {result.total_lines}",
        f"repeat groups : {len(result.groups)}",
        f"suppressed    : {result.suppressed_lines} ({rate:.1f}%)",
    ]
    for g in result.groups:
        lines.append(f"  line {g.first_lineno:>6}: {g.count}x  {g.line[:60]!r}")
    return "\n".join(lines)
