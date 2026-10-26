# WoW Forever Tracker: Design

Date: 2026-10-26
Status: awaiting owner approval

## Intent

World of Warcraft: Forever (Blizzard's new permanent "Classic+" version, launching
November 4, 2026) is new, and its official news is mixed in with retail and Classic posts
on Blizzard's sites. This project is a public, informative fan website that anyone
searching for WoW Forever information can land on, and get the latest news and patch
changes faster than digging through Blizzard's pages.

The first release is a **news and patch tracker**. Guides, a searchable database and tools
may come later, built on top of it.

Success looks like: someone searches "WoW Forever patch 1.60.1" or "WoW Forever news",
lands on the site, and immediately sees what changed and when, with a link to the official
source.

## Goals

- A home page with a launch countdown banner and one newest-first feed of WoW Forever news
  and patch-note posts (layout "A: News feed", chosen by the owner).
- A **Patches** page listing every WoW Forever patch (e.g. 1.60, 1.60.1), newest first, each
  linking to a patch page with its date, short summary, and links to the official patch
  notes.
- A **News** page: the feed with patch posts filtered out.
- Content gathered automatically from **official Blizzard sources only**.
- Runs **locally** on the owner's computer with one command; browse it in a web browser.
- WoW Forever-themed look: **"Bronze & Stone" dark theme** (chosen by the owner).

## Non-goals (for this release)

- Guides, item/quest database, search, talent planners or other tools.
- Public hosting, domain, deployment. (Later; the build should not make that hard.)
- User accounts, comments, or any user-submitted content.
- Non-WoW-Forever content (retail, Classic Era, Cataclysm Classic, etc.).
- Community sources (Warcraft Wiki, Wowhead, Reddit, news sites).

## Anti-goals (failure even if it works)

- Copying Blizzard's articles wholesale. Entries show a title, date, a short summary
  (Blizzard's own summary/opening lines, a few sentences at most) and a clear
  "Read on Blizzard.com →" link to the original.
- Looking like an official Blizzard site: no Blizzard logos or official branding art. The
  footer states "Unofficial fan site. Not affiliated with Blizzard Entertainment."
- Showing broken or empty pages when gathering fails.
- Showing retail/Classic posts as if they were WoW Forever news.

## Decided by the owner

- It's a website, informative, for anyone searching.
- Topic: World of Warcraft: Forever.
- Start with news and patches.
- Gather from official sources.
- Run locally first; pick hosting later.
- Home layout A (single newest-first news feed with countdown banner).
- Theme A: Bronze & Stone (dark), WoW Forever bronze feel.

## Decided by Claude (owner can override)

- **Language/framework:** Python with Flask, server-rendered HTML templates. No JavaScript
  framework.
- **Storage:** SQLite file in the project, so the site serves its own copy and stays up if
  Blizzard is slow or changes things.
- **Gathering schedule:** while the site runs, check for new posts every hour; also a
  "fetch now" command to pull immediately.
- **Source:** Blizzard's World of Warcraft news listing
  (`https://worldofwarcraft.blizzard.com/en-us/news`), which is server-rendered HTML
  containing article links (`/news/<id>/<slug>`) and embedded article data (title,
  published date, summary). There is no official RSS/JSON feed (checked:
  `news.blizzard.com/en-us/feed` returns 404). The listing mixes all WoW versions, so posts
  are kept only when they are about WoW Forever (e.g. "Forever" in title/summary/slug).
- **Classifying posts:** a post is a "patch" post when it is WoW Forever patch notes or
  hotfixes; otherwise "news". A patch post with a version number (e.g. "1.60.1") is grouped
  under that patch.
- **History / backfill:** the listing paginates with `?page=N` (checked: page 2 returns
  older posts, including WoW Forever ones). A one-off backfill command walks pages until
  posts predate the WoW Forever announcement (BlizzCon 2026), so the Patches page can list
  every patch. The hourly check only reads page 1. WoW patch notes and hotfixes are
  published as ordinary news articles there (e.g. "Hotfixes: October 23, 2026"); there is
  no separate patch-notes page (`/en-us/patch-notes` returns 404).
- **Edited posts:** Blizzard edits posts and marks them in the title (e.g.
  "[Updated 10/22] Choose Your Ruleset…"). When a stored post's title or summary on the
  listing changes, update the stored entry, re-fetch its article page, and show an
  "Updated <date>" label. No diff view of what changed.
- **Empty state:** if there is nothing to show (fresh install, offline), pages show a
  friendly "No WoW Forever posts gathered yet, run the fetch command" message. No seed
  content, no manual/admin entry.
- **Failure handling:** if gathering fails or the page structure changes, keep serving what
  is stored, log the problem, and never wipe stored entries.
- **Polite fetching:** one listing request per hour (plus article pages only for new posts),
  a clear User-Agent, and timeouts.
- **Countdown banner:** "Launches Nov 4 · N days to go"; on or after launch (Nov 4, 2026,
  3:00 p.m. PST) it reads "Live since Nov 4".
- **Look:** near-black stone background (`#16130f`), bronze accents (`#8c5a2b`,
  `#b5773a`, `#d9a35b`), parchment-coloured text (`#e8dcc4`), Cinzel for headings and
  Inter for body text (Google Fonts). Entries are cards with a bronze left edge; type icons
  📰 news / 🛠 patch. Must work on phone-width screens and meet normal contrast/
  accessibility standards.
- **Project location:** `/home/wec/projects/wow-forever`, as a git repository.

## Constraints

- Python 3.14 and `uv` are available locally.
- Must keep working (showing stored content) when offline or when Blizzard's page changes.
- Gathering parsers must be tested against saved copies of real Blizzard pages, not live
  requests, so tests are stable.

## Left to the builder

- Exact parsing approach for the listing page and article pages, and the "is this WoW
  Forever?" and "is this a patch post?" rules, as long as they are tested against real
  saved pages.
- How the hourly check is scheduled inside the running app.
- Database schema, template structure, CSS organisation.
- Page URLs (e.g. `/`, `/news`, `/patches`, `/patches/1.60.1`).
- Pagination of the feed if it grows long.
