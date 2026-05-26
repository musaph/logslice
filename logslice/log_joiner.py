"""log_joiner.py – Merge lines from multiple log streams by a shared field value."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, Iterator, List, Optional, Sequence

from logslice.field_extractor import extract_fields


@dataclass
class JoinedLine:
    key: str
    sources: Dict[str, str]  # source_name -> original line

    @property
    def source_count(self) -> int:
        return len(self.sources)


@dataclass
class JoinResult:
    joined: List[JoinedLine] = field(default_factory=list)
    unmatched: Dict[str, List[str]] = field(default_factory=dict)  # source_name -> lines


def total_joined(result: JoinResult) -> int:
    """Number of keys that appear in more than one source."""
    return sum(1 for j in result.joined if j.source_count > 1)


def total_unmatched(result: JoinResult) -> int:
    """Total lines that did not find a counterpart in any other source."""
    return sum(len(lines) for lines in result.unmatched.values())


def join_logs(
    sources: Dict[str, Iterable[str]],
    join_field: str,
    *,
    case_sensitive: bool = True,
) -> JoinResult:
    """Join log streams by *join_field*.

    Lines whose field value appears in at least one other source end up in
    ``JoinResult.joined``; lines with no counterpart go to
    ``JoinResult.unmatched``.
    """
    # bucket lines by (source_name, normalised key)
    buckets: Dict[str, Dict[str, str]] = {}  # key -> {source: line}
    unmatched: Dict[str, List[str]] = {name: [] for name in sources}

    for source_name, lines in sources.items():
        for line in lines:
            raw = line.rstrip("\n")
            fields = extract_fields(raw)
            value: Optional[str] = fields.get(join_field)
            if value is None:
                unmatched[source_name].append(raw)
                continue
            key = value if case_sensitive else value.lower()
            if key not in buckets:
                buckets[key] = {}
            buckets[key][source_name] = raw

    joined: List[JoinedLine] = []
    leftover: Dict[str, List[str]] = {name: list(lines) for name, lines in unmatched.items()}

    for key, source_map in buckets.items():
        if len(source_map) < 2:
            # only one source has this key — treat as unmatched
            for src, ln in source_map.items():
                leftover.setdefault(src, []).append(ln)
        else:
            joined.append(JoinedLine(key=key, sources=source_map))

    return JoinResult(joined=joined, unmatched=leftover)


def format_join_result(result: JoinResult, *, separator: str = "  |  ") -> Iterator[str]:
    """Yield human-readable lines describing each joined group."""
    for jl in result.joined:
        parts = [f"[{src}] {line}" for src, line in sorted(jl.sources.items())]
        yield f"key={jl.key!r}: " + separator.join(parts)
