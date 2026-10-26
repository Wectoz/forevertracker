# WoW Forever Tracker Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A local Flask website that gathers WoW Forever news and patch posts from Blizzard's official WoW news listing and shows them as a bronze-themed news feed, news page and patches pages.

**Architecture:** One Python package `wowforever`. `blizzard.py` fetches listing pages and pulls the embedded `model` JSON out of the HTML; `posts.py` turns raw Blizzard blog dicts into `Post` records (WoW Forever filter, news/patch kind, patch version); `store.py` keeps them in SQLite; `gather.py` runs fetch/backfill and an hourly background thread; `web.py` serves Jinja pages. A small CLI (`wowforever serve|fetch|backfill`) ties it together.

**Tech Stack:** Python 3.14, uv, Flask (only runtime dependency), stdlib `sqlite3`/`urllib`/`json`/`re`/`threading`, pytest.

**Spec:** `docs/superpowers/specs/2026-10-26-wow-forever-tracker-design.md`

## Global Constraints

- Only source: `https://worldofwarcraft.blizzard.com/en-us/news?page=N` (official Blizzard). No community sources.
- Only WoW Forever posts are stored or shown; retail/Classic posts never appear.
- Entries show title, date, short summary (Blizzard's `description`, tags stripped, max 300 chars, cut at a word boundary with "…"), and a "Read on Blizzard.com →" link to `https://worldofwarcraft.blizzard.com/en-us` + post `url`. Never the full article body.
- Footer on every page, exact copy: `Unofficial fan site. Not affiliated with Blizzard Entertainment.` No Blizzard logos or art.
- Fetching: User-Agent `WoWForeverTracker/0.1 (unofficial fan site)`, 15 s timeout, page 1 once per hour while serving.
- A failed fetch or parse never deletes or changes stored posts; it logs a warning and the site keeps serving.
- Empty state copy: `No WoW Forever posts gathered yet. Run "uv run wowforever fetch" to gather them.`
- Launch moment: `2026-11-04T23:00:00Z` (Nov 4, 3:00 p.m. PST).
- Theme "Bronze & Stone": background `#16130f`, text `#e8dcc4`, bronze `#8c5a2b` / `#b5773a` / `#d9a35b`, Cinzel headings, Inter body (Google Fonts). Works at 360 px width.
- DB file: `instance/wowforever.sqlite3` (gitignored).

## Review Focus

- Blizzard page without the `<script id="model">` block or with broken JSON → `ParseError`, nothing stored changes, warning logged (Task 1 + Task 4 tests).
- Network error / timeout / HTTP 5xx during fetch → same: stored posts untouched, CLI exits non-zero with a one-line message, serve keeps running (Task 4 tests).
- Retail/Classic posts carrying version-like numbers (`12.1.5`, `1.15.8`) or hotfix posts not about Forever → never stored, never treated as a Forever patch (Task 2 tests).
- Running fetch or backfill twice, or a post appearing on two pages → no duplicates, counts stable (Task 3 tests).
- HTML tags and entities in `title`/`description` (`&amp;`, `<p>`, `®`) → summary is plain text, rendered escaped (Task 2 + Task 5 tests).

---

### Task 1: Project setup and Blizzard listing parser

**Files:**
- Create: `pyproject.toml`, `src/wowforever/__init__.py` (empty), `src/wowforever/blizzard.py`
- Create: `tests/fixtures/news_page1.html`, `tests/fixtures/news_page2.html`
- Test: `tests/test_blizzard.py`
- Modify: `.gitignore` (add `instance/`, `.venv/`, `__pycache__/`, `.pytest_cache/`)

**Interfaces:**
- Produces:
  - `class ParseError(Exception)`, `class FetchError(Exception)`
  - `@dataclass(frozen=True) class ListingPage: blogs: list[dict]; has_next: bool`
  - `parse_listing(html: str) -> ListingPage`
  - `fetch_listing(page: int) -> str` (raises `FetchError` on any network/HTTP error)
  - constants `BASE_URL = "https://worldofwarcraft.blizzard.com/en-us"`, `USER_AGENT`, `TIMEOUT = 15`

- [ ] **Step 1: Set up the project.** Write `pyproject.toml` by hand: `name = "wowforever"`, `requires-python = ">=3.12"`, `dependencies = ["flask>=3.1"]`, `[project.scripts] wowforever = "wowforever.cli:main"`, build backend `hatchling`, `[dependency-groups] dev = ["pytest>=8"]`, `[tool.pytest.ini_options] testpaths = ["tests"]`. Run `uv sync`. Expected: `.venv` created, no errors.

- [ ] **Step 2: Save fixtures** from the real site:
  ```bash
  curl -sL -A "WoWForeverTracker/0.1 (unofficial fan site)" -o tests/fixtures/news_page1.html "https://worldofwarcraft.blizzard.com/en-us/news?page=1"
  curl -sL -A "WoWForeverTracker/0.1 (unofficial fan site)" -o tests/fixtures/news_page2.html "https://worldofwarcraft.blizzard.com/en-us/news?page=2"
  ```
  Each page contains `<script id="model">model = {...}</script>` whose JSON has `blogList.blogs` (each blog has `id`, `title`, `url`, `description`, `category`, `tags`, `keywords`, `published`, `updated`) and `paginationLinks.next`. If the fetched page's titles differ from the test values below, adjust the test's expected title to one that is on the saved page.

- [ ] **Step 3: Write failing tests** in `tests/test_blizzard.py`:
  - `test_parse_listing_reads_blogs`: page1 → `len(blogs) >= 10`, every blog has keys `id, title, url, description, published`, `has_next is True`; some blog title contains `"World of Warcraft: Forever"`.
  - `test_parse_listing_page2_differs`: ids on page 2 are not all in page 1.
  - `test_parse_listing_without_model_raises`: `parse_listing("<html></html>")` raises `ParseError`.
  - `test_parse_listing_bad_json_raises`: `parse_listing('<script id="model">model = {broken</script>')` raises `ParseError`.
  - `test_fetch_listing_wraps_errors`: monkeypatch `urllib.request.urlopen` to raise `urllib.error.URLError("x")` → `fetch_listing(1)` raises `FetchError`.

- [ ] **Step 4: Run** `uv run pytest tests/test_blizzard.py -v`. Expected: FAIL (import error).

- [ ] **Step 5: Implement `blizzard.py`.** Find the `<script id="model">` body with a regex, strip the leading `model =`, decode with `json.JSONDecoder().raw_decode` (ignores the trailing `;`). Missing script, missing `blogList.blogs`, or JSON error → `ParseError`. `has_next = bool(model["paginationLinks"]["next"])`. `fetch_listing` uses `urllib.request.Request` with the User-Agent, `timeout=TIMEOUT`, decodes UTF-8; wraps `URLError`, `HTTPError`, `TimeoutError`, `OSError` in `FetchError`.

- [ ] **Step 6: Run** `uv run pytest -v`. Expected: all PASS.

- [ ] **Step 7: Commit** `git add -A && git commit -m "feat: project setup and Blizzard news listing parser"`

---

### Task 2: Post rules (Forever filter, kind, patch version, summary)

**Files:**
- Create: `src/wowforever/posts.py`
- Test: `tests/test_posts.py`

**Interfaces:**
- Consumes: raw blog dicts from `ListingPage.blogs` (Task 1).
- Produces:
  - `@dataclass(frozen=True) class Post: id: int; title: str; url: str; summary: str; kind: str  # "news" | "patch"; version: str | None; published: datetime; updated: datetime` (datetimes timezone-aware UTC)
  - `to_post(blog: dict) -> Post | None` (None = not a WoW Forever post)
  - `make_summary(html: str, limit: int = 300) -> str`

Rules (pinned):
- **Forever:** case-insensitive `"forever"` in `title`, `description`, or `keywords` (joined). Not `content`.
- **Kind = "patch"** when `tags` (lowercased) include any of `"patch notes"`, `"hotfixes"`, `"update notes"`, or the title matches `(?i)\b(patch notes|hotfixes)\b`; otherwise `"news"`.
- **Version:** only for patch posts. First match of `\b1\.(\d{2,})(?:\.\d+)?\b` in title, then in `category`, whose minor number is `>= 60` (so `1.60`, `1.60.1`, `1.61` match; `1.15.8`, `12.1.5` don't). Else `None`.
- **URL:** `BASE_URL + blog["url"]`.
- **Summary:** strip tags, `html.unescape`, collapse whitespace; if longer than 300, cut at the last space before 300 and append `…`.

- [ ] **Step 1: Write failing tests** with small inline dicts (helper `blog(**overrides)` with defaults `id=1, title="X", url="/news/1/x", description="", category=None, tags=[], keywords=[], published="2026-10-22T15:44:03.763Z", updated="2026-10-22T15:44:03.763Z"`):
  - `test_non_forever_post_is_dropped`: title `"Midnight's 12.1.5 Content Update is Now Live"` → `None`.
  - `test_forever_news`: title `"Claim Your World of Warcraft: Forever Character Names"` → `kind == "news"`, `version is None`, `url == "https://worldofwarcraft.blizzard.com/en-us/news/1/x"`, `published == datetime(2026,10,22,15,44,3,763000,tzinfo=UTC)`.
  - `test_forever_in_description_counts`: title `"Hotfixes: November 6, 2026"`, description mentions `"World of Warcraft: Forever"`, tags `["hotfixes"]` → `kind == "patch"`, `version is None`.
  - `test_forever_patch_version_from_title`: title `"World of Warcraft: Forever Patch 1.60.1 Notes"`, tags `["patch notes"]` → `version == "1.60.1"`.
  - `test_forever_patch_version_from_category`: title `"WoW: Forever Patch Notes"`, category `"1.61"` → `version == "1.61"`.
  - `test_classic_and_retail_versions_ignored`: Forever patch post with category `"1.15.8"` → `version is None`; with title containing `"12.1.5"` → `version is None`.
  - `test_summary_strips_html_and_truncates`: `make_summary("<p>Fish &amp; Chips®</p>")` → `"Fish & Chips®"`; a 400-char word string → length ≤ 301, ends with `"…"`, no cut mid-word.

- [ ] **Step 2: Run** `uv run pytest tests/test_posts.py -v`. Expected: FAIL (import error).

- [ ] **Step 3: Implement `posts.py`** per the rules above. Parse dates with `datetime.fromisoformat` (handles the `Z`).

- [ ] **Step 4: Add a real-data test** `test_fixture_pages_yield_only_forever_posts`: run `to_post` over both fixture pages' blogs → at least 5 posts, every post's title/summary mentions "forever" (case-insensitive), no title contains `"Midnight's 12.1.5"`.

- [ ] **Step 5: Run** `uv run pytest -v`. Expected: all PASS.

- [ ] **Step 6: Commit** `git commit -am "feat: WoW Forever post rules"` (add new files first).

---

### Task 3: SQLite store

**Files:**
- Create: `src/wowforever/store.py`
- Test: `tests/test_store.py`

**Interfaces:**
- Consumes: `Post` (Task 2).
- Produces:
  - `@dataclass(frozen=True) class StoredPost(Post): edited_at: datetime | None` (templates read `id, title, url, summary, kind, version, published, edited_at`).
  - `class Store: __init__(self, path: str | Path)` (creates tables if missing; `":memory:"` allowed)
  - `Store.upsert(posts: Iterable[Post]) -> tuple[int, int]` → `(added, edited)`
  - `Store.list_posts(kind: str | None = None, limit: int = 20, offset: int = 0) -> list[StoredPost]` newest `published` first
  - `Store.count_posts(kind: str | None = None) -> int`
  - `Store.list_patches() -> list[tuple[str, date, int]]` → `(version, first_published_date, post_count)` newest first
  - `Store.patch_posts(version: str) -> list[StoredPost]` oldest first
  - `Store.unversioned_patch_posts() -> list[StoredPost]` newest first

Edit rule (pinned): when a post id already exists and its `title` or `summary` differs, update title/summary/kind/version/updated and set `edited_at` to the post's `updated` value; count it as edited. Same title+summary → no change, not counted. Use `sqlite3` with one connection per `Store`, `check_same_thread=False` and a `threading.Lock` around writes (the hourly thread writes while Flask reads).

- [ ] **Step 1: Write failing tests** (use `Store(":memory:")` and a `make_post(**overrides)` helper):
  - `test_upsert_adds_and_lists_newest_first`
  - `test_upsert_twice_is_idempotent`: second upsert of same posts → `(0, 0)`, `count_posts() == 2`.
  - `test_edited_title_marks_edited`: re-upsert id 1 with title `"[Updated 10/22] …"` and later `updated` → `(0, 1)`; listed post has new title and `edited_at == that updated`.
  - `test_filter_by_kind_and_paging`: 25 news + 1 patch → `list_posts("news", limit=20)` has 20, `offset=20` has 5, `count_posts("patch") == 1`.
  - `test_patches_grouping`: patch posts versions `1.60` (Sep 17), `1.60.1` (Oct 20, two posts), one unversioned → `list_patches()` is `[("1.60.1", date(2026,10,20), 2), ("1.60", date(2026,9,17), 1)]`; `unversioned_patch_posts()` has 1.
  - `test_persists_to_file(tmp_path)`: upsert, reopen `Store(tmp_path/"db.sqlite3")` → post still there.

- [ ] **Step 2: Run** `uv run pytest tests/test_store.py -v`. Expected: FAIL.
- [ ] **Step 3: Implement `store.py`.** Store datetimes as ISO strings in UTC.
- [ ] **Step 4: Run** `uv run pytest -v`. Expected: all PASS.
- [ ] **Step 5: Commit** `"feat: SQLite post store"`.

---

### Task 4: Gathering (fetch, backfill, hourly) and CLI fetch/backfill

**Files:**
- Create: `src/wowforever/gather.py`, `src/wowforever/cli.py`
- Test: `tests/test_gather.py`

**Interfaces:**
- Consumes: `fetch_listing`, `parse_listing`, `FetchError`, `ParseError` (Task 1); `to_post` (Task 2); `Store` (Task 3).
- Produces:
  - `fetch_latest(store: Store, fetch: Callable[[int], str] = fetch_listing) -> tuple[int, int]` — page 1 only.
  - `backfill(store: Store, fetch=fetch_listing, cutoff: datetime = BACKFILL_CUTOFF, max_pages: int = 40, delay: float = 1.0) -> tuple[int, int]` — pages 1, 2, … until `has_next` is false, or the oldest blog on a page is older than `cutoff`, or `max_pages`. `BACKFILL_CUTOFF = datetime(2026, 8, 1, tzinfo=UTC)` (before the WoW Forever announcement/beta). Sleep `delay` seconds between pages.
  - `start_hourly(store: Store, interval: float = 3600, fetch=fetch_listing) -> threading.Thread` — daemon thread: run `fetch_latest` immediately, then every `interval`; catches `FetchError`/`ParseError`, logs `logger.warning("Gathering failed: %s", err)`, keeps looping.
  - `cli.main(argv: list[str] | None = None) -> int` with subcommands `fetch`, `backfill`, `serve` (serve wired in Task 5) and `--db PATH` (default `instance/wowforever.sqlite3`, parent dir created). `fetch`/`backfill` print `Added N, updated M WoW Forever posts.` and return 0; on `FetchError`/`ParseError` print `Could not gather from Blizzard: <err>` to stderr and return 1.

Each page is upserted only after it parsed successfully. In `backfill`, a page that fails stops the run and the error propagates; pages stored before it stay stored. No article pages are fetched: the listing's embedded blog data already carries title, description and `updated`, so edits are detected from it.

- [ ] **Step 1: Write failing tests** using fixtures and a fake `fetch` (`lambda n: FIXTURES[n]`):
  - `test_fetch_latest_stores_forever_posts`: `Store(":memory:")` → added ≥ 1, no non-Forever titles stored.
  - `test_fetch_latest_twice_adds_nothing`: second call returns `(0, 0)`.
  - `test_backfill_walks_pages`: fake serves page1/page2 fixtures and records calls; `backfill(store, fetch=fake, max_pages=2, delay=0, cutoff=datetime(2000,1,1,tzinfo=UTC))` → called with `[1, 2]`, posts from both fixtures stored.
  - `test_backfill_stops_when_no_next`: fake serves page 1 with `"next":"/en-us/news?page=3"` replaced by `"next":null` → called only with `[1]`.
  - `test_backfill_stops_at_cutoff`: `cutoff=datetime(2030,1,1,tzinfo=UTC)` → called only with `[1]`.
  - `test_fetch_error_leaves_store_untouched`: pre-filled store, fake raises `FetchError` → `fetch_latest` raises, `count_posts()` unchanged.
  - `test_hourly_survives_errors(caplog)`: fake fails first call, succeeds second; `start_hourly(store, interval=0.01, fetch=fake)`; wait until store has posts (poll ≤ 2 s) → posts present and `"Gathering failed"` in `caplog.text`.
  - `test_cli_fetch_reports_failure(monkeypatch, tmp_path, capsys)`: patch `wowforever.gather.fetch_listing`/cli's reference to raise `FetchError("offline")` → `main(["--db", str(tmp_path/"d.sqlite3"), "fetch"]) == 1`, stderr contains `Could not gather from Blizzard`.

- [ ] **Step 2: Run** `uv run pytest tests/test_gather.py -v`. Expected: FAIL.
- [ ] **Step 3: Implement `gather.py` and `cli.py`** (argparse; configure `logging.basicConfig(level=INFO)` in `main`).
- [ ] **Step 4: Run** `uv run pytest -v`. Expected: all PASS.
- [ ] **Step 5: Live check** `uv run wowforever fetch`. Expected: `Added N, updated 0 WoW Forever posts.` with N ≥ 1. Then `uv run wowforever backfill`. Expected: exits 0, more posts added.
- [ ] **Step 6: Commit** `"feat: gather posts from Blizzard (fetch, backfill, hourly)"`.

---

### Task 5: Website (pages, countdown, Bronze & Stone theme, serve)

**Files:**
- Create: `src/wowforever/web.py`, `src/wowforever/countdown.py`
- Create: `src/wowforever/templates/base.html`, `feed.html`, `patches.html`, `patch.html`
- Create: `src/wowforever/static/style.css`
- Modify: `src/wowforever/cli.py` (`serve` subcommand)
- Test: `tests/test_countdown.py`, `tests/test_web.py`

**Interfaces:**
- Consumes: `Store` and its methods (Task 3); `start_hourly` (Task 4).
- Produces:
  - `launch_banner(now: datetime) -> str`; `LAUNCH = datetime(2026, 11, 4, 23, 0, tzinfo=UTC)`
  - `create_app(store: Store) -> Flask`
  - `serve`: `wowforever serve [--port 5000]` → opens Store, `start_hourly(store)`, `app.run(host="127.0.0.1", port=port, use_reloader=False)`.

Countdown copy (pinned), counting whole days by UTC calendar date difference between `now` and `LAUNCH`:
- before launch, ≥ 2 days: `Launches Nov 4 · N days to go`
- 1 day: `Launches Nov 4 · 1 day to go`
- same date, before 23:00 UTC: `Launches today · Nov 4, 3:00 p.m. PST`
- at/after `LAUNCH`: `Live since Nov 4`

Routes:
- `/` — banner + feed of all posts, 20 per page (`?page=N`, "Older posts →" / "← Newer posts" links; invalid or out-of-range page → 404).
- `/news` — same feed with `kind="news"` only.
- `/patches` — versioned patches (`list_patches`) newest first, each linking to `/patches/<version>` with date and post count; below, a "Hotfixes & update notes" list from `unversioned_patch_posts`.
- `/patches/<version>` — version heading, release date (first post), its posts as entries; unknown version → 404.
- Every entry card: type icon (📰 news / 🛠 patch), date (e.g. `Oct 22, 2026`), title, summary, `Updated Oct 22` label when `edited_at` is set, link `Read on Blizzard.com →` (`rel="noopener"`, `target="_blank"`).
- Empty store → the pinned empty-state copy instead of the list (all list pages).
- `base.html`: header `WOW FOREVER TRACKER` with nav (Home, News, Patches), footer copy, Google Fonts link for Cinzel 600/800 + Inter 400/600, `<meta name="viewport" content="width=device-width, initial-scale=1">`, `<title>` per page (e.g. `WoW Forever Patches · WoW Forever Tracker`), `<meta name="description">`.
- `style.css`: Bronze & Stone per Global Constraints and the approved mockup (dark stone gradient nav with 2 px `#8c5a2b` bottom border; banner bronze gradient `#5a3a1c → #8c5a2b` with `#ffe2a8` text; cards `#211b15` with `1px #4a3725` border and `3px #b5773a` left edge; links `#d9a35b`; visible focus outline). Single column, max-width ~760 px, 16 px side padding.

- [ ] **Step 1: Write failing countdown tests** for each copy line: `now=2026-10-26 12:00Z` → `"Launches Nov 4 · 9 days to go"`; `2026-11-03 12:00Z` → `"… 1 day to go"`; `2026-11-04 10:00Z` → `"Launches today · Nov 4, 3:00 p.m. PST"`; `2026-11-04 22:00Z` and `2026-12-01` → `"Live since Nov 4"`.
- [ ] **Step 2: Write failing web tests** with `create_app(store).test_client()` and a `Store(":memory:")` filled via `make_post`:
  - `test_empty_store_shows_empty_message` for `/`, `/news`, `/patches` (200, contains `No WoW Forever posts gathered yet`).
  - `test_home_lists_posts_with_link_and_footer`: contains a post title, `Read on Blizzard.com`, its full Blizzard URL, and `Unofficial fan site. Not affiliated with Blizzard Entertainment.`
  - `test_news_excludes_patch_posts`.
  - `test_patch_page_and_unknown_version`: `/patches/1.60.1` 200 with its post; `/patches/9.9` 404.
  - `test_pagination`: 25 posts → `/` has 20 entries and "Older posts", `/?page=2` has 5, `/?page=3` 404, `/?page=abc` 404.
  - `test_html_in_title_is_escaped`: post titled `<script>alert(1)</script>` → response contains `&lt;script&gt;`, not the raw tag.
  - `test_edited_label`: post with `edited_at` → `Updated` label present.
- [ ] **Step 3: Run** `uv run pytest tests/test_countdown.py tests/test_web.py -v`. Expected: FAIL.
- [ ] **Step 4: Implement** `countdown.py`, `web.py`, templates, `style.css`, and the `serve` subcommand. Dates formatted with a Jinja filter (no locale dependence).
- [ ] **Step 5: Run** `uv run pytest -v`. Expected: all PASS.
- [ ] **Step 6: Live check.** `uv run wowforever serve` (background), then `curl -s localhost:5000/ | grep -c "Read on Blizzard.com"` ≥ 1, and `/news`, `/patches` return 200. Open in a browser at desktop and 360 px width: Bronze & Stone look matches the approved mockup, no horizontal scroll. Stop the server.
- [ ] **Step 7: Add `README.md`** with the three commands (`uv sync`, `uv run wowforever backfill`, `uv run wowforever serve` → http://127.0.0.1:5000) and the unofficial-fan-site note.
- [ ] **Step 8: Commit** `"feat: WoW Forever tracker website with Bronze & Stone theme"`.
