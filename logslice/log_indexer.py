"""Build a simple positional index mapping keywords to line numbers."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, Iterator, List


@dataclass
class IndexEntry:
    keyword: str
    line_numbers: List[int] = field(default_factory=list)

    @property
    def hit_count(self) -> int:
        return len(self.line_numbers)


@dataclass
class LogIndex:
    entries: Dict[str, IndexEntry] = field(default_factory=dict)

    @property
    def total_keywords(self) -> int:
        return len(self.entries)

    @property
    def total_hits(self) -> int:
        return sum(e.hit_count for e in self.entries.values())


def build_index(
    lines: Iterable[str],
    keywords: Iterable[str],
    *,
    case_sensitive: bool = False,
) -> LogIndex:
    """Scan *lines* and record which line numbers contain each keyword."""
    kw_list = list(keywords)
    if not case_sensitive:
        normalised = [kw.lower() for kw in kw_list]
    else:
        normalised = kw_list

    index = LogIndex()
    for kw in kw_list:
        index.entries[kw] = IndexEntry(keyword=kw)

    for lineno, line in enumerate(lines, start=1):
        haystack = line if case_sensitive else line.lower()
        for kw, norm in zip(kw_list, normalised):
            if norm in haystack:
                index.entries[kw].line_numbers.append(lineno)

    return index


def lookup(
    index: LogIndex,
    keyword: str,
    *,
    case_sensitive: bool = False,
) -> List[int]:
    """Return line numbers for *keyword*, honouring case sensitivity."""
    if not case_sensitive:
        for kw, entry in index.entries.items():
            if kw.lower() == keyword.lower():
                return list(entry.line_numbers)
        return []
    entry = index.entries.get(keyword)
    return list(entry.line_numbers) if entry else []


def iter_index_report(index: LogIndex) -> Iterator[str]:
    """Yield human-readable summary lines for each indexed keyword."""
    for kw, entry in sorted(index.entries.items()):
        hits = entry.hit_count
        lines_preview = ", ".join(str(n) for n in entry.line_numbers[:5])
        if entry.hit_count > 5:
            lines_preview += ", ..."
        yield f"{kw!r}: {hits} hit(s) [{lines_preview}]"
