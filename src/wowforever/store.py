"""SQLite storage for gathered WoW Forever posts."""

import json
import sqlite3
import threading
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path

from wowforever.classnotes import text_lines
from wowforever.forum import FORUM_URL, ForumPost
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
    edited_at TEXT,
    thumbnail TEXT
);
CREATE INDEX IF NOT EXISTS posts_published ON posts (published);
CREATE TABLE IF NOT EXISTS updates (
    post_id INTEGER PRIMARY KEY,
    topic_id INTEGER NOT NULL,
    kind TEXT NOT NULL,
    url TEXT NOT NULL,
    posted TEXT NOT NULL,
    title TEXT NOT NULL DEFAULT '',
    summary TEXT NOT NULL DEFAULT '',
    html TEXT NOT NULL DEFAULT '',
    edited_at TEXT
);
CREATE INDEX IF NOT EXISTS updates_posted ON updates (posted);
CREATE TABLE IF NOT EXISTS update_edits (
    post_id INTEGER NOT NULL,
    seen TEXT NOT NULL,
    added TEXT NOT NULL,
    removed TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS update_edits_post ON update_edits (post_id);
CREATE TABLE IF NOT EXISTS announced (
    url TEXT PRIMARY KEY
);
CREATE TABLE IF NOT EXISTS class_changes (
    post_id INTEGER NOT NULL,
    class TEXT NOT NULL,
    html TEXT NOT NULL,
    PRIMARY KEY (post_id, class)
);
"""
_COLUMNS = "id, title, url, summary, kind, version, published, updated, edited_at, thumbnail"
# Columns added after the tables first shipped; older databases get them on open.
_ADDED_COLUMNS = {
    "posts": {"thumbnail": "TEXT"},
    "updates": {"title": "TEXT NOT NULL DEFAULT ''", "summary": "TEXT NOT NULL DEFAULT ''",
                "html": "TEXT NOT NULL DEFAULT ''", "edited_at": "TEXT"},
}
# The feed: news-site posts plus every forum notes post (shown as patch posts without a version),
# each forum post with the comma-separated classes it has changes for.
_FEED_COLUMNS = _COLUMNS + ", classes"
_FEED = (
    f"(SELECT {_COLUMNS}, NULL AS classes FROM posts UNION ALL"
    " SELECT post_id, title, url, summary, 'patch', NULL, posted, posted, edited_at, NULL,"
    " (SELECT group_concat(class) FROM class_changes c WHERE c.post_id = updates.post_id) FROM updates)"
)


@dataclass(frozen=True)
class StoredPost(Post):
    edited_at: datetime | None
    classes: tuple[str, ...] = ()  # classes a forum notes post has changes for

    @property
    def on_forums(self) -> bool:
        return self.url.startswith(FORUM_URL)


@dataclass(frozen=True)
class ClassUpdate:
    """One forum update as seen from one class; html is None when it has no changes for that class."""

    post_id: int
    kind: str
    posted: datetime
    url: str
    html: str | None


@dataclass(frozen=True)
class Edit:
    """Lines Blizzard added to and removed from a notes post, as first seen by a gather."""

    seen: datetime
    added: list[str]
    removed: list[str]


@dataclass(frozen=True)
class Notes:
    """One forum notes post in full."""

    id: int
    kind: str
    title: str
    summary: str
    url: str
    posted: datetime
    html: str
    edits: list[Edit]


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
        thumbnail=row["thumbnail"],
        classes=tuple(sorted(row["classes"].split(","))) if row["classes"] else (),
    )


def _row_to_update(row: sqlite3.Row) -> ClassUpdate:
    return ClassUpdate(row["post_id"], row["kind"], datetime.fromisoformat(row["posted"]), row["url"], row["html"])


class Store:
    def __init__(self, path: str | Path):
        self._conn = sqlite3.connect(str(path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._lock = threading.Lock()
        with self._lock, self._conn:
            self._conn.executescript(_SCHEMA)
            for table, columns in _ADDED_COLUMNS.items():
                have = {row["name"] for row in self._conn.execute(f"PRAGMA table_info({table})")}
                for column, decl in columns.items():
                    if column not in have:
                        self._conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {decl}")

    def upsert(self, posts: Iterable[Post]) -> tuple[int, int]:
        added = edited = 0
        with self._lock, self._conn:
            for post in posts:
                row = self._conn.execute(
                    "SELECT title, summary, thumbnail FROM posts WHERE id = ?", (post.id,)
                ).fetchone()
                if row is None:
                    self._conn.execute(
                        f"INSERT INTO posts ({_COLUMNS}) VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL, ?)",
                        (post.id, post.title, post.url, post.summary, post.kind, post.version,
                         post.published.isoformat(), post.updated.isoformat(), post.thumbnail),
                    )
                    added += 1
                    continue
                if row["thumbnail"] != post.thumbnail:
                    # A new header image is not an edit worth flagging to readers.
                    self._conn.execute("UPDATE posts SET thumbnail = ? WHERE id = ?", (post.thumbnail, post.id))
                if (row["title"], row["summary"]) != (post.title, post.summary):
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
        sql = f"SELECT {_FEED_COLUMNS} FROM {_FEED} {where} ORDER BY {order}, id LIMIT ? OFFSET ?"
        with self._lock:
            rows = self._conn.execute(sql, (*params, limit, offset)).fetchall()
        return [_row_to_post(r) for r in rows]

    def list_posts(self, kind: str | None = None, limit: int = 20, offset: int = 0) -> list[StoredPost]:
        if kind is None:
            return self._select(limit=limit, offset=offset)
        return self._select("WHERE kind = ?", (kind,), limit=limit, offset=offset)

    def count_posts(self, kind: str | None = None) -> int:
        sql, params = f"SELECT COUNT(*) FROM {_FEED}", ()
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

    def save_update(self, post: ForumPost, kind: str, sections: dict[str, str] | None,
                    title: str = "", summary: str = "", html: str = "", now: datetime | None = None) -> None:
        """Store a forum notes post. `sections` replaces its class sections; None leaves them as they are.
        `html` is the whole post; when its text changed since the last gather, the change is kept as an Edit."""
        now = now or datetime.now(UTC)
        with self._lock, self._conn:
            row = self._conn.execute("SELECT html FROM updates WHERE post_id = ?", (post.id,)).fetchone()
            old = text_lines(row["html"]) if row and row["html"] else []
            new = text_lines(html)
            edited = bool(old and new and old != new)
            if edited:
                old_set, new_set = set(old), set(new)
                added = [line for line in new if line not in old_set]
                removed = [line for line in old if line not in new_set]
                self._conn.execute(
                    "INSERT INTO update_edits (post_id, seen, added, removed) VALUES (?, ?, ?, ?)",
                    (post.id, now.isoformat(), json.dumps(added), json.dumps(removed)),
                )
            self._conn.execute(
                "INSERT INTO updates (post_id, topic_id, kind, url, posted, title, summary, html)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
                " ON CONFLICT (post_id) DO UPDATE SET topic_id = excluded.topic_id, kind = excluded.kind,"
                " url = excluded.url, posted = excluded.posted, title = excluded.title, summary = excluded.summary,"
                " html = excluded.html",
                (post.id, post.topic_id, kind, post.url, post.posted.isoformat(), title, summary, html),
            )
            if edited:
                self._conn.execute("UPDATE updates SET edited_at = ? WHERE post_id = ?", (now.isoformat(), post.id))
            if sections is None:
                return
            self._conn.execute("DELETE FROM class_changes WHERE post_id = ?", (post.id,))
            self._conn.executemany(
                "INSERT INTO class_changes (post_id, class, html) VALUES (?, ?, ?)",
                [(post.id, cls, html) for cls, html in sections.items()],
            )

    def class_updates(self, cls: str) -> list[ClassUpdate]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT u.post_id, u.kind, u.posted, u.url, c.html FROM updates u"
                " LEFT JOIN class_changes c ON c.post_id = u.post_id AND c.class = ?"
                # Only updates with class notes at all; a general-only post is not "no changes" news.
                " WHERE EXISTS (SELECT 1 FROM class_changes x WHERE x.post_id = u.post_id)"
                " ORDER BY u.posted DESC, u.post_id DESC",
                (cls,),
            ).fetchall()
        return [_row_to_update(r) for r in rows]

    def notes(self, post_id: int | None = None) -> list[Notes]:
        """One forum notes post with its edits (newest first), or every one when `post_id` is None."""
        where, params = ("WHERE post_id = ?", (post_id,)) if post_id is not None else ("", ())
        with self._lock:
            rows = self._conn.execute(
                f"SELECT post_id, kind, title, summary, url, posted, html FROM updates {where}"
                " ORDER BY posted DESC, post_id DESC", params).fetchall()
            edits = self._conn.execute(
                f"SELECT post_id, seen, added, removed FROM update_edits {where} ORDER BY seen DESC, rowid DESC",
                params).fetchall()
        by_post: dict[int, list[Edit]] = {}
        for e in edits:
            by_post.setdefault(e["post_id"], []).append(
                Edit(datetime.fromisoformat(e["seen"]), json.loads(e["added"]), json.loads(e["removed"])))
        return [Notes(r["post_id"], r["kind"], r["title"], r["summary"], r["url"], datetime.fromisoformat(r["posted"]),
                      r["html"], by_post.get(r["post_id"], [])) for r in rows]

    def unannounced(self) -> list[StoredPost] | None:
        """Feed posts not yet announced on Discord, oldest first; None if nothing was ever announced."""
        with self._lock:
            if self._conn.execute("SELECT 1 FROM announced LIMIT 1").fetchone() is None:
                return None
        return self._select("WHERE url NOT IN (SELECT url FROM announced)", order="published ASC")

    def mark_announced(self, urls: Iterable[str]) -> None:
        with self._lock, self._conn:
            self._conn.executemany("INSERT OR IGNORE INTO announced (url) VALUES (?)", [(u,) for u in urls])

    def note_topics(self) -> dict[int, str]:
        with self._lock:
            rows = self._conn.execute("SELECT DISTINCT topic_id, kind FROM updates").fetchall()
        return {r["topic_id"]: r["kind"] for r in rows}

    def prune_topic(self, topic_id: int, keep: set[int]) -> None:
        """Remove a topic's stored updates whose post is not in `keep`."""
        with self._lock, self._conn:
            stale = [r[0] for r in self._conn.execute(
                "SELECT post_id FROM updates WHERE topic_id = ?", (topic_id,)) if r[0] not in keep]
            self._conn.executemany("DELETE FROM class_changes WHERE post_id = ?", [(i,) for i in stale])
            self._conn.executemany("DELETE FROM update_edits WHERE post_id = ?", [(i,) for i in stale])
            self._conn.executemany("DELETE FROM updates WHERE post_id = ?", [(i,) for i in stale])
