import urllib.error
import urllib.request
from pathlib import Path

import pytest

from wowforever.blizzard import FetchError, ParseError, fetch_listing, parse_listing

FIXTURES = Path(__file__).parent / "fixtures"


def load(name):
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_parse_listing_reads_blogs():
    page = parse_listing(load("news_page1.html"))
    assert len(page.blogs) >= 10
    for blog in page.blogs:
        assert {"id", "title", "url", "description", "published"} <= blog.keys()
    assert page.has_next is True
    assert any("World of Warcraft: Forever" in b["title"] for b in page.blogs)


def test_parse_listing_page2_differs():
    ids1 = {b["id"] for b in parse_listing(load("news_page1.html")).blogs}
    ids2 = {b["id"] for b in parse_listing(load("news_page2.html")).blogs}
    assert ids2 - ids1


def test_parse_listing_without_model_raises():
    with pytest.raises(ParseError):
        parse_listing("<html></html>")


def test_parse_listing_bad_json_raises():
    with pytest.raises(ParseError):
        parse_listing('<script id="model">model = {broken</script>')


def test_fetch_listing_wraps_errors(monkeypatch):
    def boom(*args, **kwargs):
        raise urllib.error.URLError("x")

    monkeypatch.setattr(urllib.request, "urlopen", boom)
    with pytest.raises(FetchError):
        fetch_listing(1)


def test_fetch_listing_wraps_broken_responses(monkeypatch):
    import http.client

    def broken(*args, **kwargs):
        raise http.client.IncompleteRead(b"partial")
    monkeypatch.setattr(urllib.request, "urlopen", broken)
    with pytest.raises(FetchError):
        fetch_listing(1)


def test_images_are_only_fetched_from_blizzard_image_servers():
    from wowforever.blizzard import fetch_image

    for url in ("http://bnetcmsus-a.akamaihd.net/x.png", "https://169.254.169.254/latest/meta-data",
                "https://bnetcmsus-a.akamaihd.net.evil.example/x.png", "https://localhost/x.png"):
        with pytest.raises(FetchError, match="not a Blizzard image server"):
            fetch_image(url)


def test_image_redirects_away_from_blizzard_are_refused():
    from wowforever.blizzard import _ImageRedirects

    handler, request = _ImageRedirects(), urllib.request.Request("https://bnetcmsus-a.akamaihd.net/x.png")
    with pytest.raises(urllib.error.URLError, match="refused"):
        handler.redirect_request(request, None, 302, "Found", {}, "http://127.0.0.1:8080/admin")
    allowed = handler.redirect_request(request, None, 302, "Found", {}, "https://bnetcmseu-a.akamaihd.net/y.png")
    assert allowed.full_url == "https://bnetcmseu-a.akamaihd.net/y.png"
