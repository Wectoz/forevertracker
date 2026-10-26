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

## Publishing

The site is published to GitHub Pages by `.github/workflows/publish.yml`. Every hour (and on every push to `master`) it gathers new posts from Blizzard, runs `uv run wowforever build`, and deploys the static files. If Blizzard can't be reached, it republishes what it already has.

To build the static site locally: `uv run wowforever build --out _site --base-path /wow-forever-news`.
