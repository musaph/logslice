"""Tests for logslice.cli_bookmark."""
import io
import pytest

from logslice.cli_bookmark import run_bookmark


@pytest.fixture()
def store(tmp_path):
    return str(tmp_path / "bm.json")


def _run(argv, store):
    out = io.StringIO()
    err = io.StringIO()
    code = run_bookmark(["--store", store] + argv, out=out, err=err)
    return code, out.getvalue(), err.getvalue()


def test_set_returns_zero(store):
    code, out, _ = _run(["set", "k1", "/tmp/app.log", "0", "1"], store)
    assert code == 0
    assert "k1" in out


def test_set_with_label_shows_label(store):
    code, out, _ = _run(["set", "k1", "/tmp/app.log", "100", "5", "--label", "post-deploy"], store)
    assert code == 0
    assert "post-deploy" in out


def test_get_existing_bookmark(store):
    _run(["set", "k1", "/tmp/app.log", "256", "10"], store)
    code, out, _ = _run(["get", "k1"], store)
    assert code == 0
    assert "256" in out
    assert "10" in out


def test_get_missing_bookmark_returns_one(store):
    code, _, err = _run(["get", "missing"], store)
    assert code == 1
    assert "missing" in err


def test_delete_existing_returns_zero(store):
    _run(["set", "k1", "/tmp/app.log", "0", "1"], store)
    code, out, _ = _run(["delete", "k1"], store)
    assert code == 0
    assert "deleted" in out


def test_delete_missing_returns_one(store):
    code, _, err = _run(["delete", "ghost"], store)
    assert code == 1
    assert "ghost" in err


def test_list_empty_store(store):
    code, out, _ = _run(["list"], store)
    assert code == 0
    assert "No bookmarks" in out


def test_list_shows_all_entries(store):
    _run(["set", "a", "/a.log", "0", "1"], store)
    _run(["set", "b", "/b.log", "500", "20"], store)
    code, out, _ = _run(["list"], store)
    assert code == 0
    assert "/a.log" in out
    assert "/b.log" in out


def test_set_overwrites_and_get_reflects_update(store):
    _run(["set", "k", "/f.log", "0", "1"], store)
    _run(["set", "k", "/f.log", "999", "50"], store)
    _, out, _ = _run(["get", "k"], store)
    assert "999" in out
    assert "50" in out


def test_delete_then_get_returns_one(store):
    _run(["set", "k", "/f.log", "0", "1"], store)
    _run(["delete", "k"], store)
    code, _, _ = _run(["get", "k"], store)
    assert code == 1
