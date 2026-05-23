"""Log line encoding and decoding utilities.

Supports converting log lines between plain text, JSON, and logfmt formats.
"""
from __future__ import annotations

import json
from typing import Dict, Iterable, Iterator, Optional


def _parse_logfmt(line: str) -> Dict[str, str]:
    """Parse a logfmt-style line into a dict."""
    result: Dict[str, str] = {}
    for token in line.split():
        if "=" in token:
            key, _, value = token.partition("=")
            result[key] = value.strip('"')
        else:
            result[token] = "true"
    return result


def encode_as_json(line: str) -> str:
    """Wrap a plain log line as a JSON object with a 'message' key."""
    return json.dumps({"message": line.rstrip("\n")})


def encode_as_logfmt(fields: Dict[str, str]) -> str:
    """Encode a dict of fields as a logfmt string."""
    parts = []
    for key, value in fields.items():
        if " " in value or "=" in value or '"' in value:
            value = '"' + value.replace('"', '\\"') + '"'
        parts.append(f"{key}={value}")
    return " ".join(parts)


def decode_line(line: str) -> Optional[Dict[str, str]]:
    """Attempt to decode a log line as JSON or logfmt.

    Returns a dict of fields, or None if the line is unstructured.
    """
    stripped = line.strip()
    if stripped.startswith("{"):
        try:
            obj = json.loads(stripped)
            if isinstance(obj, dict):
                return {str(k): str(v) for k, v in obj.items()}
        except json.JSONDecodeError:
            pass
    if "=" in stripped:
        return _parse_logfmt(stripped)
    return None


def transcode_lines(
    lines: Iterable[str],
    target_format: str = "json",
) -> Iterator[str]:
    """Re-encode each log line into *target_format*.

    Supported target formats: ``'json'``, ``'logfmt'``, ``'plain'``.

    Lines that cannot be decoded are passed through unchanged.
    """
    if target_format not in {"json", "logfmt", "plain"}:
        raise ValueError(f"Unsupported target format: {target_format!r}")

    for line in lines:
        fields = decode_line(line)
        if fields is None:
            yield line.rstrip("\n")
            continue
        if target_format == "json":
            yield json.dumps(fields)
        elif target_format == "logfmt":
            yield encode_as_logfmt(fields)
        else:
            yield line.rstrip("\n")


def count_decodable(lines: Iterable[str]) -> int:
    """Return the number of lines that can be decoded as structured data."""
    return sum(1 for line in lines if decode_line(line) is not None)
