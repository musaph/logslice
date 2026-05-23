"""Tests for logslice.log_bookmark."""
import json
import os
import pytest

from logslice.log_bookmark import (
    Bookmark,
    delete_bookmark,
    get_bookmark,
    list_bookmarks,
    load_bookmarks,
    save_bookmarks,
    set_bookmark,
)


@pytest.fixture()
def store(tmp_path):
    return str(tmp_path / "bookmarks.json")


def test_load_bookmarks_missing_file_returns_empty(store):
    assert load_bookmarks(store) == {}


def test_save_and_load_round_trip(store):
    bm = Bookmark(path="/var/log/app.log", offset=1024, line_number=42, label="after-deploy")
    save_bookmarks(store, {"deploy": bm})
    loaded = load_bookmarks(store)
    assert "deploy" in loaded
    assert loaded["deploy"].offset == 1024
    assert loaded["deploy"].label == "after-deploy"


def test_set_bookmark_creates_entry(store):
    bm = set_bookmark(store, "k1", "/tmp/a.log", offset=0, line_number=1)
    assert bm.path == "/tmp/a.log"
    assert get_bookmark(store, "k1") is not None


def test_set_bookmark_overwrites_existing(store):
    set_bookmark(store, "k1", "/tmp/a.log", offset=0, line_number=1)
    set_bookmark(store, "k1", "/tmp/a.log", offset=500, line_number=20)
    bm = get_bookmark(store, "k1")
    assert bm.offset == 500
    assert bm.line_number == 20


def test_get_bookmark_missing_key_returns_none(store):
    assert get_bookmark(store, "nope") is None


def test_delete_bookmark_returns_true_when_found(store):
    set_bookmark(store, "k1", "/tmp/a.log", offset=0, line_number=1)
    result = delete_bookmark(store, "k1")
    assert result is True
    assert get_bookmark(store, "k1") is None


def test_delete_bookmark_returns_false_when_missing(store):
    assert delete_bookmark(store, "ghost") is False


def test_list_bookmarks_sorted_by_key(store):
    set_bookmark(store, "z", "/z.log", offset=0, line_number=1)
    set_bookmark(store, "a", "/a.log", offset=0, line_number=1)
    set_bookmark(store, "m", "/m.log", offset=0, line_number=1)
    keys = [bm.path for bm in list_bookmarks(store)]
    assert keys == ["/a.log", "/m.log", "/z.log"]


def test_list_bookmarks_empty_store(store):
    assert list_bookmarks(store) == []


def test_bookmark_label_optional(store):
    bm = set_bookmark(store, "k", "/f.log", offset=10, line_number=2)
    assert bm.label is None
    loaded = get_bookmark(store, "k")
    assert loaded.label is None


def test_bookmark_to_dict_contains_all_fields():
    bm = Bookmark(path="/x.log", offset=8, line_number=3, label="test")
    d = bm.to_dict()
    assert d == {"path": "/x.log", "offset": 8, "line_number": 3, "label": "test"}


def test_bookmark_from_dict_round_trip():
    original = Bookmark(path="/y.log", offset=16, line_number=5, label=None)
    restored = Bookmark.from_dict(original.to_dict())
    assert restored == original


def test_store_file_is_valid_json(store):
    set_bookmark(store, "x", "/x.log", offset=0, line_number=1, label="lbl")
    with open(store) as fh:
        data = json.load(fh)
    assert "x" in data
