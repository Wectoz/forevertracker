from wowforever.gamelinks import Linker, keys_in, tooltips
from wowforever.store import Store
from wowforever.web import create_app

from .test_store import make_forum_post, make_staff


def ability(name, description="", level=1, talent=False):
    return {"name": name, "level": level, "ranks": [], "talent": talent, "races": [], "icon": 1, "description": description}


GAME = {
    "classes": {
        "Warrior": {"abilities": [ability("Charge", "Charge an enemy."), ability("Mortal Strike", "Ouch.", 40, True),
                                  ability("Enrage", "Warrior enrage.")],
                    "talents": [{"name": "Arms", "talents": [
                        {"name": "Mortal Strike", "icon": 1, "ranks": ["Ouch."], "requires": None, "tier": 6, "column": 1},
                        {"name": "Improved Charge", "icon": 1, "ranks": ["More rage.", None], "requires": None,
                         "tier": 1, "column": 0}]}]},
        "Druid": {"abilities": [ability("Enrage", "Druid enrage."), ability("Barkskin", "Tough skin.")], "talents": []},
    },
    "races": {"Gnome": [{"name": "Eureka!", "icon": 2, "description": "Smart."}]},
    "professions": {"Alchemy": [{"name": "Nature's Elixir", "icon": 3, "item": {
        "name": "Nature's Elixir", "quality": 2, "slot": None, "lines": [], "effects": ["Use: Heals."], "description": None}}]},
}


def linked(html, section=None):
    return str(Linker(GAME).link(html, section))


def test_tooltips_cover_abilities_talents_racials_and_items():
    tips = tooltips(GAME)
    assert tips["warrior-mortal-strike"]["kind"] == "Warrior talent · Level 40"  # the ability, not a second talent entry
    assert tips["warrior-improved-charge"] == {"name": "Improved Charge", "icon": 1, "owner": "Warrior",
                                               "kind": "Warrior talent · Arms, 2 ranks", "desc": "More rage."}
    assert tips["gnome-eureka"]["kind"] == "Gnome racial"
    assert tips["item-nature-s-elixir"]["effects"] == ["Use: Heals."]


def test_link_wraps_names_longest_first():
    html = linked("<li>Improved Charge and Charge</li>")
    assert '<span class="gl" tabindex="0" data-tip="warrior-improved-charge">Improved Charge</span>' in html
    assert '<span class="gl" tabindex="0" data-tip="warrior-charge">Charge</span></li>' in html


def test_link_leaves_links_code_and_partial_words_alone():
    assert linked('<a href="/x">Charge</a> <code>Charge</code> Charged Charge-up') == \
        '<a href="/x">Charge</a> <code>Charge</code> Charged Charge-up'


def test_shared_names_follow_the_class_heading():
    assert "data-tip" not in linked("<p>Enrage</p>")  # two classes, different text: no guess
    assert 'data-tip="druid-enrage"' in linked("<p>Enrage</p>", "Druid")
    html = linked("<h3>Warrior</h3><li>Enrage</li><h3>Druid</h3><li>Enrage</li>")
    assert html.index("warrior-enrage") < html.index("druid-enrage")


def test_name_ending_a_longer_unknown_name_is_not_linked():
    assert "data-tip" not in linked("<li>Missile Barkskin is new</li>")
    assert 'data-tip="druid-barkskin"' in linked("<li>Reduced Barkskin cooldown. The Barkskin</li>")
    assert linked("<li>Druid Barkskin</li>").count("data-tip") == 1


def test_curly_and_escaped_apostrophes_match():
    assert 'data-tip="item-nature-s-elixir">Nature’s Elixir</span>' in linked("Nature’s Elixir")
    assert 'data-tip="item-nature-s-elixir">Nature&#39;s Elixir</span>' in linked("Nature&#39;s Elixir")
    assert 'data-tip="gnome-eureka">Eureka!</span>' in linked("Eureka! is better")


def test_keys_in():
    assert keys_in(linked("Charge, Barkskin")) == {"warrior-charge", "druid-barkskin"}


def test_pages_link_names_and_serve_only_the_tooltips_they_use():
    store = Store(":memory:")
    store.save_update(make_forum_post(), "hotfix", {"Warrior": "<ul><li>Mortal Strike damage up</li></ul>"})
    store.add_blue_posts([make_staff(excerpt="Sprint is fine")])
    client = create_app(store).test_client()
    page = client.get("/classes/warrior").text
    assert '<span class="gl" tabindex="0" data-tip="warrior-mortal-strike">Mortal Strike</span>' in page
    assert 'href="/tooltips.json"' in page and "gamelinks.js" in page
    assert 'data-tip="rogue-sprint">Sprint</span>' in client.get("/blue").text
    tips = client.get("/tooltips.json").json
    assert set(tips) == {"warrior-mortal-strike", "rogue-sprint"}
    assert "gamelinks.js" not in client.get("/news").text
