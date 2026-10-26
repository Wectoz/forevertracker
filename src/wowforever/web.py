"""Flask website: news feed, news, patches."""

from datetime import UTC, date, datetime

from flask import Flask, abort, render_template, request, url_for

from wowforever.countdown import LAUNCH, launch_banner, time_left
from wowforever.store import Store

PAGE_SIZE = 20


def _short_date(value: date | datetime) -> str:
    return f"{value:%b} {value.day}, {value.year}"


def _month_day(value: date | datetime) -> str:
    return f"{value:%b} {value.day}"


def create_app(store: Store) -> Flask:
    app = Flask(__name__)
    app.jinja_env.filters["short_date"] = _short_date
    app.jinja_env.filters["month_day"] = _month_day

    @app.context_processor
    def banner():
        now = datetime.now(UTC)
        return {"banner": launch_banner(now), "left": time_left(now), "launch_iso": LAUNCH.isoformat()}

    def page_url(endpoint: str, page: int) -> str:
        # Path-based pages ("/page/2/") so the site also works as plain static files.
        return url_for(endpoint) if page == 1 else url_for(f"{endpoint}_page", page=page)

    def feed(kind: str | None, endpoint: str, page: int, heading: str, title: str, description: str):
        total = store.count_posts(kind)
        if page < 1 or (page > 1 and (page - 1) * PAGE_SIZE >= total):
            abort(404)
        posts = store.list_posts(kind, limit=PAGE_SIZE, offset=(page - 1) * PAGE_SIZE)
        return render_template(
            "feed.html", posts=posts, heading=heading, page_title=title, description=description,
            newer_url=page_url(endpoint, page - 1) if page > 1 else None,
            older_url=page_url(endpoint, page + 1) if page * PAGE_SIZE < total else None,
        )

    @app.errorhandler(404)
    def not_found(error):
        return render_template("not_found.html", page_title="Page not found · WoW Forever Tracker",
                               description="This page does not exist."), 404

    @app.get("/")
    def home():
        return home_page(1)

    @app.get("/page/<int:page>/")
    def home_page(page: int):
        if page == 1 and request.endpoint == "home_page":
            abort(404)
        return feed(None, "home", page, "Latest WoW Forever news & patches", "WoW Forever Tracker",
                    "The latest World of Warcraft: Forever news and patch notes, gathered from Blizzard.")

    @app.get("/news")
    def news():
        return news_page(1)

    @app.get("/news/page/<int:page>/")
    def news_page(page: int):
        if page == 1 and request.endpoint == "news_page":
            abort(404)
        return feed("news", "news", page, "WoW Forever news", "WoW Forever News · WoW Forever Tracker",
                    "World of Warcraft: Forever announcements and news, gathered from Blizzard.")

    @app.get("/patches")
    def patches():
        return render_template(
            "patches.html", patches=store.list_patches(), hotfixes=store.unversioned_patch_posts(),
            has_posts=store.count_posts() > 0,
            page_title="WoW Forever Patches · WoW Forever Tracker",
            description="Every World of Warcraft: Forever patch, hotfix and update note.",
        )

    @app.get("/patches/<version>")
    def patch(version: str):
        posts = store.patch_posts(version)
        if not posts:
            abort(404)
        return render_template(
            "patch.html", version=version, posts=posts,
            page_title=f"WoW Forever Patch {version} · WoW Forever Tracker",
            description=f"What changed in World of Warcraft: Forever patch {version}.",
        )

    return app
