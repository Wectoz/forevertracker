"""Class abilities and talents, racials and profession recipes, read from the WoW Forever game client.

`wowforever gamedata` turns the client's tables into gamedata.json (committed); the site only reads that file.
"""

import json
import re
from functools import cache
from pathlib import Path

from wowforever import wdc5
from wowforever.classnotes import CLASSES

DATA_FILE = Path(__file__).parent / "gamedata.json"

# file name (as TACTTool writes it) -> table name in WoWDBDefs
TABLES = {
    "chrclasses": "ChrClasses", "chrraces": "ChrRaces", "skillline": "SkillLine",
    "skilllineability": "SkillLineAbility", "spellname": "SpellName", "spell": "Spell",
    "spelllevels": "SpellLevels", "spelleffect": "SpellEffect", "spellmisc": "SpellMisc",
    "spellduration": "SpellDuration", "spellradius": "SpellRadius", "talent": "Talent", "talenttab": "TalentTab",
    "skillraceclassinfo": "SkillRaceClassInfo", "itemsparse": "ItemSparse", "itemeffect": "ItemEffect", "itemxitemeffect": "ItemXItemEffect",
}

CLASS_SKILLS, SECONDARY_SKILLS, PROFESSIONS = 7, 9, 11  # SkillLine.CategoryID
SECONDARY_PROFESSIONS = {"Cooking", "First Aid", "Fishing"}
PET_TRAINING = "Beast Training"  # the Hunter's pet abilities, taught to pets rather than learned
TEACHES_SPELL = 6  # ItemEffect.TriggerType of a recipe item
LEARNED_WITH_SKILL = 1  # SkillLineAbility.AcquireMethod: known as soon as you learn the profession

# Spell IDs Blizzard used for Season of Discovery. The client still ships them, but they are not part of Forever:
# none of them appear in Forever's patch notes, while Forever's own additions (Riptide, Penance, ...) start at 1235000.
SEASON_OF_DISCOVERY = (range(397000, 470000), range(1200000, 1235000))


def is_season_of_discovery(spell_id: int) -> bool:
    return any(spell_id in ids for ids in SEASON_OF_DISCOVERY)


def read_tables(db2: Path, defs: Path) -> dict[str, dict[int, dict]]:
    return {table: wdc5.read(db2 / f"{name}.db2", table, defs) for name, table in TABLES.items()}


def _num(x: float) -> str:
    x = round(x, 1)
    return str(int(x)) if x == int(x) else str(x)


def _duration(ms: float) -> str:
    seconds = ms / 1000
    if seconds >= 60 and seconds % 60 == 0:
        return f"{int(seconds // 60)} min"
    return f"{_num(seconds)} sec"


_TOKEN = re.compile(r"\$(\d*)([sSmMdDtToOaAxX])(\d?)")
_CONDITION = re.compile(r"\$\?[^\[]*?((?:\[[^\[\]]*\])+)")


class Describer:
    """Spell descriptions with their $-placeholders filled in from the spell's effects."""

    def __init__(self, t: dict[str, dict[int, dict]]):
        self.text = {k: v["Description_lang"] for k, v in t["Spell"].items()}
        self.effects = {(e["SpellID"], e["EffectIndex"]): e for e in t["SpellEffect"].values() if e["DifficultyID"] == 0}
        durations = {k: v["Duration"] for k, v in t["SpellDuration"].items()}
        self.durations = {m["SpellID"]: durations.get(m["DurationIndex"])
                          for m in t["SpellMisc"].values() if m["DifficultyID"] == 0}
        self.radius = {k: v["Radius"] for k, v in t["SpellRadius"].items()}

    def value(self, spell: int, letter: str, index: str, in_formula: bool) -> float | str | None:
        effect = self.effects.get((spell, int(index or 1) - 1))
        duration = self.durations.get(spell)
        period = effect and effect["EffectAuraPeriod"]
        match letter.lower():
            case "s" | "m":
                return effect and abs(effect["EffectBasePointsF"])
            case "d":
                if not duration or duration < 0:
                    return None
                return duration / 1000 if in_formula else _duration(duration)
            case "t":
                return period and period / 1000 or None
            case "o":
                return period and duration and abs(effect["EffectBasePointsF"]) * duration / period or None
            case "x":
                return effect and effect["EffectChainTargets"] or None
            case "a":
                return effect and self.radius.get(effect["EffectRadiusIndex"][0])
        return None

    def __call__(self, spell: int) -> str | None:
        """The description, or None when it is empty or has a placeholder this can't fill."""
        text = self.text.get(spell, "")
        text = re.sub(r"\$[lL]([^:;]*):([^;]*);", r"\2", text)  # singular:plural
        text = re.sub(r"\$[gG]([^:;]*):([^;]*);", r"\1", text)  # male:female
        for _ in range(3):  # talent conditionals, nested: keep the last branch, the spell without the talent
            text = _CONDITION.sub(lambda m: re.findall(r"\[([^\[\]]*)\]", m[1])[-1], text)
        text = re.sub(r"\$/(\d+);(\d*)([sSmMoO])(\d)", lambda m: f"${{${m[2]}{m[3]}{m[4]}/{m[1]}}}", text)
        text = re.sub(r"\$<\w+>", "1", text)  # spell power and other bonuses: the value without them

        def token(m: re.Match, in_formula: bool) -> str:
            v = self.value(int(m[1]) if m[1] else spell, m[2], m[3], in_formula)
            if v is None:
                return m[0]
            return v if isinstance(v, str) else (repr(v) if in_formula else _num(v))

        def formula(m: re.Match) -> str:
            expr = _TOKEN.sub(lambda t: token(t, True), m[1])
            if not re.fullmatch(r"[\d.+\-*/() ]+", expr):
                return m[0]
            try:
                return _num(eval(expr, {"__builtins__": {}}))  # digits and arithmetic only, checked above
            except (SyntaxError, ZeroDivisionError):
                return m[0]

        text = re.sub(r"\$\{([^{}]*)\}(?:\.\d)?", formula, text)
        text = " ".join(_TOKEN.sub(lambda t: token(t, False), text).split())
        return text if text and "$" not in text else None


def _race_mask(row: dict) -> int:
    low, high = row["RaceMasks"]
    return low | high << 32


def _hidden(name: str | None) -> bool:
    """Blizzard's internal spells, marked "do not display" / "do not translate"."""
    return not name or "(DND)" in name or "[DNT]" in name


def _class_data(t, describe, names, levels, bit: int, playable: dict[str, int]) -> dict:
    trees, talent_names = [], set()
    for tab in sorted((v for v in t["TalentTab"].values() if v["ClassMask"] & bit), key=lambda v: v["OrderIndex"]):
        talents = []
        for talent in t["Talent"].values():
            ranks = [s for s in talent["SpellRank"] if s]
            if talent["TabID"] != tab["ID"] or not ranks or _hidden(names.get(ranks[0])) \
                    or is_season_of_discovery(ranks[0]):
                continue
            talents.append({"name": names[ranks[0]], "tier": talent["TierID"], "column": talent["ColumnIndex"],
                            "level": 10 + 5 * talent["TierID"], "ranks": len(ranks), "description": describe(ranks[0])})
        talents.sort(key=lambda x: (x["tier"], x["column"]))
        talent_names |= {x["name"] for x in talents}
        trees.append({"name": tab["Name_lang"], "talents": talents})

    skills = t["SkillLine"]
    lines = {r["SkillID"] for r in t["SkillRaceClassInfo"].values()
             if r["ClassMask"] == bit and r["SkillID"] in skills and skills[r["SkillID"]]["CategoryID"] == CLASS_SKILLS
             and skills[r["SkillID"]]["DisplayName_lang"] != PET_TRAINING}
    everyone = sum(1 << b for b in playable.values())
    ranks_by_name: dict[str, dict[int, dict]] = {}
    for row in t["SkillLineAbility"].values():
        spell = row["Spell"]
        if (row["SkillLine"] not in lines or row["ClassMask"] and not row["ClassMask"] & bit
                or is_season_of_discovery(spell) or levels.get(spell, 0) < 1 or _hidden(names.get(spell))):
            continue
        ranks_by_name.setdefault(names[spell], {}).setdefault(levels[spell], row)
    abilities = []
    for name, by_level in ranks_by_name.items():
        if name in talent_names and len(by_level) == 1:
            continue  # a talent with nothing to train: it is on the Talents tab
        (level, first), *later = sorted(by_level.items())
        mask = _race_mask(first) & everyone
        abilities.append({
            "name": name, "level": level, "ranks": [lvl for lvl, _ in later], "talent": name in talent_names,
            "races": [] if mask in (0, everyone) else [r for r, b in playable.items() if mask >> b & 1],
            "description": describe(first["Spell"]),
        })
    abilities.sort(key=lambda a: (a["level"], a["name"]))
    return {"abilities": abilities, "talents": trees}


def _races(t, describe, names) -> dict:
    lines = {k for k, v in t["SkillLine"].items()
             if v["CategoryID"] == SECONDARY_SKILLS and "Racial" in v["DisplayName_lang"]}
    rows = [r for r in t["SkillLineAbility"].values()
            if r["SkillLine"] in lines and not _hidden(names.get(r["Spell"])) and not is_season_of_discovery(r["Spell"])]
    races = {}
    for race_id, race in sorted(t["ChrRaces"].items()):
        bit = race.get("PlayableRaceBit", -1)
        if bit < 0:
            continue
        racials = {}
        for r in sorted(rows, key=lambda r: r["Spell"]):
            if _race_mask(r) >> bit & 1:
                # one entry per name: some racials are separate spells per class with the same name
                racials.setdefault(names[r["Spell"]], describe(r["Spell"]))
        if racials:
            races[race["Name_lang"]] = {"bit": bit, "racials": [{"name": n, "description": d} for n, d in racials.items()]}
    return races


def _professions(t, names) -> dict:
    effects = t["ItemEffect"]
    taught: dict[int, list[int]] = {}
    for link in t["ItemXItemEffect"].values():
        effect = effects.get(link["ItemEffectID"])
        if effect and effect["TriggerType"] == TEACHES_SPELL:
            taught.setdefault(effect["SpellID"], []).append(link["ItemID"])
    items = t["ItemSparse"]
    lines = {k: v["DisplayName_lang"] for k, v in t["SkillLine"].items()
             if v["CategoryID"] == PROFESSIONS and "[DNT]" not in v["DisplayName_lang"] or (v["CategoryID"] == SECONDARY_SKILLS
                                                   and v["DisplayName_lang"] in SECONDARY_PROFESSIONS)}
    out: dict[str, list] = {}
    for row in sorted(t["SkillLineAbility"].values(), key=lambda r: r["Spell"]):
        spell, line = row["Spell"], row["SkillLine"]
        if line not in lines or row["TrivialSkillLineRankHigh"] <= 1 or not names.get(spell) \
                or is_season_of_discovery(spell):
            continue  # no skill-up range: the profession's own spells (ranks, Find Fish), not recipes
        recipe = {"name": names[spell], "yellow": row["TrivialSkillLineRankLow"],
                  "grey": row["TrivialSkillLineRankHigh"], "source": "Trainer", "skill": None}
        item = next((items[i] for i in taught.get(spell, []) if items.get(i, {}).get("Display_lang")), None)
        if item:
            recipe.update(source=item["Display_lang"], skill=item["RequiredSkillRank"] or None)
        elif row["AcquireMethod"] == LEARNED_WITH_SKILL:
            recipe["source"] = "Known when you learn the profession"
        out.setdefault(lines[line], []).append(recipe)
    for recipes in out.values():
        recipes.sort(key=lambda r: (r["yellow"], r["name"]))
    return dict(sorted(out.items()))


def build(t: dict[str, dict[int, dict]], build_name: str) -> dict:
    describe = Describer(t)
    names = {k: v["Name_lang"] for k, v in t["SpellName"].items()}
    levels = {r["SpellID"]: r["SpellLevel"] for r in t["SpellLevels"].values() if r["DifficultyID"] == 0}
    class_ids = {v["Name_lang"]: k for k, v in t["ChrClasses"].items()}
    races = _races(t, describe, names)
    playable = {name: race.pop("bit") for name, race in races.items()}
    return {
        "build": build_name,
        "classes": {cls: _class_data(t, describe, names, levels, 1 << (class_ids[cls] - 1), playable)
                    for cls in CLASSES},
        "races": {name: race["racials"] for name, race in races.items()},
        "professions": _professions(t, names),
    }


def client_build(db2: Path) -> str:
    """The build the tables came from, e.g. "1.60.1.70630", as written in every .db2 header."""
    raw = (db2 / "spell.db2").read_bytes()[8:136].split(b"\0")[0].decode()
    return ".".join(raw.removeprefix("WOWSTATIC_").split("_"))


@cache
def load() -> dict:
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))
