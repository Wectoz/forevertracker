"""SQLite storage for gathered WoW Forever posts."""

import sqlite3
import threading
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from wowforever.posts import Post

_SCHEMA = """
CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    url TEXT NOT NULL,
    summary TEXT NOT NULL,
    kind TEXT NOT NULL,
    version TEXT,
    published TEXT NOT NULL,
    updated TEXT NOT NULL,
    edited_at TEXT
);
CREATE INDEX IF NOT EXISTS posts_published ON posts (published);
"""
_COLUMNS = "id, title, url, summary, kind, version, published, updated, edited_at"


@dataclass(frozen=True)
class StoredPost(Post):
    edited_at: datetime | None


def _row_to_post(row: sqlite3.Row) -> StoredPost:
    return StoredPost(
        id=row["id"],
        title=row["title"],
        url=row["url"],
        summary=row["summary"],
        kind=row["kind"],
        version=row["version"],
        published=datetime.fromisoformat(row["published"]),
        updated=datetime.fromisoformat(row["updated"]),
        edited_at=datetime.fromisoformat(row["edited_at"]) if row["edited_at"] else None,
    )


class Store:
    def __init__(self, path: str | Path):
        self._conn = sqlite3.connect(str(path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._lock = threading.Lock()
        with self._lock, self._conn:
            self._conn.executescript(_SCHEMA)

    def upsert(self, posts: Iterable[Post]) -> tuple[int, int]:
        added = edited = 0
        with self._lock, self._conn:
            for post in posts:
                row = self._conn.execute(
                    "SELECT title, summary FROM posts WHERE id = ?", (post.id,)
                ).fetchone()
                if row is None:
                    self._conn.execute(
                        f"INSERT INTO posts ({_COLUMNS}) VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL)",
                        (post.id, post.title, post.url, post.summary, post.kind, post.version,
                         post.published.isoformat(), post.updated.isoformat()),
                    )
                    added += 1
                elif (row["title"], row["summary"]) != (post.title, post.summary):
                    self._conn.execute(
                        "UPDATE posts SET title = ?, summary = ?, kind = ?, version = ?, updated = ?,"
                        " edited_at = ? WHERE id = ?",
                        (post.title, post.summary, post.kind, post.version,
                         post.updated.isoformat(), post.updated.isoformat(), post.id),
                    )
                    edited += 1
        return added, edited

    def _select(self, where: str = "", params: tuple = (), order: str = "published DESC",
                limit: int = -1, offset: int = 0) -> list[StoredPost]:
        sql = f"SELECT {_COLUMNS} FROM posts {where} ORDER BY {order}, id LIMIT ? OFFSET ?"
        with self._lock:
            rows = self._conn.execute(sql, (*params, limit, offset)).fetchall()
        return [_row_to_post(r) for r in rows]

    def list_posts(self, kind: str | None = None, limit: int = 20, offset: int = 0) -> list[StoredPost]:
        if kind is None:
            return self._select(limit=limit, offset=offset)
        return self._select("WHERE kind = ?", (kind,), limit=limit, offset=offset)

    def count_posts(self, kind: str | None = None) -> int:
        sql, params = "SELECT COUNT(*) FROM posts", ()
        if kind is not None:
            sql, params = sql + " WHERE kind = ?", (kind,)
        with self._lock:
            return self._conn.execute(sql, params).fetchone()[0]

    def list_patches(self) -> list[tuple[str, date, int]]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT version, MIN(published) AS first, COUNT(*) AS n FROM posts"
                " WHERE kind = 'patch' AND version IS NOT NULL"
                " GROUP BY version ORDER BY first DESC"
            ).fetchall()
        return [(r["version"], datetime.fromisoformat(r["first"]).date(), r["n"]) for r in rows]

    def patch_posts(self, version: str) -> list[StoredPost]:
        return self._select("WHERE kind = 'patch' AND version = ?", (version,), order="published ASC")

    def unversioned_patch_posts(self) -> list[StoredPost]:
        return self._select("WHERE kind = 'patch' AND version IS NULL")
