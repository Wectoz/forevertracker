"""SQLite storage for gathered WoW Forever posts."""

import sqlite3
import threading
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from wowforever.forum import ForumPost
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
CREATE TABLE IF NOT EXISTS updates (
    post_id INTEGER PRIMARY KEY,
    topic_id INTEGER NOT NULL,
    kind TEXT NOT NULL,
    url TEXT NOT NULL,
    posted TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS updates_posted ON updates (posted);
CREATE TABLE IF NOT EXISTS class_changes (
    post_id INTEGER NOT NULL,
    class TEXT NOT NULL,
    html TEXT NOT NULL,
    PRIMARY KEY (post_id, class)
);
"""
_COLUMNS = "id, title, url, summary, kind, version, published, updated, edited_at"


@dataclass(frozen=True)
class StoredPost(Post):
    edited_at: datetime | None


@dataclass(frozen=True)
class ClassUpdate:
    """One forum update as seen from one class; html is None when it has no changes for that class."""

    kind: str
    posted: datetime
    url: str
    html: str | None


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

    def save_update(self, post: ForumPost, kind: str, sections: dict[str, str]) -> None:
        with self._lock, self._conn:
            self._conn.execute(
                "INSERT INTO updates (post_id, topic_id, kind, url, posted) VALUES (?, ?, ?, ?, ?)"
                " ON CONFLICT (post_id) DO UPDATE SET topic_id = excluded.topic_id, kind = excluded.kind,"
                " url = excluded.url, posted = excluded.posted",
                (post.id, post.topic_id, kind, post.url, post.posted.isoformat()),
            )
            self._conn.execute("DELETE FROM class_changes WHERE post_id = ?", (post.id,))
            self._conn.executemany(
                "INSERT INTO class_changes (post_id, class, html) VALUES (?, ?, ?)",
                [(post.id, cls, html) for cls, html in sections.items()],
            )

    def class_updates(self, cls: str) -> list[ClassUpdate]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT u.kind, u.posted, u.url, c.html FROM updates u"
                " LEFT JOIN class_changes c ON c.post_id = u.post_id AND c.class = ?"
                " ORDER BY u.posted DESC, u.post_id DESC",
                (cls,),
            ).fetchall()
        return [ClassUpdate(r["kind"], datetime.fromisoformat(r["posted"]), r["url"], r["html"]) for r in rows]

    def note_topics(self) -> dict[int, str]:
        with self._lock:
            rows = self._conn.execute("SELECT DISTINCT topic_id, kind FROM updates").fetchall()
        return {r["topic_id"]: r["kind"] for r in rows}
