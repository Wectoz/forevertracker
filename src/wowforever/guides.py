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

# Spell names as in the Forever beta client, collected by foreverdb.net and cross-checked against
# wowclassicforever.info and Blizzard's patch notes. Nothing above the beta's
# level 30 cap, and nothing that needs you to type in your own item names.
MACROS = {
    "Druid": (
        Macro("Break roots into Cat Form", "Drops your form and shifts straight back into Cat Form, "
              "which frees you from roots and slows.",
              "#showtooltip Cat Form\n/cancelform\n/cast Cat Form"),
        Macro("Bear Form, Maul, Shift for Swipe", "Shifts into Bear Form if needed, then Mauls, "
              "or Swipes while you hold Shift.",
              "#showtooltip\n/startattack [form:1,harm,nodead]\n"
              "/cast [form:1,mod:shift] Swipe; [form:1] Maul; Bear Form"),
        Macro("Cat Form, then Prowl", "First press shifts into Cat Form, the next one Prowls. "
              "Pressing again never breaks stealth.",
              "#showtooltip Prowl\n/cast [noform][form:1] Cat Form; !Prowl"),
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
        Macro("Every aspect on one key", "Hawk by default, Cheetah with Shift, Monkey with Ctrl. "
              "Never switches the current aspect off.",
              "#showtooltip\n/cast [mod:shift] !Aspect of the Cheetah; [mod:ctrl] !Aspect of the Monkey; "
              "!Aspect of the Hawk"),
        Macro("Every trap on one key", "Freezing Trap by default, Immolation Trap with Shift, "
              "Frost Trap with Ctrl.",
              "#showtooltip\n/cast [mod:shift] Immolation Trap; [mod:ctrl] Frost Trap; Freezing Trap"),
        Macro("Arcane Shot that keeps Auto Shot on", "Fires Arcane Shot and makes sure Auto Shot keeps going.",
              "#showtooltip Arcane Shot\n/cast !Auto Shot\n/cast Arcane Shot"),
        Macro("Pet attack, follow or stay", "Attacks your mouseover or target. Shift brings the pet back, Ctrl makes "
              "it stay.",
              "/petfollow [mod:shift]\n/petstay [mod:ctrl]\n/petattack [nomod,@mouseover,harm,nodead][nomod]"),
        Macro("Clean Feign Death", "Stops attacking, calls your pet back and Feigns Death.",
              "#showtooltip Feign Death\n/stopattack\n/petfollow\n/cast Feign Death"),
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
        Macro("Ice Block, press again to leave it", "Casts Ice Block, and a second press removes it once you're safe.",
              "#showtooltip Ice Block\n/stopcasting\n/cancelaura Ice Block\n/cast Ice Block"),
        Macro("Mana Shield and wards", "Mana Shield by default, Fire Ward with Shift, Frost Ward with Ctrl.",
              "#showtooltip\n/cast [mod:shift] Fire Ward; [mod:ctrl] Frost Ward; Mana Shield"),
        Macro("Arcane Intellect on mouseover", "Buffs the friend under your mouse, your target, or yourself.",
              "#showtooltip Arcane Intellect\n/cast [@mouseover,help,nodead][help,nodead][@player] Arcane Intellect"),
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
        Macro("Fortitude, Spirit or Shadow Protection", "Fortitude by default, Divine Spirit with Shift, Shadow "
              "Protection with Ctrl.",
              "#showtooltip\n/cast [mod:shift,@mouseover,help,nodead][mod:shift,@player] Divine Spirit; "
              "[mod:ctrl,@mouseover,help,nodead][mod:ctrl,@player] Shadow Protection; "
              "[@mouseover,help,nodead][help,nodead][@player] Power Word: Fortitude"),
        Macro("Resurrection on the dead", "Resurrects the dead player under your mouse, or your dead target.",
              "#showtooltip Resurrection\n/cast [@mouseover,help,dead][help,dead] Resurrection"),
    ),
    "Rogue": (
        Macro("One opener key", "From Stealth: Ambush, Garrote with Ctrl, Cheap Shot with Shift. "
              "Out of Stealth: Sinister Strike.",
              "#showtooltip\n/cast [stealth,mod:shift] Cheap Shot; [stealth,mod:ctrl] Garrote; [stealth] Ambush; "
              "Sinister Strike\n/startattack [nostealth]"),
        Macro("Sap your mouseover or focus", "Enters Stealth if needed, then Saps the enemy under your mouse, "
              "your focus, or your target.",
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
    ),
    "Shaman": (
        Macro("Call of the Elements, Shift for Totemic Recall", "Drops a full set of totems in one cast. "
              "Ctrl drops your second set.",
              "#showtooltip\n/cast [mod:shift] Totemic Recall; [mod:ctrl] Call of the Ancestors; Call of the Elements"),
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
        Macro("Lightning Shield, Shift for Water Shield", "Keeps your shield up with one key.",
              "#showtooltip\n/cast [mod:shift] Water Shield; Lightning Shield"),
        Macro("Grounding Totem, even mid-cast", "Stops your cast and drops Grounding Totem to soak an incoming spell.",
              "#showtooltip Grounding Totem\n/stopcasting\n/cast Grounding Totem"),
        Macro("Ancestral Spirit on the dead", "Resurrects the dead player under your mouse, or your dead target.",
              "#showtooltip Ancestral Spirit\n/cast [@mouseover,help,dead][help,dead] Ancestral Spirit"),
    ),
    "Warlock": (
        Macro("Send your demon in", "Sends your demon at your target with its own opening attack.",
              "#showtooltip\n/petattack\n/cast [pet:Voidwalker] Torment; [pet:Succubus/Incubus] Lash of Pain; "
              "[pet:Imp] Firebolt"),
        Macro("Summon any demon", "Imp by default, Voidwalker with Shift, Succubus with Ctrl, "
              "Felhunter with Alt. Uses Fel Domination in combat.",
              "#showtooltip\n/cast [combat] Fel Domination\n/cast [mod:shift] Summon Voidwalker; "
              "[mod:ctrl] Summon Succubus; [mod:alt] Summon Felhunter; Summon Imp"),
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
        Macro("Victory Rush, else Heroic Strike", "Uses Victory Rush after a kill, otherwise queues Heroic Strike.",
              "#showtooltip\n/cast Victory Rush\n/cast Heroic Strike"),
        Macro("Interrupt from any stance", "Shield Bash in Battle or Defensive Stance, Pummel in Berserker Stance.",
              "#showtooltip\n/cast [stance:1/2] Shield Bash; Pummel"),
        Macro("Revenge with Shield Block", "Revenge and Shield Block on one press. Hold Shift for Revenge only.",
              "#showtooltip Revenge\n/startattack\n/cast Revenge\n/cast [nomod:shift] Shield Block"),
        Macro("Shield Wall, Shift for Last Stand", "Switches to Defensive Stance if needed.",
              "#showtooltip Shield Wall\n/cast [mod:shift] Last Stand; [stance:2] Shield Wall; Defensive Stance"),
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
