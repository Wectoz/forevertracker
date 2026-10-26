"""Flask website: news feed, news, patches."""

from datetime import UTC, date, datetime

from flask import Flask, abort, render_template, request

from wowforever.countdown import launch_banner
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
        return {"banner": launch_banner(datetime.now(UTC))}

    def feed(kind: str | None, endpoint: str, heading: str, title: str, description: str):
        raw = request.args.get("page", "1")
        if not raw.isdigit() or int(raw) < 1:
            abort(404)
        page = int(raw)
        total = store.count_posts(kind)
        if page > 1 and (page - 1) * PAGE_SIZE >= total:
            abort(404)
        posts = store.list_posts(kind, limit=PAGE_SIZE, offset=(page - 1) * PAGE_SIZE)
        return render_template(
            "feed.html", posts=posts, page=page, has_older=page * PAGE_SIZE < total,
            endpoint=endpoint, heading=heading, page_title=title, description=description,
        )

    @app.get("/")
    def home():
        return feed(None, "home", "Latest WoW Forever news & patches", "WoW Forever Tracker",
                    "The latest World of Warcraft: Forever news and patch notes, gathered from Blizzard.")

    @app.get("/news")
    def news():
        return feed("news", "news", "WoW Forever news", "WoW Forever News · WoW Forever Tracker",
                    "World of Warcraft: Forever announcements and news, gathered from Blizzard.")

    @app.get("/patches")
    def patches():
        return render_template(
            "patches.html", patches=store.list_patches(), hotfixes=store.unversioned_patch_posts(),
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
