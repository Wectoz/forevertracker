"""Render the whole site to static files (for GitHub Pages)."""

import re
import shutil
from collections import deque
from pathlib import Path

from wowforever.store import Store
from wowforever.web import create_app

_HREF_RE = re.compile(r'href="([^"#?]+)')


def build_site(store: Store, out: Path, base_path: str = "") -> int:
    """Write every page reachable from the home page into `out`; returns the page count.

    `base_path` is where the site will be served from, e.g. "/wow-forever-news" for a
    GitHub Pages project site; every link and asset URL is prefixed with it.
    """
    base_path = base_path.rstrip("/")
    app = create_app(store)
    client = app.test_client()
    base_url = "http://localhost" + base_path + "/"

    out.mkdir(parents=True, exist_ok=True)
    seen, queue, pages = {"/"}, deque(["/"]), 0
    while queue:
        path = queue.popleft()
        response = client.get(path, base_url=base_url)
        if response.status_code != 200:
            raise RuntimeError(f"{path} returned {response.status_code}")
        html = response.get_data(as_text=True)
        target = out / path.strip("/") / "index.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(html, encoding="utf-8")
        pages += 1
        for href in _HREF_RE.findall(html):
            if not href.startswith(base_path + "/"):
                continue  # external link
            link = href[len(base_path):]
            if link.startswith("/static/") or link in seen:
                continue
            seen.add(link)
            queue.append(link)

    missing = client.get("/this-page-does-not-exist", base_url=base_url)
    (out / "404.html").write_text(missing.get_data(as_text=True), encoding="utf-8")
    shutil.copytree(app.static_folder, out / "static", dirs_exist_ok=True)
    return pages
