from datetime import UTC, date, datetime, timedelta

from wowforever.forum import ForumPost
from wowforever.posts import Post
from wowforever.store import Store


def make_post(**overrides):
    data = dict(
        id=1,
        title="WoW Forever news",
        url="https://worldofwarcraft.blizzard.com/en-us/news/1/x",
        summary="Summary",
        kind="news",
        version=None,
        published=datetime(2026, 10, 20, 12, tzinfo=UTC),
        updated=datetime(2026, 10, 20, 12, tzinfo=UTC),
    )
    data.update(overrides)
    return Post(**data)


def test_upsert_adds_and_lists_newest_first():
    store = Store(":memory:")
    old = make_post(id=1, published=datetime(2026, 10, 1, tzinfo=UTC))
    new = make_post(id=2, published=datetime(2026, 10, 2, tzinfo=UTC))
    assert store.upsert([old, new]) == (2, 0)
    listed = store.list_posts()
    assert [p.id for p in listed] == [2, 1]
    assert listed[0].published == new.published
    assert listed[0].edited_at is None


def test_upsert_twice_is_idempotent():
    store = Store(":memory:")
    posts = [make_post(id=1), make_post(id=2)]
    store.upsert(posts)
    assert store.upsert(posts) == (0, 0)
    assert store.count_posts() == 2


def test_edited_title_marks_edited():
    store = Store(":memory:")
    store.upsert([make_post(id=1, title="Choose Your Ruleset")])
    later = datetime(2026, 10, 22, 15, tzinfo=UTC)
    assert store.upsert([make_post(id=1, title="[Updated 10/22] Choose Your Ruleset", updated=later)]) == (0, 1)
    (post,) = store.list_posts()
    assert post.title == "[Updated 10/22] Choose Your Ruleset"
    assert post.edited_at == later


def test_filter_by_kind_and_paging():
    store = Store(":memory:")
    base = datetime(2026, 9, 1, tzinfo=UTC)
    store.upsert(make_post(id=i, published=base + timedelta(days=i)) for i in range(25))
    store.upsert([make_post(id=100, kind="patch")])
    assert len(store.list_posts("news", limit=20)) == 20
    assert len(store.list_posts("news", limit=20, offset=20)) == 5
    assert store.count_posts("patch") == 1
    assert store.count_posts("news") == 25


def test_patches_grouping():
    store = Store(":memory:")
    store.upsert([
        make_post(id=1, kind="patch", version="1.60", published=datetime(2026, 9, 17, tzinfo=UTC)),
        make_post(id=2, kind="patch", version="1.60.1", published=datetime(2026, 10, 20, tzinfo=UTC)),
        make_post(id=3, kind="patch", version="1.60.1", published=datetime(2026, 10, 21, tzinfo=UTC)),
        make_post(id=4, kind="patch", version=None),
    ])
    assert store.list_patches() == [("1.60.1", date(2026, 10, 20), 2), ("1.60", date(2026, 9, 17), 1)]
    assert [p.id for p in store.patch_posts("1.60.1")] == [2, 3]
    assert [p.id for p in store.unversioned_patch_posts()] == [4]


def test_persists_to_file(tmp_path):
    path = tmp_path / "db.sqlite3"
    Store(path).upsert([make_post(id=7)])
    assert [p.id for p in Store(path).list_posts()] == [7]


def make_forum_post(**overrides):
    data = dict(
        id=1,
        topic_id=10,
        number=1,
        cooked="",
        posted=datetime(2026, 10, 16, tzinfo=UTC),
        url="https://us.forums.blizzard.com/en/wow/t/10/1",
    )
    data.update(overrides)
    return ForumPost(**data)


def test_class_updates_newest_first_with_gaps():
    store = Store(":memory:")
    store.save_update(make_forum_post(id=1, posted=datetime(2026, 9, 24, tzinfo=UTC)), "beta",
                      {"Mage": "<ul><li>A</li></ul>"})
    store.save_update(make_forum_post(id=2, posted=datetime(2026, 10, 16, tzinfo=UTC)), "beta",
                      {"Druid": "<ul><li>B</li></ul>"})
    updates = store.class_updates("Mage")
    assert [u.posted.day for u in updates] == [16, 24]
    assert updates[0].html is None and updates[1].html == "<ul><li>A</li></ul>"
    assert updates[1].kind == "beta"
    assert updates[1].url == "https://us.forums.blizzard.com/en/wow/t/10/1"


def test_save_update_replaces_sections():
    store = Store(":memory:")
    post = make_forum_post()
    store.save_update(post, "beta", {"Mage": "old", "Rogue": "r"})
    store.save_update(post, "beta", {"Mage": "new"})
    assert store.class_updates("Mage")[0].html == "new"
    assert store.class_updates("Rogue")[0].html is None
    assert len(store.class_updates("Mage")) == 1


def test_note_topics():
    store = Store(":memory:")
    store.save_update(make_forum_post(id=1, topic_id=10), "beta", {"Mage": "a"})
    store.save_update(make_forum_post(id=2, topic_id=10), "beta", {"Mage": "b"})
    store.save_update(make_forum_post(id=3, topic_id=11), "hotfix", {"Mage": "c"})
    assert store.note_topics() == {10: "beta", 11: "hotfix"}


def test_existing_database_gains_new_tables(tmp_path):
    import sqlite3
    path = tmp_path / "old.sqlite3"
    conn = sqlite3.connect(path)
    conn.executescript(
        "CREATE TABLE posts (id INTEGER PRIMARY KEY, title TEXT NOT NULL, url TEXT NOT NULL,"
        " summary TEXT NOT NULL, kind TEXT NOT NULL, version TEXT, published TEXT NOT NULL,"
        " updated TEXT NOT NULL, edited_at TEXT);"
        "INSERT INTO posts VALUES (1, 'Old', 'u', 's', 'news', NULL,"
        " '2026-10-01T00:00:00+00:00', '2026-10-01T00:00:00+00:00', NULL);"
    )
    conn.commit()
    conn.close()
    store = Store(path)
    assert [p.title for p in store.list_posts()] == ["Old"]
    assert store.class_updates("Mage") == []
