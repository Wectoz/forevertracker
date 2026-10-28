from datetime import date

import pytest

from wowforever import gamediff
from wowforever.store import Store
from wowforever.web import create_app


def game(build="1", fireball="Hurls a fiery ball for 10 damage.", level=1, ranks=("Rank one.",), recipe_yellow=10,
         racial="Smart.", items=()):
    return {
        "build": build,
        "classes": {"Mage": {
            "abilities": [{"name": "Fireball", "level": level, "ranks": [6, 12], "talent": False, "races": [],
                           "icon": 1, "description": fireball}],
            "talents": [{"name": "Fire", "talents": [{"name": "Impact", "tier": 1, "column": 0, "icon": 1,
                                                       "ranks": list(ranks), "requires": None}]}]}},
        "races": {"Gnome": [{"name": "Eureka!", "icon": 2, "description": racial}]},
        "professions": {"Alchemy": [{"name": "Minor Healing Potion", "icon": 3, "yellow": recipe_yellow, "grey": 50,
                                     "source": "Trainer", "skill": None, "makes": 1, "item": None, "description": None,
                                     "reagents": [[1, "Peacebloom", 4]]}]},
        "items": [{"id": 9, "name": name, "quality": 2, "level": 20, "lines": lines, "effects": []} for name, lines in items],
    }


@pytest.fixture
def changes_file(tmp_path, monkeypatch):
    path = tmp_path / "gamechanges.json"
    monkeypatch.setattr(gamediff, "CHANGES_FILE", path)
    return path


def test_no_changes_between_equal_data():
    assert gamediff.changes(game(), game()) == []


def test_changes_list_added_removed_and_changed_fields():
    old = game(items=[("Old Belt", ["Waist"])])
    new = game(fireball="Hurls a fiery ball for 12 damage.", level=2, ranks=("Rank one.", "Rank two."),
               recipe_yellow=15, racial="Smarter.", items=[("Old Belt", ["Waist", "+2 Stamina"])])
    new["classes"]["Mage"]["abilities"].append({**new["classes"]["Mage"]["abilities"][0], "name": "Frostbolt"})
    new["races"]["Gnome"] = []
    assert gamediff.changes(old, new) == [
        {"section": "Mage", "what": "ability", "name": "Fireball", "change": "changed", "details": [
            {"field": "Learned at level", "before": 1, "after": 2},
            {"field": "Description", "before": "Hurls a fiery ball for 10 damage.",
             "after": "Hurls a fiery ball for 12 damage."}]},
        {"section": "Mage", "what": "ability", "name": "Frostbolt", "change": "added", "details": []},
        {"section": "Mage", "what": "talent", "name": "Impact (Fire)", "change": "changed", "details": [
            {"field": "Ranks", "before": 1, "after": 2}]},
        {"section": "Gnome", "what": "racial", "name": "Eureka!", "change": "removed", "details": []},
        {"section": "Alchemy", "what": "recipe", "name": "Minor Healing Potion", "change": "changed", "details": [
            {"field": "Turns yellow at", "before": 10, "after": 15}]},
        {"section": "Items", "what": "item", "name": "Old Belt", "change": "changed", "details": [
            {"field": "Tooltip", "before": ["Waist"], "after": ["Waist", "+2 Stamina"]}]},
    ]


def test_record_adds_the_newest_update_first(changes_file):
    assert gamediff.record(game("1"), game("1"), date(2026, 11, 1)) == 0 and not changes_file.exists()
    gamediff.record(game("1"), game("2", level=3), date(2026, 11, 5))
    gamediff.record(game("2", level=3), game("3", level=4), date(2026, 11, 9))
    assert [(u["date"], u["from"], u["to"]) for u in gamediff.load()] == [("2026-11-09", "2", "3"), ("2026-11-05", "1", "2")]


def test_word_diff_marks_new_and_gone_words():
    assert gamediff.word_diff("Deals 10 damage.", "Deals 12 fire damage.") == \
        "Deals <del>10</del> <ins>12 fire</ins> damage."
    assert gamediff.word_diff(["Waist"], ["Waist", "+2 <Stamina>"]) == "Waist · <ins>+2 &lt;Stamina&gt;</ins>"
    assert gamediff.word_diff(None, "New text") == "<ins>New text</ins>"


def test_game_changes_page(changes_file):
    client = create_app(Store(":memory:")).test_client()
    assert "No changes recorded yet" in client.get("/game-changes").text
    assert 'href="/game-changes"' in client.get("/patches").text
    gamediff.record(game("1"), game("2", fireball="Hurls a fiery ball for 12 damage."), date(2026, 11, 5))
    html = client.get("/game-changes").text
    assert "build 1 → 2" in html and '<span class="spell">Fireball</span>' in html
    assert "Hurls a fiery ball for <del>10</del> <ins>12</ins> damage." in html
