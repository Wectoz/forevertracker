from datetime import UTC, datetime

import pytest

from wowforever import cli
from wowforever.blizzard import FetchError
from wowforever.discord import PER_RUN, announce, message, webhook_sender
from wowforever.store import Store

from .test_store import make_post


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
