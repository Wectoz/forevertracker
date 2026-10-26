from datetime import UTC, datetime, timedelta

from wowforever.build import build_site
from wowforever.store import Store

from .test_store import make_post


def filled_store():
    store = Store(":memory:")
    base = datetime(2026, 9, 1, tzinfo=UTC)
    store.upsert(make_post(id=i, title=f"Forever news {i}", published=base + timedelta(days=i)) for i in range(25))
    store.upsert([make_post(id=100, title="Patch 1.60.1 Notes", kind="patch", version="1.60.1")])
    return store


def test_build_writes_every_page(tmp_path):
    pages = build_site(filled_store(), tmp_path, base_path="/wow-forever-news")
    for path in ("index.html", "page/2/index.html", "news/index.html", "news/page/2/index.html",
                 "patches/index.html", "patches/1.60.1/index.html", "static/style.css", "static/countdown.js",
                 "404.html"):
        assert (tmp_path / path).is_file(), path
    assert pages >= 6


def test_build_links_use_base_path(tmp_path):
    build_site(filled_store(), tmp_path, base_path="/wow-forever-news")
    home = (tmp_path / "index.html").read_text()
    assert 'href="/wow-forever-news/news"' in home
    assert 'href="/wow-forever-news/static/style.css' in home
    assert 'href="/wow-forever-news/page/2/"' in home


def test_build_empty_store(tmp_path):
    build_site(Store(":memory:"), tmp_path, base_path="")
    assert "No WoW Forever posts gathered yet" in (tmp_path / "index.html").read_text()


def test_build_writes_class_pages_and_icons(tmp_path):
    build_site(Store(":memory:"), tmp_path, base_path="/wow-forever-news")
    assert (tmp_path / "classes/mage/index.html").is_file()
    assert (tmp_path / "static/classes/mage.jpg").is_file()
    assert 'href="/wow-forever-news/classes/mage"' in (tmp_path / "index.html").read_text()
