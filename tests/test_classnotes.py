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
    assert '<a href="https://example.com/x" target="_blank" rel="noopener nofollow">ok</a>' in out
    assert "bad" in out


def test_paragraph_heading_followed_by_list():
    html = ("<p><strong>Items</strong></p><ul><li><strong>Mage</strong><ul><li>not a class change</li></ul></li></ul>"
            "<p><strong>Classes</strong></p>\n<ul>\n<li><strong>Mage</strong>\n<ul><li>A</li></ul>\n</li>\n</ul>")
    assert split_classes(html) == {"Mage": "<ul><li>A</li></ul>"}


def test_every_real_build_post_has_class_sections():
    built = [n for n, p in enumerate(posts(), 1) if p["cooked"]]
    assert [n for n in built if split_classes(posts()[n - 1]["cooked"])] == [1, 4, 5, 6]
    assert "Rogue" not in split_classes(posts()[4]["cooked"])


def test_quoted_notes_in_a_reply_are_ignored():
    html = ('<aside class="quote"><blockquote><p><strong>Classes</strong></p>'
            '<ul><li><strong>Mage</strong><ul><li>Frostbolt buffed.</li></ul></li></ul></blockquote></aside>'
            "<p>We're looking into the Frostbolt change.</p>")
    assert split_classes(html) == {}


def test_later_classes_heading_is_found_when_the_first_has_no_list():
    html = ("<p><strong>Classes</strong></p><p>Class changes are below.</p>"
            "<p><strong>Classes</strong></p><ul><li><strong>Mage</strong><ul><li>A</li></ul></li></ul>")
    assert split_classes(html) == {"Mage": "<ul><li>A</li></ul>"}


def test_links_open_safely_and_relative_links_point_at_the_forums():
    html = ('<ul><li><strong>Classes</strong><ul><li><strong>Mage</strong><ul><li>'
            '<a href="https://example.com/x">abs</a> <a href="/en/wow/t/123">rel</a> <a href="#p-1">anchor</a>'
            '</li></ul></li></ul></li></ul>')
    out = split_classes(html)["Mage"]
    assert '<a href="https://example.com/x" target="_blank" rel="noopener nofollow">abs</a>' in out
    assert '<a href="https://us.forums.blizzard.com/en/wow/t/123" target="_blank" rel="noopener nofollow">rel</a>' in out
    assert "anchor" in out and "#p-1" not in out


def _luminance(hex_color):
    channels = [int(hex_color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    channels = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def test_class_colors_are_readable_on_the_dark_backgrounds():
    # WCAG AA for normal text: 4.5:1. Backgrounds: page, menu, card, and the menu's hover/current row.
    for background in ("#16130f", "#211b15", "#1f1913", "#2c231a"):
        for name, color in CLASS_COLORS.items():
            light, dark = sorted([_luminance(color), _luminance(background)], reverse=True)
            assert (light + 0.05) / (dark + 0.05) >= 4.5, (name, background)


def test_clean_html_keeps_structure_and_drops_quotes_scripts_and_images():
    from wowforever.classnotes import clean_html

    cooked = ('<h1>Big</h1><h2><a name="x" href="#x"></a>Change Log</h2><aside class="quote">quoted</aside>'
              '<script>bad()</script><p>Hi <img src="e.png"><a href="/t/1">thread</a></p><h6>small</h6>')
    assert clean_html(cooked) == ('<h2>Big</h2><h2>Change Log</h2><p>Hi <a href="https://us.forums.blizzard.com/t/1"'
                                  ' target="_blank" rel="noopener nofollow">thread</a></p><h4>small</h4>')


def test_text_lines_one_per_block():
    from wowforever.classnotes import text_lines

    assert text_lines("<p>a &amp; <b>b</b></p><h2>T</h2><ul><li>x<ul><li>y</li></ul></li></ul>") == ["a & b", "T", "x", "y"]
