import struct
from pathlib import Path

import pytest

from wowforever import gamedata, wdc5
from wowforever.classnotes import CLASSES

FIXTURES = Path(__file__).parent / "fixtures" / "gamedata"
HUNTER = 3  # ChrClasses ID; class bit 1 << 2


def test_reads_a_client_table():
    rows = wdc5.read(FIXTURES / "skilllinecategory.db2", "SkillLineCategory", FIXTURES)
    assert rows[7]["Name_lang"] == "Class Skills"
    assert rows[11]["Name_lang"] == "Professions"
    assert {k: v["SortIndex"] for k, v in rows.items()}[9] == 4


def spell(sid, name, text="", level=0, base=0.0, duration=None, period=0, chain=0, icon=0, effect=0, item=0):
    """Rows for one spell across the spell tables."""
    return {
        "SpellName": {sid: {"Name_lang": name}},
        "Spell": {sid: {"Description_lang": text}},
        "SpellLevels": {sid: {"SpellID": sid, "SpellLevel": level, "DifficultyID": 0}} if level else {},
        "SpellEffect": {sid: {"SpellID": sid, "EffectIndex": 0, "DifficultyID": 0, "EffectBasePointsF": base,
                              "EffectAuraPeriod": period, "EffectChainTargets": chain, "EffectRadiusIndex": [0, 0],
                              "EffectMiscValue": [0, 0], "EffectPointsPerResource": 0.0, "EffectAmplitude": 0.0,
                              "Effect": effect, "EffectItemType": item}},
        "SpellMisc": {sid: {"SpellID": sid, "DifficultyID": 0, "DurationIndex": duration or 0, "SpellIconFileDataID": icon}},
    }


def tables(*parts) -> dict:
    t = {table: {} for table in gamedata.TABLES.values()}
    t["SpellDuration"] = {1: {"Duration": 8000}, 2: {"Duration": 600000}}
    t["ChrClasses"] = {i + 1: {"Name_lang": name} for i, name in
                       enumerate(["Warrior", "Paladin", "Hunter", "Rogue", "Priest", "Shaman", "Mage", "Warlock", "Druid"])}
    for part in parts:
        for table, rows in part.items():
            t[table].update(rows)
    return t


@pytest.mark.parametrize("text, expected", [
    ("Reduces Physical damage taken by $s1% for $d.", "Reduces Physical damage taken by 10% for 8 sec."),
    ("Lasts $d.", "Lasts 10 min."),
    ("Generate $/10;s1 Rage.", "Generate 1 Rage."),
    ("Deals ${$s1*2} damage.", "Deals 20 damage."),
    ("Increases threat by $?a12792[${$s1+5}%][$s1%].", "Increases threat by 10%."),
    ("Hits $x1 $ltarget:targets;.", "Hits 3 targets."),
    ("Deals ${19*$<frostdamage>} damage.", "Deals 19 damage."),
    ("Back to $z.", None),  # a placeholder this can't fill: no description rather than a wrong one
    ("", None),
    ("The next $n attacks, $h% chance, up to $u stacks.", "The next 3 attacks, 20% chance, up to 5 stacks."),
    ("Hits up to $i enemies of level $v or lower.", "Hits up to 4 enemies of level 50 or lower."),
    ("Converts $*15;s1 mana.", "Converts 150 mana."),
    ("Deals ${$s1+$SPFR*0.1+$rap} damage.", "Deals 10 damage."),
    ("|cFFFF2020Requires Bear Form|r Charge.", "Requires Bear Form Charge."),
    ("Roots. $@spelldesc2", "Roots. Deals 7 damage."),
])
def test_describe_fills_placeholders(text, expected):
    t = tables(spell(1, "Test", text, base=10, duration=1, chain=3), spell(2, "Other", "Deals $s1 damage.", base=7))
    t["SpellAuraOptions"] = {1: {"SpellID": 1, "DifficultyID": 0, "ProcCharges": 3, "ProcChance": 20, "CumulativeAura": 5}}
    t["SpellTargetRestrictions"] = {1: {"SpellID": 1, "DifficultyID": 0, "MaxTargets": 4, "MaxTargetLevel": 50}}
    if "Lasts" in text:
        t["SpellMisc"][1]["DurationIndex"] = 2
    assert gamedata.Describer(t)(1) == expected


def test_describe_falls_back_to_the_buff_text():
    t = tables(spell(1, "Cat Form (Passive)"))
    t["Spell"][1]["AuraDescription_lang"] = "Immune to Polymorph."
    assert gamedata.Describer(t)(1) == "Immune to Polymorph."


def hunter_data(*parts):
    t = tables(
        {"SkillLine": {50: {"CategoryID": 7, "DisplayName_lang": "Beast Mastery"},
                       261: {"CategoryID": 7, "DisplayName_lang": "Beast Training"}},
         "SkillRaceClassInfo": {1: {"SkillID": 50, "ClassMask": 4}, 2: {"SkillID": 261, "ClassMask": 4}}},
        *parts)
    return gamedata.build(t, "1.60.1.1")["classes"]["Hunter"]


def ability(row_id, sid, line=50, class_mask=4, races=(0, 0)):
    return {"SkillLineAbility": {row_id: {"SkillLine": line, "Spell": sid, "ClassMask": class_mask,
                                          "RaceMasks": list(races), "AcquireMethod": 0}}}


def test_class_abilities_group_ranks_and_skip_pets_and_season_of_discovery():
    data = hunter_data(
        spell(1978, "Serpent Sting", "Poisons for $s1.", level=4, base=20, icon=132204), ability(1, 1978),
        spell(13549, "Serpent Sting", level=10), ability(2, 13549, class_mask=0),
        spell(5000, "Execute", level=24), ability(7, 5000),  # the first rank has no text, a later one does
        spell(5001, "Execute", "Finish them for $s1.", level=32, base=125), ability(8, 5001),
        spell(17253, "Bite", level=1), ability(3, 17253, line=261),  # pet ability
        spell(409379, "Kill Command", level=1), ability(4, 409379),  # Season of Discovery rune
        spell(1293241, "Summon Hawk", level=25), ability(5, 1293241),  # Forever's own
        spell(9999, "Hunter Passive (DND)", level=1), ability(6, 9999),
    )
    assert data["abilities"] == [
        {"name": "Serpent Sting", "level": 4, "ranks": [10], "talent": False, "races": [], "icon": 132204,
         "description": "Poisons for 20."},
        {"name": "Execute", "level": 24, "ranks": [32], "talent": False, "races": [], "icon": None,
         "description": "Finish them for 125."},
        {"name": "Summon Hawk", "level": 25, "ranks": [], "talent": False, "races": [], "icon": None, "description": None},
    ]


def test_talents_by_tree_and_trained_talent_ranks_are_tagged():
    talent = lambda tier, column, ranks, prereq=0, rank=0: {
        "TabID": 1, "TierID": tier, "ColumnIndex": column, "SpellRank": ranks, "PrereqTalent": [prereq, 0, 0],
        "PrereqRank": [rank, 0, 0]}
    data = hunter_data(
        {"TalentTab": {1: {"ID": 1, "Name_lang": "Marksmanship", "ClassMask": 4, "OrderIndex": 1}},
         "Talent": {1: talent(2, 1, [19434, 0], prereq=2, rank=1),
                    2: talent(0, 0, [19407, 19412, 0]),
                    3: talent(1, 0, [19420], prereq=99)}},  # its prerequisite isn't in the tree
        spell(19434, "Aimed Shot", level=20, icon=135130), ability(1, 19434),
        spell(20900, "Aimed Shot", level=28), ability(2, 20900),
        spell(19407, "Improved Concussive Shot", "Dazes $s1% longer.", level=1, base=1), ability(3, 19407),
        spell(19412, "Improved Concussive Shot", "Dazes $s1% longer.", base=2),
        spell(19420, "Lethal Shots"),
    )
    assert [t["name"] for t in data["talents"]] == ["Marksmanship"]
    assert data["talents"][0]["talents"] == [
        {"name": "Improved Concussive Shot", "tier": 0, "column": 0, "icon": None,
         "ranks": ["Dazes 1% longer.", "Dazes 2% longer."], "requires": None},
        {"name": "Lethal Shots", "tier": 1, "column": 0, "icon": None, "ranks": [None], "requires": None},
        {"name": "Aimed Shot", "tier": 2, "column": 1, "icon": 135130, "ranks": [None], "requires": [0, 2]},
    ]
    assert [(a["name"], a["talent"], a["ranks"]) for a in data["abilities"]] == [("Aimed Shot", True, [28])]


RACES = {"ChrRaces": {1: {"Name_lang": "Human", "PlayableRaceBit": 0}, 4: {"Name_lang": "Night Elf", "PlayableRaceBit": 3},
                      9: {"Name_lang": "Goblin", "PlayableRaceBit": 8},
                      95: {"Name_lang": "High Order Skyborne", "PlayableRaceBit": 32}},
         "SkillLine": {754: {"CategoryID": 9, "DisplayName_lang": "Racial - Human"},
                       126: {"CategoryID": 9, "DisplayName_lang": "Night Elf Racial"},
                       2980: {"CategoryID": 9, "DisplayName_lang": "Skyborne Racial"}}}


def test_races_list_their_racials_once_and_skip_races_without_any():
    data = gamedata.build(tables(
        RACES,
        spell(20598, "The Human Spirit", "Spirit increased by $s1%.", base=5), ability(1, 20598, 754, 0, (1, 0)),
        spell(1259803, "Expansive Mind", level=0), ability(2, 1259803, 754, 8, (1, 0)),
        spell(1259802, "Expansive Mind"), ability(3, 1259802, 754, 1, (1, 0)),  # same racial, another class
        spell(1259416, "Walk on Air"), ability(4, 1259416, 2980, 0, (0, 1)),
    ), "b")
    assert data["races"] == {
        "Human": [{"name": "The Human Spirit", "icon": None, "description": "Spirit increased by 5%."},
                  {"name": "Expansive Mind", "icon": None, "description": None}],
        "High Order Skyborne": [{"name": "Walk on Air", "icon": None, "description": None}],
    }


def test_class_abilities_name_the_only_races_that_learn_them():
    data = hunter_data(RACES, spell(20598, "Racial Test"), ability(9, 20598, 754, 0, (1, 0)),
                       spell(20580, "Shadowmeld"), ability(10, 20580, 126, 0, (8, 0)),
                       spell(7, "Starshards", level=10), ability(1, 7, races=(8, 0)),
                       spell(8, "Arcane Shot", level=6), ability(2, 8, races=(0xFFFFFFFF, 0xFFFFFFFF)))
    assert [(a["name"], a["races"]) for a in data["abilities"]] == [("Arcane Shot", []), ("Starshards", ["Night Elf"])]


def test_professions_list_recipes_with_their_source():
    recipe = lambda row_id, sid, low, high, acquire=0: {"SkillLineAbility": {row_id: {
        "SkillLine": 197, "Spell": sid, "TrivialSkillLineRankLow": low, "TrivialSkillLineRankHigh": high,
        "AcquireMethod": acquire, "ClassMask": 0, "RaceMasks": [0, 0]}}}
    data = gamedata.build(tables(
        {"SkillLine": {197: {"CategoryID": 11, "DisplayName_lang": "Tailoring"},
                       2933: {"CategoryID": 11, "DisplayName_lang": "Test Profession [DNT]"}},
         "ItemSparse": {7: {"Display_lang": "Pattern: Red Woolen Bag", "RequiredSkillRank": 115},
                        2592: {"Display_lang": "Wool Cloth"}},
         "Item": {5764: {"IconFileDataID": 133639}, 2592: {"IconFileDataID": 132911}},
         "SpellReagents": {1: {"SpellID": 6688, "Reagent": [2592, 0], "ReagentCount": [3, 0]}},
         "ItemEffect": {70: {"TriggerType": 6, "SpellID": 6688}},
         "ItemXItemEffect": {1: {"ItemEffectID": 70, "ItemID": 7}}},
        spell(3908, "Tailoring"), recipe(1, 3908, 0, 0),  # the profession itself
        spell(2963, "Bolt of Linen Cloth", icon=136243), recipe(2, 2963, 25, 50, acquire=1),
        spell(6688, "Red Woolen Bag", effect=24, item=5764, icon=1), recipe(3, 6688, 115, 150),  # shows the bag
        spell(3915, "Brown Linen Shirt", "Makes a shirt."), recipe(4, 3915, 35, 70),
        spell(435827, "Hyperconductive Arcano-Filament"), recipe(5, 435827, 200, 220),  # Season of Discovery
    ), "b")
    extra = {"makes": 0, "item": None, "description": None, "reagents": []}
    assert data["professions"] == {"Tailoring": [
        {"name": "Bolt of Linen Cloth", "icon": 136243, "yellow": 25, "grey": 50, "source": "Starting recipe",
         "skill": None, **extra},
        {"name": "Brown Linen Shirt", "icon": None, "yellow": 35, "grey": 70, "source": "Trainer", "skill": None,
         **extra, "description": "Makes a shirt."},
        {"name": "Red Woolen Bag", "icon": 133639, "yellow": 115, "grey": 150, "source": "Pattern: Red Woolen Bag",
         "skill": 115, **extra, "reagents": [[3, "Wool Cloth", 132911]]},
    ]}


def item_tables(item_class, subclass, slot, quality=3, level=63, **sparse):
    t = tables({
        "Item": {1: {"ClassID": item_class, "SubclassID": subclass}},
        "ItemSparse": {1: {"Display_lang": "Test Item", "ItemLevel": level, "OverallQualityID": quality,
                           "InventoryType": slot, "Bonding": 2, "RequiredLevel": 58, "ContainerSlots": 0,
                           "StatModifier_bonusStat": [7, 38, 32, -1], "StatPercentEditor": [5000, 10000, 2000, 0],
                           "DmgVariance": 0.5, "ItemDelay": 3800, **sparse}},
        "RandPropPoints": {level: {"Superior": [140, 100, 80, 60, 40]}},
        "ItemDamageTwoHand": {1: {"ItemLevel": level, "Quality": [0, 0, 0, 53.9, 0, 0, 0]}},
        "ItemArmorTotal": {1: {"ItemLevel": level, "Cloth": 100.0, "Leather": 0, "Mail": 0, "Plate": 0}},
        "ArmorLocation": {5: {"Clothmodifier": 0.5, "Leathermodifier": 0, "Chainmodifier": 0, "Platemodifier": 0}},
        "ItemArmorQuality": {level: {"Qualitymod": [0, 0, 0, 1.2, 0, 0, 0]}},
    })
    return gamedata.ItemTooltip(t, gamedata.Describer(t))(1)


def test_item_tooltip_works_out_damage_armor_and_stats_from_item_level():
    weapon = item_tables(2, 1, 17)  # a two-handed axe
    assert weapon["lines"] == ["Binds when equipped", "Two-Hand · Axe", "153 - 256 Damage · Speed 3.80",
                               "(53.9 damage per second)", "+70 Stamina", "Requires Level 58"]
    assert weapon["effects"] == ["Equip: +140 Attack Power.", "Equip: Improves your chance to get a critical strike by 2%."]
    robe = item_tables(4, 1, 20)  # a cloth robe: chest armor
    assert robe["lines"][1:3] == ["Chest · Cloth", "60 Armor"]


def test_items_list_gear_and_bags_but_not_test_season_of_discovery_or_unworn_items():
    def row(name, quality=2, required=10, slot=5, **extra):
        return {"Display_lang": name, "ItemLevel": 20, "OverallQualityID": quality, "InventoryType": slot,
                "Bonding": 2, "RequiredLevel": required, "ContainerSlots": 0, "StatModifier_bonusStat": [],
                "StatPercentEditor": [], **extra}
    sparse = {1: row("Linen Robe"), 2: row("Torn Robe", quality=0), 3: row("Test Robe"), 4: row("Outland Robe", required=70),
              5: row("Firestone", slot=0), 6: row("Woolen Bag", slot=18, ContainerSlots=8), 7: row("Linen Cloth"),
              8: row("90 Epic Rogue Cap"), 9: row("OLDThug Belt", slot=6), 11: row("Old Leather Belt", slot=6),
              210000: row("Rune Robe"), 217287: row("Greater Mystic Wand", slot=15)}
    kinds = {7: (7, 5), 6: (1, 0), 217287: (2, 19)}  # cloth (a trade good), a bag, a wand; the rest cloth armor
    t = tables({"ItemSparse": sparse, "Item": {i: {"ClassID": kinds.get(i, (4, 1))[0], "SubclassID": kinds.get(i, (4, 1))[1],
                                                   "IconFileDataID": 100 + i if i != 6 else 0} for i in sparse},
                "ItemModifiedAppearance": {1: {"ItemID": 6, "ItemAppearanceID": 9, "OrderIndex": 0}},
                "ItemAppearance": {9: {"DefaultIconFileDataID": 999}}})  # the bag's icon is its appearance's
    items = gamedata._items(t, gamedata.ItemTooltip(t, gamedata.Describer(t)), {"Greater Mystic Wand": "Enchanting"},
                            gamedata._item_icons(t))
    assert [(i["name"], i["slot"], i["type"], i["crafted"]) for i in items] == [
        ("Greater Mystic Wand", "Ranged", "Wand", "Enchanting"), ("Linen Robe", "Chest", "Cloth", None),
        ("Old Leather Belt", "Waist", "Cloth", None), ("Woolen Bag", "Bag", None, None)]
    assert items[-1]["icon"] == 999
    assert items[1] | {"lines": None} == {"id": 1, "icon": 101, "level": 20, "required": 10, "type": "Cloth", "crafted": None,
                                          "name": "Linen Robe", "quality": 2, "slot": "Chest", "lines": None,
                                          "effects": [], "description": None}


def test_committed_data_covers_every_class_race_and_profession():
    data = gamedata.load()
    assert set(data["classes"]) == set(CLASSES)
    assert all(data["classes"][c]["abilities"] and len(data["classes"][c]["talents"]) == 3 for c in CLASSES)
    assert {"Human", "Orc", "High Order Skyborne", "Windshaper Skyborne"} <= set(data["races"])
    assert {"Alchemy", "Cooking", "Tailoring"} <= set(data["professions"])
    assert {"Thunderfury, Blessed Blade of the Windseeker", "Wolfshead Helm"} <= {i["name"] for i in data["items"]}
    names = {a["name"] for c in CLASSES for a in data["classes"][c]["abilities"]}
    assert "Riptide" in names and "Kill Command" not in names  # Forever's addition in, Season of Discovery rune out
    assert all((gamedata.ICONS / f"{i}.jpg").exists() for i in gamedata.icon_ids(data))
    assert set(data["race_icons"]) == set(data["races"])
    assert all((gamedata.ICONS / f"race-{gamedata.slugify(r)}.png").exists() for r in data["race_icons"])


def test_packed_values_keep_only_their_declared_bits():
    # a u8 column whose 32-bit pallet entry carries the next float's bits on top (War Stomp's 5 targets)
    assert wdc5._fit(0x41A00005, {"size": 8, "unsigned": True}) == 5
    assert wdc5._fit(0xFFFF, {"size": 16, "unsigned": False}) == -1
    assert wdc5._fit(0x41A00005, {"size": 32, "unsigned": False}) == 0x41A00005


def test_announced_racial_changes_apply_to_the_client_racials():
    data = gamedata.load()
    names = {r["name"] for racials in data["races"].values() for r in racials}
    # every change still names a racial the client has; drop entries a new client build has caught up with
    assert set(gamedata.RACIAL_CHANGES) | gamedata.RACIALS_REMOVED <= names
    races = gamedata.current_races(data)
    dwarf = [r["name"] for r in races["Dwarf"]]
    assert "Earth Fury" not in dwarf and "Artisan's Precision" in dwarf
    ruthless = next(r for r in races["Human"] if r["name"] == "Ruthless")
    assert "by 1%" in ruthless["description"] and ruthless["change"]
    assert "change" not in data["races"]["Human"][0]  # the client data itself is left as read


def test_hotfix_cache_rows_latest_push_wins_and_removals(tmp_path):
    from wowforever import wdc5

    fields = [{"name": "Name_lang", "ann": set(), "type": "locstring", "unsigned": False, "size": 32, "count": 1},
              {"name": "Level", "ann": set(), "type": "int", "unsigned": False, "size": 16, "count": 1},
              {"name": "SpellID", "ann": {"noninline", "relation"}, "type": "int", "unsigned": True, "size": 32, "count": 1}]
    row = lambda name, level, spell: name.encode() + b"\0" + struct.pack("<hI", level, spell)
    entry = lambda push, table, rid, status, data=b"": struct.pack(
        "<4siiIIIIB3x", b"XFTH", 1, push, 0, table, rid, len(data), status) + data
    cache = tmp_path / "DBCache.bin"
    cache.write_bytes(struct.pack("<4sII", b"XFTH", 9, 70634) + bytes(32)
                      + entry(10, 0xAB, 1, 1, row("Fireball", 5, 133)) + entry(5, 0xAB, 1, 1, row("Old", 1, 1))
                      + entry(10, 0xAB, 2, 2) + entry(10, 0xAB, 3, 3) + entry(10, 0xCD, 1, 1, b"other table"))
    assert wdc5.read_hotfixes(cache, {0xAB: ("T", fields)}) == (
        70634, {"T": {1: {"Name_lang": "Fireball", "Level": 5, "SpellID": 133, "ID": 1}, 2: None}})
    cache.write_bytes(struct.pack("<4sII", b"XFTH", 9, 70634) + bytes(32) + entry(1, 0xAB, 1, 1, row("X", 1, 1) + b"??"))
    with pytest.raises(ValueError, match="bytes read"):
        wdc5.read_hotfixes(cache, {0xAB: ("T", fields)})


def test_attack_power_only_ranges_collapse():
    t = tables(spell(6572, "Revenge", "Counterattack for ${$m1+($<APRatio>*$apm)} to ${$M1+($<APRatio>*$apm)} damage.",
                     base=21.0))
    assert gamedata.Describer(t)(6572) == "Counterattack for 21 damage."
