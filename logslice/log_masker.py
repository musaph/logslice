"""log_masker.py – Mask specific field values in structured and unstructured log lines."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Iterable, Iterator, List, Optional

_LOGFMT_RE = re.compile(r'(\w+)=("[^"]*"|\S*)')

_MASK_TOKEN = "***"


@dataclass(frozen=True)
class MaskOptions:
    fields: List[str] = field(default_factory=list)  # field names to mask
    mask: str = _MASK_TOKEN
    case_sensitive: bool = False


@dataclass(frozen=True)
class MaskResult:
    original: str
    masked: str
    changed: bool


def _normalise_fields(fields: List[str], case_sensitive: bool) -> List[str]:
    if case_sensitive:
        return list(fields)
    return [f.lower() for f in fields]


def _mask_json(line: str, opts: MaskOptions) -> str:
    try:
        obj = json.loads(line)
    except (json.JSONDecodeError, ValueError):
        return line
    if not isinstance(obj, dict):
        return line
    targets = _normalise_fields(opts.fields, opts.case_sensitive)
    changed = False
    for key in list(obj.keys()):
        compare = key if opts.case_sensitive else key.lower()
        if compare in targets:
            obj[key] = opts.mask
            changed = True
    return json.dumps(obj) if changed else line


def _mask_logfmt(line: str, opts: MaskOptions) -> str:
    targets = _normalise_fields(opts.fields, opts.case_sensitive)

    def _replace(m: re.Match) -> str:  # type: ignore[type-arg]
        key = m.group(1)
        compare = key if opts.case_sensitive else key.lower()
        if compare in targets:
            return f"{key}={opts.mask}"
        return m.group(0)

    result = _LOGFMT_RE.sub(_replace, line)
    return result


def mask_line(line: str, opts: MaskOptions) -> MaskResult:
    """Mask field values in a single log line."""
    stripped = line.rstrip("\n")
    if not opts.fields:
        return MaskResult(original=stripped, masked=stripped, changed=False)

    # Try JSON first
    stripped_ws = stripped.lstrip()
    if stripped_ws.startswith("{"):
        masked = _mask_json(stripped, opts)
    else:
        masked = _mask_logfmt(stripped, opts)

    return MaskResult(original=stripped, masked=masked, changed=masked != stripped)


def mask_lines(
    lines: Iterable[str], opts: MaskOptions
) -> Iterator[MaskResult]:
    """Yield MaskResult for each line."""
    for line in lines:
        yield mask_line(line, opts)


def compute_mask_result(
    lines: Iterable[str], opts: MaskOptions
) -> tuple[List[str], int]:
    """Return (masked_lines, changed_count)."""
    out: List[str] = []
    changed = 0
    for r in mask_lines(lines, opts):
        out.append(r.masked)
        if r.changed:
            changed += 1
    return out, changed
