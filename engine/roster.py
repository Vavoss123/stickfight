"""Archetypes and the fictional division used for quick fights and career mode."""

import random

from .fighter import Profile, Stats

ARCHETYPES = {
    "Striker":  dict(striking=8, wrestling=4, grappling=4, cardio=6, chin=5),
    "Wrestler": dict(striking=4, wrestling=9, grappling=6, cardio=8, chin=6),
    "BJJ":      dict(striking=4, wrestling=6, grappling=10, cardio=6, chin=5),
    "Brawler":  dict(striking=7, wrestling=4, grappling=3, cardio=4, chin=8),
}

ARCHETYPE_BLURB = {
    "Striker": "Sharp hands and kicks. Wants to keep it standing.",
    "Wrestler": "Takes you down and keeps you there. Great cardio.",
    "BJJ": "Dangerous off the back. Hunts submissions everywhere.",
    "Brawler": "Iron chin and heavy hands. Gasses if it goes long.",
}

COLORS = [
    (220, 60, 60), (60, 120, 230), (240, 190, 40), (60, 190, 110),
    (170, 90, 220), (240, 130, 40), (40, 200, 210), (230, 230, 230),
]


def make(name, nickname, archetype, hometown="", record=(0, 0), tweak=None, color=None,
         height="6'0\""):
    s = dict(ARCHETYPES[archetype])
    for k, v in (tweak or {}).items():
        s[k] += v
    return Profile(name=name, nickname=nickname, archetype=archetype,
                   stats=Stats(**s).clamp(), color=color or COLORS[0],
                   hometown=hometown, wins=record[0], losses=record[1], height=height)


def quick_fighters():
    """One ready-made fighter per archetype for quick fights."""
    return [
        make("Dan Reyes", "The Hammer", "Striker", "San Diego, California", (14, 3),
             color=COLORS[0], height="5'11\""),
        make("Ivan Petrov", "The Bear", "Wrestler", "Makhachkala, Russia", (18, 1),
             color=COLORS[1], height="5'10\""),
        make("Lucas Silva", "Spider Hands", "BJJ", "Rio de Janeiro, Brazil", (12, 4),
             color=COLORS[3], height="6'1\""),
        make("Tommy Byrne", "Iron Jaw", "Brawler", "Dublin, Ireland", (21, 9),
             color=COLORS[2], height="5'9\""),
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

_FIRST = ["Jordan", "Tyler", "Andre", "Nico", "Sam", "Luis", "Kai", "Ben", "Rico", "Max",
          "Leon", "Jamal", "Eli", "Owen", "Victor", "Dmitri", "Tariq", "Hugo"]
_LAST = ["Grant", "Ortiz", "Novak", "Kane", "Mendes", "Clarke", "Burke", "Sato", "Ruiz",
         "Walsh", "Ivanov", "Price", "Diallo", "Fischer", "Moreau", "Hayes"]
_NICK = ["The Prospect", "Hurricane", "The Kid", "Bulldog", "Razor", "Showtime",
         "Cobra", "Mad Dog", "Thunder", "Flash", "Pitbull", "The Ghost"]
_TOWNS = ["Phoenix, Arizona", "Manchester, England", "Sydney, Australia", "Toronto, Canada",
          "Miami, Florida", "Warsaw, Poland", "Auckland, New Zealand", "Chicago, Illinois"]


def division():
    out = []
    for idx, (n, nick, arch, town, rec, tw) in enumerate(DIVISION):
        out.append(make(n, nick, arch, town, rec, tw, color=COLORS[(idx + 1) % len(COLORS)]))
    return out


def prospect(rng, strength=0):
    """A random unranked opponent. strength shifts all stats."""
    arch = rng.choice(list(ARCHETYPES))
    tweak = {k: strength - 1 + rng.choice((-1, 0, 0, 1)) for k in ARCHETYPES[arch]}
    rec = (rng.randint(3, 9), rng.randint(0, 4))
    return make(f"{rng.choice(_FIRST)} {rng.choice(_LAST)}", rng.choice(_NICK), arch,
                rng.choice(_TOWNS), rec, tweak, color=rng.choice(COLORS))
