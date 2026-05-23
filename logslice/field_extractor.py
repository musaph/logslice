"""Extract named fields from structured log lines (key=value, JSON, logfmt)."""

from __future__ import annotations

import json
import re
from typing import Dict, Iterable, Iterator, Optional

# Matches key=value or key="quoted value"
_KV_RE = re.compile(r'(?P<key>[\w.\-]+)=(?:"(?P<qval>[^"]*)"|(?P<val>\S+))')


def extract_fields(line: str) -> Dict[str, str]:
    """Return a dict of fields extracted from *line*.

    Detection order:
    1. JSON object on a single line.
    2. logfmt / key=value pairs.
    3. Empty dict when no structure is found.
    """
    stripped = line.strip()

    # --- JSON ---
    if stripped.startswith("{"):
        try:
            data = json.loads(stripped)
            if isinstance(data, dict):
                return {str(k): str(v) for k, v in data.items()}
        except json.JSONDecodeError:
            pass

    # --- logfmt / key=value ---
    fields: Dict[str, str] = {}
    for m in _KV_RE.finditer(line):
        key = m.group("key")
        value = m.group("qval") if m.group("qval") is not None else m.group("val")
        fields[key] = value

    return fields


def get_field(line: str, field: str) -> Optional[str]:
    """Return the value of *field* from *line*, or ``None`` if absent."""
    return extract_fields(line).get(field)


def filter_by_field(
    lines: Iterable[str],
    field: str,
    value: str,
    case_sensitive: bool = True,
) -> Iterator[str]:
    """Yield lines where *field* equals *value*."""
    needle = value if case_sensitive else value.lower()
    for line in lines:
        raw = get_field(line, field)
        if raw is None:
            continue
        candidate = raw if case_sensitive else raw.lower()
        if candidate == needle:
            yield line


def extract_field_column(
    lines: Iterable[str],
    field: str,
    default: str = "",
) -> Iterator[str]:
    """Yield the value of *field* for every line (or *default* when missing)."""
    for line in lines:
        yield get_field(line, field) or default
