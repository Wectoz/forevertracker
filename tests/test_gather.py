import logging
import re
import time
from datetime import UTC, datetime
from pathlib import Path

import pytest

from wowforever import cli, gather
from wowforever.blizzard import FetchError
from wowforever.gather import backfill, fetch_latest, start_hourly
from wowforever.posts import Post
from wowforever.store import Store

FIXTURE_DIR = Path(__file__).parent / "fixtures"
FIXTURES = {
    1: (FIXTURE_DIR / "news_page1.html").read_text(encoding="utf-8"),
    2: (FIXTURE_DIR / "news_page2.html").read_text(encoding="utf-8"),
}
LONG_AGO = datetime(2000, 1, 1, tzinfo=UTC)


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
