from datetime import UTC, datetime, timedelta

import pytest

from wowforever.store import Store
from wowforever.web import create_app

from .test_store import make_forum_post, make_post

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
    store.upsert([make_post(id=1, title="[Updated 10/22] New", updated=datetime(2026, 10, 22, 18, tzinfo=UTC))])
    assert "Updated Oct 22" in create_app(store).test_client().get("/").text


def test_home_shows_countdown_plate():
    html = client_for().get("/").text
    assert 'class="plate"' in html
    assert "Launches Nov 4" in html or "Live since Nov 4" in html or "Launches today" in html


def test_patches_page_with_news_but_no_patches():
    html = client_for(make_post(id=1, title="Some News")).get("/patches").text
    assert EMPTY not in html
    assert "No WoW Forever patch notes or hotfixes from Blizzard yet" in html


def class_client(*updates):
    store = Store(":memory:")
    for post, kind, sections in updates:
        store.save_update(post, kind, sections)
    return create_app(store).test_client()


def test_every_page_has_classes_menu_with_icons():
    html = client_for().get("/news").text
    assert "Classes" in html
    for slug in ("druid", "mage", "warrior"):
        assert f'href="/classes/{slug}"' in html
        assert f"static/classes/{slug}.jpg" in html


def test_class_page_shows_only_that_class():
    html = class_client(
        (make_forum_post(id=1, url="https://us.forums.blizzard.com/en/wow/t/10/1"), "beta",
         {"Mage": "<ul><li>Hot Streak longer</li></ul>", "Druid": "<ul><li>Wrath up</li></ul>"}),
    ).get("/classes/mage").text
    assert "Mage patch notes" in html
    assert "<li>Hot Streak longer</li>" in html and "Wrath up" not in html
    assert "Beta build · Oct 16" in html
    assert 'href="https://us.forums.blizzard.com/en/wow/t/10/1"' in html
    assert "Full notes on the Blizzard forums →" in html
    assert FOOTER in html


def test_update_without_class_changes_shows_dimmed_card():
    html = class_client((make_forum_post(), "beta", {"Druid": "<ul><li>Wrath up</li></ul>"})).get("/classes/mage").text
    assert "No Mage changes in this update." in html


def test_hotfix_label():
    html = class_client((make_forum_post(), "hotfix", {"Mage": "<ul><li>x</li></ul>"})).get("/classes/mage").text
    assert "Hotfix · Oct 16" in html


def test_class_page_with_no_updates_is_200_with_message():
    response = client_for().get("/classes/rogue")
    assert response.status_code == 200 and "No Rogue patch notes gathered yet" in response.text


def test_unknown_class_is_404():
    assert client_for().get("/classes/deathknight").status_code == 404


def test_dates_are_shown_in_pacific_time_like_blizzard():
    # 00:15 UTC on Oct 16 is still Oct 15 in California, which is how Blizzard dates its posts.
    late = datetime(2026, 10, 16, 0, 15, tzinfo=UTC)
    html = class_client((make_forum_post(posted=late), "beta", {"Mage": "<ul><li>x</li></ul>"})).get("/classes/mage").text
    assert "Beta build · Oct 15" in html
    assert "Oct 15, 2026" in client_for(make_post(published=late, updated=late)).get("/").text


def test_class_menu_marks_the_current_class():
    html = client_for().get("/classes/mage").text
    assert 'href="/classes/mage" aria-current="page"' in html
    assert 'href="/classes/druid" aria-current' not in html


def test_home_links_forum_posts_to_the_forums():
    store = Store(":memory:")
    store.save_update(make_forum_post(), "beta", {"Mage": "m"},
                      title="WoW Forever Beta Development Notes – Oct 16", summary="Today, we updated the Beta.")
    html = create_app(store).test_client().get("/").text
    assert "WoW Forever Beta Development Notes – Oct 16" in html
    assert "Read on the Blizzard forums →" in html
    assert 'href="https://us.forums.blizzard.com/en/wow/t/10/1"' in html
    assert "Today, we updated the Beta." in create_app(store).test_client().get("/patches").text


def test_pages_have_preview_tags_and_favicon():
    html = client_for().get("/news").text
    assert '<meta property="og:title" content="WoW Forever News · WoW Forever Tracker">' in html
    assert '<meta property="og:description" content="World of Warcraft: Forever announcements and news' in html
    assert '<meta property="og:image" content="http://localhost/static/social.png">' in html
    assert '<meta property="og:url" content="http://localhost/news">' in html
    assert '<link rel="canonical" href="http://localhost/news">' in html
    assert '<meta name="twitter:card" content="summary_large_image">' in html
    assert 'rel="icon" href="/static/favicon.svg"' in html
    assert 'rel="apple-touch-icon" href="/static/apple-touch-icon.png"' in html


def test_not_found_page_is_not_indexed():
    assert '<meta name="robots" content="noindex">' in client_for().get("/nope").text


def test_home_has_class_call_to_action():
    assert "Patch notes for your class →" in client_for().get("/").text
    assert "Patch notes for your class →" not in client_for().get("/news").text


def test_news_card_shows_small_lazy_thumbnail():
    html = client_for(make_post(thumbnail="https://bnetcmsus-a.akamaihd.net/cms/blog_thumbnail/x.png")).get("/").text
    assert ('<img class="thumb" src="https://bnetcmsus-a.akamaihd.net/cms/blog_thumbnail/x.png?imwidth=360"'
            ' alt="" width="180" height="101" loading="lazy">') in html


def test_news_card_without_thumbnail_has_no_image():
    html = client_for(make_post()).get("/news").text
    assert 'class="thumb"' not in html and "Blue post" not in html


def test_blue_post_card_is_tinted_with_tag_and_tile():
    store = Store(":memory:")
    store.save_update(make_forum_post(), "beta", {"Mage": "m"}, title="Notes", summary="S")
    html = create_app(store).test_client().get("/").text
    assert 'class="entry blue-post"' in html
    assert '<span class="blue-tag">Blue post</span>' in html
    assert 'class="thumb blue-tile"' in html
