"""log_linker.py – correlate log lines across files by a shared trace/request ID field."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, Iterator, List, Optional

from logslice.field_extractor import extract_fields


@dataclass
class LinkedGroup:
    """A set of log lines that share the same value for the link field."""

    key: str
    lines: List[str] = field(default_factory=list)
    sources: List[str] = field(default_factory=list)  # filename / label per line

    def line_count(self) -> int:  # noqa: D401
        return len(self.lines)

    def unique_sources(self) -> List[str]:
        return sorted(set(self.sources))


@dataclass
class LinkResult:
    groups: List[LinkedGroup] = field(default_factory=list)
    unmatched: List[str] = field(default_factory=list)

    def total_groups(self) -> int:  # noqa: D401
        return len(self.groups)

    def total_matched(self) -> int:  # noqa: D401
        return sum(g.line_count() for g in self.groups)

    def total_unmatched(self) -> int:  # noqa: D401
        return len(self.unmatched)


def link_logs(
    sources: Iterable[tuple[str, Iterable[str]]],
    link_field: str,
    case_sensitive: bool = False,
) -> LinkResult:
    """Group lines from multiple *sources* by the value of *link_field*.

    Each element of *sources* is a ``(label, lines)`` pair.
    """
    groups: Dict[str, LinkedGroup] = {}
    unmatched: List[str] = []

    norm = (lambda v: v) if case_sensitive else str.lower

    for label, lines in sources:
        for raw in lines:
            line = raw.rstrip("\n")
            fields = extract_fields(line)
            raw_val: Optional[str] = None
            for k, v in fields.items():
                if norm(k) == norm(link_field):
                    raw_val = v
                    break
            if raw_val is None:
                unmatched.append(line)
                continue
            key = norm(raw_val)
            if key not in groups:
                groups[key] = LinkedGroup(key=key)
            groups[key].lines.append(line)
            groups[key].sources.append(label)

    return LinkResult(groups=list(groups.values()), unmatched=unmatched)


def format_link_result(result: LinkResult, show_unmatched: bool = False) -> Iterator[str]:
    """Yield human-readable lines describing each linked group."""
    for group in result.groups:
        srcs = ", ".join(group.unique_sources())
        yield f"[{group.key}] ({group.line_count()} lines from: {srcs})"
        for ln in group.lines:
            yield f"  {ln}"
    if show_unmatched and result.unmatched:
        yield f"--- unmatched ({result.total_unmatched()}) ---"
        for ln in result.unmatched:
            yield f"  {ln}"
