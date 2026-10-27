"""What changed in the game data between two refreshes of gamedata.json: abilities, talents, racials, recipes and items.

`wowforever gamedata` records the changes in gamechanges.json when the client build changes; the Game data changes
page shows them, including the changes Blizzard's patch notes leave out.
"""

import difflib
import json
from datetime import date
from html import escape
from pathlib import Path

from markupsafe import Markup

CHANGES_FILE = Path(__file__).parent / "gamechanges.json"


def _field(name: str, before, after) -> dict | None:
    return None if before == after else {"field": name, "before": before, "after": after}


def _compare(section: str, what: str, old: dict, new: dict, fields) -> list[dict]:
    """Added, removed and changed entries between two {name: entry} maps; `fields(before, after)` lists the changes."""
    out = []
    for name in sorted(old.keys() | new.keys()):
        if name not in old:
            out.append({"section": section, "what": what, "name": name, "change": "added", "details": []})
        elif name not in new:
            out.append({"section": section, "what": what, "name": name, "change": "removed", "details": []})
        elif details := [d for d in fields(old[name], new[name]) if d]:
            out.append({"section": section, "what": what, "name": name, "change": "changed", "details": details})
    return out


def _ability(a: dict, b: dict) -> list:
    return [_field("Learned at level", a["level"], b["level"]), _field("Later ranks at", ", ".join(map(str, a["ranks"])), ", ".join(map(str, b["ranks"]))),
            _field("Description", a["description"], b["description"])]


def _talent(a: dict, b: dict) -> list:
    return [_field("Ranks", len(a["ranks"]), len(b["ranks"])),
            _field("Position", f"row {a['tier'] + 1}, column {a['column'] + 1}", f"row {b['tier'] + 1}, column {b['column'] + 1}"),
            *(_field(f"Rank {i + 1}", x, y) for i, (x, y) in enumerate(zip(a["ranks"], b["ranks"])))]


def _racial(a: dict, b: dict) -> list:
    return [_field("Description", a["description"], b["description"])]


def _recipe(a: dict, b: dict) -> list:
    reagents = lambda r: ", ".join(f"{count} {name}" if count > 1 else name for count, name, _ in r["reagents"])
    item = lambda r: r["item"] or {}
    return [_field("Turns yellow at", a["yellow"], b["yellow"]), _field("Turns grey at", a["grey"], b["grey"]),
            _field("Learned from", a["source"], b["source"]), _field("Skill to learn", a["skill"], b["skill"]),
            _field("Reagents", reagents(a), reagents(b)), _field("Makes", a["makes"], b["makes"]),
            _field("Item", item(a).get("lines"), item(b).get("lines")),
            _field("Item effects", item(a).get("effects"), item(b).get("effects")),
            _field("Description", a["description"], b["description"])]


def _item(a: dict, b: dict) -> list:
    return [_field("Name", a["name"], b["name"]), _field("Quality", a["quality"], b["quality"]),
            _field("Item level", a["level"], b["level"]), _field("Tooltip", a["lines"], b["lines"]),
            _field("Effects", a["effects"], b["effects"])]


def changes(old: dict, new: dict) -> list[dict]:
    """Every difference between two versions of gamedata.json, by class, race, profession and "Items"."""
    out = []
    for cls in new["classes"]:
        a, b = old["classes"].get(cls, {"abilities": [], "talents": []}), new["classes"][cls]
        out += _compare(cls, "ability", {x["name"]: x for x in a["abilities"]}, {x["name"]: x for x in b["abilities"]},
                        _ability)
        # by tree too: Rogues have a Hack and Slash in two trees
        talents = lambda data: {f"{t['name']} ({tree['name']})": t for tree in data["talents"] for t in tree["talents"]}
        out += _compare(cls, "talent", talents(a), talents(b), _talent)
    for race in old["races"].keys() | new["races"].keys():
        out += _compare(race, "racial", {x["name"]: x for x in old["races"].get(race, [])},
                        {x["name"]: x for x in new["races"].get(race, [])}, _racial)
    for profession in old["professions"].keys() | new["professions"].keys():
        out += _compare(profession, "recipe", {x["name"]: x for x in old["professions"].get(profession, [])},
                        {x["name"]: x for x in new["professions"].get(profession, [])}, _recipe)
    by_id = lambda data: {i["id"]: i for i in data.get("items", [])}
    items = _compare("Items", "item", by_id(old), by_id(new), _item)
    names = {**by_id(old), **by_id(new)}
    out += [{**change, "name": names[change["name"]]["name"]} for change in items]
    return out


def record(old: dict, new: dict, today: date) -> int:
    """Add the changes from `old` to `new` to the top of the changes file; returns how many there were."""
    found = changes(old, new)
    if found:
        history = load()
        history.insert(0, {"date": today.isoformat(), "from": old["build"], "to": new["build"], "changes": found})
        CHANGES_FILE.write_text(json.dumps(history, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return len(found)


def load() -> list[dict]:
    return json.loads(CHANGES_FILE.read_text(encoding="utf-8")) if CHANGES_FILE.exists() else []


def by_section(found: list[dict]) -> dict[str, list[dict]]:
    """Changes grouped by class, race, profession and "Items", in that order."""
    out: dict[str, list[dict]] = {}
    for change in found:
        out.setdefault(change["section"], []).append(change)
    return out


def word_diff(before, after) -> Markup:
    """`after`, with the words that are new marked <ins> and the ones that are gone <del>; tooltip lines (lists)
    are compared line by line."""
    lines = isinstance(before, list) or isinstance(after, list)
    split = (lambda x: list(x or [])) if lines else (lambda x: str(x).split(" ") if x not in (None, "") else [])
    joiner = "<br>" if lines else " "
    show = lambda part: joiner.join(map(escape, part))
    a, b = split(before), split(after)
    out = []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if op in ("delete", "replace"):
            out.append(f"<del>{show(a[i1:i2])}</del>")
        if op in ("insert", "replace"):
            out.append(f"<ins>{show(b[j1:j2])}</ins>")
        if op == "equal":
            out.append(show(a[i1:i2]))
    return Markup(joiner.join(out))
