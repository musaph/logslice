"""log_transformer.py — Apply field-level transformations to structured log lines."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Callable, Dict, Iterable, Iterator, List, Optional

from logslice.field_extractor import extract_fields


@dataclass
class TransformOptions:
    """Controls which fields are transformed and how."""
    transforms: Dict[str, Callable[[str], str]] = field(default_factory=dict)
    add_fields: Dict[str, str] = field(default_factory=dict)
    remove_fields: List[str] = field(default_factory=list)
    passthrough_unstructured: bool = True


@dataclass
class TransformResult:
    total: int = 0
    transformed: int = 0
    skipped: int = 0


def _to_logfmt(fields: Dict[str, str]) -> str:
    parts = []
    for k, v in fields.items():
        if " " in v or "=" in v or '"' in v:
            v = '"' + v.replace('"', '\\"') + '"'
        parts.append(f"{k}={v}")
    return " ".join(parts)


def transform_line(line: str, opts: TransformOptions) -> Optional[str]:
    """Apply transformations to a single log line.

    Returns the transformed line, or the original if it is unstructured and
    *passthrough_unstructured* is True, or None to drop the line.
    """
    stripped = line.rstrip("\n")
    fields = extract_fields(stripped)

    if not fields:
        return stripped if opts.passthrough_unstructured else None

    # Apply field-level transforms
    for key, fn in opts.transforms.items():
        if key in fields:
            fields[key] = fn(fields[key])

    # Remove fields
    for key in opts.remove_fields:
        fields.pop(key, None)

    # Add / overwrite fields
    for key, value in opts.add_fields.items():
        fields[key] = value

    # Re-serialise in the same format as the original
    if stripped.lstrip().startswith("{"):
        return json.dumps(fields)
    return _to_logfmt(fields)


def transform_lines(
    lines: Iterable[str],
    opts: TransformOptions,
) -> Iterator[str]:
    """Yield transformed lines, skipping lines that transform to None."""
    for line in lines:
        result = transform_line(line, opts)
        if result is not None:
            yield result


def compute_transform_result(
    lines: Iterable[str],
    opts: TransformOptions,
) -> TransformResult:
    """Run transformations and return aggregate statistics."""
    stats = TransformResult()
    for line in lines:
        stats.total += 1
        result = transform_line(line, opts)
        if result is None:
            stats.skipped += 1
        elif result != line.rstrip("\n"):
            stats.transformed += 1
    return stats
