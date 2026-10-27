"""Read Blizzard's WoW Forever notes threads (beta notes, patch notes, hotfixes) from the forums."""

import http.client
import json
import re
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from wowforever.blizzard import TIMEOUT, USER_AGENT, FetchError, ParseError
from wowforever.countdown import PACIFIC
from wowforever.posts import make_summary

FORUM_URL = "https://us.forums.blizzard.com/en/wow"
CATEGORY_ID = 349  # WoW Forever
_NOTES_TITLE_RE = re.compile(r"(?i)\b(notes|hotfix(es)?|known issues)\b")
_BATCH = 20
FOREVER_CATEGORIES = frozenset({346, 347, 348, 349})  # the WoW Forever forum categories
TRACKER_PATH = "/groups/blizzard-tracker/posts.json"
_NEWS_ACCOUNT = "BlizzardEntertainment"  # the corporate news account, not a staff voice
# "WoW Forever Beta Development Notes – Updated October 15" → "WoW Forever Beta Development Notes"
_TITLE_DATE_RE = re.compile(r"\s*[–—-]\s*(?:updated\s+)?[a-z]+\.?\s+\d{1,2}(?:,?\s+\d{4})?\s*$", re.I)
_FIRST_PARAGRAPH_RE = re.compile(r"<p>(.*?)</p>", re.S)

FetchJson = Callable[[str], dict]


@dataclass(frozen=True)
class NoteTopic:
    id: int
    title: str
    kind: str  # "beta" | "patch" | "hotfix"


@dataclass(frozen=True)
class ForumPost:
    id: int
    topic_id: int
    number: int
    cooked: str
    posted: datetime
    url: str
    thread_title: str


@dataclass(frozen=True)
class StaffPost:
    id: int
    topic_id: int
    number: int
    author: str
    author_title: str
    thread_title: str
    excerpt: str
    posted: datetime
    url: str


def fetch_json(path: str) -> dict:
    url = FORUM_URL + path
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            return json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, http.client.HTTPException, TimeoutError, OSError, UnicodeDecodeError, ValueError) as err:
        raise FetchError(f"{url}: {err}") from err


def is_known_issues(title: str) -> bool:
    return "known issues" in title.lower()


def topic_kind(title: str) -> str:
    lowered = title.lower()
    if is_known_issues(title):
        return "known"
    if "hotfix" in lowered:
        return "hotfix"
    if "beta" in lowered:
        return "beta"
    return "patch"


def note_topics(category: dict) -> list[NoteTopic]:
    try:
        staff = {u["id"] for u in category.get("users") or [] if u.get("admin") or u.get("moderator")}
        topics = []
        for topic in category["topic_list"]["topics"]:
            posters = topic.get("posters") or []
            started_by_staff = bool(posters) and posters[0].get("user_id") in staff
            if started_by_staff and _NOTES_TITLE_RE.search(topic["title"]):
                topics.append(NoteTopic(int(topic["id"]), topic["title"], topic_kind(topic["title"])))
    except (KeyError, TypeError, ValueError, AttributeError) as err:
        raise ParseError(f"unexpected forum category: {err!r}") from err
    return topics


def feed_title(post: ForumPost) -> str:
    """The thread's name without its date, plus this post's date: one title per build or hotfix post."""
    day = post.posted.astimezone(PACIFIC)
    return f"{_TITLE_DATE_RE.sub('', post.thread_title)} – {day:%b} {day.day}"


def feed_summary(cooked: str) -> str:
    """The post's opening paragraph, e.g. "Today, we updated the WoW Forever Beta with a new build…"."""
    first = _FIRST_PARAGRAPH_RE.search(cooked)
    return make_summary(first.group(1) if first else cooked)


def thread_posts(topic_id: int, fetch: FetchJson) -> list[ForumPost]:
    try:
        thread = fetch(f"/t/{topic_id}.json")
        title = thread.get("title") or ""
        stream = thread["post_stream"]
        raw = list(stream["posts"])
        have = {p["id"] for p in raw}
        missing = [i for i in stream["stream"] if i not in have]
        for start in range(0, len(missing), _BATCH):
            ids = "&".join(f"post_ids[]={i}" for i in missing[start:start + _BATCH])
            raw += fetch(f"/t/{topic_id}/posts.json?{ids}")["post_stream"]["posts"]
        posts = [
            ForumPost(
                id=int(p["id"]), topic_id=topic_id, number=int(p["post_number"]), cooked=p["cooked"],
                posted=datetime.fromisoformat(p["created_at"]),
                url=f"{FORUM_URL}/t/{topic_id}/{p['post_number']}", thread_title=title,
            )
            for p in raw
            if p.get("staff") and (p.get("cooked") or "").strip()
        ]
    except (KeyError, TypeError, ValueError, AttributeError) as err:
        raise ParseError(f"unexpected forum thread {topic_id}: {err!r}") from err
    return sorted(posts, key=lambda p: p.number)


def tracker_page(fetch: FetchJson, before: int | None = None) -> tuple[list[StaffPost], int | None, datetime | None]:
    """One page (20 posts, newest first) of Blizzard staff posts in the WoW Forever categories, plus the
    id to pass as `before` for the next page (the last post of the unfiltered page, None when it is empty)
    and the oldest `created_at` on the unfiltered page (None when it is empty)."""
    path = TRACKER_PATH if before is None else f"{TRACKER_PATH}?before_post_id={before}"
    try:
        raw = fetch(path)["posts"]
        posts = [
            StaffPost(
                id=int(p["id"]), topic_id=int(p["topic_id"]), number=int(p["post_number"]),
                author=p["username"], author_title=p.get("user_title") or "",
                thread_title=p["topic_title"], excerpt=make_summary(p.get("excerpt") or ""),
                posted=datetime.fromisoformat(p["created_at"]),
                url=f"{FORUM_URL}/t/{p['topic_id']}/{p['post_number']}",
            )
            for p in raw
            if p["category_id"] in FOREVER_CATEGORIES and p["username"] != _NEWS_ACCOUNT
        ]
        next_before = int(raw[-1]["id"]) if raw else None
        oldest = min((datetime.fromisoformat(p["created_at"]) for p in raw), default=None)
    except (KeyError, TypeError, ValueError, AttributeError) as err:
        raise ParseError(f"unexpected forum tracker page: {err!r}") from err
    return posts, next_before, oldest
