"""log_differ.py – Compare two log streams and report added/removed lines."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Iterator, List


@dataclass
class DiffResult:
    """Result of comparing two log streams."""

    added: List[str] = field(default_factory=list)
    removed: List[str] = field(default_factory=list)
    common: List[str] = field(default_factory=list)

    @property
    def total_added(self) -> int:
        return len(self.added)

    @property
    def total_removed(self) -> int:
        return len(self.removed)

    @property
    def total_common(self) -> int:
        return len(self.common)


def diff_logs(
    baseline: Iterable[str],
    current: Iterable[str],
    *,
    strip: bool = True,
) -> DiffResult:
    """Return lines added, removed, and common between *baseline* and *current*.

    Comparison is set-based (order-independent).  Duplicate lines are counted
    only once.
    """
    def _normalise(lines: Iterable[str]) -> set:
        if strip:
            return {ln.rstrip("\n") for ln in lines if ln.strip()}
        return {ln for ln in lines if ln}

    base_set = _normalise(baseline)
    curr_set = _normalise(current)

    return DiffResult(
        added=sorted(curr_set - base_set),
        removed=sorted(base_set - curr_set),
        common=sorted(base_set & curr_set),
    )


def iter_diff_lines(result: DiffResult) -> Iterator[str]:
    """Yield human-readable diff lines prefixed with +/-/space."""
    for line in result.removed:
        yield f"- {line}"
    for line in result.added:
        yield f"+ {line}"
    for line in result.common:
        yield f"  {line}"


def format_diff(result: DiffResult) -> str:
    """Return a formatted diff summary string."""
    lines = [
        f"Added  : {result.total_added}",
        f"Removed: {result.total_removed}",
        f"Common : {result.total_common}",
    ]
    return "\n".join(lines)
