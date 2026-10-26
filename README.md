# WoW Forever Tracker

An unofficial fan site that gathers World of Warcraft: Forever news and patch notes from
Blizzard's official WoW news page and shows them as a simple, bronze-themed feed.

Unofficial fan site. Not affiliated with Blizzard Entertainment.

## Run it

```bash
uv sync                       # install
uv run wowforever backfill    # one-time: gather every WoW Forever post so far
uv run wowforever serve       # run the site at http://127.0.0.1:5000 (checks for new posts hourly)
```

`uv run wowforever fetch` gathers the newest posts right away. Run the tests with `uv run pytest`.
