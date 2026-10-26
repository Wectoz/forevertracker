from datetime import UTC, datetime
from pathlib import Path

from wowforever.blizzard import parse_listing
from wowforever.posts import make_summary, to_post

FIXTURES = Path(__file__).parent / "fixtures"


def blog(**overrides):
    data = {
        "id": 1,
        "title": "X",
        "url": "/news/1/x",
        "description": "",
        "category": None,
        "tags": [],
        "keywords": [],
        "published": "2026-10-22T15:44:03.763Z",
        "updated": "2026-10-22T15:44:03.763Z",
    }
    data.update(overrides)
    return data


def test_non_forever_post_is_dropped():
    assert to_post(blog(title="Midnight's 12.1.5 Content Update is Now Live")) is None


def test_forever_news():
    post = to_post(blog(title="Claim Your World of Warcraft: Forever Character Names"))
    assert post.kind == "news"
    assert post.version is None
    assert post.url == "https://worldofwarcraft.blizzard.com/en-us/news/1/x"
    assert post.published == datetime(2026, 10, 22, 15, 44, 3, 763000, tzinfo=UTC)


def test_forever_in_description_counts():
    post = to_post(
        blog(
            title="Hotfixes: November 6, 2026",
            description="Hotfixes for World of Warcraft: Forever and Classic Era.",
            tags=["hotfixes"],
        )
    )
    assert post.kind == "patch"
    assert post.version is None


def test_forever_patch_version_from_title():
    post = to_post(blog(title="World of Warcraft: Forever Patch 1.60.1 Notes", tags=["patch notes"]))
    assert post.kind == "patch"
    assert post.version == "1.60.1"


def test_forever_patch_version_from_category():
    post = to_post(blog(title="WoW: Forever Patch Notes", category="1.61"))
    assert post.kind == "patch"
    assert post.version == "1.61"


def test_classic_and_retail_versions_ignored():
    classic = to_post(blog(title="WoW: Forever Patch Notes", category="1.15.8"))
    retail = to_post(blog(title="WoW: Forever and 12.1.5 Hotfixes", tags=["hotfixes"]))
    assert classic.version is None
    assert retail.version is None


def test_summary_strips_html_and_truncates():
    assert make_summary("<p>Fish &amp; Chips®</p>") == "Fish & Chips®"
    long = " ".join(["word"] * 80)  # 399 chars
    summary = make_summary(long)
    assert len(summary) <= 301
    assert summary.endswith("…")
    assert summary[:-1].split(" ")[-1] == "word"


def test_fixture_pages_yield_only_forever_posts():
    posts = []
    for name in ("news_page1.html", "news_page2.html"):
        html = (FIXTURES / name).read_text(encoding="utf-8")
        posts += [p for p in map(to_post, parse_listing(html).blogs) if p]
    assert len(posts) >= 5
    for post in posts:
        assert "forever" in (post.title + post.summary).lower()
    assert not any("Midnight's 12.1.5" in p.title for p in posts)
