"""Flask website: news feed, news, patches, class pages, races, professions, addons, macros, Atom feeds and search."""

from collections import Counter
from datetime import UTC, date, datetime, timedelta
from urllib.parse import quote

from flask import Flask, abort, jsonify, render_template, request, url_for

from wowforever import gamediff, gamedata, gamelinks
from wowforever.classnotes import CLASS_COLORS, CLASSES, class_for_slug, slug
from wowforever.countdown import LAUNCH, PACIFIC, launch_banner, time_left
from wowforever.guides import ADDONS_UPDATED, CATEGORIES, GENERAL_MACROS, MACROS, TRENDING
from wowforever.posts import plain_text
from wowforever.store import ClassUpdate, Store

PAGE_SIZE = 20
FEED_SIZE = 50
STALE_AFTER = timedelta(minutes=30)
REGION_NAMES = {"us": "Americas", "eu": "Europe"}
# The Items page's slot filter, in the order of the character sheet.
ITEM_SLOTS = ("Head", "Neck", "Shoulder", "Back", "Chest", "Shirt", "Tabard", "Wrist", "Hands", "Waist", "Legs", "Feet",
              "Finger", "Trinket", "Main Hand", "One-Hand", "Two-Hand", "Off Hand", "Held In Off-hand", "Ranged",
              "Thrown", "Relic", "Bag")
UPDATE_LABELS = {"beta": "Beta build", "patch": "Patch notes", "hotfix": "Hotfix", "known": "Known Issues"}


def _local(value: date | datetime) -> date | datetime:
    # Showing UTC would put Blizzard's late-evening posts a day ahead.
    return value.astimezone(PACIFIC) if isinstance(value, datetime) and value.tzinfo else value


def _short_date(value: date | datetime) -> str:
    value = _local(value)
    return f"{value:%b} {value.day}, {value.year}"


def _month_day(value: date | datetime) -> str:
    value = _local(value)
    return f"{value:%b} {value.day}"


def _checked_time(value: datetime) -> str:
    value = _local(value)
    hour = value.hour % 12 or 12
    return f"{value:%b} {value.day}, {hour}:{value:%M} {'a.m.' if value.hour < 12 else 'p.m.'} PT"


def _ago(delta: timedelta) -> str:
    minutes = max(int(delta.total_seconds() // 60), 0)
    if minutes < 120:
        return f"{minutes} minute{'s' if minutes != 1 else ''}"
    return f"{minutes // 60} hours"


POPULATION_LEVELS = ("Low", "Medium", "High", "Full")  # coloured light to bright; any other label is grey
STRIP_DAYS, STRIP_HOURS = 7, 2  # the population charts: the last week, in two-hour blocks


def _population_strip(checks: list[tuple[datetime, bool, str]], now: datetime) -> dict:
    """A realm's last week in blocks, each with its CSS class and hover text: "Down" if the realm was down at any check
    in it, else the population at its last check. Also a one-line summary for screen readers."""
    step = timedelta(hours=STRIP_HOURS)
    end = now.replace(minute=0, second=0, microsecond=0) - timedelta(hours=now.hour % STRIP_HOURS) + step
    blocks = []
    for i in range(STRIP_DAYS * 24 // STRIP_HOURS):
        start = end - step * (STRIP_DAYS * 24 // STRIP_HOURS - i)
        inside = [c for c in checks if start <= c[0] < start + step]
        state = None if not inside else "Down" if not all(up for _, up, _ in inside) else inside[-1][2]
        css = "none" if state is None else state.lower() if state in (*POPULATION_LEVELS, "Down") else "other"
        blocks.append({"css": css, "state": state,
                       "title": f"{start:%a %b %-d, %H:%M}–{start + step:%H:%M} UTC: {state or 'not checked'}"})
    seen = Counter(b["state"] for b in blocks if b["state"] and b["state"] != "Down")
    down = sum(b["state"] == "Down" for b in blocks)
    summary = (f"mostly {seen.most_common(1)[0][0]}" if seen else "no checks yet") + (f", down in {down} of them" if down else "")
    return {"blocks": blocks, "summary": f"last 7 days in two-hour blocks: {summary}"}


def _anchors(updates: list[ClassUpdate]) -> dict[int, str]:
    """A readable, stable anchor per update, e.g. "hotfix-2026-11-06". Assigned oldest first, so a later
    update on the same day gets the suffixed anchor and links already shared keep working."""
    anchors: dict[int, str] = {}
    for update in sorted(updates, key=lambda u: (u.posted, u.post_id)):
        anchor = f"{update.kind}-{_local(update.posted):%Y-%m-%d}"
        anchors[update.post_id] = anchor if anchor not in anchors.values() else f"{anchor}-{update.post_id}"
    return anchors


def create_app(store: Store) -> Flask:
    app = Flask(__name__)
    app.jinja_env.filters["short_date"] = _short_date
    app.jinja_env.filters["month_day"] = _month_day
    app.jinja_env.filters["checked_time"] = _checked_time
    app.jinja_env.filters["slugify"] = gamedata.slugify
    app.jinja_env.filters["word_diff"] = gamediff.word_diff
    game = gamedata.load()
    linker = gamelinks.Linker(game)
    app.jinja_env.filters["gamelinks"] = linker.link

    @app.context_processor
    def banner():
        now = datetime.now(UTC)
        root = request.url_root.rstrip("/")
        latest_patch = store.list_posts("patch", limit=1) if now >= LAUNCH else []
        return {"banner": launch_banner(now), "left": time_left(now), "launch_iso": LAUNCH.isoformat(),
                "latest_patch": latest_patch[0] if latest_patch else None,
                "known_issues": store.latest_known_issues(), "has_realms": bool(store.realms()),
                "page_url": root + request.path, "site_root": root, "game_build": game["build"],
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

    @app.get("/blue")
    def blue():
        return blue_page(1)

    @app.get("/blue/page/<int:page>/")
    def blue_page(page: int):
        if page == 1 and request.endpoint == "blue_page":
            abort(404)
        total = store.count_blue_posts()
        if page < 1 or (page > 1 and (page - 1) * PAGE_SIZE >= total):
            abort(404)
        return render_template(
            "blue.html", gamelinks=True, posts=store.list_blue_posts(limit=PAGE_SIZE, offset=(page - 1) * PAGE_SIZE),
            newer_url=page_url("blue", page - 1) if page > 1 else None,
            older_url=page_url("blue", page + 1) if page * PAGE_SIZE < total else None,
            page_title="WoW Forever Blue Posts · WoW Forever Tracker",
            description="What Blizzard staff are saying about World of Warcraft: Forever on the official forums.",
        )

    @app.get("/realms")
    def realms():
        data = store.realms()
        if not data:
            abort(404)
        now = datetime.now(UTC)
        history = store.realm_history(now - timedelta(days=STRIP_DAYS))
        sections = [{"name": REGION_NAMES[region], "checked": checked, "realms": rows,
                     "strips": {r.name: _population_strip(history.get((region, r.name), []), now) for r in rows}}
                    for region, (checked, rows) in data.items()]
        oldest = min(checked for checked, _ in data.values())
        stale = _ago(now - oldest) if now - oldest > STALE_AFTER else None
        return render_template(
            "realms.html", sections=sections, stale=stale,
            page_title="WoW Forever Realm Status · WoW Forever Tracker",
            description="Which World of Warcraft: Forever realms are up, and how busy they are.",
        )

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
        updates = store.class_updates(cls)
        return render_template(
            "class.html", gamelinks=True, cls=cls, slug=name, current_class=name, color=CLASS_COLORS[cls], updates=updates,
            anchors=_anchors(updates), labels=UPDATE_LABELS, data=game["classes"][cls], macros=MACROS[cls],
            page_title=f"{cls} Abilities, Talents & Patch Notes · WoW Forever Tracker",
            description=f"Every World of Warcraft: Forever {cls} ability by level, the talent trees, macros "
                        "and every change from beta builds, patches and hotfixes.",
        )

    @app.get("/races")
    def races():
        return render_template(
            "races.html", races=gamedata.current_races(game), race_icons=game["race_icons"],
            racial_notes=gamedata.RACIAL_NOTES, page_title="WoW Forever Races & Racials · WoW Forever Tracker",
            description="The racial abilities of every World of Warcraft: Forever race, Skyborne included.",
        )

    @app.get("/professions")
    def professions():
        return render_template(
            "professions.html", professions=game["professions"], icons=game["profession_icons"],
            secondary_professions=gamedata.SECONDARY_PROFESSIONS,
            page_title="WoW Forever Professions · WoW Forever Tracker",
            description="Every World of Warcraft: Forever profession recipe, where it comes from and its skill-ups.",
        )

    @app.get("/professions/<name>")
    def profession(name: str):
        found = next((p for p in game["professions"] if gamedata.slugify(p) == name), None)
        if found is None:
            abort(404)
        return render_template(
            "profession.html", name=found, recipes=game["professions"][found],
            profession_icon=game["profession_icons"].get(found),
            page_title=f"WoW Forever {found} Recipes · WoW Forever Tracker",
            description=f"All {len(game['professions'][found])} World of Warcraft: Forever {found} recipes, "
                        "where they come from and their skill-ups.",
        )

    @app.get("/game-changes")
    def game_changes():
        return render_template(
            "game_changes.html", updates=[{**u, "date": date.fromisoformat(u["date"]), "sections": gamediff.by_section(u["changes"])}
                                          for u in gamediff.load()], build=game["build"],
            page_title="WoW Forever Game Data Changes · WoW Forever Tracker",
            description="Every change to World of Warcraft: Forever abilities, talents, racials and recipes found in the "
                        "game files, including the ones the patch notes leave out.",
        )

    @app.get("/items")
    def items():
        present = {i["slot"] for i in game["items"]}
        return render_template(
            "items.html", count=len(game["items"]), slots=[s for s in ITEM_SLOTS if s in present],
            types=sorted({i["type"] for i in game["items"] if i["type"]}),
            professions=sorted({i["crafted"] for i in game["items"] if i["crafted"]}),
            page_title="WoW Forever Items · WoW Forever Tracker",
            description=f"Search all {len(game['items'])} World of Warcraft: Forever weapons, armor and bags by slot, "
                        "type, quality and level, with their in-game tooltips.",
        )

    @app.get("/items.json")
    def items_json():
        return jsonify(game["items"])

    @app.get("/notes/<int:post_id>")
    def notes(post_id: int):
        found = store.notes(post_id)
        if not found:
            abort(404)
        post = found[0]
        title = post.title or f"{UPDATE_LABELS[post.kind]}, {_short_date(post.posted)}"
        return render_template(
            "notes.html", gamelinks=True, post=post, title=title, label=UPDATE_LABELS[post.kind],
            page_title=f"{title} · WoW Forever Tracker",
            description=post.summary or f"World of Warcraft: Forever {UPDATE_LABELS[post.kind].lower()}.",
        )

    @app.get("/addons")
    def addons():
        return render_template(
            "addons.html", sections=(("Trending right now", TRENDING), *CATEGORIES), updated=ADDONS_UPDATED,
            page_title="WoW Forever Addons · WoW Forever Tracker",
            description="The best World of Warcraft: Forever addons by category, and the new ones everyone is "
                        "trying, with links to CurseForge.",
        )

    @app.get("/macros")
    def macros():
        return render_template(
            "macros.html", macros=[("All classes", "general", None, GENERAL_MACROS)]
            + [(name, slug(name), CLASS_COLORS[name], MACROS[name]) for name in CLASSES],
            page_title="WoW Forever Macros for Every Class · WoW Forever Tracker",
            description="Ready-to-copy World of Warcraft: Forever macros for all nine classes.",
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

    @app.get("/blue/feed.xml")
    def blue_feed():
        entries = [{"id": p.url, "title": f"{p.author}: {p.thread_title}", "url": p.url, "published": p.posted,
                    "updated": p.posted, "summary": p.excerpt, "html": None}
                   for p in store.list_blue_posts(limit=FEED_SIZE)]
        return atom("WoW Forever Blue Posts · WoW Forever Tracker", url_for("blue"), entries)

    @app.get("/classes/<name>/feed.xml")
    def class_feed(name: str):
        cls = class_or_404(name)
        entries = [{"id": f"{u.url}#{name}", "title": f"{cls}: {UPDATE_LABELS[u.kind]}, {_month_day(u.posted)}",
                    "url": u.url, "published": u.posted, "updated": u.posted, "summary": None, "html": u.html}
                   for u in store.class_updates(cls) if u.html][:FEED_SIZE]
        return atom(f"{cls} patch notes · WoW Forever Tracker", url_for("class_page", name=name), entries)

    @app.get("/tooltips.json")
    def tooltips_json():
        # Only the tooltips some page links to: every crafted item's would be most of a megabyte.
        texts = [(u.html, cls) for cls in CLASSES for u in store.class_updates(cls)]
        texts += [(n.html, None) for n in store.notes()] + [(p.excerpt, None) for p in store.list_blue_posts(limit=-1)]
        used = {key for text, section in texts for key in gamelinks.keys_in(linker.link(text, section))}
        return jsonify({key: tip for key, tip in linker.tips.items() if key in used})

    @app.get("/search")
    def search():
        return render_template("search.html", page_title="Search · WoW Forever Tracker",
                               description="Search every World of Warcraft: Forever news post, class change, ability, talent, racial, recipe, item, macro and addon.")

    @app.get("/search.json")
    def search_index():
        items = [{"title": p.title, "url": p.url, "label": "Patch" if p.kind == "patch" else "News",
                  "date": _short_date(p.published), "text": p.summary, "external": True}
                 for p in store.list_posts(limit=-1) if not p.on_forums]  # forum posts: as notes below
        items += [{"title": n.title, "url": url_for("notes", post_id=n.id), "label": UPDATE_LABELS[n.kind],
                   "date": _short_date(n.posted), "text": plain_text(n.html) or n.summary, "external": False}
                  for n in store.notes()]
        for cls in CLASSES:
            updates = store.class_updates(cls)
            anchors = _anchors(updates)
            items += [{"title": f"{cls} · {UPDATE_LABELS[u.kind]}",
                       "url": url_for("class_page", name=slug(cls), _anchor=anchors[u.post_id]),
                       "label": cls, "date": _short_date(u.posted), "text": plain_text(u.html), "external": False}
                      for u in updates if u.html]
        return jsonify(items + game_index())

    def game_index() -> list[dict]:
        """The game data for search: abilities, talents, racials, recipes, items, macros and addons."""
        entry = lambda title, url, label, text="", external=False: {
            "title": title, "url": url, "label": label, "date": "", "text": text or "", "external": external}
        out = []
        for cls in CLASSES:
            data, page = game["classes"][cls], lambda tab: url_for("class_page", name=slug(cls), _anchor=tab)
            out += [entry(a["name"], page("abilities"), f"{cls} ability", a["description"]) for a in data["abilities"]]
            out += [entry(t["name"], page("talents"), f"{cls} talent · {tree['name']}", next(filter(None, t["ranks"]), ""))
                    for tree in data["talents"] for t in tree["talents"]]
        for race, racials in gamedata.current_races(game).items():
            out += [entry(r["name"], url_for("races", _anchor=gamedata.slugify(race)), f"{race} racial", r["description"])
                    for r in racials]
        for profession, recipes in game["professions"].items():
            page = url_for("profession", name=gamedata.slugify(profession))
            out += [entry(r["name"], f"{page}?q={quote(r['name'])}", f"{profession} recipe", f"Learned from {r['source']}")
                    for r in recipes]
        out += [entry(i["name"], f"{url_for('items')}?q={quote(i['name'])}", "Item",
                      " · ".join(filter(None, [i["slot"], i["type"], f"item level {i['level']}"])))
                for i in {i["name"]: i for i in game["items"]}.values()]  # one result per name
        for name, macros in [("General", GENERAL_MACROS), *((cls, MACROS[cls]) for cls in CLASSES)]:
            out += [entry(m.name, url_for("macros", _anchor=slug(name) if name in CLASSES else "general"),
                          f"{name} macro", m.blurb) for m in macros]
        out += [entry(a.name, a.url, "Addon", a.blurb, external=True)
                for _, addons in (("Trending", TRENDING), *CATEGORIES) for a in addons]
        return out

    return app
