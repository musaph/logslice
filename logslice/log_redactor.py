"""log_redactor.py – Redact or mask specific field values in structured log lines."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Generator, Iterable, List, Optional


@dataclass
class RedactOptions:
    fields: List[str] = field(default_factory=list)   # field names to redact (JSON/logfmt)
    patterns: List[str] = field(default_factory=list) # regex patterns whose matches are masked
    mask: str = "***REDACTED***"
    case_sensitive: bool = False


def _redact_json(line: str, opts: RedactOptions) -> str:
    try:
        obj = json.loads(line)
    except (json.JSONDecodeError, ValueError):
        return line
    changed = False
    for key in list(obj.keys()):
        canonical = key if opts.case_sensitive else key.lower()
        targets = opts.fields if opts.case_sensitive else [f.lower() for f in opts.fields]
        if canonical in targets:
            obj[key] = opts.mask
            changed = True
    return json.dumps(obj) if changed else line


def _redact_logfmt(line: str, opts: RedactOptions) -> str:
    targets = set(opts.fields if opts.case_sensitive else [f.lower() for f in opts.fields])

    def _replace_pair(m: re.Match) -> str:  # type: ignore[type-arg]
        key = m.group(1)
        canonical = key if opts.case_sensitive else key.lower()
        if canonical in targets:
            return f"{key}={opts.mask}"
        return m.group(0)

    return re.sub(r'(\w+)=(?:"[^"]*"|\S*)', _replace_pair, line)


def _redact_patterns(line: str, opts: RedactOptions) -> str:
    flags = 0 if opts.case_sensitive else re.IGNORECASE
    for pat in opts.patterns:
        line = re.sub(pat, opts.mask, line, flags=flags)
    return line


def redact_line(line: str, opts: Optional[RedactOptions] = None) -> str:
    """Return *line* with sensitive fields/patterns replaced by the mask."""
    if opts is None:
        return line
    stripped = line.rstrip("\n")
    if stripped.startswith("{"):
        stripped = _redact_json(stripped, opts)
    elif "=" in stripped:
        stripped = _redact_logfmt(stripped, opts)
    if opts.patterns:
        stripped = _redact_patterns(stripped, opts)
    return stripped


def redact_lines(
    lines: Iterable[str], opts: Optional[RedactOptions] = None
) -> Generator[str, None, None]:
    """Yield each line after applying redaction rules."""
    for line in lines:
        yield redact_line(line, opts)


def count_redacted(lines: Iterable[str], opts: Optional[RedactOptions] = None) -> int:
    """Return the number of lines that were altered by redaction."""
    count = 0
    for line in lines:
        if redact_line(line, opts) != line.rstrip("\n"):
            count += 1
    return count
