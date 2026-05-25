"""Tests for logslice.log_transformer."""
from __future__ import annotations

import json
from typing import List

import pytest

from logslice.log_transformer import (
    TransformOptions,
    TransformResult,
    compute_transform_result,
    transform_line,
    transform_lines,
)


def _collect(lines) -> List[str]:
    return list(transform_lines(lines, TransformOptions()))


# ---------------------------------------------------------------------------
# transform_line — JSON
# ---------------------------------------------------------------------------

def test_json_field_transformed():
    line = json.dumps({"level": "info", "msg": "hello"})
    opts = TransformOptions(transforms={"level": str.upper})
    result = transform_line(line, opts)
    assert json.loads(result)["level"] == "INFO"


def test_json_untargeted_field_unchanged():
    line = json.dumps({"level": "info", "msg": "hello"})
    opts = TransformOptions(transforms={"level": str.upper})
    result = transform_line(line, opts)
    assert json.loads(result)["msg"] == "hello"


def test_json_field_removed():
    line = json.dumps({"level": "info", "msg": "hello", "secret": "abc"})
    opts = TransformOptions(remove_fields=["secret"])
    result = transform_line(line, opts)
    assert "secret" not in json.loads(result)


def test_json_field_added():
    line = json.dumps({"msg": "hi"})
    opts = TransformOptions(add_fields={"env": "prod"})
    result = transform_line(line, opts)
    assert json.loads(result)["env"] == "prod"


def test_json_add_overwrites_existing():
    line = json.dumps({"env": "dev"})
    opts = TransformOptions(add_fields={"env": "prod"})
    result = transform_line(line, opts)
    assert json.loads(result)["env"] == "prod"


# ---------------------------------------------------------------------------
# transform_line — logfmt
# ---------------------------------------------------------------------------

def test_logfmt_field_transformed():
    line = "level=info msg=hello"
    opts = TransformOptions(transforms={"level": str.upper})
    result = transform_line(line, opts)
    assert "level=INFO" in result


def test_logfmt_field_removed():
    line = "level=info secret=abc"
    opts = TransformOptions(remove_fields=["secret"])
    result = transform_line(line, opts)
    assert "secret" not in result


def test_logfmt_field_added():
    line = "msg=hello"
    opts = TransformOptions(add_fields={"env": "prod"})
    result = transform_line(line, opts)
    assert "env=prod" in result


# ---------------------------------------------------------------------------
# Unstructured lines
# ---------------------------------------------------------------------------

def test_unstructured_passed_through_by_default():
    line = "plain log line without fields"
    opts = TransformOptions()
    assert transform_line(line, opts) == line


def test_unstructured_dropped_when_passthrough_false():
    line = "plain log line"
    opts = TransformOptions(passthrough_unstructured=False)
    assert transform_line(line, opts) is None


# ---------------------------------------------------------------------------
# transform_lines generator
# ---------------------------------------------------------------------------

def test_transform_lines_skips_none_results():
    lines = ["plain line", json.dumps({"msg": "ok"})]
    opts = TransformOptions(passthrough_unstructured=False)
    results = list(transform_lines(lines, opts))
    assert len(results) == 1
    assert json.loads(results[0])["msg"] == "ok"


def test_transform_lines_empty_input_yields_nothing():
    assert list(transform_lines([], TransformOptions())) == []


# ---------------------------------------------------------------------------
# compute_transform_result
# ---------------------------------------------------------------------------

def test_compute_result_counts_total():
    lines = ["plain", json.dumps({"k": "v"})]
    stats = compute_transform_result(lines, TransformOptions())
    assert stats.total == 2


def test_compute_result_counts_transformed():
    lines = [json.dumps({"level": "info"})]
    opts = TransformOptions(transforms={"level": str.upper})
    stats = compute_transform_result(lines, opts)
    assert stats.transformed == 1


def test_compute_result_counts_skipped():
    lines = ["plain", json.dumps({"k": "v"})]
    opts = TransformOptions(passthrough_unstructured=False)
    stats = compute_transform_result(lines, opts)
    assert stats.skipped == 1
