from wowforever.classnotes import CLASSES
from wowforever.guides import ESSENTIALS, MACRO_LIMIT, MACROS, TRENDING


def test_every_class_has_macros_and_nothing_else():
    assert set(MACROS) == set(CLASSES)
    assert all(MACROS[cls] for cls in CLASSES)


def test_macros_fit_in_the_game():
    for cls, macros in MACROS.items():
        for macro in macros:
            assert len(macro.text) <= MACRO_LIMIT, (cls, macro.name)
            assert 1 <= macro.level <= 30, (cls, macro.name)  # nothing above the beta's level cap
            assert "{" not in macro.text, (cls, macro.name)  # no placeholders to fill in


def test_addons_link_to_curseforge_once_each():
    addons = ESSENTIALS + TRENDING
    assert len({a.slug for a in addons}) == len(addons)
    assert all(a.url.startswith("https://www.curseforge.com/wow/addons/") for a in addons)
