"""Gather WoW Forever posts from Blizzard into the store."""

import logging
import threading
import time
from collections.abc import Callable
from datetime import UTC, datetime

from wowforever.blizzard import FetchError, ParseError, fetch_listing, parse_listing
from wowforever.posts import to_post
from wowforever.store import Store

logger = logging.getLogger(__name__)

# Before the WoW Forever announcement and beta, so backfill covers every Forever post.
BACKFILL_CUTOFF = datetime(2026, 8, 1, tzinfo=UTC)

Fetch = Callable[[int], str]


def _gather_page(store: Store, fetch: Fetch, page: int) -> tuple[int, int, bool, datetime | None]:
    listing = parse_listing(fetch(page))
    posts = []
    oldest = None
    for blog in listing.blogs:
        try:
            published = datetime.fromisoformat(blog["published"])
            post = to_post(blog)
        except (KeyError, ValueError, TypeError) as err:
            logger.warning("Skipping malformed Blizzard post %r: %r", blog.get("id"), err)
            continue
        oldest = published if oldest is None else min(oldest, published)
        if post:
            posts.append(post)
    added, edited = store.upsert(posts)
    return added, edited, listing.has_next, oldest


def fetch_latest(store: Store, fetch: Fetch | None = None) -> tuple[int, int]:
    added, edited, _, _ = _gather_page(store, fetch or fetch_listing, 1)
    return added, edited


def backfill(store: Store, fetch: Fetch | None = None, cutoff: datetime = BACKFILL_CUTOFF,
             max_pages: int = 40, delay: float = 1.0) -> tuple[int, int]:
    fetch = fetch or fetch_listing
    total_added = total_edited = 0
    for page in range(1, max_pages + 1):
        if page > 1 and delay:
            time.sleep(delay)
        added, edited, has_next, oldest = _gather_page(store, fetch, page)
        total_added += added
        total_edited += edited
        if not has_next or oldest is None or oldest < cutoff:
            break
    return total_added, total_edited


def start_hourly(store: Store, interval: float = 3600, fetch: Fetch | None = None) -> threading.Thread:
    def run():
        while True:
            try:
                added, edited = fetch_latest(store, fetch)
                logger.info("Gathered: added %d, updated %d WoW Forever posts", added, edited)
            except (FetchError, ParseError) as err:
                logger.warning("Gathering failed: %s", err)
            except Exception:
                # Keep the hourly check alive; stored posts are untouched by a failed run.
                logger.exception("Gathering failed unexpectedly")
            time.sleep(interval)

    thread = threading.Thread(target=run, name="hourly-gather", daemon=True)
    thread.start()
    return thread
