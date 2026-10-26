import json
from pathlib import Path

from wowforever.classnotes import CLASS_COLORS, CLASSES, class_for_slug, slug, split_classes

FIXTURES = Path(__file__).parent / "fixtures"


def posts():
    thread = json.loads((FIXTURES / "forum_thread.json").read_text(encoding="utf-8"))
    return thread["post_stream"]["posts"]


def test_classes_and_slugs():
    assert CLASSES == ("Druid", "Hunter", "Mage", "Paladin", "Priest", "Rogue", "Shaman", "Warlock", "Warrior")
    assert set(CLASS_COLORS) == set(CLASSES)
    assert slug("Mage") == "mage"
    assert class_for_slug("mage") == "Mage"
    assert class_for_slug("deathknight") is None


def test_real_post_splits_into_all_classes():
    sections = split_classes(posts()[0]["cooked"])
    assert set(sections) == set(CLASSES)
    assert "Hot Streak buff duration has been increased to 20 seconds" in sections["Mage"]
    assert "<strong>Fire</strong>" in sections["Mage"]
    assert "Wrath base damage increased" not in sections["Mage"]
    assert "Wrath base damage increased" in sections["Druid"]


def test_general_class_changes_are_left_out():
    sections = split_classes(posts()[0]["cooked"])
    assert not any("re-spec" in html for html in sections.values())


def test_developer_notes_are_kept():
    assert "<em>Developers" in split_classes(posts()[0]["cooked"])["Mage"]


def test_no_classes_section_returns_empty():
    assert split_classes("") == {}
    assert split_classes("<p>Known issues</p><ul><li><strong>Mage</strong><ul><li>x</li></ul></li></ul>") == {}


def test_heading_case_and_wrapping_tolerated():
    html = "<ul><li><strong>CLASSES</strong><ul><li><strong> mage </strong><ul><li>A</li></ul></li></ul></li></ul>"
    assert split_classes(html)["Mage"] == "<ul><li>A</li></ul>"


def test_unsafe_markup_is_stripped():
    html = ('<ul><li><strong>Classes</strong><ul><li><strong>Rogue</strong><ul>'
            '<li onclick="x()" style="color:red">Hi<script>alert(1)</script>'
            '<a href="javascript:alert(1)">bad</a><a href="https://example.com/x" class="c">ok</a></li>'
            '</ul></li></ul></li></ul>')
    out = split_classes(html)["Rogue"]
    assert "script" not in out and "alert" not in out and "onclick" not in out and "style" not in out
    assert 'href="javascript' not in out
    assert '<a href="https://example.com/x">ok</a>' in out
    assert "bad" in out
