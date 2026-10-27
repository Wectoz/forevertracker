"""Command line: wowforever fetch | backfill | serve | build | announce | realms | gamedata."""

import argparse
import logging
import os
import sys
from pathlib import Path

from wowforever import gather
from wowforever.blizzard import FetchError, ParseError
from wowforever.store import Store

DEFAULT_DB = "instance/wowforever.sqlite3"


def _open_store(path: str) -> Store:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    return Store(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="wowforever", description="Unofficial WoW Forever news tracker")
    parser.add_argument("--db", default=DEFAULT_DB, help=f"database file (default: {DEFAULT_DB})")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("fetch", help="gather the newest WoW Forever posts")
    commands.add_parser("backfill", help="gather every WoW Forever post since the announcement")
    serve = commands.add_parser("serve", help="run the website and gather new posts hourly")
    serve.add_argument("--port", type=int, default=5000)
    build = commands.add_parser("build", help="write the site as static files")
    build.add_argument("--out", default="_site", help="output folder (default: _site)")
    build.add_argument("--base-path", default="", help='URL prefix the site is served under, e.g. "/wow-forever-news"')
    build.add_argument("--site-url", help='full site address, e.g. "https://wectoz.github.io/wow-forever-news";'
                                          " sets the base path and adds absolute preview URLs and a sitemap")
    commands.add_parser("announce", help="post new WoW Forever posts to the Discord webhook in $DISCORD_WEBHOOK_URL")
    commands.add_parser("realms", help="read WoW Forever realm status using $BLIZZARD_CLIENT_ID and $BLIZZARD_CLIENT_SECRET")
    gamedata = commands.add_parser("gamedata", help="rebuild gamedata.json from tables extracted from the game client")
    gamedata.add_argument("db2", type=Path, help="folder with the extracted .db2 files")
    gamedata.add_argument("defs", type=Path, help="WoWDBDefs definitions folder")
    args = parser.parse_args(argv)

    if args.command == "gamedata":
        import json

        from wowforever import gamedata as gd

        data = gd.build(gd.read_tables(args.db2, args.defs), gd.client_build(args.db2))
        gd.DATA_FILE.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Wrote {gd.DATA_FILE.name} from build {data['build']}: {len(data['races'])} races, "
              f"{sum(map(len, data['professions'].values()))} recipes.")
        return 0

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    store = _open_store(args.db)

    if args.command == "serve":
        from wowforever.web import create_app

        gather.start_hourly(store)
        create_app(store).run(host="127.0.0.1", port=args.port, use_reloader=False)
        return 0

    if args.command == "build":
        from wowforever.build import build_site

        pages = build_site(store, Path(args.out), base_path=args.base_path, site_url=args.site_url)
        print(f"Built {pages} pages into {args.out}.")
        return 0

    if args.command == "announce":
        from wowforever.discord import announce, webhook_sender

        url = os.environ.get("DISCORD_WEBHOOK_URL", "").strip()
        if not url:
            print("DISCORD_WEBHOOK_URL is not set; nothing announced.")
            return 0
        try:
            posted = announce(store, webhook_sender(url))
        except (FetchError, ValueError) as err:
            print(f"Could not announce on Discord: {err}", file=sys.stderr)
            return 1
        print(f"Announced {posted} new posts on Discord.")
        return 0

    if args.command == "realms":
        from wowforever import realms

        client_id = os.environ.get("BLIZZARD_CLIENT_ID", "").strip()
        client_secret = os.environ.get("BLIZZARD_CLIENT_SECRET", "").strip()
        if not client_id or not client_secret:
            print("BLIZZARD_CLIENT_ID/BLIZZARD_CLIENT_SECRET not set; realm status skipped.")
            return 0
        failed = 0
        for region in realms.REGIONS:
            try:
                found = realms.forever_realms(region, realms.token(client_id, client_secret))
            except (FetchError, ParseError) as err:
                print(f"Could not read {region.upper()} realms: {err}", file=sys.stderr)
                failed += 1
                continue
            store.save_realms(region, found)
            print(f"Saved {len(found)} {region.upper()} realms.")
        return 1 if failed == len(realms.REGIONS) else 0

    status = 0
    try:
        if args.command == "fetch":
            added, edited = gather.fetch_latest(store, gather.fetch_listing)
        else:
            added, edited = gather.backfill(store, gather.fetch_listing)
    except (FetchError, ParseError) as err:
        print(f"Could not gather from Blizzard: {err}", file=sys.stderr)
        status = 1  # the forum is a separate site, so still gather from it below
    else:
        print(f"Added {added}, updated {edited} WoW Forever posts.")
    try:
        saved = gather.gather_class_notes(store, gather.fetch_json)
    except (FetchError, ParseError) as err:
        # The news is already gathered; a forum outage must not fail the run.
        print(f"Could not gather class notes from the forums: {err}", file=sys.stderr)
    else:
        print(f"Saved {saved} class patch-note updates.")
    try:
        blue = gather.gather_blue_posts(store, gather.fetch_json)
    except (FetchError, ParseError) as err:
        print(f"Could not gather blue posts from the forums: {err}", file=sys.stderr)
    else:
        print(f"Added {blue} blue posts.")
    return status
