from datetime import UTC, datetime, timedelta

import pytest

from wowforever.store import Store
from wowforever.web import create_app

from .test_store import make_post

EMPTY = "No WoW Forever posts gathered yet"
FOOTER = "Unofficial fan site. Not affiliated with Blizzard Entertainment."


def client_for(*posts):
    store = Store(":memory:")
    store.upsert(posts)
    return create_app(store).test_client()


@pytest.mark.parametrize("path", ["/", "/news", "/patches"])
def test_empty_store_shows_empty_message(path):
    response = client_for().get(path)
    assert response.status_code == 200
    assert EMPTY in response.text
    assert FOOTER in response.text


def test_home_lists_posts_with_link_and_footer():
    post = make_post(title="Claim Your Forever Names", url="https://worldofwarcraft.blizzard.com/en-us/news/9/claim")
    html = client_for(post).get("/").text
    assert "Claim Your Forever Names" in html
    assert "Read on Blizzard.com" in html
    assert 'href="https://worldofwarcraft.blizzard.com/en-us/news/9/claim"' in html
    assert FOOTER in html
    assert "Launches Nov 4" in html or "Live since Nov 4" in html or "Launches today" in html


def test_news_excludes_patch_posts():
    html = client_for(
        make_post(id=1, title="Some News"),
        make_post(id=2, title="Some Hotfixes", kind="patch"),
    ).get("/news").text
    assert "Some News" in html
    assert "Some Hotfixes" not in html


def test_patches_page_lists_versions_and_hotfixes():
    html = client_for(
        make_post(id=1, title="Patch 1.60.1 Notes", kind="patch", version="1.60.1"),
        make_post(id=2, title="Hotfixes: November 6", kind="patch"),
    ).get("/patches").text
    assert 'href="/patches/1.60.1"' in html
    assert "Hotfixes: November 6" in html


def test_patch_page_and_unknown_version():
    client = client_for(make_post(id=1, title="Patch 1.60.1 Notes", kind="patch", version="1.60.1"))
    response = client.get("/patches/1.60.1")
    assert response.status_code == 200
    assert "Patch 1.60.1 Notes" in response.text
    assert client.get("/patches/9.9").status_code == 404


def test_pagination():
    base = datetime(2026, 9, 1, tzinfo=UTC)
    client = client_for(*(make_post(id=i, published=base + timedelta(days=i)) for i in range(25)))
    first = client.get("/").text
    assert first.count('class="entry"') == 20
    assert "Older posts" in first
    assert 'href="/page/2/"' in first
    second = client.get("/page/2/").text
    assert second.count('class="entry"') == 5
    assert 'href="/"' in second and "Newer posts" in second
    assert client.get("/page/3/").status_code == 404
    assert client.get("/page/1/").status_code == 404
    assert client.get("/page/abc/").status_code == 404


def test_html_in_title_is_escaped():
    html = client_for(make_post(title="<script>alert(1)</script>")).get("/").text
    assert "&lt;script&gt;" in html
    assert "<script>alert(1)</script>" not in html


def test_edited_label():
    edited = make_post(id=1, title="Old")
    client = client_for(edited)
    assert "Updated" not in client.get("/").text
    store = Store(":memory:")
    store.upsert([edited])
    store.upsert([make_post(id=1, title="[Updated 10/22] New", updated=datetime(2026, 10, 22, tzinfo=UTC))])
    assert "Updated Oct 22" in create_app(store).test_client().get("/").text


def test_home_shows_countdown_plate():
    html = client_for().get("/").text
    assert 'class="plate"' in html
    assert "Launches Nov 4" in html or "Live since Nov 4" in html or "Launches today" in html


def test_patches_page_with_news_but_no_patches():
    html = client_for(make_post(id=1, title="Some News")).get("/patches").text
    assert EMPTY not in html
    assert "No WoW Forever patch notes or hotfixes from Blizzard yet" in html
