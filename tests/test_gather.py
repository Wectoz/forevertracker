import logging
import re
import time
from datetime import UTC, datetime
from pathlib import Path

import pytest

from wowforever import cli, gather
import json

from wowforever.blizzard import FetchError
from wowforever.gather import backfill, fetch_latest, gather_class_notes, start_hourly
from wowforever.posts import Post
from wowforever.store import Store

FIXTURE_DIR = Path(__file__).parent / "fixtures"
FIXTURES = {
    1: (FIXTURE_DIR / "news_page1.html").read_text(encoding="utf-8"),
    2: (FIXTURE_DIR / "news_page2.html").read_text(encoding="utf-8"),
}
LONG_AGO = datetime(2000, 1, 1, tzinfo=UTC)


FORUM = {
    "/c/349.json": json.loads((FIXTURE_DIR / "forum_category.json").read_text(encoding="utf-8")),
    "/t/2360696.json": json.loads((FIXTURE_DIR / "forum_thread.json").read_text(encoding="utf-8")),
}


def forum_fetch(pages=None):
    pages = pages or FORUM
    calls = []

    def fetch(path):
        calls.append(path)
        return json.loads(json.dumps(pages[path]))  # a fresh copy per call
    fetch.calls = calls
    return fetch


@pytest.fixture(autouse=True)
def no_live_forum(monkeypatch):
    monkeypatch.setattr(gather, "fetch_json", forum_fetch())


class FakeFetch:
    def __init__(self, pages=FIXTURES):
        self.pages = pages
        self.calls = []

    def __call__(self, n):
        self.calls.append(n)
        return self.pages[n]


def test_fetch_latest_stores_forever_posts():
    store = Store(":memory:")
    added, edited = fetch_latest(store, fetch=FakeFetch())
    assert added >= 1 and edited == 0
    assert all("forever" in (p.title + p.summary).lower() for p in store.list_posts(limit=100))


def test_fetch_latest_twice_adds_nothing():
    store = Store(":memory:")
    fetch_latest(store, fetch=FakeFetch())
    assert fetch_latest(store, fetch=FakeFetch()) == (0, 0)


def test_backfill_walks_pages():
    store = Store(":memory:")
    fake = FakeFetch()
    added, _ = backfill(store, fetch=fake, cutoff=LONG_AGO, max_pages=2, delay=0)
    assert fake.calls == [1, 2]
    page1_only = Store(":memory:")
    fetch_latest(page1_only, fetch=FakeFetch())
    assert store.count_posts() > page1_only.count_posts()


def test_backfill_stops_when_no_next():
    last_page = re.sub(r'"next":"[^"]*"', '"next":null', FIXTURES[1])
    assert last_page != FIXTURES[1]
    fake = FakeFetch({1: last_page, 2: FIXTURES[2]})
    backfill(Store(":memory:"), fetch=fake, cutoff=LONG_AGO, delay=0)
    assert fake.calls == [1]


def test_backfill_stops_at_cutoff():
    fake = FakeFetch()
    backfill(Store(":memory:"), fetch=fake, cutoff=datetime(2030, 1, 1, tzinfo=UTC), delay=0)
    assert fake.calls == [1]


def test_fetch_error_leaves_store_untouched():
    store = Store(":memory:")
    fetch_latest(store, fetch=FakeFetch())
    before = store.count_posts()

    def failing(n):
        raise FetchError("offline")

    with pytest.raises(FetchError):
        fetch_latest(store, fetch=failing)
    assert store.count_posts() == before


def test_hourly_survives_errors(caplog):
    store = Store(":memory:")
    calls = []

    def flaky(n):
        calls.append(n)
        if len(calls) == 1:
            raise FetchError("offline")
        return FIXTURES[1]

    caplog.set_level(logging.WARNING)
    start_hourly(store, interval=0.01, fetch=flaky)
    deadline = time.monotonic() + 2
    while store.count_posts() == 0 and time.monotonic() < deadline:
        time.sleep(0.01)
    assert store.count_posts() > 0
    assert "Gathering failed" in caplog.text


def test_cli_fetch_reports_failure(monkeypatch, tmp_path, capsys):
    def failing(n):
        raise FetchError("offline")

    monkeypatch.setattr(gather, "fetch_listing", failing)
    assert cli.main(["--db", str(tmp_path / "d.sqlite3"), "fetch"]) == 1
    assert "Could not gather from Blizzard" in capsys.readouterr().err


def test_cli_fetch_reports_counts(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(gather, "fetch_listing", FakeFetch())
    assert cli.main(["--db", str(tmp_path / "d.sqlite3"), "fetch"]) == 0
    assert "WoW Forever posts." in capsys.readouterr().out


def test_hourly_survives_unexpected_errors(caplog):
    store = Store(":memory:")
    calls = []

    def broken_then_ok(n):
        calls.append(n)
        if len(calls) == 1:
            raise RuntimeError("surprise")
        return FIXTURES[1]

    caplog.set_level(logging.WARNING)
    start_hourly(store, interval=0.01, fetch=broken_then_ok)
    deadline = time.monotonic() + 2
    while store.count_posts() == 0 and time.monotonic() < deadline:
        time.sleep(0.01)
    assert store.count_posts() > 0


def test_malformed_blog_is_skipped_not_fatal(caplog):
    good = '{"id":5,"title":"WoW: Forever news","url":"/news/5/x","description":"","published":"2026-10-20T00:00:00Z"}'
    bad = '{"id":6,"title":"WoW: Forever promo","url":"/news/6/y"}'
    page = '<script id="model">model = {"blogList":{"blogs":[' + bad + "," + good + ']},"paginationLinks":{"next":null}}</script>'
    store = Store(":memory:")
    caplog.set_level(logging.WARNING)
    assert fetch_latest(store, fetch=lambda n: page) == (1, 0)
    assert "Skipping malformed" in caplog.text


def test_cli_build_writes_site(tmp_path, capsys):
    out = tmp_path / "site"
    assert cli.main(["--db", str(tmp_path / "d.sqlite3"), "build", "--out", str(out), "--base-path", "/wow-forever-news"]) == 0
    assert (out / "index.html").is_file()
    assert "Built" in capsys.readouterr().out


def test_gather_class_notes_saves_builds_with_class_sections():
    store = Store(":memory:")
    assert gather_class_notes(store, forum_fetch()) == 4
    mage = store.class_updates("Mage")
    assert len(mage) == 4 and all(u.kind == "beta" for u in mage) and all(u.html for u in mage)
    rogue = store.class_updates("Rogue")  # the Oct 8 build (post 5) has no Rogue section
    assert [u.html is None for u in rogue] == [False, True, False, False]


def test_post_without_classes_section_is_not_saved(caplog):
    thread = json.loads(json.dumps(FORUM["/t/2360696.json"]))
    post = thread["post_stream"]["posts"][3]
    post["cooked"] = post["cooked"].replace("<strong>Classes</strong>", "<strong>Other</strong>")
    caplog.set_level(logging.INFO)
    store = Store(":memory:")
    assert gather_class_notes(store, forum_fetch({**FORUM, "/t/2360696.json": thread})) == 3
    assert "https://us.forums.blizzard.com/en/wow/t/2360696/4" in caplog.text
    assert len(store.class_updates("Mage")) == 3


def test_known_topic_refreshed_after_it_leaves_the_category_page():
    store = Store(":memory:")
    gather_class_notes(store, forum_fetch())
    category = json.loads(json.dumps(FORUM["/c/349.json"]))
    category["topic_list"]["topics"] = [t for t in category["topic_list"]["topics"] if t["id"] != 2360696]
    fetch = forum_fetch({**FORUM, "/c/349.json": category})
    assert gather_class_notes(store, fetch) == 4
    assert "/t/2360696.json" in fetch.calls


def test_cli_fetch_survives_forum_outage(monkeypatch, tmp_path, capsys):
    def down(path):
        raise FetchError("forum offline")

    monkeypatch.setattr(gather, "fetch_listing", FakeFetch())
    monkeypatch.setattr(gather, "fetch_json", down)
    assert cli.main(["--db", str(tmp_path / "d.sqlite3"), "fetch"]) == 0
    out, err = capsys.readouterr()
    assert "WoW Forever posts." in out
    assert "Could not gather class notes from the forums" in err


def test_cli_fetch_reports_class_notes(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(gather, "fetch_listing", FakeFetch())
    assert cli.main(["--db", str(tmp_path / "d.sqlite3"), "fetch"]) == 0
    assert "Saved 4 class patch-note updates." in capsys.readouterr().out


def test_hourly_gathers_class_notes():
    store = Store(":memory:")
    start_hourly(store, interval=0.01, fetch=lambda n: FIXTURES[1], fetch_forum=forum_fetch())
    deadline = time.monotonic() + 2
    while len(store.class_updates("Mage")) < 4 and time.monotonic() < deadline:
        time.sleep(0.01)
    assert len(store.class_updates("Mage")) == 4


def thread_copy(topic_id, id_offset):
    """The real beta thread re-numbered as another topic, with its own post ids."""
    thread = json.loads(json.dumps(FORUM["/t/2360696.json"]))
    thread["id"] = topic_id
    thread["post_stream"]["stream"] = [i + id_offset for i in thread["post_stream"]["stream"]]
    for post in thread["post_stream"]["posts"]:
        post["id"] += id_offset
    return thread


def test_failing_thread_does_not_block_other_threads(caplog):
    store = Store(":memory:")
    gather_class_notes(store, forum_fetch())
    category = json.loads(json.dumps(FORUM["/c/349.json"]))
    new_topic = dict(next(t for t in category["topic_list"]["topics"] if t["id"] == 2360696),
                     id=999, title="WoW Forever Patch 1.0 Notes")
    category["topic_list"]["topics"].append(new_topic)
    pages = {"/c/349.json": category, "/t/999.json": thread_copy(999, 10_000_000)}

    def fetch(path):
        if path == "/t/2360696.json":
            raise FetchError("HTTP 404")
        return json.loads(json.dumps(pages[path]))

    caplog.set_level(logging.WARNING)
    assert gather_class_notes(store, fetch) == 4
    assert {u.kind for u in store.class_updates("Mage")} == {"beta", "patch"}
    assert "2360696" in caplog.text


def test_category_failure_still_raises():
    def down(path):
        raise FetchError("forum offline")

    with pytest.raises(FetchError):
        gather_class_notes(Store(":memory:"), down)


def test_post_edited_to_drop_its_class_notes_is_removed():
    store = Store(":memory:")
    gather_class_notes(store, forum_fetch())
    thread = json.loads(json.dumps(FORUM["/t/2360696.json"]))
    thread["post_stream"]["posts"][0]["cooked"] = "<p>Notes moved to a new thread.</p>"
    assert gather_class_notes(store, forum_fetch({**FORUM, "/t/2360696.json": thread})) == 3
    assert len(store.class_updates("Mage")) == 3


def test_deleted_post_is_removed():
    store = Store(":memory:")
    gather_class_notes(store, forum_fetch())
    thread = json.loads(json.dumps(FORUM["/t/2360696.json"]))
    gone = thread["post_stream"]["posts"].pop(0)
    thread["post_stream"]["stream"].remove(gone["id"])
    gather_class_notes(store, forum_fetch({**FORUM, "/t/2360696.json": thread}))
    assert len(store.class_updates("Mage")) == 3


def test_thread_that_no_longer_parses_keeps_its_history():
    # A Blizzard markup change must not wipe what was gathered before.
    store = Store(":memory:")
    gather_class_notes(store, forum_fetch())
    thread = json.loads(json.dumps(FORUM["/t/2360696.json"]))
    for post in thread["post_stream"]["posts"]:
        post["cooked"] = post["cooked"].replace("Classes", "Klassen")
    assert gather_class_notes(store, forum_fetch({**FORUM, "/t/2360696.json": thread})) == 0
    assert len(store.class_updates("Mage")) == 4


def test_cli_fetch_still_gathers_class_notes_when_news_fails(monkeypatch, tmp_path, capsys):
    def failing(n):
        raise FetchError("news offline")

    monkeypatch.setattr(gather, "fetch_listing", failing)
    assert cli.main(["--db", str(tmp_path / "d.sqlite3"), "fetch"]) == 1
    out, err = capsys.readouterr()
    assert "Could not gather from Blizzard" in err
    assert "Saved 4 class patch-note updates." in out


def test_every_notes_post_becomes_a_feed_entry():
    store = Store(":memory:")
    gather_class_notes(store, forum_fetch())
    feed = store.list_posts(kind="patch")
    assert [p.title for p in feed] == [
        "WoW Forever Beta Development Notes – Oct 15",
        "WoW Forever Beta Development Notes – Oct 8",
        "WoW Forever Beta Development Notes – Oct 1",
        "WoW Forever Beta Development Notes – Sep 24",
    ]
    assert feed[-1].summary.startswith("Today, we updated the WoW Forever Beta with a new build")
    assert "Change Log" not in feed[-1].summary
    assert feed[-1].url == "https://us.forums.blizzard.com/en/wow/t/2360696/1"


def test_general_only_post_is_in_feed_but_not_on_class_pages():
    thread = json.loads(json.dumps(FORUM["/t/2360696.json"]))
    post = thread["post_stream"]["posts"][3]
    post["cooked"] = post["cooked"].replace("<strong>Classes</strong>", "<strong>Other</strong>")
    store = Store(":memory:")
    gather_class_notes(store, forum_fetch({**FORUM, "/t/2360696.json": thread}))
    assert len(store.list_posts(kind="patch")) == 4
    assert len(store.class_updates("Mage")) == 3


def test_cli_build_with_site_url_writes_sitemap(tmp_path, capsys):
    out = tmp_path / "site"
    assert cli.main(["--db", str(tmp_path / "d.sqlite3"), "build", "--out", str(out),
                     "--site-url", "https://wectoz.github.io/wow-forever-news"]) == 0
    assert "https://wectoz.github.io/wow-forever-news/news" in (out / "sitemap.xml").read_text()


def test_gather_stores_full_notes():
    store = Store(":memory:")
    gather_class_notes(store, forum_fetch())
    notes = store.notes()
    assert notes and all(n.html.startswith("<p>") for n in notes)
    assert all("<script" not in n.html for n in notes)
