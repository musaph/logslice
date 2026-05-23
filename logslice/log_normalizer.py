"""Normalise log lines to a consistent format (JSON or logfmt)."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Iterable, Iterator, Optional

from logslice.timestamp_parser import parse_timestamp
from logslice.level_filter import detect_level
from logslice.field_extractor import extract_fields

_BARE_MESSAGE_RE = re.compile(r"^\s*(?P<msg>.+)$")


@dataclass
class NormalizeOptions:
    output_format: str = "json"  # "json" or "logfmt"
    timestamp_key: str = "ts"
    level_key: str = "level"
    message_key: str = "msg"
    drop_empty: bool = True
    extra_fields: dict = field(default_factory=dict)


def _to_logfmt(record: dict) -> str:
    parts: list[str] = []
    for k, v in record.items():
        v_str = str(v)
        if " " in v_str or "=" in v_str or '"' in v_str:
            v_str = json.dumps(v_str)
        parts.append(f"{k}={v_str}")
    return " ".join(parts)


def normalize_line(line: str, opts: Optional[NormalizeOptions] = None) -> Optional[str]:
    """Return a normalised representation of *line*, or ``None`` if skipped."""
    if opts is None:
        opts = NormalizeOptions()

    stripped = line.rstrip("\n")
    if opts.drop_empty and not stripped.strip():
        return None

    record: dict = {}

    # Attempt structured extraction first
    extracted = extract_fields(stripped)
    if extracted:
        record.update(extracted)
    else:
        record[opts.message_key] = stripped.strip()

    # Ensure timestamp key present
    if opts.timestamp_key not in record:
        dt = parse_timestamp(stripped)
        if dt is not None:
            record[opts.timestamp_key] = dt.isoformat()

    # Ensure level key present
    if opts.level_key not in record:
        lvl = detect_level(stripped)
        if lvl is not None:
            record[opts.level_key] = lvl

    # Ensure message key present
    if opts.message_key not in record:
        record[opts.message_key] = stripped.strip()

    # Merge caller-supplied extra fields (do not overwrite existing)
    for k, v in opts.extra_fields.items():
        record.setdefault(k, v)

    if opts.output_format == "logfmt":
        return _to_logfmt(record)
    return json.dumps(record, ensure_ascii=False)


def normalize_lines(
    lines: Iterable[str],
    opts: Optional[NormalizeOptions] = None,
) -> Iterator[str]:
    """Yield normalised lines, skipping any that reduce to ``None``."""
    for line in lines:
        result = normalize_line(line, opts)
        if result is not None:
            yield result
