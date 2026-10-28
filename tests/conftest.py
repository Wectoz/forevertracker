import pytest

from wowforever import gather
from wowforever.blizzard import FetchError


@pytest.fixture(autouse=True)
def no_image_downloads(monkeypatch):
    """Tests never reach Blizzard's image server; a test that needs images passes its own fetch."""
    def offline(url):
        raise FetchError(f"{url}: offline in tests")
    monkeypatch.setattr(gather, "fetch_image", offline)
