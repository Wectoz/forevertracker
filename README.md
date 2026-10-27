# WoW Forever Tracker

**Every World of Warcraft: Forever news post and patch note in one place.**

👉 **[wectoz.github.io/wow-forever-news](https://wectoz.github.io/wow-forever-news/)**

WoW Forever launches **November 4 at 3:00 p.m. PST**. Blizzard posts its WoW Forever news alongside everything else on the WoW news page. This site picks out the WoW Forever posts and shows them on their own, newest first, with a countdown to launch.

## What's on the site

- **Home**: the latest WoW Forever news and patch notes together.
- **News**: every WoW Forever announcement Blizzard has published so far.
- **Patches**: patch notes grouped by version number, plus hotfixes.
- **Classes**: pick your class from the menu. Each class page has tabs: its changes from every beta build, patch and hotfix; every ability by the level you learn it; the talent trees; and its macros.
- **Races**: every race's racial abilities, Skyborne included.
- **Professions**: every recipe of every profession, where it comes from and the skill at which it turns yellow and grey.
- **Full patch notes**: every Blizzard forum notes post on its own page, not just the class parts. When Blizzard edits one, the page lists what was added and removed.
- **Blue posts**: what Blizzard staff say about WoW Forever on the official forums, newest first, with its own RSS feed.
- **Known Issues**: a link next to the launch countdown on every page, straight to Blizzard's Known Issues thread.
- **Realms**: whether each WoW Forever realm is up, and its population. This page appears once realm data is available.
- **Guides** menu: Races, Professions, Addons and Macros.
- **Addons**: the essential addons and the new Forever ones people are trying, each linked to its CurseForge page.
- **Macros**: ready-to-copy macros for all nine classes, with a Copy button on each.
- **Search**: find any post or class change, e.g. every note that mentions Sunder Armor.
- **Your class**: mark your class on its page and the site points out posts with changes for it. Class pages can also show only the changes since a given build, patch or hotfix.
- **New since your last visit**: posts you haven't seen yet get a "New" badge.
- **RSS feeds**: one for every post, and one per class (linked on each class page). They work in any feed reader or a Discord RSS bot.
- **Links to one update**: each update on a class page has a "Copy link" button, handy for sharing a hotfix.

Each post shows its date, a short summary when Blizzard gives one, and a link to the full article on Blizzard.com. The launch countdown sits at the top of every page, with the launch time in your own time zone; after launch it shows the day count and links the latest patch notes.

## Always up to date

The site checks Blizzard's news page and forums every hour and adds new WoW Forever posts on its own. Realm status is checked about every 10 minutes. If Blizzard's site is down, the tracker keeps showing what it already has and tries again on the next check.

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

The live site is published to GitHub Pages by `.github/workflows/publish.yml`, about every 10 minutes and on every push to `master`. Realm status is refreshed on every run; news and forum posts are gathered about once an hour. To build the static site locally: `uv run wowforever build --out _site --site-url https://wectoz.github.io/wow-forever-news` (this also writes `sitemap.xml`). The build fails if any page links to a page that doesn't exist.

To announce new posts in a Discord channel, create a webhook in the channel's settings (Integrations → Webhooks) and save its URL as the repository secret `DISCORD_WEBHOOK_URL`. The hourly run then posts each new WoW Forever post once (`uv run wowforever announce`). The first run only records the posts that already exist, so the channel isn't flooded with old ones.

Realm status comes from Blizzard's game data API. Create an app at [develop.battle.net](https://develop.battle.net) and save its client ID and secret as the repository secrets `BLIZZARD_CLIENT_ID` and `BLIZZARD_CLIENT_SECRET`. Then `uv run wowforever realms` reads the status of the WoW Forever realms. Without the secrets it prints a skip message and the Realms page stays hidden.

Abilities, talents, racials and recipes are read from the WoW Forever game client itself, not from a wiki. They live in `src/wowforever/gamedata.json`, which is refreshed by hand after a patch, on a PC with the game installed:

1. Get the tools once: [.NET 10](https://dotnet.microsoft.com), `git clone https://github.com/wowdev/TACTSharp` (build `TACTTool` with `dotnet build -c Release`), `git clone https://github.com/wowdev/WoWDBDefs`, and the [community listfile](https://github.com/wowdev/wow-listfile) saved as `listfile.csv`, which maps table names to file IDs.
2. Extract the tables (from WSL; adjust the game folder):
   ```sh
   for t in chrclasses chrraces skillline skilllineability skillraceclassinfo spellname spell spelllevels spelleffect spellmisc spellduration spellradius talent talenttab itemsparse itemeffect itemxitemeffect; do
     id=$(grep -i ";dbfilesclient/$t.db2$" listfile.csv | cut -d';' -f1)
     dotnet TACTTool.dll -p wowf -r eu -d "/mnt/c/Program Files (x86)/World of Warcraft" -m fdid -i $id -o db2/$t.db2
   done
   ```
3. `uv run wowforever gamedata db2 WoWDBDefs/definitions`, check the pages with `uv run wowforever serve`, and commit `gamedata.json`.

Season of Discovery spells are still in the client files; they are left out by spell ID range (see `gamedata.py`).
