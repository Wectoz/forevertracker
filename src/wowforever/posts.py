"""Turn raw Blizzard blog entries into WoW Forever posts."""

import html
import re
from dataclasses import dataclass
from datetime import datetime

from wowforever.blizzard import BASE_URL

PATCH_TAGS = {"patch notes", "hotfixes", "update notes"}
_PATCH_TITLE_RE = re.compile(r"(?i)\b(patch notes|hotfixes)\b")
# WoW Forever patches are 1.60 and up; Classic Era (1.15.x) and retail (12.x) are not.
_VERSION_RE = re.compile(r"(?<![\d.])1\.(\d{2,})(?:\.\d+)?(?![\d.]*\d)")
_TAG_RE = re.compile(r"<[^>]+>")
# Thumbnails are only kept as plain https URLs, since they go straight into an <img src>.
_SAFE_URL_RE = re.compile(r"https://[^\s\"'<>]+")
# The game's name, not the bare word "forever" (e.g. "remain in combat forever").
_FOREVER_RE = re.compile(r"(?i)\b(?:wow|warcraft):?\s+forever\b")


@dataclass(frozen=True)
class Post:
    id: int
    title: str
    url: str
    summary: str
    kind: str  # "news" | "patch"
    version: str | None
    published: datetime
    updated: datetime
    thumbnail: str | None  # the article's header image


def make_summary(text: str, limit: int = 300) -> str:
    plain = " ".join(html.unescape(_TAG_RE.sub(" ", text or "")).split())
    if len(plain) <= limit:
        return plain
    cut = plain.rfind(" ", 0, limit + 1)
    return plain[: cut if cut > 0 else limit] + "…"


def _is_forever(blog: dict) -> bool:
    keywords = blog.get("keywords") or []
    if isinstance(keywords, str):
        keywords = [keywords]
    text = " ".join([blog.get("title") or "", blog.get("description") or "", *map(str, keywords)])
    return bool(_FOREVER_RE.search(text))


def _is_patch(blog: dict) -> bool:
    tags = {str(t).lower() for t in blog.get("tags") or []}
    return bool(tags & PATCH_TAGS) or bool(_PATCH_TITLE_RE.search(blog.get("title") or ""))


def _version(blog: dict) -> str | None:
    for text in (blog.get("title") or "", blog.get("category") or ""):
        for match in _VERSION_RE.finditer(str(text)):
            if int(match.group(1)) >= 60:
                return match.group(0)
    return None


def _thumbnail(blog: dict) -> str | None:
    for key in ("thumbnail", "image"):
        image = blog.get(key)
        url = image.get("url") if isinstance(image, dict) else None
        if not isinstance(url, str):
            continue
        url = "https:" + url if url.startswith("//") else url
        if _SAFE_URL_RE.fullmatch(url):
            return url
    return None


def to_post(blog: dict) -> Post | None:
    if not _is_forever(blog):
        return None
    is_patch = _is_patch(blog)
    return Post(
        id=int(blog["id"]),
        title=make_summary(blog["title"], limit=1000),
        url=BASE_URL + blog["url"],
        summary=make_summary(blog.get("description") or ""),
        kind="patch" if is_patch else "news",
        version=_version(blog) if is_patch else None,
        published=datetime.fromisoformat(blog["published"]),
        updated=datetime.fromisoformat(blog.get("updated") or blog["published"]),
        thumbnail=_thumbnail(blog),
    )
