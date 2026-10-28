"""Class abilities and talents, racials and profession recipes, read from the WoW Forever game client.

`wowforever gamedata` turns the client's tables into gamedata.json (committed); the site only reads that file.
"""

import json
import re
import struct
from functools import cache
from pathlib import Path

from wowforever import wdc5
from wowforever.classnotes import CLASSES

DATA_FILE = Path(__file__).parent / "gamedata.json"
ICONS = Path(__file__).parent / "static" / "icons"
QUESTION_MARK = 134400  # the game's own icon for one it can't show
ICON_SIZE = 56  # shown at 28-40 px; big enough for sharp icons on high-density screens

# file name (as TACTTool writes it) -> table name in WoWDBDefs
TABLES = {
    "chrclasses": "ChrClasses", "chrraces": "ChrRaces", "skillline": "SkillLine",
    "skilllineability": "SkillLineAbility", "spellname": "SpellName", "spell": "Spell",
    "spelllevels": "SpellLevels", "spelleffect": "SpellEffect", "spellmisc": "SpellMisc",
    "spellduration": "SpellDuration", "spellradius": "SpellRadius", "talent": "Talent", "talenttab": "TalentTab",
    "skillraceclassinfo": "SkillRaceClassInfo", "itemsparse": "ItemSparse", "itemeffect": "ItemEffect", "itemxitemeffect": "ItemXItemEffect",
    "item": "Item", "spellauraoptions": "SpellAuraOptions", "spelltargetrestrictions": "SpellTargetRestrictions",
    "spellrange": "SpellRange", "spellreagents": "SpellReagents", "randproppoints": "RandPropPoints",
    "itemarmorquality": "ItemArmorQuality", "itemarmortotal": "ItemArmorTotal", "armorlocation": "ArmorLocation",
    "itemarmorshield": "ItemArmorShield", "itemdamageonehand": "ItemDamageOneHand", "itemdamagetwohand": "ItemDamageTwoHand",
    "itemdamageranged": "ItemDamageRanged", "itemdamagewand": "ItemDamageWand",
    "uitextureatlasmember": "UiTextureAtlasMember", "uitextureatlas": "UiTextureAtlas",
    "itemmodifiedappearance": "ItemModifiedAppearance", "itemappearance": "ItemAppearance",
}

CLASS_SKILLS, SECONDARY_SKILLS, PROFESSIONS = 7, 9, 11  # SkillLine.CategoryID
SECONDARY_PROFESSIONS = {"Cooking", "First Aid", "Fishing"}
PET_TRAINING = "Beast Training"  # the Hunter's pet abilities, taught to pets rather than learned
TEACHES_SPELL = 6  # ItemEffect.TriggerType of a recipe item
CREATE_ITEM = 24  # SpellEffect.Effect of a recipe that makes an item
LEARNED_WITH_SKILL = 1  # SkillLineAbility.AcquireMethod: known as soon as you learn the profession

# What an item tooltip says, by the client's codes (Item, ItemSparse, ItemEffect).
WEAPON, ARMOR, ROBE, CHEST = 2, 4, 20, 5
SLOTS = {1: "Head", 2: "Neck", 3: "Shoulder", 4: "Shirt", 5: "Chest", 6: "Waist", 7: "Legs", 8: "Feet", 9: "Wrist",
         10: "Hands", 11: "Finger", 12: "Trinket", 13: "One-Hand", 14: "Off Hand", 15: "Ranged", 16: "Back",
         17: "Two-Hand", 19: "Tabard", 20: "Chest", 21: "Main Hand", 22: "Off Hand", 23: "Held In Off-hand",
         24: "Ammo", 25: "Thrown", 26: "Ranged", 28: "Relic"}
ARMOR_TYPES = {1: "Cloth", 2: "Leather", 3: "Mail", 4: "Plate", 6: "Shield"}
WEAPON_TYPES = {0: "Axe", 1: "Axe", 2: "Bow", 3: "Gun", 4: "Mace", 5: "Mace", 6: "Polearm", 7: "Sword", 8: "Sword",
                10: "Staff", 13: "Fist Weapon", 15: "Dagger", 16: "Thrown", 18: "Crossbow", 19: "Wand", 20: "Fishing Pole"}
BONDING = {1: "Binds when picked up", 2: "Binds when equipped", 3: "Binds when used"}
EFFECT_PREFIX = {0: "Use", 1: "Equip", 2: "Chance on hit"}  # ItemEffect.TriggerType
STATS = {3: "Agility", 4: "Strength", 5: "Intellect", 6: "Spirit", 7: "Stamina", 51: "Fire Resistance",
         52: "Frost Resistance", 53: "Holy Resistance", 54: "Shadow Resistance", 55: "Nature Resistance",
         56: "Arcane Resistance"}
EQUIP_STATS = {  # shortcut: only the stats Classic crafted items use; others are left off the tooltip
    31: lambda n: f"Improves your chance to hit by {_num(n / 10)}%.",  # 10 rating per 1% at level 60
    32: lambda n: f"Improves your chance to get a critical strike by {_num(n / 14)}%.",  # 14 rating per 1%
    38: lambda n: f"+{n} Attack Power.",
    41: lambda n: f"Increases healing done by spells and effects by up to {n}.",
    42: lambda n: f"Increases damage done by magical spells and effects by up to {n}.",
    43: lambda n: f"Restores {n} mana per 5 sec.",
    45: lambda n: f"Increases damage and healing done by magical spells and effects by up to {n}.",
}
BONUS_ARMOR = 50
# RandPropPoints column for a slot's stat budget: big slots, medium slots, small slots, one-hand, ranged
BUDGET_COLUMN = {1: 0, 5: 0, 7: 0, 17: 0, 20: 0, 3: 1, 6: 1, 8: 1, 10: 1, 12: 1, 2: 2, 9: 2, 11: 2, 14: 2, 16: 2,
                 23: 2, 13: 3, 21: 3, 22: 3, 15: 4, 25: 4, 26: 4}
BUDGET = {2: "Good", 3: "Superior", 4: "Epic"}  # by OverallQualityID; lower qualities have no stats

# The Items page: gear and bags of common quality and up.
CONTAINER, QUIVER = 1, 11
LISTED_ITEMS = {WEAPON, ARMOR, CONTAINER, QUIVER}
# Blizzard's test, template and placeholder gear: "90 Epic Rogue Cap", "(OLD)Heavy Throwing Axe", "Monster - Bow",
# "QATest +1000 Spell Dmg Ring", "Gamemaster's Robe", "Black Leather D02 Boots", "Template Item".
_TEST_ITEM = re.compile(r"(?i)^\d|^\(old\)|^(?-i:OLD[A-Z ])|^monster - |\[|\b(?:test|qa|qatest|deprecated|unused|placeholder|template"
                        r"|gamemaster|dnd|dnt|ph)\b|\b(?-i:[A-Z]0\d)\b")
# Item IDs of Season of Discovery's own items, still in the client. Forever reuses some (Greater Mystic Wand); those
# are kept when a Forever recipe makes them.
SEASON_OF_DISCOVERY_ITEMS = range(190000, 240000)

# Spell IDs Blizzard used for Season of Discovery. The client still ships them, but they are not part of Forever:
# none of them appear in Forever's patch notes, while Forever's own additions (Riptide, Penance, ...) start at 1235000.
SEASON_OF_DISCOVERY = (range(397000, 470000), range(1200000, 1235000))


def is_season_of_discovery(spell_id: int) -> bool:
    return any(spell_id in ids for ids in SEASON_OF_DISCOVERY)


def read_tables(db2: Path, defs: Path) -> dict[str, dict[int, dict]]:
    return {table: wdc5.read(db2 / f"{name}.db2", table, defs) for name, table in TABLES.items()}


def apply_hotfixes(t: dict[str, dict[int, dict]], db2: Path, defs: Path, cache: Path) -> int:
    """Patch the tables with the client's hotfix cache, where Blizzard ships most changes between client patches
    (and the text of most talent ranks); returns the build the cache is from."""
    tables = {}
    for name, table in TABLES.items():
        table_hash, layout_hash = wdc5.table_hashes(db2 / f"{name}.db2")
        tables[table_hash] = (table, wdc5.parse_dbd(defs, table, layout_hash))
    build, fixes = wdc5.read_hotfixes(cache, tables)
    for table, rows in fixes.items():
        for rid, row in rows.items():
            if row is None:
                t[table].pop(rid, None)
            else:
                t[table][rid] = row
    return build


def _num(x: float) -> str:
    x = round(x, 1)
    return str(int(x)) if x == int(x) else str(x)


def _duration(ms: float) -> str:
    seconds = ms / 1000
    if seconds >= 60 and seconds % 60 == 0:
        return f"{int(seconds // 60)} min"
    return f"{_num(seconds)} sec"


_TOKEN = re.compile(r"\$(\d*)([sSmMwWdDtToOaAxXnNhHuUiIvVqQbBeErR])(\d?)")
# attack power, spell power, spirit and other character stats: the value without them
_STAT = re.compile(r"\$(?:rap|apm|ap|sp[a-z]*|bh|bc|pl|mws|mwb)\b", re.IGNORECASE)
_CONDITION = re.compile(r"\$\?[^\[]*?((?:\[[^\[\]]*\])+)")


class Describer:
    """Spell descriptions with their $-placeholders filled in from the spell's effects."""

    def __init__(self, t: dict[str, dict[int, dict]]):
        # passive auras often only have the text shown on the buff
        self.text = {k: v["Description_lang"] or v.get("AuraDescription_lang", "") for k, v in t["Spell"].items()}
        self.effects = {(e["SpellID"], e["EffectIndex"]): e for e in t["SpellEffect"].values() if e["DifficultyID"] == 0}
        durations = {k: v["Duration"] for k, v in t["SpellDuration"].items()}
        ranges = {k: v["RangeMax"][0] for k, v in t["SpellRange"].items()}
        misc = [m for m in t["SpellMisc"].values() if m["DifficultyID"] == 0]
        self.durations = {m["SpellID"]: durations.get(m["DurationIndex"]) for m in misc}
        self.ranges = {m["SpellID"]: ranges.get(m.get("RangeIndex")) for m in misc}
        self.radius = {k: v["Radius"] for k, v in t["SpellRadius"].items()}
        self.aura = {r["SpellID"]: r for r in t["SpellAuraOptions"].values() if r["DifficultyID"] == 0}
        self.targets = {r["SpellID"]: r for r in t["SpellTargetRestrictions"].values() if r["DifficultyID"] == 0}

    def value(self, spell: int, letter: str, index: str, in_formula: bool) -> float | str | None:
        effect = self.effects.get((spell, int(index or 1) - 1))
        duration = self.durations.get(spell)
        period = effect and effect["EffectAuraPeriod"]
        aura, targets = self.aura.get(spell, {}), self.targets.get(spell, {})
        match letter.lower():
            case "s" | "m" | "w":
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
            case "a":  # the radius is in either slot
                return effect and self.radius.get(effect["EffectRadiusIndex"][0] or effect["EffectRadiusIndex"][1])
            case "n":
                return aura.get("ProcCharges") or None
            case "h":
                return aura.get("ProcChance") or None
            case "u":
                return aura.get("CumulativeAura") or None
            case "i":
                return targets.get("MaxTargets") or None
            case "v":
                return targets.get("MaxTargetLevel") or None
            case "q":
                return effect and effect["EffectMiscValue"][0]
            case "b":
                return effect and effect["EffectPointsPerResource"]
            case "e":
                return effect and effect["EffectAmplitude"]
            case "r":
                return self.ranges.get(spell) or None
        return None

    def __call__(self, spell: int, depth: int = 0) -> str | None:
        """The description, or None when it is empty or has a placeholder this can't fill."""
        text = self.text.get(spell, "")
        if depth < 2:  # another spell's whole description
            text = re.sub(r"\$@spell(?:desc|tooltip)(\d+)", lambda m: self(int(m[1]), depth + 1) or m[0], text)
        text = re.sub(r"\$[lL]([^:;]*):([^;]*);", r"\2", text)  # singular:plural
        text = re.sub(r"\$[gG]([^:;]*):([^;]*);", r"\1", text)  # male:female
        for _ in range(3):  # talent conditionals, nested: keep the last branch, the spell without the talent
            text = _CONDITION.sub(lambda m: re.findall(r"\[([^\[\]]*)\]", m[1])[-1], text)
        text = re.sub(r"\$([/*])(\d+);(\d*)([sSmMoO])(\d)", lambda m: f"${{${m[3]}{m[4]}{m[5]}{m[1]}{m[2]}}}", text)
        text = re.sub(r"\$\*(?=\$)", "*", text)  # a typo in some of Blizzard's formulas
        text = re.sub(r"\|c[0-9a-fA-F]{8}|\|r", "", text, flags=re.IGNORECASE)  # text colors
        text = re.sub(r"\$<\w+>", "1", text)  # spell power and other bonuses: the value without them
        text = _STAT.sub("0", text)

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
        text = re.sub(r"\b(\d+(?:\.\d+)?) to \1\b", r"\1", text)  # a damage range that only varies with attack power
        return text if text and "$" not in text else None


class ItemTooltip:
    """An item's tooltip: armor, damage and stats are worked out from item level and quality, as the client does."""

    def __init__(self, t: dict[str, dict[int, dict]], describe: Describer):
        self.sparse, self.items, self.describe = t["ItemSparse"], t["Item"], describe
        by_level = lambda table: {r["ItemLevel"]: r for r in t[table].values()}
        self.budget, self.armor_quality, self.armor_location = t["RandPropPoints"], t["ItemArmorQuality"], t["ArmorLocation"]
        self.armor_total, self.shield = by_level("ItemArmorTotal"), by_level("ItemArmorShield")
        self.damage = {name: by_level(f"ItemDamage{name}") for name in ("OneHand", "TwoHand", "Ranged", "Wand")}
        self.effects: dict[int, list[dict]] = {}
        for link in t["ItemXItemEffect"].values():
            effect = t["ItemEffect"].get(link["ItemEffectID"])
            if effect and effect["TriggerType"] in EFFECT_PREFIX:
                self.effects.setdefault(link["ItemID"], []).append(effect)

    def _damage(self, row: dict, item: dict) -> list[str]:
        slot, speed = row["InventoryType"], row.get("ItemDelay", 0) / 1000
        table = ("Wand" if item["SubclassID"] == 19 else "Ranged") if slot in (15, 25, 26) else \
            "TwoHand" if slot == 17 else "OneHand"
        dps = self.damage[table].get(row["ItemLevel"], {}).get("Quality", [0] * 7)[row["OverallQualityID"]]
        if not dps or not speed:
            return []
        hit, spread = dps * speed, row["DmgVariance"] / 2
        return [f"{int(hit * (1 - spread))} - {int(hit * (1 + spread) + .5)} Damage · Speed {speed:.2f}",
                f"({_num(dps)} damage per second)"]

    def _armor(self, row: dict, item: dict, bonus: int) -> int:
        level, quality, sub = row["ItemLevel"], row["OverallQualityID"], item["SubclassID"]
        if sub == 6:
            return round(self.shield.get(level, {}).get("Quality", [0] * 7)[quality]) + bonus
        if not 1 <= sub <= 4:
            return bonus
        location = self.armor_location.get(CHEST if row["InventoryType"] == ROBE else row["InventoryType"])
        total = self.armor_total.get(level)
        if not location or not total or level not in self.armor_quality:
            return bonus
        kind = ("Cloth", "Leather", "Mail", "Plate")[sub - 1]
        modifier = location[("Clothmodifier", "Leathermodifier", "Chainmodifier", "Platemodifier")[sub - 1]]
        return round(total[kind] * modifier * self.armor_quality[level]["Qualitymod"][quality]) + bonus

    def __call__(self, item_id: int) -> dict | None:
        row, item = self.sparse.get(item_id), self.items.get(item_id)
        if not row or not item:
            return None
        quality, slot = row["OverallQualityID"], row["InventoryType"]
        kind = ARMOR_TYPES.get(item["SubclassID"]) if item["ClassID"] == ARMOR else \
            WEAPON_TYPES.get(item["SubclassID"]) if item["ClassID"] == WEAPON else None
        budget = self.budget.get(row["ItemLevel"], {}).get(BUDGET.get(quality), [0] * 5)[BUDGET_COLUMN.get(slot, 0)]
        values = {stat: round(percent * budget / 10000)
                  for stat, percent in zip(row["StatModifier_bonusStat"], row["StatPercentEditor"]) if stat >= 0}
        lines = [BONDING.get(row["Bonding"]), " · ".join(filter(None, [SLOTS.get(slot), kind])) or None]
        if row["ContainerSlots"]:
            lines.append(f"{row['ContainerSlots']} Slot Bag")
        if item["ClassID"] == WEAPON:
            lines += self._damage(row, item)
        armor = self._armor(row, item, values.get(BONUS_ARMOR, 0)) if item["ClassID"] == ARMOR else 0
        lines.append(f"{armor} Armor" if armor else None)
        lines += [f"+{n} {STATS[stat]}" for stat, n in values.items() if stat in STATS and n]
        if row["RequiredLevel"] > 1:
            lines.append(f"Requires Level {row['RequiredLevel']}")
        effects = [f"Equip: {EQUIP_STATS[stat](n)}" for stat, n in values.items() if stat in EQUIP_STATS and n]
        for effect in self.effects.get(item_id, []):
            if text := self.describe(effect["SpellID"]):
                effects.append(f"{EFFECT_PREFIX[effect['TriggerType']]}: {text}")
        return {"name": row["Display_lang"], "quality": quality, "slot": "Bag" if row["ContainerSlots"] else SLOTS.get(slot),
                "lines": [x for x in lines if x],
                "effects": effects, "description": row.get("Description_lang") or None}


def _race_mask(row: dict) -> int:
    low, high = row["RaceMasks"]
    return low | high << 32


def _hidden(name: str | None) -> bool:
    """Blizzard's internal spells, marked "do not display" / "do not translate"."""
    return not name or "(DND)" in name or "[DNT]" in name


def _class_data(t, describe, names, levels, icons, bit: int, playable: dict[str, int]) -> dict:
    trees, talent_names = [], set()
    for tab in sorted((v for v in t["TalentTab"].values() if v["ClassMask"] & bit), key=lambda v: v["OrderIndex"]):
        rows = {}
        for talent_id, talent in t["Talent"].items():
            ranks = [s for s in talent["SpellRank"] if s]
            if talent["TabID"] != tab["ID"] or not ranks or _hidden(names.get(ranks[0])) \
                    or is_season_of_discovery(ranks[0]):
                continue
            rows[talent_id] = talent
        order = sorted(rows, key=lambda i: (rows[i]["TierID"], rows[i]["ColumnIndex"]))
        talents = []
        for talent_id in order:
            talent = rows[talent_id]
            ranks = [s for s in talent["SpellRank"] if s]
            prereq = talent.get("PrereqTalent", [0])[0]
            talents.append({
                "name": names[ranks[0]], "tier": talent["TierID"], "column": talent["ColumnIndex"],
                "icon": icons.get(ranks[0]), "ranks": [describe(r) for r in ranks],
                # [index of the talent in this tree, points it needs]; PrereqRank counts from 0
                "requires": [order.index(prereq), talent["PrereqRank"][0] + 1] if prereq in rows else None,
            })
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
            "icon": icons.get(first["Spell"]),
            # some first ranks have no text of their own; a later rank describes the same ability
            "description": next(filter(None, (describe(row["Spell"]) for _, row in sorted(by_level.items()))), None),
        })
    abilities.sort(key=lambda a: (a["level"], a["name"]))
    return {"abilities": abilities, "talents": trees}


def _races(t, describe, names, icons) -> dict:
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
                racials.setdefault(names[r["Spell"]], {"name": names[r["Spell"]], "icon": icons.get(r["Spell"]),
                                                       "description": describe(r["Spell"])})
        if racials:
            races[race["Name_lang"]] = {"bit": bit, "racials": list(racials.values())}
    return races


def _item_icons(t) -> dict[int, int]:
    """Each item's icon: its own, else its appearance's, which is all most Classic gear has."""
    appearance = {}
    for link in sorted(t["ItemModifiedAppearance"].values(), key=lambda m: -m["OrderIndex"]):
        appearance[link["ItemID"]] = link["ItemAppearanceID"]  # the first appearance (lowest OrderIndex) wins
    out = {}
    for item_id, item in t["Item"].items():
        icon = item.get("IconFileDataID") or t["ItemAppearance"].get(appearance.get(item_id), {}).get("DefaultIconFileDataID")
        if icon:
            out[item_id] = icon
    return out


def _professions(t, describe, names, icons, item_icons) -> dict:
    effects = t["ItemEffect"]
    tooltip = ItemTooltip(t, describe)
    # the profession window shows what a recipe makes; enchants and the like make nothing and show their spell
    made = {e["SpellID"]: e for e in t["SpellEffect"].values() if e["Effect"] == CREATE_ITEM and e["DifficultyID"] == 0}
    reagents = {r["SpellID"]: r for r in t["SpellReagents"].values()}
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
        makes = made.get(spell, {})
        item_icon = item_icons.get(makes.get("EffectItemType"))
        needs = reagents.get(spell, {})
        recipe = {"name": names[spell], "icon": item_icon or icons.get(spell), "yellow": row["TrivialSkillLineRankLow"],
                  "grey": row["TrivialSkillLineRankHigh"], "source": "Trainer", "skill": None,
                  "makes": int(makes.get("EffectBasePointsF", 0)) if makes else 0,
                  "item": makes and tooltip(makes["EffectItemType"]) or None,
                  "description": None if makes else describe(spell),
                  "reagents": [[count, items.get(r, {}).get("Display_lang", "?"), item_icons.get(r)]
                               for r, count in zip(needs.get("Reagent", []), needs.get("ReagentCount", [])) if r]}
        item = next((items[i] for i in taught.get(spell, []) if items.get(i, {}).get("Display_lang")), None)
        if item:
            recipe.update(source=item["Display_lang"], skill=item["RequiredSkillRank"] or None)
        elif row["AcquireMethod"] == LEARNED_WITH_SKILL:
            recipe["source"] = "Starting recipe"
        out.setdefault(lines[line], []).append(recipe)
    for recipes in out.values():
        recipes.sort(key=lambda r: (r["yellow"], r["name"]))
    return dict(sorted(out.items()))


def _items(t, tooltip: ItemTooltip, crafted: dict[str, str], icons: dict[int, int]) -> list[dict]:
    """Every listed item's tooltip, with its icon, item level, required level, type and the profession that makes it."""
    out = []
    for item_id, row in t["ItemSparse"].items():
        item, name = t["Item"].get(item_id), row["Display_lang"]
        # quality 6 is Blizzard's developer gear; above level 60, leftovers from The Burning Crusade
        if not item or item.get("ClassID") not in LISTED_ITEMS or not 1 <= row["OverallQualityID"] <= 5 or not name \
                or row["RequiredLevel"] > 60 or _TEST_ITEM.search(name) \
                or (item_id in SEASON_OF_DISCOVERY_ITEMS and name not in crafted):
            continue
        tip = tooltip(item_id)
        if not tip["slot"]:
            continue  # not worn: warlock stones, seals and the like
        kind = ARMOR_TYPES.get(item["SubclassID"]) if item["ClassID"] == ARMOR else \
            WEAPON_TYPES.get(item["SubclassID"]) if item["ClassID"] == WEAPON else None
        out.append({"id": item_id, "icon": icons.get(item_id), "level": row["ItemLevel"],
                    "required": row["RequiredLevel"], "type": kind, "crafted": crafted.get(name), **tip})
    return sorted(out, key=lambda i: (-i["level"], i["name"]))


def _race_icons(t, races) -> dict:
    """Each race's round portrait from character creation, a piece of a bigger texture: {file ID, [left, top, w, h]}.

    The male one; both Skyborne races share theirs."""
    atlases = t["UiTextureAtlas"]
    members = {(m["CommittedName"] or "").lower(): m for m in t["UiTextureAtlasMember"].values()}
    out = {}
    for race in t["ChrRaces"].values():
        key = race.get("ClientFileString", "").lower().replace("scourge", "undead")
        member = members.get(f"raceicon128-{key}-male") or members.get(f"raceicon128-{key}-male-c60")
        if race["Name_lang"] in races and member and member["UiTextureAtlasID"] in atlases:
            out[race["Name_lang"]] = {"file": atlases[member["UiTextureAtlasID"]]["FileDataID"], "box": [
                member["CommittedLeft"], member["CommittedTop"], member["Width"], member["Height"]]}
    return out


def build(t: dict[str, dict[int, dict]], build_name: str) -> dict:
    describe = Describer(t)
    names = {k: v["Name_lang"] for k, v in t["SpellName"].items()}
    levels = {r["SpellID"]: r["SpellLevel"] for r in t["SpellLevels"].values() if r["DifficultyID"] == 0}
    icons = {m["SpellID"]: m["SpellIconFileDataID"] for m in t["SpellMisc"].values()
             if m["DifficultyID"] == 0 and m["SpellIconFileDataID"]}
    class_ids = {v["Name_lang"]: k for k, v in t["ChrClasses"].items()}
    races = _races(t, describe, names, icons)
    playable = {name: race.pop("bit") for name, race in races.items()}
    item_icons = _item_icons(t)
    professions = _professions(t, describe, names, icons, item_icons)
    crafted = {r["item"]["name"]: name for name, recipes in professions.items() for r in recipes if r["item"]}
    return {
        "build": build_name,
        "classes": {cls: _class_data(t, describe, names, levels, icons, 1 << (class_ids[cls] - 1), playable)
                    for cls in CLASSES},
        "races": {name: race["racials"] for name, race in races.items()},
        "race_icons": _race_icons(t, races),
        "professions": professions,
        "profession_icons": {v["DisplayName_lang"]: v["SpellIconFileID"] for v in t["SkillLine"].values()
                             if v["DisplayName_lang"] in professions and v.get("SpellIconFileID")},
        "items": _items(t, ItemTooltip(t, describe), crafted, item_icons),
    }


def client_build(db2: Path) -> str:
    """The build the tables came from, e.g. "1.60.1.70630", as written in every .db2 header."""
    raw = (db2 / "spell.db2").read_bytes()[8:136].split(b"\0")[0].decode()
    return ".".join(raw.removeprefix("WOWSTATIC_").split("_"))


def icon_ids(data: dict) -> set[int]:
    """Every icon (as a client file ID) the pages show."""
    spells = [*data["professions"].values(), *current_races(data).values()]
    spells.append([{"icon": icon} for icon in data["profession_icons"].values()])
    spells.append([{"icon": icon} for recipes in data["professions"].values() for r in recipes for *_, icon in r["reagents"]])
    for cls in data["classes"].values():
        spells += [cls["abilities"], *(tree["talents"] for tree in cls["talents"])]
    spells.append(data["items"])
    return {x["icon"] for group in spells for x in group if x["icon"]}


def icon_files(data: dict) -> set[int]:
    """Every client file the icons are cut from: the icons themselves and the race portraits' textures."""
    return icon_ids(data) | {art["file"] for art in data["race_icons"].values()} | {QUESTION_MARK}


def _open_blp(source: Path):
    from PIL import Image
    from PIL.BlpImagePlugin import BLPFormatError

    try:
        with Image.open(source) as image:
            return image.convert("RGBA")
    except BLPFormatError:  # uncompressed BGRA, which Pillow doesn't read: width, height and first mip offset
        raw = source.read_bytes()
        width, height, offset = struct.unpack_from("<III", raw, 12)
        return Image.frombuffer("RGBA", (width, height), raw[offset:offset + width * height * 4], "raw", "BGRA")


def write_icons(data: dict, blp: Path) -> list[int]:
    """Convert the extracted <file ID>.blp files to ICONS/<file ID>.jpg and ICONS/race-<race>.png (round, so with
    transparency); returns the file IDs that were missing."""
    from PIL import Image  # only needed here, on the PC that extracts the game files

    wanted, missing = icon_ids(data), []
    ICONS.mkdir(exist_ok=True)
    for old in ICONS.glob("*.jpg"):
        if int(old.stem) not in wanted:
            old.unlink()
    for icon in sorted(wanted):
        source = blp / f"{icon}.blp"
        if not source.exists():
            missing.append(icon)
            continue
        try:
            image = _open_blp(source).convert("RGB")
        except OSError:  # an encrypted file (the extractor writes zeros): the question mark, as in game
            image = _open_blp(blp / f"{QUESTION_MARK}.blp").convert("RGB")
            print(f"{source.name} is unreadable (encrypted?); used the question mark icon")
        image.resize((ICON_SIZE, ICON_SIZE), Image.LANCZOS).save(ICONS / f"{icon}.jpg", quality=85)
    for race, art in data["race_icons"].items():
        source = blp / f"{art['file']}.blp"
        if not source.exists():
            missing.append(art["file"])
            continue
        left, top, width, height = art["box"]
        portrait = _open_blp(source).crop((left, top, left + width, top + height))
        portrait.resize((ICON_SIZE, ICON_SIZE), Image.LANCZOS).save(ICONS / f"race-{slugify(race)}.png", optimize=True)
    return missing


def slugify(name: str) -> str:
    """A race or profession name as it appears in addresses and file names."""
    return name.lower().replace(" ", "-")


# Racial changes announced after the client build in gamedata.json: the WoW Forever Beta Development Notes of Oct 26
# (edited Oct 27 with more). Drop an entry once a new client build carries the change.
RACIAL_NOTES = ("Oct 26–27 development notes", "https://us.forums.blizzard.com/en/wow/t/2360696/7")
RACIAL_CHANGES = {  # name: (new description, or None to keep the client's; what changed)
    "Ruthless": ("Increases your critical strike chance with all spells and attacks by 1%.", "1% critical strike chance (was 2%)."),
    "The Human Spirit": ("Spirit increased by 10%.", "Spirit increased by 10% (was 5%)."),
    "Plainsrunning": ("Gain 2% increased movement speed every 5 sec spent moving, up to a maximum of 60% increase. Taking "
                      "damage or standing still will reduce this effect.",
                      "2% per stack, up to 60% (was 1%, up to 30%). No longer increases mounted speed."),
    "Endurance": ("Total Health increased by 5%.", "No longer increases critical strike damage and healing."),
    "Blood Fury": (None, "Cooldown reduced to 2 min (was 3 min)."),
    "Berserking": (None, "Lasts 15 sec (was 10 sec)."),
    "Touch of the Grave": (None, "Can happen once every 15 sec (was 25 sec)."),
    "Wind Blessed": ("Increases your spellcasting, melee, and ranged Haste by 2%.", "Haste 2% (was 3%)."),
    "Read Leyline": ("Increases your Health and Mana regeneration by 50% for 15 sec. Used at a Ley Line, it also makes you "
                     "Attuned for 1 hour, raising the bonus to 100%. Attuned lasts through death and ends when you enter a "
                     "raid. Can't be used while Innervate is active.",
                     "50% for 15 sec (was 100%); Attuned added."),
    "Skysight": ("Increases your movement speed by 15% for 15 sec. Used at an elemental convergence, it also makes you "
                 "Charged for 1 hour, raising the bonus to 30%. Charged lasts through death and ends when you enter a raid.",
                 "15% for 15 sec (was 10%); Charged added."),
}
RACIALS_REMOVED = {"Earth Fury", "Savage"}
RACIALS_ADDED = {
    "Dwarf": [{"name": "Artisan's Precision", "icon": QUESTION_MARK,  # not in the client yet
               "description": "Increases your chance to hit with spells and attacks by 1%.", "change": "New racial."}],
    # Command is not in the client yet: Classic's Command icon (War Cry)
    "Orc": [{"name": "Command", "icon": 132351, "description": "Damage dealt by Hunter and Warlock pets increased by 5%.",
             "change": "Back as a racial."}],
}


def current_races(data: dict) -> dict:
    """The client's racials with the changes announced since that build."""
    out = {}
    for race, racials in data["races"].items():
        current = []
        for racial in racials:
            if racial["name"] in RACIALS_REMOVED:
                continue
            if racial["name"] in RACIAL_CHANGES:
                description, change = RACIAL_CHANGES[racial["name"]]
                racial = {**racial, "description": description or racial["description"], "change": change}
            current.append(racial)
        out[race] = current + RACIALS_ADDED.get(race, [])
    return out


@cache
def load() -> dict:
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))
