"""Announce new WoW Forever posts in a Discord channel through a webhook."""

import http.client
import json
import logging
import time
import urllib.error
import urllib.request
from collections.abc import Callable

from wowforever.blizzard import TIMEOUT, USER_AGENT, FetchError
from wowforever.forum import StaffPost
from wowforever.store import StoredPost, Store

logger = logging.getLogger(__name__)

WEBHOOK_PREFIXES = ("https://discord.com/api/webhooks/", "https://discordapp.com/api/webhooks/")
PER_RUN = 10  # more than this in one hour is more likely a glitch than news; the rest wait for the next run
BLUE, BRONZE = 0x3D6FB0, 0xD9A35B

Send = Callable[[dict], None]


def message(post: StoredPost) -> dict:
    return {
        "username": "WoW Forever Tracker",
        "allowed_mentions": {"parse": []},  # a post title must never ping @everyone
        "embeds": [{
            "title": post.title[:256],
            "url": post.url,
            "description": post.summary[:4000],
            "color": BLUE if post.on_forums else BRONZE,
            "timestamp": post.published.isoformat(),
            "footer": {"text": "Blue post · Blizzard forums" if post.on_forums else "Blizzard news"},
        }],
    }


def blue_message(post: StaffPost) -> dict:
    return {
        "username": "WoW Forever Tracker",
        "allowed_mentions": {"parse": []},
        "embeds": [{
            "title": f"{post.author}: {post.thread_title}"[:256],
            "url": post.url,
            "description": post.excerpt[:4000],
            "color": BLUE,
            "timestamp": post.posted.isoformat(),
            "footer": {"text": "Blue post · Blizzard forums"},
        }],
    }


def webhook_sender(url: str) -> Send:
    if not url.startswith(WEBHOOK_PREFIXES):
        raise ValueError("not a Discord webhook URL")

    def send(payload: dict) -> None:
        request = urllib.request.Request(
            url, data=json.dumps(payload).encode(), method="POST",
            headers={"Content-Type": "application/json", "User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT):
                pass
        except (urllib.error.URLError, http.client.HTTPException, TimeoutError, OSError) as err:
            raise FetchError(f"Discord webhook: {err}") from err  # never log the URL: it is the secret

    return send


def announce(store: Store, send: Send, delay: float = 1.0) -> int:
    """Post every feed post, then every blue post, not announced yet, oldest first; returns how many were posted.

    The first run only records what is already there, so connecting a webhook (or rebuilding the
    database) does not flood the channel with old posts."""
    pending = store.unannounced()
    if pending is None:
        store.mark_announced(p.url for p in store.list_posts(limit=-1))
        store.mark_blue_announced(p.id for p in store.list_blue_posts(limit=-1))
        logger.info("First Discord run: recorded existing posts without announcing them")
        return 0
    posted = 0
    for post in pending[:PER_RUN]:
        if posted and delay:
            time.sleep(delay)
        send(message(post))
        store.mark_announced([post.url])  # one at a time, so a failure part-way never repeats a post
        posted += 1
    for blue in store.unannounced_blue_posts()[:PER_RUN - posted]:
        if posted and delay:
            time.sleep(delay)
        send(blue_message(blue))
        store.mark_blue_announced([blue.id])
        posted += 1
    return posted
