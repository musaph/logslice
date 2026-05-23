"""Bookmark management: save and restore read positions in log files."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from typing import Dict, Optional


@dataclass
class Bookmark:
    path: str
    offset: int
    line_number: int
    label: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Bookmark":
        return cls(**data)


def load_bookmarks(store_path: str) -> Dict[str, Bookmark]:
    """Load all bookmarks from a JSON store file."""
    if not os.path.exists(store_path):
        return {}
    with open(store_path, "r", encoding="utf-8") as fh:
        raw = json.load(fh)
    return {key: Bookmark.from_dict(val) for key, val in raw.items()}


def save_bookmarks(store_path: str, bookmarks: Dict[str, Bookmark]) -> None:
    """Persist bookmarks to a JSON store file."""
    with open(store_path, "w", encoding="utf-8") as fh:
        json.dump({k: v.to_dict() for k, v in bookmarks.items()}, fh, indent=2)


def set_bookmark(
    store_path: str,
    key: str,
    file_path: str,
    offset: int,
    line_number: int,
    label: Optional[str] = None,
) -> Bookmark:
    """Create or update a named bookmark and persist it."""
    bookmarks = load_bookmarks(store_path)
    bm = Bookmark(path=file_path, offset=offset, line_number=line_number, label=label)
    bookmarks[key] = bm
    save_bookmarks(store_path, bookmarks)
    return bm


def get_bookmark(store_path: str, key: str) -> Optional[Bookmark]:
    """Retrieve a bookmark by key, or None if not found."""
    return load_bookmarks(store_path).get(key)


def delete_bookmark(store_path: str, key: str) -> bool:
    """Remove a bookmark by key. Returns True if it existed."""
    bookmarks = load_bookmarks(store_path)
    if key not in bookmarks:
        return False
    del bookmarks[key]
    save_bookmarks(store_path, bookmarks)
    return True


def list_bookmarks(store_path: str) -> list[Bookmark]:
    """Return all bookmarks sorted by key."""
    bms = load_bookmarks(store_path)
    return [bms[k] for k in sorted(bms)]
