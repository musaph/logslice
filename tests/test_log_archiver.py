"""Tests for logslice.log_archiver."""

from __future__ import annotations

import gzip
import zipfile
from pathlib import Path

import pytest

from logslice.log_archiver import (
    ArchiveResult,
    archive_to_gzip,
    archive_to_zip,
    format_archive_result,
)


@pytest.fixture()
def log_file(tmp_path: Path) -> Path:
    p = tmp_path / "app.log"
    p.write_text("line one\nline two\nline three\n" * 20)
    return p


@pytest.fixture()
def second_log_file(tmp_path: Path) -> Path:
    p = tmp_path / "error.log"
    p.write_text("ERROR something went wrong\n" * 10)
    return p


# --- ArchiveResult -----------------------------------------------------------

def test_ratio_zero_when_no_original_bytes():
    r = ArchiveResult(source_path="a", archive_path="b", original_bytes=0, compressed_bytes=0)
    assert r.ratio == 0.0


def test_ratio_between_zero_and_one(log_file, tmp_path):
    result = archive_to_gzip(log_file, tmp_path / "app.log.gz")
    assert 0.0 <= result.ratio <= 1.0


# --- archive_to_gzip ---------------------------------------------------------

def test_gzip_creates_file(log_file, tmp_path):
    dest = tmp_path / "app.log.gz"
    archive_to_gzip(log_file, dest)
    assert dest.exists()


def test_gzip_default_dest_adds_gz_suffix(log_file):
    result = archive_to_gzip(log_file)
    assert result.archive_path.endswith(".gz")
    assert Path(result.archive_path).exists()


def test_gzip_content_is_valid(log_file, tmp_path):
    dest = tmp_path / "app.log.gz"
    archive_to_gzip(log_file, dest)
    with gzip.open(dest, "rt") as f:
        content = f.read()
    assert "line one" in content


def test_gzip_result_paths(log_file, tmp_path):
    dest = tmp_path / "app.log.gz"
    result = archive_to_gzip(log_file, dest)
    assert result.source_path == str(log_file)
    assert result.archive_path == str(dest)


def test_gzip_compressed_bytes_smaller(log_file, tmp_path):
    dest = tmp_path / "app.log.gz"
    result = archive_to_gzip(log_file, dest)
    assert result.compressed_bytes < result.original_bytes


# --- archive_to_zip ----------------------------------------------------------

def test_zip_creates_file(log_file, second_log_file, tmp_path):
    dest = tmp_path / "bundle.zip"
    archive_to_zip([log_file, second_log_file], dest)
    assert dest.exists()


def test_zip_returns_one_result_per_source(log_file, second_log_file, tmp_path):
    dest = tmp_path / "bundle.zip"
    results = archive_to_zip([log_file, second_log_file], dest)
    assert len(results) == 2


def test_zip_contains_both_files(log_file, second_log_file, tmp_path):
    dest = tmp_path / "bundle.zip"
    archive_to_zip([log_file, second_log_file], dest)
    with zipfile.ZipFile(dest) as zf:
        names = zf.namelist()
    assert "app.log" in names
    assert "error.log" in names


def test_zip_all_archive_paths_point_to_same_zip(log_file, second_log_file, tmp_path):
    dest = tmp_path / "bundle.zip"
    results = archive_to_zip([log_file, second_log_file], dest)
    assert all(r.archive_path == str(dest) for r in results)


# --- format_archive_result ---------------------------------------------------

def test_format_contains_paths(log_file, tmp_path):
    dest = tmp_path / "app.log.gz"
    result = archive_to_gzip(log_file, dest)
    text = format_archive_result(result)
    assert str(log_file) in text
    assert str(dest) in text


def test_format_contains_saved_percentage(log_file, tmp_path):
    dest = tmp_path / "app.log.gz"
    result = archive_to_gzip(log_file, dest)
    text = format_archive_result(result)
    assert "saved" in text
    assert "%" in text
