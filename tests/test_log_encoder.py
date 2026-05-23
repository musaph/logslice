"""Tests for logslice.log_encoder."""
import json
from typing import List

import pytest

from logslice.log_encoder import (
    count_decodable,
    decode_line,
    encode_as_json,
    encode_as_logfmt,
    transcode_lines,
)


def _collect(it) -> List[str]:
    return list(it)


# ---------------------------------------------------------------------------
# encode_as_json
# ---------------------------------------------------------------------------

def test_encode_as_json_wraps_message():
    result = encode_as_json("hello world")
    assert json.loads(result) == {"message": "hello world"}


def test_encode_as_json_strips_trailing_newline():
    result = encode_as_json("hello\n")
    assert json.loads(result)["message"] == "hello"


# ---------------------------------------------------------------------------
# encode_as_logfmt
# ---------------------------------------------------------------------------

def test_encode_as_logfmt_simple():
    result = encode_as_logfmt({"level": "info", "msg": "started"})
    assert "level=info" in result
    assert "msg=started" in result


def test_encode_as_logfmt_quotes_values_with_spaces():
    result = encode_as_logfmt({"msg": "hello world"})
    assert 'msg="hello world"' in result


# ---------------------------------------------------------------------------
# decode_line
# ---------------------------------------------------------------------------

def test_decode_line_json():
    line = '{"level": "error", "msg": "oops"}'
    result = decode_line(line)
    assert result == {"level": "error", "msg": "oops"}


def test_decode_line_logfmt():
    line = "level=info msg=started"
    result = decode_line(line)
    assert result["level"] == "info"
    assert result["msg"] == "started"


def test_decode_line_plain_returns_none():
    assert decode_line("plain unstructured log line") is None


def test_decode_line_invalid_json_falls_back_to_logfmt():
    line = "{bad json} level=warn"
    result = decode_line(line)
    assert result is not None
    assert "level" in result


# ---------------------------------------------------------------------------
# transcode_lines
# ---------------------------------------------------------------------------

def test_transcode_to_json():
    lines = ["level=info msg=ok"]
    results = _collect(transcode_lines(lines, target_format="json"))
    assert len(results) == 1
    obj = json.loads(results[0])
    assert obj["level"] == "info"


def test_transcode_to_logfmt():
    lines = ['{"level": "debug", "msg": "trace"}']
    results = _collect(transcode_lines(lines, target_format="logfmt"))
    assert "level=debug" in results[0]


def test_transcode_plain_passthrough():
    lines = ["just a plain line"]
    results = _collect(transcode_lines(lines, target_format="plain"))
    assert results == ["just a plain line"]


def test_transcode_undecodable_passthrough():
    lines = ["no structure here"]
    results = _collect(transcode_lines(lines, target_format="json"))
    assert results == ["no structure here"]


def test_transcode_invalid_format_raises():
    with pytest.raises(ValueError, match="Unsupported"):
        _collect(transcode_lines(["line"], target_format="xml"))


# ---------------------------------------------------------------------------
# count_decodable
# ---------------------------------------------------------------------------

def test_count_decodable_mixed():
    lines = [
        '{"a": "1"}',
        "level=info",
        "plain text",
        "another plain",
    ]
    assert count_decodable(lines) == 2


def test_count_decodable_empty():
    assert count_decodable([]) == 0
