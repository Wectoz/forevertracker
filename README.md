# WoW Forever Tracker

News, patch notes and game data for World of Warcraft: Forever, in one place.

**[forevertracker.net](https://forevertracker.net)**

Blizzard posts WoW Forever news in among everything else on the WoW site. This site collects the Forever posts, the forum patch notes and what Blizzard staff say on the forums, and adds what's in the game client itself: abilities, talents, items and recipes. It updates itself every hour.

## On the site

- News and patch notes, newest first, with a countdown to launch on November 4.
- Full forum patch notes on their own pages. When Blizzard edits one, the page shows what was added and removed.
- Blue posts from Blizzard staff.
- A page per class: every change to it, its abilities by level, a talent calculator with shareable builds, and macros. Changes can be filtered to those since a given build or hotfix.
- Races, professions with every recipe and its skill levels, and every item, each with its in-game tooltip.
- Game data changes: what changed in the client between builds, including what the patch notes leave out.
- Tooltips on ability, talent and item names inside patch notes.
- Realm status, with each realm's population over the last week.
- Addons worth installing and ready-to-copy macros.
- Search across all of it, with suggestions as you type.
- RSS feeds for every post and for each class.

Mark your class and posts that change it are highlighted. Posts since your last visit get a "New" badge. Both are kept in your browser only: the site has no cookies or tracking and loads nothing from other sites.

*Unofficial fan site, not affiliated with Blizzard Entertainment. World of Warcraft is a trademark of Blizzard Entertainment, Inc.*

## Development

Python with [uv](https://docs.astral.sh/uv/), Flask and SQLite.

```sh
uv sync
uv run wowforever backfill   # gather every Forever post so far
uv run wowforever serve      # http://127.0.0.1:5000, gathers new posts hourly
uv run pytest
```

`.github/workflows/publish.yml` builds the static site and deploys it to GitHub Pages every 10 minutes and on every push to `master`; posts are gathered hourly. To build it locally: `uv run wowforever build --out _site`.

Optional repository secrets:

- `DISCORD_WEBHOOK_URL`: post each new post once to a Discord channel (a webhook from the channel's Integrations settings).
- `BLIZZARD_CLIENT_ID` and `BLIZZARD_CLIENT_SECRET`, from an app at [develop.battle.net](https://develop.battle.net): realm status. Without them the Realms page is hidden.

### Game data

Abilities, talents, racials, recipes and items come from the game client, in `src/wowforever/gamedata.json`. Refresh it by hand after a patch, on a PC with the game installed:

1. Once: install [.NET 10](https://dotnet.microsoft.com), clone and build [TACTSharp](https://github.com/wowdev/TACTSharp) (`dotnet build -c Release`), clone [WoWDBDefs](https://github.com/wowdev/WoWDBDefs), and save the [community listfile](https://github.com/wowdev/wow-listfile) as `listfile.csv`.
2. Extract the tables (from WSL; adjust the game folder):
   ```sh
   for t in chrclasses chrraces skillline skilllineability skillraceclassinfo spellname spell spelllevels spelleffect spellmisc spellduration spellradius talent talenttab itemsparse itemeffect itemxitemeffect item spellauraoptions spelltargetrestrictions spellrange spellreagents randproppoints itemarmorquality itemarmortotal armorlocation itemarmorshield itemdamageonehand itemdamagetwohand itemdamageranged itemdamagewand uitextureatlasmember uitextureatlas itemmodifiedappearance itemappearance; do
     id=$(grep -i ";dbfilesclient/$t.db2$" listfile.csv | cut -d';' -f1)
     dotnet TACTTool.dll -p wowf -r eu -d "/mnt/c/Program Files (x86)/World of Warcraft" -m fdid -i $id -o db2/$t.db2
   done
   ```
3. Build the data, applying the client's hotfix cache (log in once first so it's current):
   ```sh
   uv run wowforever gamedata --hotfixes "/mnt/c/Program Files (x86)/World of Warcraft/_forever_/Cache/ADB/enUS/DBCache.bin" db2 WoWDBDefs/definitions
   ```
   A new client build also records what changed in `gamechanges.json`, for the Game data changes page. Add `--record` to record a hotfix on the same build.
4. Extract and convert the icons it lists:
   ```sh
   dotnet TACTTool.dll -p wowf -r eu -d "/mnt/c/Program Files (x86)/World of Warcraft" -m list -i db2/icons.txt -o blp
   uv run --group gamedata wowforever icons blp
   ```
5. Check the pages with `uv run wowforever serve`, then commit `gamedata.json` and `src/wowforever/static/icons/`.

Season of Discovery spells are still in the client files and are left out by spell ID range (see `gamedata.py`).
