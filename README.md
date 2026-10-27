# WoW Forever Tracker

**Every World of Warcraft: Forever news post and patch note in one place.**

👉 **[wectoz.github.io/wow-forever-news](https://wectoz.github.io/wow-forever-news/)**

WoW Forever launches **November 4 at 3:00 p.m. PST**. Blizzard posts its WoW Forever news alongside everything else on the WoW news page. This site picks out the WoW Forever posts and shows them on their own, newest first, with a countdown to launch.

## What's on the site

- **Home**: the latest WoW Forever news and patch notes together.
- **News**: every WoW Forever announcement Blizzard has published so far.
- **Patches**: patch notes grouped by version number, plus hotfixes.
- **Classes**: pick your class from the menu to see only its changes from every beta build, patch and hotfix.
- **Search**: find any post or class change, e.g. every note that mentions Sunder Armor.
- **Your class**: mark your class on its page and the site points out posts with changes for it. Class pages can also show only the changes since a given build, patch or hotfix.
- **New since your last visit**: posts you haven't seen yet get a "New" badge.
- **RSS feeds**: one for every post, and one per class (linked on each class page). They work in any feed reader or a Discord RSS bot.

Each post shows its date, a short summary when Blizzard gives one, and a link to the full article on Blizzard.com. The launch countdown sits at the top of every page; after launch it shows the day count and links the latest patch notes.

## Always up to date

The site checks Blizzard's news page every hour and adds new WoW Forever posts on its own. If Blizzard's site is down, the tracker keeps showing what it already has and tries again the next hour.

---

*Unofficial fan site. Not affiliated with or endorsed by Blizzard Entertainment. World of Warcraft and Blizzard Entertainment are trademarks of Blizzard Entertainment, Inc.*

---

## For developers

The tracker is a small Python app ([uv](https://docs.astral.sh/uv/) + Flask + SQLite).

```bash
uv sync                       # install
uv run wowforever backfill    # one-time: gather every WoW Forever post so far
uv run wowforever serve       # run the site at http://127.0.0.1:5000 (checks for new posts hourly)
```

`uv run wowforever fetch` gathers the newest posts right away. Run the tests with `uv run pytest`.

The live site is published to GitHub Pages by `.github/workflows/publish.yml`, every hour and on every push to `master`. To build the static site locally: `uv run wowforever build --out _site --site-url https://wectoz.github.io/wow-forever-news` (this also writes `sitemap.xml`). The build fails if any page links to a page that doesn't exist.
