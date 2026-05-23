"""Tests for logslice.log_pipeline."""
from __future__ import annotations

from typing import Iterable, Iterator

import pytest

from logslice.log_pipeline import Pipeline, make_pipeline, run_pipeline


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _upper(lines: Iterable[str]) -> Iterator[str]:
    return (l.upper() for l in lines)


def _exclaim(lines: Iterable[str]) -> Iterator[str]:
    return (l.rstrip("\n") + "!" for l in lines)


def _only_a(lines: Iterable[str]) -> Iterator[str]:
    return (l for l in lines if "a" in l.lower())


SOURCE = ["alpha", "beta", "gamma", "delta"]


# ---------------------------------------------------------------------------
# Pipeline class
# ---------------------------------------------------------------------------

def test_empty_pipeline_passes_source_through():
    p = Pipeline()
    assert list(p.run(SOURCE)) == SOURCE


def test_single_step_applied():
    p = Pipeline()
    p.pipe(_upper)
    assert list(p.run(["hello"])) == ["HELLO"]


def test_multiple_steps_applied_in_order():
    p = Pipeline()
    p.pipe(_upper)
    p.pipe(_exclaim)
    result = list(p.run(["hello"]))
    assert result == ["HELLO!"]


def test_pipe_returns_self_for_chaining():
    p = Pipeline()
    returned = p.pipe(_upper)
    assert returned is p


def test_len_reflects_number_of_steps():
    p = Pipeline()
    assert len(p) == 0
    p.pipe(_upper)
    assert len(p) == 1
    p.pipe(_exclaim)
    assert len(p) == 2


def test_filter_step_reduces_lines():
    p = Pipeline()
    p.pipe(_only_a)
    result = list(p.run(SOURCE))
    assert result == ["alpha", "beta", "gamma", "delta"]
    # only lines containing 'a'
    assert all("a" in l for l in result)


def test_run_is_lazy_generator():
    import types
    p = Pipeline()
    p.pipe(_upper)
    gen = p.run(iter(SOURCE))
    assert isinstance(gen, types.GeneratorType)


# ---------------------------------------------------------------------------
# make_pipeline
# ---------------------------------------------------------------------------

def test_make_pipeline_creates_pipeline_with_steps():
    p = make_pipeline(_upper, _exclaim)
    assert len(p) == 2
    assert list(p.run(["hi"])) == ["HI!"]


def test_make_pipeline_no_steps_is_identity():
    p = make_pipeline()
    assert list(p.run(["x", "y"])) == ["x", "y"]


# ---------------------------------------------------------------------------
# run_pipeline
# ---------------------------------------------------------------------------

def test_run_pipeline_returns_list():
    result = run_pipeline(SOURCE, _upper)
    assert isinstance(result, list)


def test_run_pipeline_applies_steps():
    result = run_pipeline(["hello", "world"], _upper, _exclaim)
    assert result == ["HELLO!", "WORLD!"]


def test_run_pipeline_limit_truncates_output():
    result = run_pipeline(SOURCE, _upper, limit=2)
    assert result == ["ALPHA", "BETA"]


def test_run_pipeline_limit_larger_than_output_returns_all():
    result = run_pipeline(SOURCE, _upper, limit=100)
    assert len(result) == len(SOURCE)


def test_run_pipeline_empty_source_returns_empty_list():
    result = run_pipeline([], _upper, _exclaim)
    assert result == []
