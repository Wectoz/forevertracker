"""Hand-picked addons and class macros for the Addons and Macros pages. Refreshed by hand, not gathered."""

from dataclasses import dataclass
from datetime import date

ADDONS_UPDATED = date(2026, 10, 27)
MACRO_LIMIT = 255  # characters the game allows in one macro


@dataclass(frozen=True)
class Addon:
    name: str
    slug: str  # the addon's CurseForge project, e.g. "questie"
    blurb: str

    @property
    def url(self) -> str:
        return f"https://www.curseforge.com/wow/addons/{self.slug}"


@dataclass(frozen=True)
class Macro:
    name: str
    level: int
    blurb: str
    text: str


# Long-standing addons that ship a Forever build on CurseForge.
ESSENTIALS = (
    Addon("Questie", "questie", "Shows quest givers, objectives and turn-ins on your map and minimap."),
    Addon("Details!", "details", "Damage, healing and threat meter, to see how you and your group are doing."),
    Addon("Auctionator", "auctionator", "Faster auction house searches and selling, with price history in tooltips."),
    Addon("Baganator", "baganator", "All your bags in one window, with search and an optional category view."),
    Addon("Leatrix Plus", "leatrix-plus", "Dozens of small quality-of-life switches: auto-repair, faster looting, "
                                          "less clutter."),
    Addon("Leatrix Maps", "leatrix-maps", "Reveals unexplored map areas and adds coordinates."),
    Addon("Deadly Boss Mods", "deadly-boss-mods", "Timers and warnings for boss abilities. The core works on Forever; "
                                                  "timers for Forever's new bosses may come later."),
)

# Made for Forever, and the most downloaded of the new ones.
TRENDING = (
    Addon("ClassicUI Forever", "classicui-forever", "Brings back the original Classic look for Forever's interface, "
                                                    "one element at a time."),
    Addon("Overlord Forever", "overlord-forever", "World PvP campaign: fight over territory, guild keeps and outposts "
                                                  "with weekly rankings."),
    Addon("ForeverPlus", "foreverplus", "Buff and consumable reminders, quest and vendor automation, and profiles "
                                        "shared across characters."),
    Addon("AtlasLoot Classic Forever", "atlasloot-forever", "Loot tables for every dungeon and raid, best-in-slot "
                                                            "lists and an honor rank calculator."),
    Addon("ForeverUI", "foreverui", "A complete replacement interface: unit and raid frames, action bars, "
                                    "nameplates, bags and chat."),
    Addon("Dungeon Quests Forever", "dungeon-quests-forever", "Step-by-step guide to every dungeon quest and "
                                                              "pre-quest, with an arrow and map pins."),
)

# Spell names as in the Forever beta client, collected and checked by foreverdb.net. Nothing above the beta's
# level 30 cap, and nothing that needs you to type in your own item names.
MACROS = {
    "Druid": (
        Macro("Break roots into Cat Form", 20, "Drops your form and shifts straight back into Cat Form, "
              "which frees you from roots and slows.",
              "#showtooltip Cat Form\n/cancelform\n/cast Cat Form"),
        Macro("Bear Form, Maul, Shift for Swipe", 10, "Shifts into Bear Form if needed, then Mauls, "
              "or Swipes while you hold Shift.",
              "#showtooltip\n/startattack [form:1,harm,nodead]\n/cast [form:1,mod:shift] Swipe; [form:1] Maul; Bear Form"),
        Macro("Cat Form, then Prowl", 20, "First press shifts into Cat Form, the next one Prowls. "
              "Pressing again never breaks stealth.",
              "#showtooltip Prowl\n/cast [noform][form:1] Cat Form; !Prowl"),
        Macro("Rejuvenation on mouseover, Shift for Regrowth", 4, "Heals the friend under your mouse, "
              "your target, or yourself, without changing target.",
              "#showtooltip\n/cast [mod:shift,@mouseover,help,nodead][mod:shift,help,nodead][mod:shift,@player] "
              "Regrowth; [@mouseover,help,nodead][help,nodead][@player] Rejuvenation"),
        Macro("Cure Poison, Shift for Remove Curse", 14, "Cleanses the friend under your mouse, your target, "
              "or yourself.",
              "#showtooltip\n/cast [mod:shift,@mouseover,help,nodead][mod:shift,help,nodead][mod:shift,@player] "
              "Remove Curse; [@mouseover,help,nodead][help,nodead][@player] Cure Poison"),
        Macro("Mark of the Wild, Shift for Thorns", 1, "Buffs the friend under your mouse, your target, or yourself.",
              "#showtooltip\n/cast [mod:shift,@mouseover,help,nodead][mod:shift,help,nodead][mod:shift,@player] "
              "Thorns; [@mouseover,help,nodead][help,nodead][@player] Mark of the Wild"),
    ),
    "Hunter": (
        Macro("Mark and send the pet", 6, "Puts Hunter's Mark on your target and sends your pet in.",
              "#showtooltip Hunter's Mark\n/petattack\n/cast Hunter's Mark"),
        Macro("Auto Shot that stays on", 1, "Starts Auto Shot and sends your pet. "
              "A second press doesn't switch Auto Shot off.",
              "#showtooltip Auto Shot\n/petattack\n/cast !Auto Shot"),
        Macro("Call, mend or revive your pet", 10, "Calls your pet if it's missing and heals it if it's out. "
              "Hold Shift to revive it.",
              "#showtooltip\n/cast [mod:shift] Revive Pet; [nopet] Call Pet; Mend Pet"),
        Macro("Aimed Shot, Shift for Multi-Shot", 20, "Two shots on one key.",
              "#showtooltip\n/cast [mod:shift] Multi-Shot; Aimed Shot"),
        Macro("Every aspect on one key", 10, "Hawk by default, Cheetah with Shift, Monkey with Ctrl. "
              "Never switches the current aspect off.",
              "#showtooltip\n/cast [mod:shift] !Aspect of the Cheetah; [mod:ctrl] !Aspect of the Monkey; "
              "!Aspect of the Hawk"),
        Macro("Every trap on one key", 20, "Freezing Trap by default, Immolation Trap with Shift, "
              "Frost Trap with Ctrl.",
              "#showtooltip\n/cast [mod:shift] Immolation Trap; [mod:ctrl] Frost Trap; Freezing Trap"),
    ),
    "Mage": (
        Macro("Polymorph your focus or mouseover", 8, "Sheeps your focus, then the enemy under your mouse, "
              "then your target.",
              "#showtooltip Polymorph\n/cast [@focus,harm,nodead][@mouseover,harm,nodead][] Polymorph"),
        Macro("Counterspell, even mid-cast", 24, "Stops your own cast and interrupts your focus, "
              "mouseover or target.",
              "#showtooltip Counterspell\n/stopcasting\n/cast [@focus,harm,nodead][@mouseover,harm,nodead][] "
              "Counterspell"),
        Macro("Frost Nova right now", 10, "Cancels your cast and roots everything in melee range.",
              "#showtooltip Frost Nova\n/stopcasting\n/cast Frost Nova"),
        Macro("Blink, even mid-cast", 20, "Stops your cast and Blinks, breaking stuns and roots.",
              "#showtooltip Blink\n/stopcasting\n/cast Blink"),
        Macro("Flamestrike at your cursor", 16, "Lands Flamestrike where your mouse points, "
              "no targeting circle.",
              "#showtooltip Flamestrike\n/cast [@cursor] Flamestrike"),
        Macro("Water, food or mana gem", 6, "Conjures water, food with Shift, or a Mana Agate with Ctrl.",
              "#showtooltip\n/cast [mod:shift] Conjure Food; [mod:ctrl] Conjure Mana Agate; Conjure Water"),
    ),
    "Paladin": (
        Macro("Holy Light on mouseover, Shift for Flash of Light", 1, "Heals the friend under your mouse, "
              "your target, or yourself.",
              "#showtooltip\n/cast [mod:shift,@mouseover,help,nodead][mod:shift,help,nodead][mod:shift,@player] "
              "Flash of Light; [@mouseover,help,nodead][help,nodead][@player] Holy Light"),
        Macro("Purify your mouseover or yourself", 8, "Removes a poison and a disease from the friend under "
              "your mouse, your target, or you.",
              "#showtooltip Purify\n/cast [@mouseover,help,nodead][help,nodead][@player] Purify"),
        Macro("Might, Wisdom or Kings", 4, "Blessing of Might by default, Wisdom with Shift, Kings with Ctrl, "
              "on your mouseover or yourself.",
              "#showtooltip\n/cast [mod:shift,@mouseover,help,nodead][mod:shift,@player] Blessing of Wisdom; "
              "[mod:ctrl,@mouseover,help,nodead][mod:ctrl,@player] Blessing of Kings; "
              "[@mouseover,help,nodead][@player] Blessing of Might"),
        Macro("Every aura on one key", 1, "Devotion Aura by default, Retribution with Shift, "
              "Concentration with Ctrl.",
              "#showtooltip\n/cast [mod:shift] Retribution Aura; [mod:ctrl] Concentration Aura; Devotion Aura"),
        Macro("Holy Strike with Judgement", 6, "Attacks, Judges when it's ready, and Holy Strikes. "
              "Hold Shift to save Judgement.",
              "#showtooltip Holy Strike\n/startattack\n/cast [nomod:shift] Judgement\n/cast Holy Strike"),
        Macro("Hammer of Justice your focus", 8, "Stops your cast and stuns your focus, mouseover or target. "
              "Doubles as an interrupt.",
              "#showtooltip Hammer of Justice\n/stopcasting\n/cast [@focus,harm,nodead][@mouseover,harm,nodead][] "
              "Hammer of Justice"),
    ),
    "Priest": (
        Macro("Heal on mouseover, Shift for Flash Heal", 16, "Heals the friend under your mouse, "
              "your target, or yourself.",
              "#showtooltip\n/cast [mod:shift,@mouseover,help,nodead][mod:shift,help,nodead][mod:shift,@player] "
              "Flash Heal; [@mouseover,help,nodead][help,nodead][@player] Heal"),
        Macro("Power Word: Shield on mouseover", 6, "Shields the friend under your mouse, your target, or yourself.",
              "#showtooltip Power Word: Shield\n/cast [@mouseover,help,nodead][help,nodead][@player] "
              "Power Word: Shield"),
        Macro("Renew on mouseover", 8, "Puts Renew on the friend under your mouse, your target, or yourself.",
              "#showtooltip Renew\n/cast [@mouseover,help,nodead][help,nodead][@player] Renew"),
        Macro("Dispel friend or foe", 18, "Cleanses a friend or strips a buff from an enemy under your mouse, "
              "then your target, then you.",
              "#showtooltip Dispel Magic\n/cast [@mouseover,help,nodead][@mouseover,harm,nodead][help,nodead]"
              "[harm,nodead][@player] Dispel Magic"),
        Macro("Shadow Word: Pain on mouseover", 4, "Spreads Shadow Word: Pain without switching targets.",
              "#showtooltip Shadow Word: Pain\n/cast [@mouseover,harm,nodead][] Shadow Word: Pain"),
        Macro("Wand that stays on", 1, "Starts shooting your wand. A second press doesn't stop it.",
              "#showtooltip Shoot\n/cast !Shoot"),
    ),
    "Rogue": (
        Macro("One opener key", 18, "From Stealth: Ambush, Garrote with Ctrl, Cheap Shot with Shift. "
              "Out of Stealth: Sinister Strike.",
              "#showtooltip\n/cast [stealth,mod:shift] Cheap Shot; [stealth,mod:ctrl] Garrote; [stealth] Ambush; "
              "Sinister Strike\n/startattack [nostealth]"),
        Macro("Sap your mouseover or focus", 10, "Enters Stealth if needed, then Saps the enemy under your mouse, "
              "your focus, or your target.",
              "#showtooltip Sap\n/cast [nostealth] !Stealth; [@mouseover,harm,nodead][@focus,harm,nodead][] Sap"),
        Macro("Kick your focus or mouseover", 12, "Interrupts your focus, the enemy under your mouse, "
              "or your target.",
              "#showtooltip Kick\n/cast [@focus,harm,nodead][@mouseover,harm,nodead][] Kick"),
        Macro("Every finisher on one key", 10, "Eviscerate by default, Slice and Dice with Shift, "
              "Rupture with Ctrl, Expose Armor with Alt.",
              "#showtooltip\n/cast [mod:shift] Slice and Dice; [mod:ctrl] Rupture; [mod:alt] Expose Armor; "
              "Eviscerate"),
        Macro("Clean Vanish", 22, "Stops auto-attack first, so your next swing can't pull you out of Stealth.",
              "#showtooltip Vanish\n/stopattack\n/cast Vanish"),
    ),
    "Shaman": (
        Macro("Call of the Elements, Shift for Totemic Recall", 20, "Drops a full set of totems in one cast. "
              "Ctrl drops your second set.",
              "#showtooltip\n/cast [mod:shift] Totemic Recall; [mod:ctrl] Call of the Ancestors; Call of the Elements"),
        Macro("Every shock on one key", 4, "Earth Shock by default, Frost Shock with Shift, Flame Shock with Ctrl.",
              "#showtooltip\n/cast [mod:shift] Frost Shock; [mod:ctrl] Flame Shock; Earth Shock"),
        Macro("Earth Shock interrupt, even mid-cast", 4, "Stops your cast and shocks your focus, "
              "mouseover or target.",
              "#showtooltip Earth Shock\n/stopcasting\n/cast [@focus,harm,nodead][@mouseover,harm,nodead][] "
              "Earth Shock"),
        Macro("Healing Wave on mouseover, Alt for yourself", 1, "Heals the friend under your mouse, "
              "your target, or yourself.",
              "#showtooltip Healing Wave\n/cast [mod:alt,@player][@mouseover,help,nodead][help,nodead][@player] "
              "Healing Wave"),
        Macro("Every weapon imbue", 1, "Rockbiter by default, Flametongue with Shift, Frostbrand with Ctrl, "
              "Windfury with Alt.",
              "#showtooltip\n/cast [mod:shift] Flametongue Weapon; [mod:ctrl] Frostbrand Weapon; "
              "[mod:alt] Windfury Weapon; Rockbiter Weapon"),
        Macro("Ghost Wolf that stays on", 20, "Shifts into Ghost Wolf. Pressing again doesn't cancel it.",
              "#showtooltip Ghost Wolf\n/cast !Ghost Wolf"),
    ),
    "Warlock": (
        Macro("Send your demon in", 1, "Sends your demon at your target with its own opening attack.",
              "#showtooltip\n/petattack\n/cast [pet:Voidwalker] Torment; [pet:Succubus/Incubus] Lash of Pain; "
              "[pet:Imp] Firebolt"),
        Macro("Summon any demon", 10, "Imp by default, Voidwalker with Shift, Succubus with Ctrl, "
              "Felhunter with Alt. Uses Fel Domination in combat.",
              "#showtooltip\n/cast [combat] Fel Domination\n/cast [mod:shift] Summon Voidwalker; "
              "[mod:ctrl] Summon Succubus; [mod:alt] Summon Felhunter; Summon Imp"),
        Macro("Bane of Agony, then Immolate", 8, "Press twice per enemy. Starts over on a new target "
              "or out of combat.",
              "#showtooltip\n/castsequence reset=target/combat Bane of Agony, Immolate"),
        Macro("Every curse on one key", 4, "Curse of Weakness by default, Recklessness with Shift, "
              "the Elements with Ctrl, on your mouseover or target.",
              "#showtooltip\n/cast [mod:shift,@mouseover,harm,nodead][mod:shift] Curse of Recklessness; "
              "[mod:ctrl,@mouseover,harm,nodead][mod:ctrl] Curse of the Elements; "
              "[@mouseover,harm,nodead][] Curse of Weakness"),
        Macro("Fear your focus or mouseover", 8, "Fears your focus, the enemy under your mouse, or your target.",
              "#showtooltip Fear\n/cast [@focus,harm,nodead][@mouseover,harm,nodead][] Fear"),
        Macro("Healthstone, Shift for Soulstone", 10, "Creates a Healthstone, or a Soulstone while you hold Shift.",
              "#showtooltip\n/cast [mod:shift] Create Soulstone; Create Healthstone"),
    ),
    "Warrior": (
        Macro("Overpower from any stance", 12, "Overpowers in Battle Stance, or switches to it first.",
              "#showtooltip Overpower\n/startattack\n/cast [stance:1] Overpower; Battle Stance"),
        Macro("Execute from any stance", 24, "Executes, switching out of Defensive Stance first if needed.",
              "#showtooltip Execute\n/startattack\n/cast [stance:2] Battle Stance; Execute"),
        Macro("Taunt your mouseover, Shift for Mocking Blow", 10, "Taunts the enemy under your mouse or your "
              "target, changing stance first if needed.",
              "#showtooltip\n/cast [mod:shift,stance:1,@mouseover,harm,nodead][mod:shift,stance:1] Mocking Blow; "
              "[mod:shift] Battle Stance; [stance:2,@mouseover,harm,nodead][stance:2] Taunt; Defensive Stance"),
        Macro("Sunder Armor, finding a target", 10, "Targets the nearest enemy if you have none, "
              "starts attacking and Sunders.",
              "#showtooltip Sunder Armor\n/targetenemy [noharm][dead]\n/startattack\n/cast Sunder Armor"),
        Macro("Heroic Strike, Shift for Cleave", 1, "Queues Heroic Strike on your next swing, "
              "or Cleave for groups.",
              "#showtooltip\n/startattack\n/cast [mod:shift] Cleave; Heroic Strike"),
        Macro("Bloodrage into Battle Shout", 10, "Instant Rage, then Battle Shout, on one press.",
              "#showtooltip Battle Shout\n/cast Bloodrage\n/cast Battle Shout"),
    ),
}
