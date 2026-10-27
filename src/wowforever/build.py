"""Render the whole site to static files (for GitHub Pages)."""

import re
import shutil
from collections import deque
from pathlib import Path
from urllib.parse import urlsplit
from xml.sax.saxutils import escape

from wowforever.store import Store
from wowforever.web import create_app

_HREF_RE = re.compile(r'href="([^"#?]+)')


def build_site(store: Store, out: Path, base_path: str = "", site_url: str | None = None) -> int:
    """Write every page reachable from the home page into `out`; returns the page count.

    `base_path` is where the site will be served from, e.g. "/wow-forever-news" for a
    GitHub Pages project site; every link and asset URL is prefixed with it. `site_url` is the
    site's full address, e.g. "https://wectoz.github.io/wow-forever-news": it sets the base path,
    makes preview and canonical URLs absolute, and adds a sitemap.xml.
    """
    if site_url:
        site_url = site_url.rstrip("/")
        base_path = urlsplit(site_url).path
        base_url = site_url + "/"
    else:
        base_path = base_path.rstrip("/")
        base_url = "http://localhost" + base_path + "/"
    app = create_app(store)
    client = app.test_client()

    out.mkdir(parents=True, exist_ok=True)
    seen, queue, pages, written = {"/"}, deque(["/"]), 0, []
    while queue:
        path = queue.popleft()
        response = client.get(path, base_url=base_url)
        if response.status_code != 200:
            raise RuntimeError(f"{path} returned {response.status_code}")
        body = response.get_data(as_text=True)
        if response.mimetype != "text/html":
            # A data file (Atom feed, search index): written as is, and not a page to crawl or list.
            target = out / path.strip("/")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(body, encoding="utf-8")
            continue
        target = out / path.strip("/") / "index.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body, encoding="utf-8")
        pages += 1
        written.append(path)
        for href in _HREF_RE.findall(body):
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
    if site_url:
        urls = "".join(f"  <url><loc>{escape(site_url + path)}</loc></url>\n" for path in written)
        (out / "sitemap.xml").write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls}</urlset>\n',
            encoding="utf-8",
        )
    return pages
