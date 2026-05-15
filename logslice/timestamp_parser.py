"""Timestamp detection and parsing for structured and unstructured log lines."""

import re
from datetime import datetime
from typing import Optional

# Common log timestamp patterns ordered by specificity
TIMESTAMP_PATTERNS = [
    # ISO 8601: 2024-01-15T13:45:00.123Z or 2024-01-15T13:45:00+00:00
    (r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?', '%Y-%m-%dT%H:%M:%S'),
    # Common syslog: Jan 15 13:45:00
    (r'[A-Z][a-z]{2}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}', '%b %d %H:%M:%S'),
    # Date + time: 2024-01-15 13:45:00
    (r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}(?:\.\d+)?', '%Y-%m-%d %H:%M:%S'),
    # Date + time with slash: 15/Jan/2024:13:45:00
    (r'\d{2}/[A-Z][a-z]{2}/\d{4}:\d{2}:\d{2}:\d{2}', '%d/%b/%Y:%H:%M:%S'),
    # Epoch seconds (10 digits)
    (r'\b\d{10}\b', None),
    # Epoch milliseconds (13 digits)
    (r'\b\d{13}\b', None),
]

_COMPILED = [(re.compile(pattern), fmt) for pattern, fmt in TIMESTAMP_PATTERNS]


def parse_timestamp(line: str) -> Optional[datetime]:
    """Extract and parse the first timestamp found in a log line.

    Returns a naive datetime (UTC assumed) or None if no timestamp is found.
    """
    for regex, fmt in _COMPILED:
        match = regex.search(line)
        if not match:
            continue
        raw = match.group(0)
        try:
            if fmt is None:
                # Epoch handling
                epoch = int(raw)
                if len(raw) == 13:
                    epoch //= 1000
                return datetime.utcfromtimestamp(epoch)
            # Strip fractional seconds and timezone for strptime simplicity
            clean = re.sub(r'\.\d+', '', raw)
            clean = re.sub(r'(?:Z|[+-]\d{2}:?\d{2})$', '', clean)
            return datetime.strptime(clean, fmt)
        except (ValueError, OSError):
            continue
    return None
