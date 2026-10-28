from datetime import UTC, datetime, timedelta

import pytest

from wowforever.realms import Realm
from wowforever.store import Store
from wowforever.web import create_app

from .test_store import make_forum_post, make_post, make_staff

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
    assert "Launches Nov 4" in html or "Live now" in html or "Launches today" in html


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
    assert "Launches Nov 4" in html or "Live now" in html or "Launches today" in html


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
    assert 'Beta build · <time datetime="2026-10-16T18:00:00+00:00">Oct 16</time>' in html
    assert 'href="https://us.forums.blizzard.com/en/wow/t/10/1"' in html
    assert 'href="/notes/1">Full notes →' in html
    assert 'id="beta-2026-10-16"' in html
    assert FOOTER in html


def test_update_without_class_changes_shows_dimmed_card():
    html = class_client((make_forum_post(), "beta", {"Druid": "<ul><li>Wrath up</li></ul>"})).get("/classes/mage").text
    assert "No Mage changes in this update." in html


def test_hotfix_label():
    html = class_client((make_forum_post(), "hotfix", {"Mage": "<ul><li>x</li></ul>"})).get("/classes/mage").text
    assert "Hotfix · <time" in html and ">Oct 16</time>" in html


def test_class_page_with_no_updates_is_200_with_message():
    response = client_for().get("/classes/rogue")
    assert response.status_code == 200 and "No Rogue patch notes gathered yet" in response.text


def test_unknown_class_is_404():
    assert client_for().get("/classes/deathknight").status_code == 404


def test_dates_are_shown_in_pacific_time_like_blizzard():
    # 00:15 UTC on Oct 16 is still Oct 15 in California, which is how Blizzard dates its posts.
    late = datetime(2026, 10, 16, 0, 15, tzinfo=UTC)
    html = class_client((make_forum_post(posted=late), "beta", {"Mage": "<ul><li>x</li></ul>"})).get("/classes/mage").text
    assert "Beta build · <time" in html and ">Oct 15</time>" in html
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
    assert '<a class="source" href="/notes/1">Read the full notes →</a>' in html
    assert "Blizzard forums ↗" in html
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
    assert 'class="thumb"' not in html and "blue-tag" not in html


def test_blue_post_card_is_tinted_with_tag_and_tile():
    store = Store(":memory:")
    store.save_update(make_forum_post(), "beta", {"Mage": "m"}, title="Notes", summary="S")
    html = create_app(store).test_client().get("/").text
    assert 'class="entry blue-post"' in html
    assert '<span class="blue-tag">Blue post</span>' in html
    assert 'class="thumb blue-tile"' in html


def test_atom_feed_lists_newest_posts_escaped():
    response = client_for(
        make_post(id=1, title="Old <b>news</b>", published=datetime(2026, 10, 1, tzinfo=UTC)),
        make_post(id=2, title="New news", url="https://worldofwarcraft.blizzard.com/en-us/news/2/new",
                  published=datetime(2026, 10, 2, tzinfo=UTC)),
    ).get("/feed.xml")
    assert response.mimetype == "application/atom+xml"
    xml = response.text
    assert xml.index("New news") < xml.index("Old &lt;b&gt;news&lt;/b&gt;")
    assert "<id>https://worldofwarcraft.blizzard.com/en-us/news/2/new</id>" in xml
    assert "<updated>2026-10-02T00:00:00+00:00</updated>" in xml
    assert "<summary>Summary</summary>" in xml


def test_empty_atom_feed_is_valid():
    assert "<entry>" not in client_for().get("/feed.xml").text


def test_class_feed_has_only_updates_with_changes_for_that_class():
    xml = class_client(
        (make_forum_post(id=1, url="https://us.forums.blizzard.com/en/wow/t/10/1"), "hotfix",
         {"Mage": "<ul><li>Hot Streak longer</li></ul>"}),
        (make_forum_post(id=2, url="https://us.forums.blizzard.com/en/wow/t/10/2"), "beta",
         {"Druid": "<ul><li>Wrath up</li></ul>"}),
    ).get("/classes/mage/feed.xml").text
    assert "<title>Mage: Hotfix, Oct 16</title>" in xml
    assert "<id>https://us.forums.blizzard.com/en/wow/t/10/1#mage</id>" in xml
    assert '<content type="html">&lt;ul&gt;&lt;li&gt;Hot Streak longer&lt;/li&gt;&lt;/ul&gt;</content>' in xml
    assert "Wrath up" not in xml


def test_class_feed_unknown_class_is_404():
    assert client_for().get("/classes/deathknight/feed.xml").status_code == 404


def test_pages_link_their_feeds():
    client = client_for()
    assert 'type="application/atom+xml" title="WoW Forever Tracker" href="/feed.xml"' in client.get("/").text
    assert 'href="/classes/mage/feed.xml"' in client.get("/classes/mage").text


def test_search_index_has_posts_and_plain_text_class_changes():
    store = Store(":memory:")
    store.upsert([make_post(id=1, title="Claim Your Forever Names")])
    store.save_update(make_forum_post(), "hotfix", {"Warrior": "<ul><li><strong>Mortal Strike</strong> &amp; more</li></ul>"})
    client = create_app(store).test_client()
    items = client.get("/search.json").json
    assert {"title": "Claim Your Forever Names", "url": "https://worldofwarcraft.blizzard.com/en-us/news/1/x",
            "label": "News", "date": "Oct 20, 2026", "text": "Summary", "external": True} in items
    assert {"title": "Warrior · Hotfix", "url": "/classes/warrior#hotfix-2026-10-16", "label": "Warrior", "date": "Oct 16, 2026",
            "text": "Mortal Strike & more", "external": False} in items
    page = client.get("/search").text
    assert 'data-index="/search.json"' in page and 'href="/search.json"' in page


def test_forum_posts_carry_their_classes_for_the_my_class_highlight():
    store = Store(":memory:")
    store.save_update(make_forum_post(), "beta", {"Warrior": "w", "Mage": "m"}, title="Beta notes")
    store.upsert([make_post(id=5, title="Plain news")])
    html = create_app(store).test_client().get("/").text
    assert 'class="entry blue-post" data-classes="mage warrior"' in html
    assert html.count("data-classes") == 1


def test_class_page_offers_changes_since_each_older_update():
    html = class_client(
        (make_forum_post(id=1, posted=datetime(2026, 10, 10, 18, tzinfo=UTC)), "beta", {"Mage": "<ul><li>a</li></ul>"}),
        (make_forum_post(id=2, posted=datetime(2026, 10, 12, 18, tzinfo=UTC)), "beta", {"Druid": "<ul><li>b</li></ul>"}),
        (make_forum_post(id=3, posted=datetime(2026, 10, 14, 18, tzinfo=UTC)), "hotfix", {"Mage": "<ul><li>c</li></ul>"}),
    ).get("/classes/mage").text
    # The newest Mage update is offered; the oldest is not, since "since the oldest" is everything.
    assert '<option value="2026-10-14T18:00:00+00:00">Hotfix · Oct 14</option>' in html
    assert "2026-10-10T18" not in html.split("<select>")[1].split("</select>")[0]
    assert 'data-class="mage" data-name="Mage"' in html


def test_plate_links_latest_patch_after_launch(monkeypatch):
    from wowforever import web

    class AfterLaunch(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime(2026, 11, 6, 12, tzinfo=UTC)

    monkeypatch.setattr(web, "datetime", AfterLaunch)
    html = client_for(
        make_post(id=1, title="Hotfixes: November 5", kind="patch", url="https://example.com/hotfix"),
        make_post(id=2, title="Later news", published=datetime(2026, 11, 6, tzinfo=UTC)),
    ).get("/").text
    assert "Live now · Day 3" in html
    assert 'Latest: <a href="https://example.com/hotfix" target="_blank" rel="noopener">Hotfixes: November 5</a>' in html


def test_search_index_has_full_notes_once():
    store = Store(":memory:")
    store.save_update(make_forum_post(), "hotfix", {}, title="WoW Forever Hotfixes – Oct 16",
                      summary="Hotfixes.", html="<p>Hotfixes.</p><ul><li>Ragefire Chasm loot fixed</li></ul>")
    items = create_app(store).test_client().get("/search.json").json
    assert items == [{"title": "WoW Forever Hotfixes – Oct 16", "url": "/notes/1", "label": "Hotfix",
                      "date": "Oct 16, 2026", "text": "Hotfixes. Ragefire Chasm loot fixed", "external": False}]


def test_notes_page_shows_full_notes_and_edits():
    store = Store(":memory:")
    post = make_forum_post()
    store.save_update(post, "hotfix", {}, title="WoW Forever Hotfixes – Oct 16", summary="Hotfixes.",
                      html="<h2>Dungeons</h2><ul><li>Old fix</li></ul>")
    store.save_update(post, "hotfix", {}, title="WoW Forever Hotfixes – Oct 16", summary="Hotfixes.",
                      html="<h2>Dungeons</h2><ul><li>New fix</li></ul>", now=datetime(2026, 10, 17, 20, tzinfo=UTC))
    client = create_app(store).test_client()
    html = client.get("/notes/1").text
    assert "<h1>WoW Forever Hotfixes – Oct 16</h1>" in html
    assert "<h2>Dungeons</h2><ul><li>New fix</li></ul>" in html
    assert "Blizzard edited these notes · seen Oct 17" in html
    assert '<ul class="added"><li>New fix</li></ul>' in html and '<ul class="removed"><li>Old fix</li></ul>' in html
    assert 'href="https://us.forums.blizzard.com/en/wow/t/10/1"' in html
    assert "Updated Oct 17" in client.get("/").text  # the feed card flags the edit
    assert client.get("/notes/2").status_code == 404


def test_notes_page_before_full_notes_are_gathered():
    store = Store(":memory:")
    store.save_update(make_forum_post(), "beta", {}, title="Beta notes", summary="New build.")
    html = create_app(store).test_client().get("/notes/1").text
    assert "New build. The full notes will appear here after the next hourly check" in html


def test_class_anchors_are_stable_when_a_second_update_lands_the_same_day():
    from wowforever.store import ClassUpdate
    from wowforever.web import _anchors

    first = ClassUpdate(1, "hotfix", datetime(2026, 11, 6, 18, tzinfo=UTC), "u1", "x")
    second = ClassUpdate(2, "hotfix", datetime(2026, 11, 6, 22, tzinfo=UTC), "u2", "y")
    assert _anchors([first]) == {1: "hotfix-2026-11-06"}
    assert _anchors([second, first]) == {1: "hotfix-2026-11-06", 2: "hotfix-2026-11-06-2"}


def test_plate_has_a_slot_for_the_local_launch_time():
    assert '<p class="plate-local" hidden></p>' in client_for().get("/").text


def test_menu_links_addons_and_macros():
    html = client_for().get("/").text
    assert 'href="/addons"' in html
    assert 'href="/macros"' in html


def test_addons_page_links_each_addon_to_curseforge():
    html = client_for().get("/addons").text
    assert "Trending right now" in html and "Questing &amp; leveling" in html
    assert 'href="https://www.curseforge.com/wow/addons/questie" target="_blank" rel="noopener"' in html
    assert 'src="/static/addons/questie.png"' in html
    assert "List updated Oct 27, 2026" in html


def test_macros_page_has_a_section_per_class_with_escaped_macro_text():
    html = client_for().get("/macros").text
    for cls in ("general", "druid", "hunter", "mage", "paladin", "priest", "rogue", "shaman", "warlock", "warrior"):
        assert f'<section class="macro-class tab-panel" id="{cls}"' in html
        assert f'href="#{cls}"' in html
    assert "#showtooltip Hunter&#39;s Mark\n/petattack\n/cast Hunter&#39;s Mark" in html
    assert "tabs.js" in html


def test_home_links_latest_known_issues():
    store = Store(":memory:")
    assert "Known Issues" not in create_app(store).test_client().get("/").text
    store.save_update(make_forum_post(id=5, topic_id=11), "known", {}, title="Known Issues", html="<p>Bug</p>")
    html = create_app(store).test_client().get("/").text
    assert "Known Issues" in html and 'href="/notes/5"' in html


def test_notes_page_for_known_issues():
    store = Store(":memory:")
    store.save_update(make_forum_post(id=5, topic_id=11), "known", {}, title="Known Issues", html="<p>Bug</p>")
    response = create_app(store).test_client().get("/notes/5")
    assert response.status_code == 200 and "Known Issues" in response.text
    assert "All patches" not in response.text and 'class="crumb"><a href="/">' in response.text


def test_known_issues_edit_log_heading():
    store = Store(":memory:")
    post = make_forum_post(id=5, topic_id=11)
    store.save_update(post, "known", {}, title="Known Issues", html="<p>Bug</p>")
    store.save_update(post, "known", {}, title="Known Issues", html="<p>Bug 2</p>", now=datetime(2026, 10, 17, 20, tzinfo=UTC))
    text = create_app(store).test_client().get("/notes/5").text
    assert "Blizzard edited this list" in text and "these notes" not in text


def blue_client(*staff):
    store = Store(":memory:")
    store.add_blue_posts(staff)
    return create_app(store).test_client()


def test_blue_page_lists_posts_newest_first():
    old = make_staff(id=1, thread_title="Older thread", excerpt="Old words", url="https://f/1",
                     posted=datetime(2026, 10, 1, 12, tzinfo=UTC))
    new = make_staff(id=2, thread_title="Newer thread", excerpt="New words", url="https://f/2",
                     posted=datetime(2026, 10, 5, 12, tzinfo=UTC))
    html = blue_client(old, new).get("/blue").text
    assert "WoW Forever Blue Posts · WoW Forever Tracker" in html
    assert html.index("Newer thread") < html.index("Older thread")
    assert "Kaivax" in html and "Community Manager" in html
    assert "New words" in html and "Oct 5, 2026" in html
    assert 'href="https://f/2"' in html and "Read on the forums" in html
    assert 'href="/blue/feed.xml"' in html


def test_blue_page_empty():
    response = blue_client().get("/blue")
    assert response.status_code == 200
    assert EMPTY in response.text


def test_blue_pagination_404_past_end():
    posts = [make_staff(id=i, url=f"https://f/{i}", posted=datetime(2026, 10, 1, tzinfo=UTC) + timedelta(hours=i))
             for i in range(1, 22)]
    client = blue_client(*posts)
    assert '"/blue/page/2/"' in client.get("/blue").text
    assert client.get("/blue/page/2/").status_code == 200
    assert client.get("/blue/page/3/").status_code == 404
    assert client.get("/blue/page/1/").status_code == 404
    assert blue_client().get("/blue/page/2/").status_code == 404


def test_blue_feed_is_atom():
    response = blue_client(make_staff(thread_title="A <b> thread", url="https://f/1")).get("/blue/feed.xml")
    assert response.mimetype == "application/atom+xml"
    assert "<id>https://f/1</id>" in response.text
    assert "Kaivax: A &lt;b&gt; thread" in response.text


def test_nav_has_blue_posts():
    assert 'href="/blue">Blue posts</a>' in client_for().get("/").text


def realm_client(us_checked=None, eu_checked=None):
    store = Store(":memory:")
    store.save_realms("us", [Realm("us", "Zeta", "PvE", False, "Low"), Realm("us", "Alpha", "PvP", True, "High")],
                      now=us_checked)
    store.save_realms("eu", [Realm("eu", "Beta", "RP", True, "Full")], now=eu_checked)
    return create_app(store).test_client()


def test_realms_page_lists_regions_and_status():
    response = realm_client().get("/realms")
    html = response.text
    assert response.status_code == 200
    assert "<title>WoW Forever Realm Status · WoW Forever Tracker</title>" in html
    assert "Americas" in html and "Europe" in html
    assert html.index("Alpha") < html.index("Zeta")
    assert ">Up<" in html and ">Down<" in html
    assert "Checked" in html and "<time datetime=" in html
    assert ">Realms</a>" in html
    assert "isn't answering" not in html


def test_realms_page_404_and_no_nav_without_data():
    client = client_for()
    assert client.get("/realms").status_code == 404
    assert ">Realms</a>" not in client.get("/").text


def test_realms_page_warns_when_stale():
    html = realm_client(us_checked=datetime.now(UTC) - timedelta(hours=2)).get("/realms").text
    assert "Last checked 2 hours ago; Blizzard's API isn't answering right now." in html
    html = realm_client(us_checked=datetime.now(UTC) - timedelta(minutes=45)).get("/realms").text
    assert "Last checked 45 minutes ago" in html


def test_class_page_has_tabs_for_changes_abilities_talents_and_macros():
    html = client_for().get("/classes/hunter").text
    for tab in ("changes", "abilities", "talents", "macros"):
        assert f'<section class="tab-panel' in html and f'id="{tab}"' in html
        assert f'href="#{tab}"' in html
    assert '<span class="spell">Arcane Shot</span>' in html
    assert 'src="/static/icons/' in html
    assert "Marksmanship" in html and 'class="talent has-tip"' in html and 'class="talent-data"' in html
    assert "#showtooltip Hunter&#39;s Mark" in html
    assert "From the WoW Forever game client" in html


def test_guides_menu_links_races_professions_addons_and_macros():
    html = client_for().get("/").text
    assert "Guides ▾" in html
    for path in ("/races", "/professions", "/addons", "/macros"):
        assert f'href="{path}"' in html


def test_races_page_lists_racials():
    html = client_for().get("/races").text
    assert 'id="high-order-skyborne"' in html
    assert '<span class="spell">Stoneform</span>' in html
    assert 'src="/static/icons/race-dwarf.png"' in html
    assert "Artisan&#39;s Precision" in html and "Updated: " in html
    assert "From the WoW Forever game client" in html


def test_profession_pages():
    client = client_for()
    assert 'href="/professions/first-aid"' in client.get("/professions").text
    html = client.get("/professions/tailoring").text
    assert '>Bolt of Linen Cloth</span>' in html and 'id="apprentice"' in html and 'role="tooltip"' in html
    assert "the game files don't say what skill a trainer asks" in html
    assert client.get("/professions/underwater-basket-weaving").status_code == 404


def test_realm_history_is_kept_30_days_and_drawn_as_a_week_of_blocks():
    from wowforever.web import _population_strip

    store = Store(":memory:")
    start = datetime(2026, 11, 1, tzinfo=UTC)
    for hours, up, population in [(0, True, "Low"), (1, True, "High"), (24 * 31, True, "Medium"),
                                   (24 * 31 + 1, False, "Medium"), (24 * 31 + 2, True, "Full")]:
        store.save_realms("us", [Realm("us", "Alpha", "PvP", up, population)], now=start + timedelta(hours=hours))
    now = start + timedelta(hours=24 * 31 + 3)
    history = store.realm_history(start)[("us", "Alpha")]
    assert [p for _, _, p in history] == ["Medium", "Medium", "Full"]  # the first day's checks are over 30 days old

    strip = _population_strip(history, now)
    blocks = strip["blocks"]
    assert len(blocks) == 84 and blocks[-1]["css"] == "full"
    assert blocks[-2]["css"] == "down"  # 00:00-02:00: down at one check
    assert blocks[-2]["title"] == "Wed Dec 2, 00:00–02:00 UTC: Down"
    assert blocks[0]["css"] == "none" and blocks[0]["title"].endswith("UTC: not checked")
    assert strip["summary"] == "last 7 days in two-hour blocks: mostly Full, down in 1 of them"


def test_realms_page_draws_each_realms_week():
    store = Store(":memory:")
    store.save_realms("us", [Realm("us", "Alpha", "PvP", True, "High")])
    html = create_app(store).test_client().get("/realms").text
    assert html.count('class="pop-high"') >= 2  # the legend and the latest block
    assert 'aria-label="Alpha, last 7 days in two-hour blocks: mostly High"' in html
