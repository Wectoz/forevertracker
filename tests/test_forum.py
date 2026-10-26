import json
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

import pytest

from wowforever.blizzard import FetchError, ParseError
from wowforever.forum import fetch_json, note_topics, thread_posts, topic_kind

FIXTURES = Path(__file__).parent / "fixtures"


def load(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def fake_fetch(mapping):
    def fetch(path):
        assert path in mapping, f"unexpected fetch: {path}"
        return mapping[path]
    return fetch


def test_note_topics_picks_staff_notes_threads_only():
    topics = note_topics(load("forum_category.json"))
    # "Thank You For Testing" and "Known Issues" have no "notes"; the player thread is not staff.
    assert [(t.id, t.kind) for t in topics] == [(2360696, "beta")]


def test_note_topics_ignores_notes_threads_started_by_players():
    category = load("forum_category.json")
    for topic in category["topic_list"]["topics"]:
        if topic["id"] == 2392000:
            topic["title"] = "My patch notes wishlist"
    assert [t.id for t in note_topics(category)] == [2360696]


def test_topic_kind():
    assert topic_kind("WoW Forever Hotfixes – November 12") == "hotfix"
    assert topic_kind("WoW Forever Beta Development Notes") == "beta"
    assert topic_kind("WoW Forever 1.60 Patch Notes") == "patch"


def test_thread_posts_skips_empty_posts():
    posts = thread_posts(2360696, fake_fetch({"/t/2360696.json": load("forum_thread.json")}))
    assert [p.number for p in posts] == [1, 4, 5, 6]
    assert posts[0].posted.date() == date(2026, 9, 24)
    assert posts[0].url == "https://us.forums.blizzard.com/en/wow/t/2360696/1"
    assert posts[0].topic_id == 2360696
    assert "Hot Streak" in posts[0].cooked


def test_thread_posts_fetches_posts_not_inline():
    thread = load("forum_thread.json")
    later = thread["post_stream"]["posts"][3:]
    thread["post_stream"]["posts"] = thread["post_stream"]["posts"][:3]
    ids = "&".join(f"post_ids[]={p['id']}" for p in later)
    fetch = fake_fetch({"/t/2360696.json": thread,
                        f"/t/2360696/posts.json?{ids}": {"post_stream": {"posts": later}}})
    assert [p.number for p in thread_posts(2360696, fetch)] == [1, 4, 5, 6]


def test_thread_posts_ignores_non_staff_posts():
    thread = load("forum_thread.json")
    thread["post_stream"]["posts"][3]["staff"] = False
    posts = thread_posts(2360696, fake_fetch({"/t/2360696.json": thread}))
    assert [p.number for p in posts] == [1, 5, 6]


def test_bad_shape_raises_parse_error():
    with pytest.raises(ParseError):
        thread_posts(1, fake_fetch({"/t/1.json": {"nope": 1}}))
    with pytest.raises(ParseError):
        note_topics({"topic_list": None})


def test_fetch_json_wraps_network_errors(monkeypatch):
    def boom(*args, **kwargs):
        raise urllib.error.URLError("down")
    monkeypatch.setattr(urllib.request, "urlopen", boom)
    with pytest.raises(FetchError):
        fetch_json("/c/349.json")


def test_fetch_json_wraps_broken_responses(monkeypatch):
    import http.client

    def broken(*args, **kwargs):
        raise http.client.IncompleteRead(b"partial")
    monkeypatch.setattr(urllib.request, "urlopen", broken)
    with pytest.raises(FetchError):
        fetch_json("/c/349.json")
