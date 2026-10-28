"""Ability, talent, racial and item names in patch notes and blue posts, marked for their in-game tooltip.

`tooltips` is the data behind the tooltips (served as /tooltips.json); `Linker.link` wraps each name in the post
HTML in a span that gamelinks.js gives that tooltip.
"""

import re
from html import escape, unescape

from markupsafe import Markup

from wowforever.gamedata import current_races

# Names that are also everyday English or Blizzard's own name; at the start of a sentence they would be linked by
# mistake. shortcut: a fixed list, read off the names in gamedata.json; add to it when a new patch shows a bad link.
COMMON_WORDS = {
    "Aftermath", "Aggression", "Anticipation", "Apocalypse", "Bane", "Bastion", "Blizzard", "Cataclysm", "Concussion",
    "Conviction", "Cruelty", "Cultivation", "Darkness", "Deadliness", "Deflection", "Devastation", "Efficiency",
    "Endurance", "Entrapment", "Feedback", "Ferocity", "Hardiness", "Illumination", "Impact", "Initiative",
    "Inspiration", "Intensity", "Lethality", "Malice", "Martyrdom", "Meditation", "Murder", "Naturalist",
    "Opportunity", "Perception", "Precision", "Purification", "Quickness", "Reckoning", "Redemption", "Reflection",
    "Regeneration", "Resurrection", "Ruin", "Ruthlessness", "Savage", "Setup", "Subtlety", "Suppression",
    "Survivalist", "Toughness", "Vengeance", "Venom", "Vigor", "Vindication",
}
_QUOTE = "(?:'|’|&#39;)"  # escaped text (a blue post excerpt) has &#39;
_TAG = re.compile(r"(<[^>]*>)")
_SKIP = {"a", "code", "pre"}  # text that is already a link, or not prose
# A capitalized word right before a name usually means the name is the end of a longer one we don't know
# ("Missile Barrage", "Desert Crawler's Claw", "Improved Holy Strike"). These words, class, race and talent tree
# names, and a verb starting the sentence ("Reduced Penance", "Using Skysight") don't.
_LEAD_INS = {"The", "A", "An", "Your", "Rank", "Talent", "Racial", "Pet", "Since", "When", "If", "While", "After",
             "Both", "All", "Each", "Only"}
_PREVIOUS_WORD = re.compile(r"(?<![\w’'-])([A-Z][\w-]*)(?:[’']s)? $")


def _key(*parts: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", " ".join(parts).lower()).strip("-")


def tooltips(game: dict) -> dict[str, dict]:
    """Every linkable name's tooltip, by key: name, icon, kind (the line under the name), owner (its class or race,
    or None), and the tooltip's text lines."""
    out = {}
    for cls, data in game["classes"].items():
        for ability in data["abilities"]:
            ranks = f" · later ranks at {', '.join(map(str, ability['ranks']))}" if ability["ranks"] else ""
            out[_key(cls, ability["name"])] = {
                "name": ability["name"], "icon": ability["icon"], "owner": cls,
                "kind": f"{cls} {'talent' if ability['talent'] else 'ability'} · Level {ability['level']}{ranks}",
                "desc": ability["description"]}
        for tree in data["talents"]:
            for talent in tree["talents"]:
                key = _key(cls, talent["name"])
                if key in out:
                    continue  # a talent that is also an ability: the ability tooltip already says "talent"
                ranks = len(talent["ranks"])
                out[key] = {"name": talent["name"], "icon": talent["icon"], "owner": cls,
                            "kind": f"{cls} talent · {tree['name']}, {ranks} rank{'s' if ranks > 1 else ''}",
                            "desc": next((r for r in talent["ranks"] if r), None)}
    for race, racials in current_races(game).items():
        for racial in racials:
            out[_key(race, racial["name"])] = {"name": racial["name"], "icon": racial["icon"], "owner": race,
                                              "kind": f"{race} racial", "desc": racial["description"]}
    for recipes in game["professions"].values():
        for recipe in recipes:
            item = recipe.get("item")
            if item and _key("item", item["name"]) not in out:
                out[_key("item", item["name"])] = {
                    "name": item["name"], "icon": recipe["icon"], "owner": None, "quality": item["quality"],
                    "kind": item["slot"] or "Item", "lines": item["lines"], "effects": item["effects"],
                    "desc": item["description"]}
    for item in game["items"]:
        # one-word names ("Bracers", "Gloves") are too likely to be plain words
        if item["quality"] >= 2 and " " in item["name"] and _key("item", item["name"]) not in out:
            out[_key("item", item["name"])] = {
                "name": item["name"], "icon": item["icon"], "owner": None, "quality": item["quality"],
                "kind": f"Item level {item['level']}", "lines": item["lines"], "effects": item["effects"],
                "desc": item["description"]}
    return out


def keys_in(html: str) -> set[str]:
    """The tooltips that linked HTML uses."""
    return set(re.findall(r'class="gl" tabindex="0" data-tip="([^"]+)"', html))


class Linker:
    """Marks the names in post HTML that have a tooltip."""

    def __init__(self, game: dict):
        tips = tooltips(game)
        self.by_name: dict[str, list[str]] = {}
        for key, tip in tips.items():
            if tip["name"] not in COMMON_WORDS:
                self.by_name.setdefault(tip["name"].replace("’", "'"), []).append(key)
        self.tips = tips
        self.sections = {tip["owner"] for tip in tips.values() if tip["owner"]}  # the classes and races
        trees = {tree["name"] for data in game["classes"].values() for tree in data["talents"]}
        self.lead_ins = _LEAD_INS | self.sections | trees
        # Longest first, so "Improved Charge" wins over "Charge"; a quote matches both ' and ’.
        names = sorted(self.by_name, key=len, reverse=True)
        alternatives = "|".join(re.escape(escape(n, quote=False)).replace("'", _QUOTE) for n in names)
        self.pattern = re.compile(rf"(?<![\w-])(?:{alternatives})(?![\w-])")

    def key_for(self, name: str, section: str | None) -> str | None:
        """The tooltip a name gets: its own section's (class or race) when it has one; else the only tooltip with
        that name, or none when classes share the name but not the text."""
        keys = self.by_name.get(name.replace("’", "'"), [])
        own = [k for k in keys if self.tips[k]["owner"] == section]
        if own:
            return own[0]
        if len({self.tips[k]["desc"] for k in keys}) == 1:
            return keys[0]
        return None

    def link(self, html: str | None, section: str | None = None) -> Markup:
        """`html` with every known name wrapped in <span class="gl" data-tip="key">. `section` is the class or race
        the text is about; in full patch notes it follows the class and race headings."""
        if not html:
            return Markup(html or "")
        out, skipping = [], 0
        for part in _TAG.split(html):
            if part.startswith("<"):
                tag = re.match(r"</?([a-zA-Z0-9]+)", part)
                if tag and tag.group(1).lower() in _SKIP:
                    skipping += -1 if part.startswith("</") else 1
                out.append(part)
                continue
            heading = part.strip().replace("’", "'")
            if heading in self.sections:
                section = heading
            if skipping > 0 or not part.strip():
                out.append(part)
                continue
            out.append(self.pattern.sub(lambda m: self._wrap(m, section), part))
        return Markup("".join(out))

    def _wrap(self, match: re.Match, section: str | None) -> str:
        text = match.group(0)
        previous = _PREVIOUS_WORD.search(match.string, 0, match.start())
        if previous:
            word = previous.group(1)
            verb = word.endswith(("ed", "ing")) and word != "Improved"
            if not verb and word not in self.lead_ins:
                return text
        key = self.key_for(unescape(text), section)
        return f'<span class="gl" tabindex="0" data-tip="{key}">{text}</span>' if key else text

