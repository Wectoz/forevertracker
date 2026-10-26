from datetime import UTC, date, datetime, timedelta

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
