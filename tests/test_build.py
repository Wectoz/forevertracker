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


SITE = "https://wectoz.github.io/wow-forever-news"


def test_build_with_site_url_writes_sitemap_and_absolute_preview_urls(tmp_path):
    build_site(filled_store(), tmp_path, site_url=SITE)
    sitemap = (tmp_path / "sitemap.xml").read_text()
    assert f"<loc>{SITE}/</loc>" in sitemap
    assert f"<loc>{SITE}/classes/mage</loc>" in sitemap
    assert f"<loc>{SITE}/patches/1.60.1</loc>" in sitemap
    assert "this-page-does-not-exist" not in sitemap
    home = (tmp_path / "index.html").read_text()
    assert f'<meta property="og:image" content="{SITE}/static/social.png">' in home
    assert f'<link rel="canonical" href="{SITE}/">' in home
    assert 'href="/wow-forever-news/news"' in home
    for name in ("favicon.svg", "favicon-32.png", "apple-touch-icon.png", "social.png"):
        assert (tmp_path / "static" / name).is_file(), name


def test_build_fails_on_a_broken_internal_link(tmp_path, monkeypatch):
    import pytest

    from wowforever import build
    from wowforever.web import create_app

    def app_with_broken_link(store):
        app = create_app(store)
        app.view_functions["home"] = lambda: '<a href="/missing-page">gone</a>'
        return app

    monkeypatch.setattr(build, "create_app", app_with_broken_link)
    with pytest.raises(RuntimeError, match="/missing-page"):
        build_site(Store(":memory:"), tmp_path)


def test_build_writes_feeds_and_search_index_as_files(tmp_path):
    import json

    build_site(filled_store(), tmp_path, site_url=SITE)
    feed = (tmp_path / "feed.xml").read_text()
    assert feed.startswith('<?xml version="1.0" encoding="utf-8"?>')
    assert f'<link rel="self" href="{SITE}/feed.xml"/>' in feed
    assert (tmp_path / "classes/mage/feed.xml").is_file()
    items = json.loads((tmp_path / "search.json").read_text())
    assert any(item["title"] == "Patch 1.60.1 Notes" for item in items)
    assert (tmp_path / "search/index.html").is_file()
    sitemap = (tmp_path / "sitemap.xml").read_text()
    assert "feed.xml" not in sitemap and "search.json" not in sitemap
