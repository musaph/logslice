"""log_tailer.py — Follow a log file in real time, yielding new lines as they appear."""

from __future__ import annotations

import io
import os
import time
from typing import Callable, Generator, Optional


DEFAULT_POLL_INTERVAL: float = 0.25  # seconds


def _file_size(path: str) -> int:
    """Return the current byte size of *path*, or 0 if it does not exist."""
    try:
        return os.path.getsize(path)
    except OSError:
        return 0


def tail_file(
    path: str,
    *,
    poll_interval: float = DEFAULT_POLL_INTERVAL,
    max_lines: Optional[int] = None,
    predicate: Optional[Callable[[str], bool]] = None,
    follow_rotations: bool = True,
) -> Generator[str, None, None]:
    """Yield new lines appended to *path* as they arrive.

    Parameters
    ----------
    path:
        Path to the log file to watch.
    poll_interval:
        Seconds to sleep between polls when no new data is available.
    max_lines:
        Stop after yielding this many lines.  ``None`` means no limit.
    predicate:
        Optional callable; only lines for which ``predicate(line)`` is truthy
        are yielded.
    follow_rotations:
        If ``True``, detect when the file shrinks (rotation / truncation) and
        seek back to the beginning automatically.
    """
    emitted = 0
    last_size = 0

    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        # Seek to end so we only yield *new* content.
        fh.seek(0, io.SEEK_END)
        last_size = fh.tell()

        while True:
            if max_lines is not None and emitted >= max_lines:
                return

            current_size = _file_size(path)

            if follow_rotations and current_size < last_size:
                # File was rotated or truncated — start from the beginning.
                fh.seek(0)
                last_size = 0

            line = fh.readline()
            if not line:
                # No new data yet; update size reference and wait.
                last_size = current_size
                time.sleep(poll_interval)
                continue

            last_size = fh.tell()
            stripped = line.rstrip("\n")

            if predicate is not None and not predicate(stripped):
                continue

            yield stripped
            emitted += 1


def tail_lines(
    path: str,
    n: int = 10,
) -> list[str]:
    """Return the last *n* lines of *path* without following."""
    if n <= 0:
        return []
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        all_lines = fh.readlines()
    return [ln.rstrip("\n") for ln in all_lines[-n:]]
