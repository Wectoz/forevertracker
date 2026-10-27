"""Flask website: news feed, news, patches, class patch notes, Atom feeds and search."""

from datetime import UTC, date, datetime

from flask import Flask, abort, jsonify, render_template, request, url_for

from wowforever.classnotes import CLASS_COLORS, CLASSES, class_for_slug, slug
from wowforever.countdown import LAUNCH, PACIFIC, launch_banner, time_left
from wowforever.posts import plain_text
from wowforever.store import Store

PAGE_SIZE = 20
FEED_SIZE = 50
UPDATE_LABELS = {"beta": "Beta build", "patch": "Patch notes", "hotfix": "Hotfix"}


def _local(value: date | datetime) -> date | datetime:
    # Showing UTC would put Blizzard's late-evening posts a day ahead.
    return value.astimezone(PACIFIC) if isinstance(value, datetime) and value.tzinfo else value


def _short_date(value: date | datetime) -> str:
    value = _local(value)
    return f"{value:%b} {value.day}, {value.year}"


def _month_day(value: date | datetime) -> str:
    value = _local(value)
    return f"{value:%b} {value.day}"


def create_app(store: Store) -> Flask:
    app = Flask(__name__)
    app.jinja_env.filters["short_date"] = _short_date
    app.jinja_env.filters["month_day"] = _month_day

    @app.context_processor
    def banner():
        now = datetime.now(UTC)
        root = request.url_root.rstrip("/")
        latest_patch = store.list_posts("patch", limit=1) if now >= LAUNCH else []
        return {"banner": launch_banner(now), "left": time_left(now), "launch_iso": LAUNCH.isoformat(),
                "latest_patch": latest_patch[0] if latest_patch else None,
                "page_url": root + request.path, "site_root": root,
                "classes": [(name, slug(name), CLASS_COLORS[name]) for name in CLASSES]}

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
            show_class_cta=endpoint == "home" and page == 1,
            newer_url=page_url(endpoint, page - 1) if page > 1 else None,
            older_url=page_url(endpoint, page + 1) if page * PAGE_SIZE < total else None,
        )

    @app.errorhandler(404)
    def not_found(error):
        return render_template("not_found.html", page_title="Page not found · WoW Forever Tracker",
                               description="This page does not exist.", noindex=True), 404

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

    def class_or_404(name: str) -> str:
        cls = class_for_slug(name)
        if cls is None or name != slug(cls):
            abort(404)
        return cls

    @app.get("/classes/<name>")
    def class_page(name: str):
        cls = class_or_404(name)
        return render_template(
            "class.html", cls=cls, slug=name, current_class=name, color=CLASS_COLORS[cls], updates=store.class_updates(cls),
            labels=UPDATE_LABELS,
            page_title=f"{cls} Patch Notes · WoW Forever Tracker",
            description=f"Every World of Warcraft: Forever change for the {cls} class, "
                        "from beta builds, patches and hotfixes.",
        )

    def atom(title: str, page: str, entries: list[dict]):
        root = request.url_root.rstrip("/")
        updated = max((e["updated"] for e in entries), default=datetime.now(UTC))
        xml = render_template("atom.xml", title=title, feed_url=root + request.path, page_url=root + page,
                              updated=updated, entries=entries)
        return app.response_class(xml, mimetype="application/atom+xml")

    @app.get("/feed.xml")
    def feed_xml():
        entries = [{"id": p.url, "title": p.title, "url": p.url, "published": p.published,
                    "updated": p.edited_at or p.published, "summary": p.summary, "html": None}
                   for p in store.list_posts(limit=FEED_SIZE)]
        return atom("WoW Forever Tracker", url_for("home"), entries)

    @app.get("/classes/<name>/feed.xml")
    def class_feed(name: str):
        cls = class_or_404(name)
        entries = [{"id": f"{u.url}#{name}", "title": f"{cls}: {UPDATE_LABELS[u.kind]}, {_month_day(u.posted)}",
                    "url": u.url, "published": u.posted, "updated": u.posted, "summary": None, "html": u.html}
                   for u in store.class_updates(cls) if u.html][:FEED_SIZE]
        return atom(f"{cls} patch notes · WoW Forever Tracker", url_for("class_page", name=name), entries)

    @app.get("/search")
    def search():
        return render_template("search.html", page_title="Search · WoW Forever Tracker",
                               description="Search every World of Warcraft: Forever news post and class change.")

    @app.get("/search.json")
    def search_index():
        items = [{"title": p.title, "url": p.url, "label": "Patch" if p.kind == "patch" else "News",
                  "date": _short_date(p.published), "text": p.summary, "external": True}
                 for p in store.list_posts(limit=-1)]
        items += [{"title": f"{cls} · {UPDATE_LABELS[u.kind]}", "url": url_for("class_page", name=slug(cls)),
                   "label": cls, "date": _short_date(u.posted), "text": plain_text(u.html), "external": False}
                  for cls, u in store.all_class_changes()]
        return jsonify(items)

    return app
