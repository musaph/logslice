"""log_archiver.py — Compress and archive log files into gzip or zip bundles."""

from __future__ import annotations

import gzip
import shutil
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List


@dataclass(frozen=True)
class ArchiveResult:
    source_path: str
    archive_path: str
    original_bytes: int
    compressed_bytes: int

    @property
    def ratio(self) -> float:
        """Compression ratio (0.0–1.0); 0.0 means no data."""
        if self.original_bytes == 0:
            return 0.0
        return 1.0 - self.compressed_bytes / self.original_bytes


def archive_to_gzip(source: str | Path, dest: str | Path | None = None) -> ArchiveResult:
    """Compress *source* to a .gz file and return an ArchiveResult.

    If *dest* is None the archive is placed alongside *source* with a .gz suffix.
    """
    src = Path(source)
    dst = Path(dest) if dest is not None else src.with_suffix(src.suffix + ".gz")

    original_bytes = src.stat().st_size
    with src.open("rb") as f_in, gzip.open(dst, "wb") as f_out:
        shutil.copyfileobj(f_in, f_out)

    compressed_bytes = dst.stat().st_size
    return ArchiveResult(
        source_path=str(src),
        archive_path=str(dst),
        original_bytes=original_bytes,
        compressed_bytes=compressed_bytes,
    )


def archive_to_zip(
    sources: Iterable[str | Path],
    dest: str | Path,
    *,
    compression: int = zipfile.ZIP_DEFLATED,
) -> List[ArchiveResult]:
    """Pack one or more log files into a single zip archive.

    Returns one ArchiveResult per source file.
    """
    dst = Path(dest)
    results: List[ArchiveResult] = []

    with zipfile.ZipFile(dst, "w", compression=compression) as zf:
        for source in sources:
            src = Path(source)
            original_bytes = src.stat().st_size
            zf.write(src, arcname=src.name)
            info = zf.getinfo(src.name)
            results.append(
                ArchiveResult(
                    source_path=str(src),
                    archive_path=str(dst),
                    original_bytes=original_bytes,
                    compressed_bytes=info.compress_size,
                )
            )

    return results


def format_archive_result(result: ArchiveResult) -> str:
    """Return a human-readable summary line for an ArchiveResult."""
    ratio_pct = result.ratio * 100
    return (
        f"{result.source_path} -> {result.archive_path} "
        f"({result.original_bytes} B -> {result.compressed_bytes} B, "
        f"{ratio_pct:.1f}% saved)"
    )
