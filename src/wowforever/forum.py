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

FORUM_URL = "https://us.forums.blizzard.com/en/wow"
CATEGORY_ID = 349  # WoW Forever
_NOTES_TITLE_RE = re.compile(r"(?i)\b(notes|hotfix(es)?)\b")
_BATCH = 20

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


def fetch_json(path: str) -> dict:
    url = FORUM_URL + path
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            return json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, http.client.HTTPException, TimeoutError, OSError, UnicodeDecodeError, ValueError) as err:
        raise FetchError(f"{url}: {err}") from err


def topic_kind(title: str) -> str:
    lowered = title.lower()
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


def thread_posts(topic_id: int, fetch: FetchJson) -> list[ForumPost]:
    try:
        stream = fetch(f"/t/{topic_id}.json")["post_stream"]
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
                url=f"{FORUM_URL}/t/{topic_id}/{p['post_number']}",
            )
            for p in raw
            if p.get("staff") and (p.get("cooked") or "").strip()
        ]
    except (KeyError, TypeError, ValueError) as err:
        raise ParseError(f"unexpected forum thread {topic_id}: {err!r}") from err
    return sorted(posts, key=lambda p: p.number)
