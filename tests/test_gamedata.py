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


def spell(sid, name, text="", level=0, base=0.0, duration=None, period=0, chain=0):
    """Rows for one spell across the spell tables."""
    return {
        "SpellName": {sid: {"Name_lang": name}},
        "Spell": {sid: {"Description_lang": text}},
        "SpellLevels": {sid: {"SpellID": sid, "SpellLevel": level, "DifficultyID": 0}} if level else {},
        "SpellEffect": {sid: {"SpellID": sid, "EffectIndex": 0, "DifficultyID": 0, "EffectBasePointsF": base,
                              "EffectAuraPeriod": period, "EffectChainTargets": chain, "EffectRadiusIndex": [0, 0]}},
        "SpellMisc": {sid: {"SpellID": sid, "DifficultyID": 0, "DurationIndex": duration or 0}},
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
])
def test_describe_fills_placeholders(text, expected):
    t = tables(spell(1, "Test", text, base=10, duration=1, chain=3))
    if "Lasts" in text:
        t["SpellMisc"][1]["DurationIndex"] = 2
    assert gamedata.Describer(t)(1) == expected


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
        spell(1978, "Serpent Sting", "Poisons for $s1.", level=4, base=20), ability(1, 1978),
        spell(13549, "Serpent Sting", level=10), ability(2, 13549, class_mask=0),
        spell(17253, "Bite", level=1), ability(3, 17253, line=261),  # pet ability
        spell(409379, "Kill Command", level=1), ability(4, 409379),  # Season of Discovery rune
        spell(1293241, "Summon Hawk", level=25), ability(5, 1293241),  # Forever's own
        spell(9999, "Hunter Passive (DND)", level=1), ability(6, 9999),
    )
    assert data["abilities"] == [
        {"name": "Serpent Sting", "level": 4, "ranks": [10], "talent": False, "races": [],
         "description": "Poisons for 20."},
        {"name": "Summon Hawk", "level": 25, "ranks": [], "talent": False, "races": [], "description": None},
    ]


def test_talents_by_tree_and_trained_talent_ranks_are_tagged():
    data = hunter_data(
        {"TalentTab": {1: {"ID": 1, "Name_lang": "Marksmanship", "ClassMask": 4, "OrderIndex": 1}},
         "Talent": {1: {"TabID": 1, "TierID": 2, "ColumnIndex": 1, "SpellRank": [19434, 0]},
                    2: {"TabID": 1, "TierID": 0, "ColumnIndex": 0, "SpellRank": [19407, 19412, 0]}}},
        spell(19434, "Aimed Shot", level=20), ability(1, 19434),
        spell(20900, "Aimed Shot", level=28), ability(2, 20900),
        spell(19407, "Improved Concussive Shot", level=1), ability(3, 19407),  # talent only: not an ability
    )
    assert [t["name"] for t in data["talents"]] == ["Marksmanship"]
    assert [(t["name"], t["level"], t["ranks"]) for t in data["talents"][0]["talents"]] == [
        ("Improved Concussive Shot", 10, 2), ("Aimed Shot", 20, 1)]
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
        "Human": [{"name": "The Human Spirit", "description": "Spirit increased by 5%."},
                  {"name": "Expansive Mind", "description": None}],
        "High Order Skyborne": [{"name": "Walk on Air", "description": None}],
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
         "ItemSparse": {7: {"Display_lang": "Pattern: Red Woolen Bag", "RequiredSkillRank": 115}},
         "ItemEffect": {70: {"TriggerType": 6, "SpellID": 6688}},
         "ItemXItemEffect": {1: {"ItemEffectID": 70, "ItemID": 7}}},
        spell(3908, "Tailoring"), recipe(1, 3908, 0, 0),  # the profession itself
        spell(2963, "Bolt of Linen Cloth"), recipe(2, 2963, 25, 50, acquire=1),
        spell(6688, "Red Woolen Bag"), recipe(3, 6688, 115, 150),
        spell(3915, "Brown Linen Shirt"), recipe(4, 3915, 35, 70),
        spell(435827, "Hyperconductive Arcano-Filament"), recipe(5, 435827, 200, 220),  # Season of Discovery
    ), "b")
    assert data["professions"] == {"Tailoring": [
        {"name": "Bolt of Linen Cloth", "yellow": 25, "grey": 50, "source": "Known when you learn the profession",
         "skill": None},
        {"name": "Brown Linen Shirt", "yellow": 35, "grey": 70, "source": "Trainer", "skill": None},
        {"name": "Red Woolen Bag", "yellow": 115, "grey": 150, "source": "Pattern: Red Woolen Bag", "skill": 115},
    ]}


def test_committed_data_covers_every_class_race_and_profession():
    data = gamedata.load()
    assert set(data["classes"]) == set(CLASSES)
    assert all(data["classes"][c]["abilities"] and len(data["classes"][c]["talents"]) == 3 for c in CLASSES)
    assert {"Human", "Orc", "High Order Skyborne", "Windshaper Skyborne"} <= set(data["races"])
    assert {"Alchemy", "Cooking", "Tailoring"} <= set(data["professions"])
    names = {a["name"] for c in CLASSES for a in data["classes"][c]["abilities"]}
    assert "Riptide" in names and "Kill Command" not in names  # Forever's addition in, Season of Discovery rune out
