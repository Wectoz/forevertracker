"""Command line: wowforever fetch | backfill | serve."""

import argparse
import logging
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
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    store = _open_store(args.db)

    try:
        if args.command == "fetch":
            added, edited = gather.fetch_latest(store, gather.fetch_listing)
        else:
            added, edited = gather.backfill(store, gather.fetch_listing)
    except (FetchError, ParseError) as err:
        print(f"Could not gather from Blizzard: {err}", file=sys.stderr)
        return 1
    print(f"Added {added}, updated {edited} WoW Forever posts.")
    return 0
