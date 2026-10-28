"""Fetch Blizzard's WoW news listing and read the post data embedded in it."""

import http.client
import json
import re
import urllib.error
import urllib.request
from dataclasses import dataclass

BASE_URL = "https://worldofwarcraft.blizzard.com/en-us"
USER_AGENT = "WoWForeverTracker/0.1 (unofficial fan site)"
TIMEOUT = 15

_MODEL_RE = re.compile(r'<script id="model">\s*model\s*=\s*(.*?)</script>', re.S)


class ParseError(Exception):
    """The listing page did not have the structure we expect."""


class FetchError(Exception):
    """The listing page could not be downloaded."""


@dataclass(frozen=True)
class ListingPage:
    blogs: list[dict]
    has_next: bool


def parse_listing(html: str) -> ListingPage:
    match = _MODEL_RE.search(html)
    if not match:
        raise ParseError("news model script not found")
    try:
        model, _ = json.JSONDecoder().raw_decode(match.group(1))
        blogs = model["blogList"]["blogs"]
        has_next = bool((model.get("paginationLinks") or {}).get("next"))
    except (ValueError, KeyError, TypeError) as err:
        raise ParseError(f"unexpected news model: {err}") from err
    if not isinstance(blogs, list):
        raise ParseError("blogList.blogs is not a list")
    return ListingPage(blogs=blogs, has_next=has_next)


MAX_IMAGE_BYTES = 2_000_000


def fetch_image(url: str) -> tuple[str, bytes]:
    """A news card image, as (type, bytes); anything that is not a small image is refused."""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            mimetype = response.headers.get_content_type()
            data = response.read(MAX_IMAGE_BYTES + 1)
    except (urllib.error.URLError, http.client.HTTPException, TimeoutError, OSError) as err:
        raise FetchError(f"{url}: {err}") from err
    if not mimetype.startswith("image/") or len(data) > MAX_IMAGE_BYTES:
        raise FetchError(f"{url}: not a small image ({mimetype}, {len(data)} bytes)")
    return mimetype, data


def fetch_listing(page: int) -> str:
    url = f"{BASE_URL}/news?page={page}"
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            return response.read().decode("utf-8")
    except (urllib.error.URLError, http.client.HTTPException, TimeoutError, OSError, UnicodeDecodeError) as err:
        raise FetchError(f"{url}: {err}") from err
