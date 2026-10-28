"""Hand-picked addons and class macros for the Addons and Macros pages. Refreshed by hand, not gathered."""

from dataclasses import dataclass
from datetime import date

ADDONS_UPDATED = date(2026, 10, 27)
MACRO_LIMIT = 255  # characters the game allows in one macro


@dataclass(frozen=True)
class Addon:
    name: str
    slug: str  # the addon's CurseForge project, e.g. "questie"; its icon is static/addons/<slug>.png
    blurb: str

    @property
    def url(self) -> str:
        return f"https://www.curseforge.com/wow/addons/{self.slug}"


@dataclass(frozen=True)
class Macro:
    name: str
    blurb: str
    text: str


# Made for Forever, and the most downloaded of the new ones.
TRENDING = (
    Addon("ClassicUI Forever", "classicui-forever", "Brings back the original Classic look for Forever's interface, "
                                                    "one element at a time."),
    Addon("Overlord Forever", "overlord-forever", "World PvP campaign: fight over territory, guild keeps and outposts "
                                                  "with weekly rankings."),
    Addon("ForeverPlus", "foreverplus", "Buff and consumable reminders, quest and vendor automation, and profiles "
                                        "shared across characters."),
    Addon("ForeverForge", "foreverforge", "Auto quest accept and turn-in, junk selling and repairs, plus NPC voice "
                                          "narration and UI skins."),
    Addon("AtlasLoot Classic Forever", "atlasloot-forever", "Loot tables for every dungeon and raid, best-in-slot "
                                                            "lists and an honor rank calculator."),
    Addon("ForeverUI", "foreverui", "A complete replacement interface: unit and raid frames, action bars, "
                                    "nameplates, bags and chat."),
    Addon("Dungeon Quests Forever", "dungeon-quests-forever", "Step-by-step guide to every dungeon quest and "
                                                              "pre-quest, with an arrow and map pins."),
)

# Long-standing addons that ship a Forever build on CurseForge, by what they help with.
CATEGORIES = (
    ("Questing & leveling", (
        Addon("Questie", "questie", "Shows quest givers, objectives and turn-ins on your map and minimap."),
        Addon("Guidelime", "guidelime", "Step-by-step leveling guides in a small on-screen window, with an arrow "
                                        "to the next stop."),
        Addon("Hardcore", "hardcore", "Extra tools for one-life play: death alerts, achievements and checks for "
                                      "your guild."),
    )),
    ("Maps & navigation", (
        Addon("Leatrix Maps", "leatrix-maps", "Reveals unexplored map areas and adds coordinates."),
        Addon("TomTom", "tomtom", "Waypoint arrow and coordinates: type /way and follow the arrow."),
        Addon("HandyNotes", "handynotes", "Your own notes as pins on the map, and the base for many pin packs."),
    )),
    ("Combat", (
        Addon("Details!", "details", "Damage, healing and threat meter, to see how you and your group are doing."),
        Addon("Deadly Boss Mods", "deadly-boss-mods", "Timers and warnings for boss abilities. The core works on "
                                                      "Forever; timers for Forever's new bosses may come later."),
        Addon("BigWigs", "big-wigs", "The lighter alternative to Deadly Boss Mods, with the same idea: boss timers "
                                     "and warnings."),
        Addon("Plater", "plater-nameplates", "Clearer enemy nameplates with threat colors, cast bars and debuffs."),
    )),
    ("Interface & quality of life", (
        Addon("Leatrix Plus", "leatrix-plus", "Dozens of small quality-of-life switches: auto-repair, faster "
                                              "looting, less clutter."),
        Addon("Bartender4", "bartender4", "Move, resize and add action bars, with mouseover fading."),
        Addon("Dominos", "dominos", "A simpler way to rearrange your action bars."),
        Addon("MoveAny", "moveany", "Move, scale and hide any part of the default interface."),
    )),
    ("Bags & gear", (
        Addon("Baganator", "baganator", "All your bags in one window, with search and an optional category view."),
        Addon("Bagnon", "bagnon", "The classic all-in-one bag, and it shows your other characters' items too."),
        Addon("Pawn", "pawn", "Tells you in the tooltip whether a drop is an upgrade for your class and spec."),
    )),
    ("Auction house & gathering", (
        Addon("Auctionator", "auctionator", "Faster auction house searches and selling, with price history in "
                                            "tooltips."),
        Addon("GatherMate2", "gathermate2", "Remembers every herb, ore and fishing node you find and pins them on "
                                            "the map."),
    )),
)

# Spell names as in the Forever client, collected by foreverdb.net and cross-checked against
# wowclassicforever.info and Blizzard's patch notes. Up to the level 60 cap, and nothing that
# needs you to type in your own item names. Talent spells aren't promised to every spec.
MACROS = {
    "Druid": (
        Macro("Break roots into Cat Form", "Drops your form and shifts straight back into Cat Form, "
              "which frees you from roots and slows.",
              "#showtooltip Cat Form\n/cancelform\n/cast Cat Form"),
        Macro("Bear Form, Maul, Shift for Swipe", "Shifts into Bear Form if needed, then Mauls, "
              "or Swipes while you hold Shift.",
              "#showtooltip\n/startattack [form:1,harm,nodead]\n"
              "/cast [form:1,mod:shift] Swipe; [form:1] Maul; Bear Form"),
        Macro("Cat Form, then Prowl", "First press shifts into Cat Form from any form, the next one Prowls. "
              "Pressing again never breaks stealth.",
              "#showtooltip Prowl\n/cast !Cat Form\n/cast [nostealth] Prowl"),
        Macro("Rejuvenation on mouseover, Shift for Regrowth", "Heals the friend under your mouse, "
              "your target, or yourself, without changing target.",
              "#showtooltip\n/cast [mod:shift,@mouseover,help,nodead][mod:shift,help,nodead][mod:shift,@player] "
              "Regrowth; [@mouseover,help,nodead][help,nodead][@player] Rejuvenation"),
        Macro("Cure Poison, Shift for Remove Curse", "Cleanses the friend under your mouse, your target, "
              "or yourself.",
              "#showtooltip\n/cast [mod:shift,@mouseover,help,nodead][mod:shift,help,nodead][mod:shift,@player] "
              "Remove Curse; [@mouseover,help,nodead][help,nodead][@player] Cure Poison"),
        Macro("Mark of the Wild, Shift for Thorns", "Buffs the friend under your mouse, your target, or yourself.",
              "#showtooltip\n/cast [mod:shift,@mouseover,help,nodead][mod:shift,help,nodead][mod:shift,@player] "
              "Thorns; [@mouseover,help,nodead][help,nodead][@player] Mark of the Wild"),
        Macro("The right travel form", "Aquatic Form in water, Travel Form outdoors, Cat Form indoors.",
              "#showtooltip\n/cast [swimming] Aquatic Form; [outdoors] Travel Form; Cat Form"),
        Macro("Leave your form and heal yourself", "Drops Bear or Cat Form and casts Rejuvenation on you, or Regrowth "
              "with Shift.",
              "#showtooltip\n/cancelform\n/cast [mod:shift,@player] Regrowth; [@player] Rejuvenation"),
        Macro("Entangling Roots your focus", "Roots your focus, the enemy under your mouse, or your target.",
              "#showtooltip Entangling Roots\n/cast [@focus,harm,nodead][@mouseover,harm,nodead][] Entangling Roots"),
        Macro("Rebirth in combat, Revive out of it", "Resurrects the dead friend under your mouse or your dead target.",
              "#showtooltip\n/cast [combat,@mouseover,help,dead][combat,help,dead] Rebirth; "
              "[@mouseover,help,dead][help,dead] Revive"),
        Macro("Faerie Fire from any form", "Faerie Fire on the enemy under your mouse or your target, and starts "
              "attacking in Bear or Cat Form. Free in those forms.",
              "#showtooltip Faerie Fire\n/startattack [form,harm,nodead]\n/cast [@mouseover,harm,nodead][] Faerie Fire"),
        Macro("Primal Bite, else Lacerate", "Primal Bite when it's ready, Lacerate while it's on cooldown.",
              "#showtooltip\n/startattack\n/cast Primal Bite\n/cast Lacerate"),
        Macro("Barkskin, Shift for Frenzied Regeneration", "Barkskin in any form. Hold Shift in Bear Form to turn "
              "Rage into health.",
              "#showtooltip\n/cast [mod:shift,form:1] Frenzied Regeneration; Barkskin"),
        Macro("Innervate on mouseover", "Innervates the friend under your mouse, your target, or yourself.",
              "#showtooltip Innervate\n/cast [@mouseover,help,nodead][help,nodead][@player] Innervate"),
        Macro("Instant Healing Touch", "Nature's Swiftness, then Healing Touch on the friend under your mouse, "
              "your target, or yourself.",
              "#showtooltip Healing Touch\n/cast Nature's Swiftness\n"
              "/cast [@mouseover,help,nodead][help,nodead][@player] Healing Touch"),
        Macro("Swiftmend on mouseover", "Instantly heals the friend under your mouse, your target, or yourself, "
              "if they have your Rejuvenation or Regrowth.",
              "#showtooltip Swiftmend\n/cast [@mouseover,help,nodead][help,nodead][@player] Swiftmend"),
        Macro("Wild Growth on mouseover", "Heals the party of the friend under your mouse, your target's party, "
              "or your own.",
              "#showtooltip Wild Growth\n/cast [@mouseover,help,nodead][help,nodead][@player] Wild Growth"),
        Macro("Hurricane at your cursor", "Drops Hurricane where your mouse points, no targeting circle.",
              "#showtooltip Hurricane\n/cast [@cursor] Hurricane"),
        Macro("Ravage from Prowl, Shred out of it", "Opens with Ravage while you're stealthed, then Shreds. "
              "Both need you behind the target.",
              "#showtooltip\n/startattack\n/cast [stealth] Ravage; Shred"),
        Macro("Hibernate your focus", "Puts your focus, the enemy under your mouse, or your target to sleep. "
              "Beasts and Dragonkin only.",
              "#showtooltip Hibernate\n/cast [@focus,harm,nodead][@mouseover,harm,nodead][] Hibernate"),
    ),
    "Hunter": (
        Macro("Mark and send the pet", "Puts Hunter's Mark on your target and sends your pet in.",
              "#showtooltip Hunter's Mark\n/petattack\n/cast Hunter's Mark"),
        Macro("Auto Shot that stays on", "Starts Auto Shot and sends your pet. "
              "A second press doesn't switch Auto Shot off.",
              "#showtooltip Auto Shot\n/petattack\n/cast !Auto Shot"),
        Macro("Call, mend or revive your pet", "Calls your pet if it's missing and heals it if it's out. "
              "Hold Shift to revive it.",
              "#showtooltip\n/cast [mod:shift] Revive Pet; [nopet] Call Pet; Mend Pet"),
        Macro("Aimed Shot, Shift for Multi-Shot", "Two shots on one key.",
              "#showtooltip\n/cast [mod:shift] Multi-Shot; Aimed Shot"),
        Macro("Every aspect on one key", "Hawk by default, Cheetah with Shift, Monkey with Ctrl, Pack with Alt. "
              "Never switches the current aspect off.",
              "#showtooltip\n/cast [mod:alt] !Aspect of the Pack; [mod:shift] !Aspect of the Cheetah; "
              "[mod:ctrl] !Aspect of the Monkey; !Aspect of the Hawk"),
        Macro("Every trap on one key", "Freezing Trap by default, Immolation Trap with Shift, "
              "Frost Trap with Ctrl, Explosive Trap with Alt.",
              "#showtooltip\n/cast [mod:alt] Explosive Trap; [mod:shift] Immolation Trap; [mod:ctrl] Frost Trap; "
              "Freezing Trap"),
        Macro("Arcane Shot that keeps Auto Shot on", "Fires Arcane Shot and makes sure Auto Shot keeps going.",
              "#showtooltip Arcane Shot\n/cast !Auto Shot\n/cast Arcane Shot"),
        Macro("Pet attack, follow or stay", "Attacks your mouseover or target. Shift brings the pet back, Ctrl makes "
              "it stay.",
              "/petfollow [mod:shift]\n/petstay [mod:ctrl]\n/petattack [nomod,@mouseover,harm,nodead][nomod]"),
        Macro("Clean Feign Death", "Stops attacking, calls your pet back and Feigns Death.",
              "#showtooltip Feign Death\n/stopattack\n/petfollow\n/cast Feign Death"),
        Macro("Stings on one key", "Serpent Sting by default, Viper Sting with Shift, Scorpid Sting with Ctrl.",
              "#showtooltip\n/cast [mod:shift] Viper Sting; [mod:ctrl] Scorpid Sting; Serpent Sting"),
        Macro("Scatter Shot your focus or mouseover", "Disorients your focus, the enemy under your mouse, "
              "or your target.",
              "#showtooltip Scatter Shot\n/cast [@focus,harm,nodead][@mouseover,harm,nodead][] Scatter Shot"),
        Macro("Feign Death, then Freezing Trap", "In combat it Feigns Death and calls your pet back. Press again "
              "once you're out of combat to lay a Freezing Trap.",
              "#showtooltip\n/stopattack\n/petfollow\n/cast [combat] Feign Death; Freezing Trap"),
        Macro("Wing Clip, Shift for Disengage", "Slows the enemy in your face, or drops its threat on you "
              "with Shift.",
              "#showtooltip\n/cast [mod:shift] Disengage; Wing Clip"),
        Macro("Melee on one key", "Counterattack after a parry, Mongoose Bite after a dodge, Raptor Strike "
              "otherwise.",
              "#showtooltip\n/startattack\n/cast Counterattack\n/cast Mongoose Bite\n/cast Raptor Strike"),
        Macro("Volley at your cursor", "Drops Volley where your mouse points, no targeting circle.",
              "#showtooltip Volley\n/cast [@cursor] Volley"),
        Macro("Flare at your cursor", "Fires Flare where your mouse points, so stealthed Rogues and Druids "
              "show up.",
              "#showtooltip Flare\n/cast [@cursor] Flare"),
        Macro("Summon Hawk on your mouseover", "Sends your hawk at the enemy under your mouse, or your target. "
              "It stays on that enemy.",
              "#showtooltip Summon Hawk\n/cast [@mouseover,harm,nodead][] Summon Hawk"),
        Macro("Tranquilizing Shot your focus or mouseover", "Removes Frenzy from your focus, the enemy under "
              "your mouse, or your target.",
              "#showtooltip Tranquilizing Shot\n/cast [@focus,harm,nodead][@mouseover,harm,nodead][] "
              "Tranquilizing Shot"),
    ),
    "Mage": (
        Macro("Polymorph your focus or mouseover", "Sheeps your focus, then the enemy under your mouse, "
              "then your target.",
              "#showtooltip Polymorph\n/cast [@focus,harm,nodead][@mouseover,harm,nodead][] Polymorph"),
        Macro("Counterspell, even mid-cast", "Stops your own cast and interrupts your focus, "
              "mouseover or target.",
              "#showtooltip Counterspell\n/stopcasting\n/cast [@focus,harm,nodead][@mouseover,harm,nodead][] "
              "Counterspell"),
        Macro("Frost Nova right now", "Cancels your cast and roots everything in melee range.",
              "#showtooltip Frost Nova\n/stopcasting\n/cast Frost Nova"),
        Macro("Blink, even mid-cast", "Stops your cast and Blinks, breaking stuns and roots.",
              "#showtooltip Blink\n/stopcasting\n/cast Blink"),
        Macro("Flamestrike at your cursor", "Lands Flamestrike where your mouse points, "
              "no targeting circle.",
              "#showtooltip Flamestrike\n/cast [@cursor] Flamestrike"),
        Macro("Water, food or mana gem", "Conjures water, food with Shift, or a Mana Agate with Ctrl.",
              "#showtooltip\n/cast [mod:shift] Conjure Food; [mod:ctrl] Conjure Mana Agate; Conjure Water"),
        Macro("Blizzard at your cursor", "Channels Blizzard where your mouse points, no targeting circle.",
              "#showtooltip Blizzard\n/cast [@cursor] Blizzard"),
        Macro("Ice Block, press again to leave it", "Frost talent. Casts Ice Block, and a second press removes it "
              "once you're safe.",
              "#showtooltip Ice Block\n/stopcasting\n/cancelaura Ice Block\n/cast Ice Block"),
        Macro("Mana Shield and wards", "Mana Shield by default, Fire Ward with Shift, Frost Ward with Ctrl.",
              "#showtooltip\n/cast [mod:shift] Fire Ward; [mod:ctrl] Frost Ward; Mana Shield"),
        Macro("Arcane Intellect, Shift for Brilliance", "Buffs the friend under your mouse, your target, or "
              "yourself. Shift buffs the whole group.",
              "#showtooltip\n/cast [mod:shift] Arcane Brilliance; [@mouseover,help,nodead][help,nodead][@player] "
              "Arcane Intellect"),
        Macro("Presence of Mind Pyroblast", "Makes your next Pyroblast instant.",
              "#showtooltip Pyroblast\n/cast Presence of Mind\n/stopcasting\n/cast Pyroblast"),
        Macro("Arcane Power with trinkets", "Uses both trinkets and Arcane Power on one press.",
              "#showtooltip Arcane Power\n/use 13\n/use 14\n/cast Arcane Power"),
        Macro("Combustion with trinkets", "Uses both trinkets and Combustion on one press.",
              "#showtooltip Combustion\n/use 13\n/use 14\n/cast Combustion"),
        Macro("Use your best mana gem", "Uses the strongest mana gem in your bags.",
              "#showtooltip\n/use Mana Ruby\n/use Mana Citrine\n/use Mana Jade\n/use Mana Agate"),
        Macro("Remove Lesser Curse on mouseover", "Removes a curse from the friend under your mouse, your target, "
              "or yourself.",
              "#showtooltip Remove Lesser Curse\n/cast [@mouseover,help,nodead][help,nodead][@player] "
              "Remove Lesser Curse"),
        Macro("Ice Armor, Shift for Mage Armor", "Keeps your armor up with one key.",
              "#showtooltip\n/cast [mod:shift] Mage Armor; Ice Armor"),
        Macro("Arcane Explosion, Shift for Cone of Cold", "Area damage on one key. Ctrl casts Frost Nova.",
              "#showtooltip\n/cast [mod:shift] Cone of Cold; [mod:ctrl] Frost Nova; Arcane Explosion"),
        Macro("Frost Blast your mouseover", "Slows the enemy under your mouse, or your target, without "
              "switching targets.",
              "#showtooltip Frost Blast\n/cast [@mouseover,harm,nodead][] Frost Blast"),
    ),
    "Paladin": (
        Macro("Holy Light on mouseover, Shift for Flash of Light", "Heals the friend under your mouse, "
              "your target, or yourself.",
              "#showtooltip\n/cast [mod:shift,@mouseover,help,nodead][mod:shift,help,nodead][mod:shift,@player] "
              "Flash of Light; [@mouseover,help,nodead][help,nodead][@player] Holy Light"),
        Macro("Purify your mouseover or yourself", "Removes a poison and a disease from the friend under "
              "your mouse, your target, or you.",
              "#showtooltip Purify\n/cast [@mouseover,help,nodead][help,nodead][@player] Purify"),
        Macro("Might, Wisdom or Kings", "Blessing of Might by default, Wisdom with Shift, Kings with Ctrl, "
              "on your mouseover or yourself.",
              "#showtooltip\n/cast [mod:shift,@mouseover,help,nodead][mod:shift,@player] Blessing of Wisdom; "
              "[mod:ctrl,@mouseover,help,nodead][mod:ctrl,@player] Blessing of Kings; "
              "[@mouseover,help,nodead][@player] Blessing of Might"),
        Macro("Every aura on one key", "Devotion Aura by default, Retribution with Shift, "
              "Concentration with Ctrl.",
              "#showtooltip\n/cast [mod:shift] Retribution Aura; [mod:ctrl] Concentration Aura; Devotion Aura"),
        Macro("Holy Strike with Judgement", "Attacks, Judges when it's ready, and Holy Strikes. "
              "Hold Shift to save Judgement.",
              "#showtooltip Holy Strike\n/startattack\n/cast [nomod:shift] Judgement\n/cast Holy Strike"),
        Macro("Hammer of Justice your focus", "Stops your cast and stuns your focus, mouseover or target. "
              "Doubles as an interrupt.",
              "#showtooltip Hammer of Justice\n/stopcasting\n/cast [@focus,harm,nodead][@mouseover,harm,nodead][] "
              "Hammer of Justice"),
        Macro("Lay on Hands, Alt for yourself", "Lay on Hands on the friend under your mouse or your target. Alt "
              "always targets you.",
              "#showtooltip Lay on Hands\n/cast [mod:alt,@player][@mouseover,help,nodead][help,nodead][@player] "
              "Lay on Hands"),
        Macro("Blessing of Protection, even mid-cast", "Stops your cast and protects your mouseover or target. Alt for "
              "yourself.",
              "#showtooltip Blessing of Protection\n/stopcasting\n/cast "
              "[mod:alt,@player][@mouseover,help,nodead][help,nodead][@player] Blessing of Protection"),
        Macro("Redemption on the dead", "Resurrects the dead player under your mouse, or your dead target.",
              "#showtooltip Redemption\n/cast [@mouseover,help,dead][help,dead] Redemption"),
        Macro("Cleanse your mouseover or yourself", "Removes a poison, a disease and a magic effect from the "
              "friend under your mouse, your target, or you.",
              "#showtooltip Cleanse\n/cast [@mouseover,help,nodead][help,nodead][@player] Cleanse"),
        Macro("Holy Shock friend or foe", "Heals the friend or hits the enemy under your mouse, then your target, "
              "then heals you.",
              "#showtooltip Holy Shock\n/cast [@mouseover,help,nodead][@mouseover,harm,nodead][help,nodead]"
              "[harm,nodead][@player] Holy Shock"),
        Macro("Light's Vigil on mouseover, Alt for focus", "Puts Light's Vigil on the friend or enemy under your "
              "mouse, or your target. Alt puts it on your focus.",
              "#showtooltip Light's Vigil\n/cast [mod:alt,@focus,help,nodead][@mouseover,help,nodead]"
              "[@mouseover,harm,nodead][help,nodead][harm,nodead][@player] Light's Vigil"),
        Macro("Divine Favor into Holy Light", "Makes your next heal a sure critical, then casts Holy Light on "
              "your mouseover, target, or yourself.",
              "#showtooltip Divine Favor\n/cast Divine Favor\n/cast [@mouseover,help,nodead][help,nodead][@player] "
              "Holy Light"),
        Macro("Judgement your mouseover", "Judges the enemy under your mouse or your target. With Seal of Fury "
              "up, it's a taunt.",
              "#showtooltip Judgement\n/cast [@mouseover,harm,nodead][] Judgement"),
        Macro("Hammer of Wrath on mouseover", "Finishes off the enemy under your mouse or your target once "
              "it's below 20% health.",
              "#showtooltip Hammer of Wrath\n/cast [@mouseover,harm,nodead][] Hammer of Wrath"),
        Macro("Blessing of Freedom, even mid-cast", "Stops your cast and frees your mouseover or target from "
              "roots and slows. Alt for yourself.",
              "#showtooltip Blessing of Freedom\n/stopcasting\n/cast [mod:alt,@player][@mouseover,help,nodead]"
              "[help,nodead][@player] Blessing of Freedom"),
        Macro("Salvation, Shift to Revoke", "Gives Salvation to the friend under your mouse, your target, or "
              "yourself. Shift takes it off again.",
              "#showtooltip\n/cast [mod:shift,@mouseover,help,nodead][mod:shift,help,nodead] Revoke; "
              "[@mouseover,help,nodead][help,nodead][@player] Salvation"),
        Macro("Greater Might, Wisdom or Kings", "Greater Blessing of Might on your mouseover's or target's "
              "class, Wisdom with Shift, Kings with Ctrl.",
              "#showtooltip\n/cast [mod:shift,@mouseover,help,nodead][mod:shift,help,nodead] Greater Blessing of "
              "Wisdom; [mod:ctrl,@mouseover,help,nodead][mod:ctrl,help,nodead] Greater Blessing of Kings; "
              "[@mouseover,help,nodead][help,nodead] Greater Blessing of Might"),
        Macro("Repentance your focus", "Incapacitates your focus, mouseover or target. Only works on "
              "Humanoids.",
              "#showtooltip Repentance\n/cast [@focus,harm,nodead][@mouseover,harm,nodead][] Repentance"),
    ),
    "Priest": (
        Macro("Heal on mouseover, Shift for Flash Heal", "Heals the friend under your mouse, "
              "your target, or yourself.",
              "#showtooltip\n/cast [mod:shift,@mouseover,help,nodead][mod:shift,help,nodead][mod:shift,@player] "
              "Flash Heal; [@mouseover,help,nodead][help,nodead][@player] Heal"),
        Macro("Power Word: Shield on mouseover", "Shields the friend under your mouse, your target, or yourself.",
              "#showtooltip Power Word: Shield\n/cast [@mouseover,help,nodead][help,nodead][@player] "
              "Power Word: Shield"),
        Macro("Renew on mouseover", "Puts Renew on the friend under your mouse, your target, or yourself.",
              "#showtooltip Renew\n/cast [@mouseover,help,nodead][help,nodead][@player] Renew"),
        Macro("Dispel friend or foe", "Cleanses a friend or strips a buff from an enemy under your mouse, "
              "then your target, then you.",
              "#showtooltip Dispel Magic\n/cast [@mouseover,help,nodead][@mouseover,harm,nodead][help,nodead]"
              "[harm,nodead][@player] Dispel Magic"),
        Macro("Shadow Word: Pain on mouseover", "Spreads Shadow Word: Pain without switching targets.",
              "#showtooltip Shadow Word: Pain\n/cast [@mouseover,harm,nodead][] Shadow Word: Pain"),
        Macro("Wand that stays on", "Starts shooting your wand. A second press doesn't stop it.",
              "#showtooltip Shoot\n/cast !Shoot"),
        Macro("Psychic Scream right now", "Stops your cast and sends nearby enemies running.",
              "#showtooltip Psychic Scream\n/stopcasting\n/cast Psychic Scream"),
        Macro("Fortitude, Spirit or Shadow Protection", "Fortitude by default, Divine Spirit (Discipline talent) "
              "with Shift, Shadow Protection with Ctrl.",
              "#showtooltip\n/cast [mod:shift,@mouseover,help,nodead][mod:shift,@player] Divine Spirit; "
              "[mod:ctrl,@mouseover,help,nodead][mod:ctrl,@player] Shadow Protection; "
              "[@mouseover,help,nodead][help,nodead][@player] Power Word: Fortitude"),
        Macro("Resurrection on the dead", "Resurrects the dead player under your mouse, or your dead target.",
              "#showtooltip Resurrection\n/cast [@mouseover,help,dead][help,dead] Resurrection"),
        Macro("Penance on friend or foe", "Heals the friend under your mouse or your target, or hits "
              "your target if it's an enemy.",
              "#showtooltip Penance\n/cast [@mouseover,help,nodead][help,nodead][harm,nodead][@player] Penance"),
        Macro("Fear Ward on mouseover", "Wards the friend under your mouse, your target, or yourself against "
              "the next Fear.",
              "#showtooltip Fear Ward\n/cast [@mouseover,help,nodead][help,nodead][@player] Fear Ward"),
        Macro("Prayer of Mending on mouseover", "Puts Prayer of Mending on the friend under your mouse, "
              "your target, or yourself.",
              "#showtooltip Prayer of Mending\n/cast [@mouseover,help,nodead][help,nodead][@player] "
              "Prayer of Mending"),
        Macro("Binding Heal on mouseover", "Heals you and the friend under your mouse, or your target.",
              "#showtooltip Binding Heal\n/cast [@mouseover,help,nodead][help,nodead] Binding Heal"),
        Macro("Free Greater Heal", "Uses Inner Focus, then Greater Heals the friend under your mouse, "
              "your target, or yourself.",
              "#showtooltip Greater Heal\n/cast Inner Focus\n/cast [@mouseover,help,nodead][help,nodead][@player] "
              "Greater Heal"),
        Macro("Shackle your focus", "Shackles your focus, the enemy under your mouse, or your target, so "
              "you can re-shackle without switching targets.",
              "#showtooltip Shackle Undead\n/cast [@focus,harm,nodead][@mouseover,harm,nodead][] Shackle Undead"),
        Macro("Silence your focus", "Stops your cast and Silences your focus, the enemy under your mouse, "
              "or your target.",
              "#showtooltip Silence\n/stopcasting\n/cast [@focus,harm,nodead][@mouseover,harm,nodead][] Silence"),
        Macro("Shadow Word: Death mid-cast", "Breaks off your cast or Mind Flay to finish off the enemy under "
              "your mouse, or your target.",
              "#showtooltip Shadow Word: Death\n/stopcasting\n/cast [@mouseover,harm,nodead][] Shadow Word: Death"),
        Macro("Group buffs", "Prayer of Fortitude on your group by default, Prayer of Spirit with Shift, "
              "Prayer of Shadow Protection with Ctrl.",
              "#showtooltip\n/cast [mod:shift,@player] Prayer of Spirit; [mod:ctrl,@player] "
              "Prayer of Shadow Protection; [@player] Prayer of Fortitude"),
    ),
    "Rogue": (
        Macro("One opener key", "From Stealth: Ambush, Garrote with Ctrl, Cheap Shot with Shift. "
              "Out of Stealth: Sinister Strike.",
              "#showtooltip\n/cast [stealth,mod:shift] Cheap Shot; [stealth,mod:ctrl] Garrote; [stealth] Ambush; "
              "Sinister Strike\n/startattack [nostealth]"),
        Macro("Sap your mouseover or focus", "First press enters Stealth, the next Saps the enemy under your mouse, "
              "your focus, or your target. You stay in Stealth.",
              "#showtooltip Sap\n/cast [nostealth] !Stealth; [@mouseover,harm,nodead][@focus,harm,nodead][] Sap"),
        Macro("Kick your focus or mouseover", "Interrupts your focus, the enemy under your mouse, "
              "or your target.",
              "#showtooltip Kick\n/cast [@focus,harm,nodead][@mouseover,harm,nodead][] Kick"),
        Macro("Every finisher on one key", "Eviscerate by default, Slice and Dice with Shift, "
              "Rupture with Ctrl, Expose Armor with Alt.",
              "#showtooltip\n/cast [mod:shift] Slice and Dice; [mod:ctrl] Rupture; [mod:alt] Expose Armor; "
              "Eviscerate"),
        Macro("Clean Vanish", "Stops auto-attack first, so your next swing can't pull you out of Stealth.",
              "#showtooltip Vanish\n/stopattack\n/cast Vanish"),
        Macro("Evasion, Sprint or Vanish", "Evasion by default, Sprint with Shift, Vanish with Ctrl.",
              "#showtooltip\n/stopattack [mod:ctrl]\n/cast [mod:shift] Sprint; [mod:ctrl] Vanish; Evasion"),
        Macro("Cold Blood Eviscerate", "Cold Blood and Eviscerate on one press, for a guaranteed critical strike.",
              "#showtooltip Cold Blood\n/cast Cold Blood\n/cast Eviscerate"),
        Macro("Distract at your cursor", "Throws Distract where your mouse points, no targeting circle.",
              "#showtooltip Distract\n/cast [@cursor] Distract"),
        Macro("Stealth that stays on", "Enters Stealth. Pressing again doesn't take you out of it.",
              "#showtooltip Stealth\n/cast !Stealth"),
        Macro("Blind your focus or mouseover", "Stops your swing and Blinds your focus, the enemy under your mouse, "
              "or your target.",
              "#showtooltip Blind\n/stopattack\n/cast [@focus,harm,nodead][@mouseover,harm,nodead][] Blind"),
        Macro("Pick Pocket your mouseover", "Picks the pocket of the enemy under your mouse, or your target.",
              "#showtooltip Pick Pocket\n/cast [@mouseover,harm,nodead][] Pick Pocket"),
        Macro("Cold Blood Mutilate", "Cold Blood and Mutilate on one press, for a guaranteed critical strike.",
              "#showtooltip Cold Blood\n/cast Cold Blood\n/cast Mutilate"),
        Macro("Assassination finishers", "Eviscerate by default, Venom with Shift, Kidney Shot with Ctrl, "
              "Rupture with Alt.",
              "#showtooltip\n/cast [mod:shift] Venom; [mod:ctrl] Kidney Shot; [mod:alt] Rupture; Eviscerate"),
        Macro("Premeditation opener", "From Stealth: Premeditation, then Ambush. Cheap Shot with Shift.",
              "#showtooltip\n/cast [stealth] Premeditation\n/cast [stealth,mod:shift] Cheap Shot; [stealth] Ambush"),
        Macro("Blade Flurry, Ctrl cancels it", "Starts Blade Flurry. Ctrl ends it early so it can't break your "
              "Sap or Blind.",
              "#showtooltip Blade Flurry\n/cancelaura [mod:ctrl] Blade Flurry\n/cast [nomod:ctrl] Blade Flurry"),
        Macro("Adrenaline Rush with trinkets", "Uses both trinket slots, then Adrenaline Rush.",
              "#showtooltip Adrenaline Rush\n/use 13\n/use 14\n/cast Adrenaline Rush"),
    ),
    "Shaman": (
        Macro("Call of the Elements, Shift for Totemic Recall", "Drops a full set of totems in one cast. "
              "Ctrl drops your second set, Alt your third.",
              "#showtooltip\n/cast [mod:shift] Totemic Recall; [mod:alt] Call of the Spirits; "
              "[mod:ctrl] Call of the Ancestors; Call of the Elements"),
        Macro("Every shock on one key", "Earth Shock by default, Frost Shock with Shift, Flame Shock with Ctrl.",
              "#showtooltip\n/cast [mod:shift] Frost Shock; [mod:ctrl] Flame Shock; Earth Shock"),
        Macro("Earth Shock interrupt, even mid-cast", "Stops your cast and shocks your focus, "
              "mouseover or target.",
              "#showtooltip Earth Shock\n/stopcasting\n/cast [@focus,harm,nodead][@mouseover,harm,nodead][] "
              "Earth Shock"),
        Macro("Healing Wave on mouseover, Alt for yourself", "Heals the friend under your mouse, "
              "your target, or yourself.",
              "#showtooltip Healing Wave\n/cast [mod:alt,@player][@mouseover,help,nodead][help,nodead][@player] "
              "Healing Wave"),
        Macro("Every weapon imbue", "Rockbiter by default, Flametongue with Shift, Frostbrand with Ctrl, "
              "Windfury with Alt.",
              "#showtooltip\n/cast [mod:shift] Flametongue Weapon; [mod:ctrl] Frostbrand Weapon; "
              "[mod:alt] Windfury Weapon; Rockbiter Weapon"),
        Macro("Ghost Wolf that stays on", "Shifts into Ghost Wolf. Pressing again doesn't cancel it.",
              "#showtooltip Ghost Wolf\n/cast !Ghost Wolf"),
        Macro("Purge your mouseover", "Strips a magic buff from the enemy under your mouse, your focus, or your "
              "target.",
              "#showtooltip Purge\n/cast [@mouseover,harm,nodead][@focus,harm,nodead][] Purge"),
        Macro("Lightning Shield, Shift for Water Shield", "Keeps your shield up with one key. Water Shield needs "
              "the Restoration talent.",
              "#showtooltip\n/cast [mod:shift] Water Shield; Lightning Shield"),
        Macro("Grounding Totem, even mid-cast", "Stops your cast and drops Grounding Totem to soak an incoming spell.",
              "#showtooltip Grounding Totem\n/stopcasting\n/cast Grounding Totem"),
        Macro("Ancestral Spirit on the dead", "Resurrects the dead player under your mouse, or your dead target.",
              "#showtooltip Ancestral Spirit\n/cast [@mouseover,help,dead][help,dead] Ancestral Spirit"),
        Macro("Chain Heal on mouseover, Alt for yourself", "Starts Chain Heal on the friend under your mouse, "
              "your target, or yourself.",
              "#showtooltip Chain Heal\n/cast [mod:alt,@player][@mouseover,help,nodead][help,nodead][@player] "
              "Chain Heal"),
        Macro("Riptide on mouseover, Alt for yourself", "Riptide on the friend under your mouse, your target, "
              "or yourself. Follow up with Chain Heal on them for a stronger heal.",
              "#showtooltip Riptide\n/cast [mod:alt,@player][@mouseover,help,nodead][help,nodead][@player] Riptide"),
        Macro("Lesser Healing Wave on mouseover, Alt for yourself", "A fast heal on the friend under your mouse, "
              "your target, or yourself.",
              "#showtooltip Lesser Healing Wave\n/cast [mod:alt,@player][@mouseover,help,nodead][help,nodead]"
              "[@player] Lesser Healing Wave"),
        Macro("Instant Healing Wave", "Nature's Swiftness, then Healing Wave on your mouseover, target, "
              "or yourself.",
              "#showtooltip Nature's Swiftness\n/cast Nature's Swiftness\n"
              "/cast [@mouseover,help,nodead][help,nodead][@player] Healing Wave"),
        Macro("Cure Poison, Shift for Cure Disease", "Cleanses the friend under your mouse, your target, "
              "or yourself.",
              "#showtooltip\n/cast [mod:shift,@mouseover,help,nodead][mod:shift,help,nodead][mod:shift,@player] "
              "Cure Disease; [@mouseover,help,nodead][help,nodead][@player] Cure Poison"),
        Macro("Stormstrike with auto attack", "Starts your auto attack and Stormstrikes in one press.",
              "#showtooltip Stormstrike\n/startattack\n/cast Stormstrike"),
        Macro("Lightning Bolt, Shift for Chain Lightning", "Single target by default, Chain Lightning for packs.",
              "#showtooltip\n/cast [mod:shift] Chain Lightning; Lightning Bolt"),
        Macro("Searing Totem, Shift for Magma Totem", "Your fire totem for one target or for a pack.",
              "#showtooltip\n/cast [mod:shift] Magma Totem; Searing Totem"),
        Macro("Earthbind Totem, Shift for Tremor Totem", "Slows runners, or breaks fear, sleep and charm "
              "with Shift.",
              "#showtooltip\n/cast [mod:shift] Tremor Totem; Earthbind Totem"),
    ),
    "Warlock": (
        Macro("Send your demon in", "Sends your demon at your target with its own opening attack.",
              "#showtooltip\n/petattack\n/cast [pet:Voidwalker] Torment; [pet:Succubus/Incubus] Lash of Pain; "
              "[pet:Imp] Firebolt"),
        Macro("Summon any demon", "Imp by default, Voidwalker with Shift, Succubus with Ctrl, Incubus with "
              "Ctrl+Shift, Felhunter with Alt. Uses Fel Domination in combat if you have the talent.",
              "#showtooltip\n/cast [combat] Fel Domination\n/cast [mod:ctrl,mod:shift] Summon Incubus; "
              "[mod:shift] Summon Voidwalker; [mod:ctrl] Summon Succubus; [mod:alt] Summon Felhunter; Summon Imp"),
        Macro("Bane of Agony, then Immolate", "Press twice per enemy. Starts over on a new target "
              "or out of combat.",
              "#showtooltip\n/castsequence reset=target/combat Bane of Agony, Immolate"),
        Macro("Every curse on one key", "Curse of Weakness by default, Recklessness with Shift, "
              "the Elements with Ctrl, on your mouseover or target.",
              "#showtooltip\n/cast [mod:shift,@mouseover,harm,nodead][mod:shift] Curse of Recklessness; "
              "[mod:ctrl,@mouseover,harm,nodead][mod:ctrl] Curse of the Elements; "
              "[@mouseover,harm,nodead][] Curse of Weakness"),
        Macro("Fear your focus or mouseover", "Fears your focus, the enemy under your mouse, or your target.",
              "#showtooltip Fear\n/cast [@focus,harm,nodead][@mouseover,harm,nodead][] Fear"),
        Macro("Healthstone, Shift for Soulstone", "Creates a Healthstone, or a Soulstone while you hold Shift.",
              "#showtooltip\n/cast [mod:shift] Create Soulstone; Create Healthstone"),
        Macro("Life Tap, Shift for Health Funnel", "Turns health into mana, or heals your demon with Shift.",
              "#showtooltip\n/cast [mod:shift] Health Funnel; Life Tap"),
        Macro("Rain of Fire at your cursor", "Rains fire where your mouse points, no targeting circle.",
              "#showtooltip Rain of Fire\n/cast [@cursor] Rain of Fire"),
        Macro("Banish your focus", "Banishes your focus, mouseover or target. Works on demons and elementals.",
              "#showtooltip Banish\n/cast [@focus,harm,nodead][@mouseover,harm,nodead][] Banish"),
        Macro("Drain Soul rank 1 for shards", "The cheapest Drain Soul, for collecting Soul Shards from dying enemies.",
              "#showtooltip Drain Soul\n/cast Drain Soul(Rank 1)"),
        Macro("Corruption on mouseover, Shift for Bane of Agony", "DoTs the enemy under your mouse, or your target, "
              "without changing target.",
              "#showtooltip\n/cast [mod:shift,@mouseover,harm,nodead][mod:shift] Bane of Agony; "
              "[@mouseover,harm,nodead][] Corruption"),
        Macro("Curse of Tongues, Shift for Exhaustion, Ctrl for Idiocy", "Slows a caster's spells by default, "
              "slows a runner with Shift, or drains Intellect with Ctrl, on your mouseover or target.",
              "#showtooltip\n/cast [mod:shift,@mouseover,harm,nodead][mod:shift] Curse of Exhaustion; "
              "[mod:ctrl,@mouseover,harm,nodead][mod:ctrl] Curse of Idiocy; [@mouseover,harm,nodead][] "
              "Curse of Tongues"),
        Macro("Death Coil your mouseover", "Horrifies and drains the enemy under your mouse, or your target.",
              "#showtooltip Death Coil\n/cast [@mouseover,harm,nodead][] Death Coil"),
        Macro("Howl of Terror, even mid-cast", "Stops your cast and fears every nearby enemy.",
              "#showtooltip Howl of Terror\n/stopcasting\n/cast Howl of Terror"),
        Macro("Spell Lock your focus", "Your Felhunter silences your focus, the enemy under your mouse, "
              "or your target.",
              "#showtooltip Spell Lock\n/cast [@focus,harm,nodead][@mouseover,harm,nodead][] Spell Lock"),
        Macro("Seduce your focus", "Your Succubus or Incubus seduces your focus, the enemy under your mouse, "
              "or your target.",
              "#showtooltip Seduction\n/cast [@focus,harm,nodead][@mouseover,harm,nodead][] Seduction"),
        Macro("Firestone, Shift for Spellstone", "Creates a Firestone, or a Spellstone while you hold Shift. "
              "Both are weapon imbues in Forever and stack with oils.",
              "#showtooltip\n/cast [mod:shift] Create Spellstone; Create Firestone"),
    ),
    "Warrior": (
        Macro("Overpower from any stance", "Overpowers in Battle Stance, or switches to it first.",
              "#showtooltip Overpower\n/startattack\n/cast [stance:1] Overpower; Battle Stance"),
        Macro("Execute from any stance", "Executes, switching out of Defensive Stance first if needed.",
              "#showtooltip Execute\n/startattack\n/cast [stance:2] Battle Stance; Execute"),
        Macro("Taunt your mouseover, Shift for Mocking Blow", "Taunts the enemy under your mouse or your "
              "target, changing stance first if needed.",
              "#showtooltip\n/cast [mod:shift,stance:1,@mouseover,harm,nodead][mod:shift,stance:1] Mocking Blow; "
              "[mod:shift] Battle Stance; [stance:2,@mouseover,harm,nodead][stance:2] Taunt; Defensive Stance"),
        Macro("Sunder Armor, finding a target", "Targets the nearest enemy if you have none, "
              "starts attacking and Sunders.",
              "#showtooltip Sunder Armor\n/targetenemy [noharm][dead]\n/startattack\n/cast Sunder Armor"),
        Macro("Heroic Strike, Shift for Cleave", "Queues Heroic Strike on your next swing, "
              "or Cleave for groups.",
              "#showtooltip\n/startattack\n/cast [mod:shift] Cleave; Heroic Strike"),
        Macro("Bloodrage into Battle Shout", "Instant Rage, then Battle Shout, on one press.",
              "#showtooltip Battle Shout\n/cast Bloodrage\n/cast Battle Shout"),
        Macro("Victory Rush, plus Heroic Strike", "Uses Victory Rush when it lights up after a kill, and queues "
              "Heroic Strike on every press.",
              "#showtooltip\n/cast Victory Rush\n/cast Heroic Strike"),
        Macro("Interrupt from any stance", "Shield Bash in Battle or Defensive Stance, Pummel in Berserker Stance.",
              "#showtooltip\n/cast [stance:1/2] Shield Bash; Pummel"),
        Macro("Revenge with Shield Block", "Revenge and Shield Block on one press. Hold Shift for Revenge only.",
              "#showtooltip Revenge\n/startattack\n/cast Revenge\n/cast [nomod:shift] Shield Block"),
        Macro("Shield Wall, Shift for Last Stand", "Switches to Defensive Stance if needed.",
              "#showtooltip Shield Wall\n/cast [mod:shift] Last Stand; [stance:2] Shield Wall; Defensive Stance"),
        Macro("Charge or Intercept from any stance", "Charges from Battle Stance out of combat and Intercepts "
              "from Berserker Stance in combat, switching stance first if needed.",
              "#showtooltip\n/cast [nocombat,stance:1] Charge; [nocombat] Battle Stance; [stance:3] Intercept; "
              "Berserker Stance"),
        Macro("Spearing Strike from any stance", "Spearing Strike needs Battle Stance, so this switches first "
              "if needed.",
              "#showtooltip Spearing Strike\n/startattack\n/cast [stance:1] Spearing Strike; Battle Stance"),
        Macro("Hamstring from any stance", "Hamstrings, leaving Defensive Stance for Battle Stance first if needed.",
              "#showtooltip Hamstring\n/startattack\n/cast [stance:2] Battle Stance; Hamstring"),
        Macro("Berserker Rage from any stance", "Breaks and blocks Fear, switching to Berserker Stance first "
              "if needed.",
              "#showtooltip Berserker Rage\n/cast [stance:3] Berserker Rage; Berserker Stance"),
        Macro("Whirlwind from any stance", "Whirlwinds, switching to Berserker Stance first if needed.",
              "#showtooltip Whirlwind\n/startattack\n/cast [stance:3] Whirlwind; Berserker Stance"),
        Macro("Disarm from any stance", "Disarms your target, switching to Defensive Stance first if needed.",
              "#showtooltip Disarm\n/cast [stance:2] Disarm; Defensive Stance"),
        Macro("The big cooldown for your stance", "Retaliation in Battle Stance, Shield Wall in Defensive, "
              "Recklessness in Berserker. In Forever they no longer share a cooldown.",
              "#showtooltip\n/cast [stance:1] Retaliation; [stance:2] Shield Wall; [stance:3] Recklessness"),
        Macro("Death Wish with your trinkets", "Uses both trinket slots, then Death Wish, on one press.",
              "#showtooltip Death Wish\n/use 13\n/use 14\n/cast Death Wish"),
        Macro("Intimidating Shout on your mouseover", "Fears the enemy under your mouse, or your target, and "
              "nearby enemies.",
              "#showtooltip Intimidating Shout\n/cast [@mouseover,harm,nodead][] Intimidating Shout"),
    ),
}

# Macros any class can use.
GENERAL_MACROS = (
    Macro("Target the nearest enemy, but keep yours", "Picks the nearest enemy only when you have no living enemy "
          "targeted.",
          "/targetenemy [noharm][dead]"),
    Macro("Set your focus, Shift clears it", "Makes the unit under your mouse, or your target, your focus.",
          "/clearfocus [mod:shift]\n/focus [nomod,@mouseover,exists,nodead][nomod,@target,exists]"),
    Macro("Use your best Healthstone", "Uses the strongest Healthstone in your bags.",
          "#showtooltip\n/use Greater Healthstone\n/use Healthstone\n/use Lesser Healthstone\n"
          "/use Minor Healthstone"),
    Macro("Skull on your mouseover", "Puts the Skull marker on the unit under your mouse, or your target.",
          "/tm [@mouseover,exists,nodead][] !8"),
    Macro("Pull timer", "Tells your party you're pulling and starts a 5-second countdown.",
          "/p Pulling in 5\n/countdown 5"),
    Macro("Zoom the camera further out", "Raises the camera's maximum distance beyond the options slider.",
          "/console cameraDistanceMaxZoomFactor 2.6"),
)
