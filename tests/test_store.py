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
        thumbnail=None,
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
        posted=datetime(2026, 10, 16, 18, tzinfo=UTC),
        url="https://us.forums.blizzard.com/en/wow/t/10/1",
        thread_title="WoW Forever Beta Development Notes",
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


def test_forum_updates_appear_in_the_feed_as_patch_posts():
    store = Store(":memory:")
    store.upsert([make_post(id=5, title="Some news")])
    store.save_update(make_forum_post(id=7), "beta", {"Mage": "m"},
                      title="WoW Forever Beta Development Notes – Oct 16", summary="Today, we updated the Beta.")
    feed = store.list_posts()  # newest first: the news post is Oct 20, the forum post Oct 16
    assert [p.title for p in feed] == ["Some news", "WoW Forever Beta Development Notes – Oct 16"]
    entry = feed[1]
    assert entry.kind == "patch" and entry.version is None and entry.on_forums
    assert entry.url == "https://us.forums.blizzard.com/en/wow/t/10/1"
    assert entry.summary == "Today, we updated the Beta."
    assert not feed[0].on_forums
    assert store.count_posts() == 2 and store.count_posts("patch") == 1
    assert [p.title for p in store.list_posts("news")] == ["Some news"]
    assert [p.id for p in store.unversioned_patch_posts()] == [7]


def test_update_without_class_sections_is_in_feed_but_not_on_class_pages():
    store = Store(":memory:")
    store.save_update(make_forum_post(), "hotfix", {}, title="Hotfixes", summary="s")
    assert store.class_updates("Mage") == []
    assert len(store.list_posts()) == 1


def test_sections_none_leaves_class_rows_alone():
    store = Store(":memory:")
    post = make_forum_post()
    store.save_update(post, "beta", {"Mage": "kept"}, title="T", summary="S")
    store.save_update(post, "beta", None, title="T2", summary="S2")
    assert store.class_updates("Mage")[0].html == "kept"
    assert store.list_posts()[0].title == "T2"


def test_older_updates_table_gains_title_and_summary(tmp_path):
    import sqlite3
    path = tmp_path / "old.sqlite3"
    conn = sqlite3.connect(path)
    conn.executescript(
        "CREATE TABLE updates (post_id INTEGER PRIMARY KEY, topic_id INTEGER NOT NULL, kind TEXT NOT NULL,"
        " url TEXT NOT NULL, posted TEXT NOT NULL);"
        "INSERT INTO updates VALUES (1, 10, 'beta', 'u', '2026-10-01T18:00:00+00:00');"
    )
    conn.commit()
    conn.close()
    store = Store(path)
    assert len(store.list_posts()) == 1
    store.save_update(make_forum_post(id=1), "beta", {"Mage": "m"}, title="New", summary="S")
    assert store.list_posts()[0].title == "New"


def test_thumbnail_is_stored_and_kept_up_to_date_without_marking_an_edit():
    store = Store(":memory:")
    store.upsert([make_post(thumbnail="https://cdn.example/a.png")])
    assert store.list_posts()[0].thumbnail == "https://cdn.example/a.png"
    assert store.upsert([make_post(thumbnail="https://cdn.example/b.png")]) == (0, 0)
    post = store.list_posts()[0]
    assert post.thumbnail == "https://cdn.example/b.png" and post.edited_at is None


def test_forum_updates_have_no_thumbnail():
    store = Store(":memory:")
    store.save_update(make_forum_post(), "beta", {"Mage": "m"}, title="T", summary="S")
    assert store.list_posts()[0].thumbnail is None


def test_older_posts_table_gains_thumbnail(tmp_path):
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
    assert store.list_posts()[0].thumbnail is None
    store.upsert([make_post(id=1, title="Old", summary="s", thumbnail="https://cdn.example/a.png")])
    assert store.list_posts()[0].thumbnail == "https://cdn.example/a.png"


def test_edits_are_recorded_only_when_the_text_changes():
    store = Store(":memory:")
    post = make_forum_post()
    store.save_update(post, "beta", None)  # gathered before full notes were stored
    store.save_update(post, "beta", None, html="<ul><li>a</li><li>b</li></ul>")
    store.save_update(post, "beta", None, html="<ul><li>a</li>\n<li>b</li></ul>")  # same text
    assert store.notes(1)[0].edits == []
    assert store.list_posts()[0].edited_at is None
    seen = datetime(2026, 10, 18, tzinfo=UTC)
    store.save_update(post, "beta", None, html="<ul><li>a</li><li>c</li></ul>", now=seen)
    notes = store.notes(1)[0]
    assert notes.html == "<ul><li>a</li><li>c</li></ul>"
    assert [(e.seen, e.added, e.removed) for e in notes.edits] == [(seen, ["c"], ["b"])]
    assert store.list_posts()[0].edited_at == seen
    store.prune_topic(10, keep=set())
    assert store.notes() == []


def test_announced_posts():
    store = Store(":memory:")
    assert store.unannounced() is None
    store.upsert([make_post(id=1, url="https://a", published=datetime(2026, 10, 2, tzinfo=UTC)),
                  make_post(id=2, url="https://b", published=datetime(2026, 10, 1, tzinfo=UTC))])
    store.mark_announced(["https://a"])
    assert [p.url for p in store.unannounced()] == ["https://b"]
    store.mark_announced(["https://b", "https://b"])
    assert store.unannounced() == []


def test_known_issues_stay_out_of_feed():
    store = Store(":memory:")
    store.save_update(make_forum_post(id=1, topic_id=10), "beta", {}, title="Beta", summary="s")
    store.save_update(make_forum_post(id=2, topic_id=11), "known", {}, title="Known Issues", summary="s")
    store.mark_announced(["https://example.com/old"])
    assert [p.id for p in store.list_posts()] == [1]
    assert store.count_posts() == 1
    assert [p.id for p in store.unversioned_patch_posts()] == [1]
    assert [p.id for p in store.unannounced()] == [1]
    assert {n.id for n in store.notes()} == {1, 2}


def test_latest_known_issues_prefers_most_recent_change():
    store = Store(":memory:")
    assert store.latest_known_issues() is None
    a = make_forum_post(id=1, topic_id=10, posted=datetime(2026, 10, 8, tzinfo=UTC))
    b = make_forum_post(id=2, topic_id=11, posted=datetime(2026, 11, 4, tzinfo=UTC))
    store.save_update(a, "known", {}, title="A", html="<p>one</p>", now=datetime(2026, 10, 8, tzinfo=UTC))
    store.save_update(b, "known", {}, title="B", html="<p>x</p>", now=datetime(2026, 11, 4, tzinfo=UTC))
    assert store.latest_known_issues().id == 2
    store.save_update(a, "known", {}, title="A", html="<p>two</p>", now=datetime(2026, 11, 5, tzinfo=UTC))
    latest = store.latest_known_issues()
    assert latest.id == 1 and len(latest.edits) == 1
    assert latest.edited_at == datetime(2026, 11, 5, tzinfo=UTC)


def make_staff(**overrides):
    from wowforever.forum import StaffPost
    data = dict(id=1, topic_id=10, number=2, author="Kaivax", author_title="Community Manager",
                thread_title="Thread", excerpt="Hello", posted=datetime(2026, 10, 20, 12, tzinfo=UTC),
                url="https://us.forums.blizzard.com/en/wow/t/10/2")
    data.update(overrides)
    return StaffPost(**data)


def test_blue_posts_roundtrip_and_ignore_duplicates(tmp_path):
    store = Store(tmp_path / "t.db")
    assert not store.has_blue_posts()
    old, new = make_staff(id=1), make_staff(id=2, posted=datetime(2026, 10, 21, tzinfo=UTC))
    assert store.add_blue_posts([old, new]) == 2
    assert store.add_blue_posts([old, make_staff(id=3)]) == 1
    assert store.has_blue_posts()
    assert store.count_blue_posts() == 3
    assert store.list_blue_posts(limit=2)[0] == new
    assert store.list_blue_posts(limit=1, offset=1)[0].id in (1, 3)


def test_unannounced_blue_posts_oldest_first(tmp_path):
    store = Store(tmp_path / "t.db")
    store.add_blue_posts([make_staff(id=1, posted=datetime(2026, 10, 22, tzinfo=UTC)),
                          make_staff(id=2, posted=datetime(2026, 10, 20, tzinfo=UTC)),
                          make_staff(id=3, posted=datetime(2026, 10, 21, tzinfo=UTC))])
    store.add_blue_posts([make_staff(id=4)], announced=True)
    assert [p.id for p in store.unannounced_blue_posts()] == [2, 3, 1]
    store.mark_blue_announced([2, 3])
    assert [p.id for p in store.unannounced_blue_posts()] == [1]
