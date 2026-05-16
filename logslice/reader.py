"""Log file reader with support for plain files and gzip-compressed logs."""

import gzip
import io
import os
from typing import Generator, Union


class LogReadError(Exception):
    """Raised when a log file cannot be opened or read."""


def _open_file(path: str) -> io.TextIOWrapper:
    """Open a log file, transparently decompressing gzip if needed."""
    if not os.path.exists(path):
        raise LogReadError(f"File not found: {path}")
    if not os.path.isfile(path):
        raise LogReadError(f"Not a regular file: {path}")
    try:
        if path.endswith(".gz"):
            return gzip.open(path, "rt", encoding="utf-8", errors="replace")
        return open(path, "r", encoding="utf-8", errors="replace")
    except OSError as exc:
        raise LogReadError(f"Cannot open file '{path}': {exc}") from exc


def iter_lines(
    source: Union[str, io.IOBase],
    strip_newlines: bool = True,
) -> Generator[str, None, None]:
    """Yield lines from a file path or an already-opened file-like object.

    Args:
        source: A filesystem path (str) or a readable file-like object.
        strip_newlines: If True, trailing newline characters are stripped.

    Yields:
        Individual log lines.
    """
    if isinstance(source, str):
        fh = _open_file(source)
        try:
            yield from _yield_lines(fh, strip_newlines)
        finally:
            fh.close()
    else:
        yield from _yield_lines(source, strip_newlines)


def _yield_lines(
    fh: io.IOBase, strip_newlines: bool
) -> Generator[str, None, None]:
    for line in fh:
        yield line.rstrip("\n\r") if strip_newlines else line


def read_lines(source: Union[str, io.IOBase], strip_newlines: bool = True) -> list:
    """Read all lines from *source* into a list.

    Convenience wrapper around :func:`iter_lines`.
    """
    return list(iter_lines(source, strip_newlines=strip_newlines))


def count_lines(source: Union[str, io.IOBase]) -> int:
    """Return the total number of lines in *source*.

    This is more memory-efficient than ``len(read_lines(source))`` because it
    does not store all lines in memory at once.

    Args:
        source: A filesystem path (str) or a readable file-like object.

    Returns:
        The number of lines found in the source.
    """
    total = 0
    for _ in iter_lines(source, strip_newlines=False):
        total += 1
    return total
