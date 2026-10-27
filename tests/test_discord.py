from datetime import UTC, datetime

import pytest

from wowforever import cli
from wowforever.blizzard import FetchError
from wowforever.discord import BLUE, PER_RUN, announce, blue_message, message, webhook_sender
from wowforever.store import Store

from .test_store import make_post, make_staff


def day(n):
    return datetime(2026, 10, n, tzinfo=UTC)


def store_with(*days):
    store = Store(":memory:")
    store.upsert(make_post(id=n, url=f"https://x/{n}", title=f"Post {n}", published=day(n)) for n in days)
    return store


def test_first_run_records_existing_posts_without_posting():
    store, sent = store_with(1, 2), []
    assert announce(store, sent.append, delay=0) == 0
    assert sent == []
    assert announce(store, sent.append, delay=0) == 0


def test_new_posts_are_announced_once_oldest_first():
    store, sent = store_with(1), []
    announce(store, sent.append, delay=0)
    store.upsert([make_post(id=3, url="https://x/3", title="Post 3", published=day(3)),
                  make_post(id=2, url="https://x/2", title="Post 2", published=day(2))])
    assert announce(store, sent.append, delay=0) == 2
    assert [m["embeds"][0]["title"] for m in sent] == ["Post 2", "Post 3"]
    assert announce(store, sent.append, delay=0) == 0


def test_a_failed_post_is_retried_next_run_and_earlier_ones_are_not_repeated():
    store, sent = store_with(1), []
    announce(store, sent.append, delay=0)
    store.upsert([make_post(id=n, url=f"https://x/{n}", published=day(n)) for n in (2, 3)])

    def flaky(payload):
        if sent:
            raise FetchError("down")
        sent.append(payload)

    with pytest.raises(FetchError):
        announce(store, flaky, delay=0)
    assert len(sent) == 1
    assert [p.url for p in store.unannounced()] == ["https://x/3"]


def test_at_most_a_few_posts_per_run():
    store, sent = store_with(1), []
    announce(store, sent.append, delay=0)
    store.upsert(make_post(id=n, url=f"https://x/{n}", published=datetime(2026, 11, n, tzinfo=UTC))
                 for n in range(2, 2 + PER_RUN + 3))
    assert announce(store, sent.append, delay=0) == PER_RUN
    assert announce(store, sent.append, delay=0) == 3


def test_message_never_pings_anyone():
    store = Store(":memory:")
    store.upsert([make_post(title="@everyone patch is out")])
    payload = message(store.list_posts()[0])
    assert payload["allowed_mentions"] == {"parse": []}
    assert payload["embeds"][0]["title"] == "@everyone patch is out"


def test_only_discord_webhook_urls_are_accepted():
    with pytest.raises(ValueError):
        webhook_sender("https://example.com/hook")
    webhook_sender("https://discord.com/api/webhooks/1/abc")


def test_cli_announce_without_webhook_does_nothing(monkeypatch, tmp_path, capsys):
    monkeypatch.delenv("DISCORD_WEBHOOK_URL", raising=False)
    assert cli.main(["--db", str(tmp_path / "db.sqlite3"), "announce"]) == 0
    assert "DISCORD_WEBHOOK_URL is not set" in capsys.readouterr().out


def staff_at(n):
    return make_staff(id=n, url=f"https://f/{n}", thread_title=f"Thread {n}", posted=day(n))


def test_blue_message_shape():
    payload = blue_message(make_staff(author="Kaivax", thread_title="Thread", excerpt="Words"))
    embed = payload["embeds"][0]
    assert payload["allowed_mentions"] == {"parse": []}
    assert embed["title"] == "Kaivax: Thread" and embed["color"] == BLUE
    assert embed["description"] == "Words" and embed["footer"]["text"] == "Blue post · Blizzard forums"
    assert len(blue_message(make_staff(thread_title="x" * 400))["embeds"][0]["title"]) == 256


def test_blue_posts_announced_once():
    store, sent = store_with(1), []
    announce(store, sent.append, delay=0)
    store.add_blue_posts([staff_at(3), staff_at(2)])
    assert announce(store, sent.append, delay=0) == 2
    assert [m["embeds"][0]["title"] for m in sent] == ["Kaivax: Thread 2", "Kaivax: Thread 3"]
    assert announce(store, sent.append, delay=0) == 0


def test_first_run_marks_blue_posts_without_posting():
    store, sent = store_with(1), []
    store.add_blue_posts([staff_at(2)])
    assert announce(store, sent.append, delay=0) == 0
    assert store.unannounced_blue_posts() == []
    assert announce(store, sent.append, delay=0) == 0
    assert sent == []


def test_per_run_limit_counts_blue_posts():
    store, sent = store_with(1), []
    announce(store, sent.append, delay=0)
    store.upsert([make_post(id=n, url=f"https://x/{n}", published=datetime(2026, 11, n, tzinfo=UTC))
                  for n in (2, 3)])
    store.add_blue_posts([staff_at(n) for n in range(10, 10 + PER_RUN)])
    assert announce(store, sent.append, delay=0) == PER_RUN
    assert [m["embeds"][0]["url"] for m in sent[:2]] == ["https://x/2", "https://x/3"]
    assert len(store.unannounced_blue_posts()) == 2
