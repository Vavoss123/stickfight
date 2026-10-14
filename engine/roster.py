"""Archetypes and the fictional division used for quick fights and career mode."""

import random

from .cards import PRESETS, apply_deck
from .fighter import Profile, Stats

ARCHETYPES = {
    "Striker":  dict(striking=8, wrestling=4, grappling=4, cardio=5, chin=5),
    "Wrestler": dict(striking=4, wrestling=9, grappling=6, cardio=8, chin=6),
    "BJJ":      dict(striking=4, wrestling=6, grappling=10, cardio=6, chin=5),
    "Brawler":  dict(striking=7, wrestling=4, grappling=3, cardio=6, chin=8),
}

ARCHETYPE_BLURB = {
    "Striker": "Sharp hands and kicks. Wants to keep it standing.",
    "Wrestler": "Takes you down and keeps you there. Great cardio.",
    "BJJ": "Pulls guard, shoots singles and hunts submissions everywhere.",
    "Brawler": "Iron chin and heavy hands. Walks through shots to land bombs.",
}

COLORS = [
    (220, 60, 60), (60, 120, 230), (240, 190, 40), (60, 190, 110),
    (170, 90, 220), (240, 130, 40), (40, 200, 210), (230, 230, 230),
]


def make(name, nickname, archetype, hometown="", record=(0, 0), tweak=None, color=None,
         height="6'0\"", cards=None, weight="Welterweight", personality=""):
    """cards: (deck dict, perk list, level) or None for the style's preset deck."""
    s = dict(ARCHETYPES[archetype])
    for k, v in (tweak or {}).items():
        s[k] += v
    p = Profile(name=name, nickname=nickname, archetype=archetype,
                stats=Stats(**s).clamp(), color=color or COLORS[0],
                hometown=hometown, wins=record[0], losses=record[1], height=height,
                weight=weight, personality=personality)
    if cards is None:
        deck, perks = PRESETS[archetype]
        cards = (deck, perks, 1)
    deck, perks, level = cards
    levels = level if isinstance(level, dict) else None
    apply_deck(p, deck, perks, 1 if levels else level)
    for cid, lv in (levels or {}).items():
        p.cards[cid] = lv
    return p


def quick_fighters():
    """One ready-made fighter per archetype for quick fights."""
    return [
        make("Dan Reyes", "The Hammer", "Striker", "San Diego, California", (14, 3),
             color=COLORS[0], height="5'11\"", cards=(*PRESETS["Striker"], 2)),
        make("Ivan Petrov", "The Bear", "Wrestler", "Makhachkala, Russia", (18, 1),
             color=COLORS[1], height="5'10\"", cards=(*PRESETS["Wrestler"], 2)),
        make("Lucas Silva", "Spider Hands", "BJJ", "Rio de Janeiro, Brazil", (12, 4),
             color=COLORS[3], height="6'1\"", cards=(*PRESETS["BJJ"], 2)),
        make("Tommy Byrne", "Iron Jaw", "Brawler", "Dublin, Ireland", (21, 9),
             color=COLORS[2], height="5'9\"", cards=(*PRESETS["Brawler"], 2)),
    ]


# Signature cards for the division: (deck, perks, {card: level})
SIGNATURES = [
    ({"takedown": "doubleleg", "gnp": "hammer"}, ["heavytop", "ironlungs"],
     {"doubleleg": 3, "hammer": 2, "heavytop": 2, "ironlungs": 1}),
    ({"cross": "spinfist", "legkick": "calfkick"}, ["combo"],
     {"spinfist": 3, "calfkick": 2, "combo": 2}),
    ({"guillotine": "anaconda", "triangle": "kimura"}, ["subhunter"],
     {"anaconda": 3, "kimura": 2, "subhunter": 2}),
    ({"body": "liver"}, ["granite", "nevergiveup"], {"liver": 2, "granite": 3, "nevergiveup": 1}),
    ({"takedown": "doubleleg", "pass": "smash"}, ["base"], {"doubleleg": 2, "smash": 2, "base": 1}),
    ({"kick": "showtime"}, ["killer"], {"showtime": 2, "killer": 2}),
    ({"standup": "darce", "triangle": "gogo"}, ["subhunter"], {"darce": 2, "gogo": 1, "subhunter": 1}),
    ({"dirty": "spinelbow", "knees": "plum"}, ["killer"], {"spinelbow": 2, "plum": 1, "killer": 1}),
    ({"trip": "hiptoss", "gnp": "hammer"}, ["heavytop"], {"hiptoss": 1, "hammer": 1, "heavytop": 1}),
    ({"kick": "flyknee"}, ["dutch"], {"flyknee": 1, "dutch": 1}),
    ({"body": "liver"}, ["nevergiveup"], {"liver": 1, "nevergiveup": 1}),
]

# Champion first, then ranked 1 to 10
DIVISION = [
    ("Marcus Cole", "The Machine", "Wrestler", "Denver, Colorado", (24, 1), {"striking": 2, "grappling": 1, "chin": 1}),
    ("Kenji Watanabe", "Silent Storm", "Striker", "Osaka, Japan", (19, 2), {"wrestling": 1, "grappling": 1}),
    ("Rafael Duarte", "Anaconda", "BJJ", "Curitiba, Brazil", (17, 3), {"wrestling": 1, "striking": 1}),
    ("Darius Okafor", "The Wall", "Brawler", "Lagos, Nigeria", (16, 3), {"cardio": 2}),
    ("Aleksandr Volkov", "Wolf", "Wrestler", "Kazan, Russia", (15, 2), {"striking": 1}),
    ("Jake Morrison", "Lights Out", "Striker", "Las Vegas, Nevada", (14, 4), {"chin": 1}),
    ("Pedro Alves", "Choke Artist", "BJJ", "Manaus, Brazil", (13, 4), {}),
    ("Sean Gallagher", "The Butcher", "Brawler", "Boston, Massachusetts", (13, 5), {}),
    ("Omar Haddad", "The Lion", "Wrestler", "Amman, Jordan", (12, 3), {"wrestling": -1}),
    ("Chris Lindqvist", "Viking", "Striker", "Stockholm, Sweden", (11, 4), {"striking": -1}),
    ("Mateo Rojas", "El Toro", "Brawler", "Monterrey, Mexico", (10, 3), {"chin": -1}),
]

# Secret fighters, unlocked by achievements: (achievement id, builder)
UNLOCKABLES = [
    ("champion", lambda: make("Walt Rivers", "Old Man", "Wrestler", "Tulsa, Oklahoma", (41, 6),
                              {"striking": 2, "wrestling": 1, "grappling": 3, "cardio": 1, "chin": 2},
                              color=COLORS[7], height="5'11\"", weight="Middleweight",
                              personality="grinder",
                              cards=({"takedown": "doubleleg", "pass": "smash"}, ["base", "ironlungs"], 3))),
    ("ko10", lambda: make("Nia Brooks", "Kid Dynamite", "Brawler", "Philadelphia, Pennsylvania", (15, 0),
                          {"striking": 3, "cardio": 1}, color=COLORS[5], height="5'6\"",
                          weight="Lightweight", personality="pressure",
                          cards=({"cross": "superman", "body": "liver"}, ["killer", "nevergiveup"], 3))),
    ("tournament", lambda: make("Ren Takeda", "The Ghost", "BJJ", "Sapporo, Japan", (22, 2),
                                {"striking": 2, "wrestling": 2, "grappling": 1, "cardio": 2},
                                color=COLORS[6], height="6'0\"", weight="Welterweight",
                                personality="counter",
                                cards=({"triangle": "gogo", "rnc": "twister", "clinch": "imanari"},
                                       ["subhunter"], 3))),
    ("hall", lambda: make("Zara Kovac", "The Storm", "Striker", "Split, Croatia", (30, 1),
                          {"striking": 2, "wrestling": 3, "grappling": 2, "cardio": 2, "chin": 3},
                          color=COLORS[4], height="6'5\"", weight="Heavyweight", personality="showboat",
                          cards=({"kick": "showtime", "cross": "spinfist"}, ["killer", "granite"], 3))),
]


def unlocked(have):
    """The secret fighters for the achievements in `have` (a set of ids)."""
    return [build() for aid, build in UNLOCKABLES if aid in have]


_FIRST = ["Jordan", "Tyler", "Andre", "Nico", "Sam", "Luis", "Kai", "Ben", "Rico", "Max",
          "Leon", "Jamal", "Eli", "Owen", "Victor", "Dmitri", "Tariq", "Hugo"]
_LAST = ["Grant", "Ortiz", "Novak", "Kane", "Mendes", "Clarke", "Burke", "Sato", "Ruiz",
         "Walsh", "Ivanov", "Price", "Diallo", "Fischer", "Moreau", "Hayes"]
_NICK = ["The Prospect", "Hurricane", "The Kid", "Bulldog", "Razor", "Showtime",
         "Cobra", "Mad Dog", "Thunder", "Flash", "Pitbull", "The Ghost"]
_TOWNS = ["Phoenix, Arizona", "Manchester, England", "Sydney, Australia", "Toronto, Canada",
          "Miami, Florida", "Warsaw, Poland", "Auckland, New Zealand", "Chicago, Illinois"]


# Weight classes for the division in quick fight. In career they all fight at your weight.
DIVISION_PERSONALITIES = ["grinder", "counter", "balanced", "pressure", "headhunter", "showboat",
                          "subartist", "pressure", "trashtalk", "showboat", "headhunter"]
DIVISION_WEIGHTS = ["Welterweight", "Lightweight", "Middleweight", "Heavyweight", "Middleweight",
                    "Welterweight", "Lightweight", "Heavyweight", "Welterweight", "Middleweight",
                    "Lightweight"]


def division(weight=None):
    """The ranked division. weight puts them all in one class, for career mode."""
    out = []
    for idx, (n, nick, arch, town, rec, tw) in enumerate(DIVISION):
        out.append(make(n, nick, arch, town, rec, tw, color=COLORS[(idx + 1) % len(COLORS)],
                        cards=SIGNATURES[idx], weight=weight or DIVISION_WEIGHTS[idx],
                        personality=DIVISION_PERSONALITIES[idx]))
    return out


def prospect(rng, strength=0, weight="Welterweight"):
    """A random unranked opponent. strength shifts all stats."""
    arch = rng.choice(list(ARCHETYPES))
    tweak = {k: strength - 1 + rng.choice((-1, 0, 0, 1)) for k in ARCHETYPES[arch]}
    rec = (rng.randint(3, 9), rng.randint(0, 4))
    return make(f"{rng.choice(_FIRST)} {rng.choice(_LAST)}", rng.choice(_NICK), arch,
                rng.choice(_TOWNS), rec, tweak, color=rng.choice(COLORS), weight=weight,
                personality=rng.choice(["balanced", "pressure", "counter", "grinder", "showboat",
                                         "headhunter", "subartist", "trashtalk"]))
