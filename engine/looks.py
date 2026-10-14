"""How a fighter looks: skin, hair, beard, tattoos and the stripe on their shorts.

A profile keeps its look as a small dict. Anything missing comes from the fighter's
name, so every computer fighter has their own look and keeps it between fights.
"""

import hashlib
import random

SKINS = [(236, 232, 224), (244, 208, 178), (226, 176, 136), (190, 132, 92), (140, 94, 64),
         (108, 72, 52)]
HAIRS = ["bald", "buzz", "short", "mohawk", "topknot", "ponytail", "afro", "long"]
HAIR_NAMES = {"bald": "Bald", "buzz": "Buzz cut", "short": "Short", "mohawk": "Mohawk",
              "topknot": "Top knot", "ponytail": "Ponytail", "afro": "Afro", "long": "Long"}
HAIR_COLORS = [(34, 28, 26), (92, 58, 34), (226, 190, 100), (196, 92, 40), (170, 170, 176),
               (230, 60, 70), (70, 120, 240), (120, 220, 120)]
SHORTS = [(220, 60, 60), (60, 120, 230), (240, 190, 40), (60, 190, 110), (170, 90, 220),
          (240, 130, 40), (40, 200, 210), (230, 230, 230), (34, 34, 40), (240, 110, 180)]
TATTOOS = ["none", "sleeve", "sleeves", "chest", "legs", "full"]
TATTOO_NAMES = {"none": "None", "sleeve": "One sleeve", "sleeves": "Both arms", "chest": "Chest",
                "legs": "Legs", "full": "Full body"}
TRIMS = [None, (255, 255, 255), (240, 196, 60), (34, 34, 40), (220, 60, 60), (60, 120, 230)]

# How often the computer's fighters get each hair style
_HAIR_WEIGHTS = [3, 4, 4, 1, 1, 1, 1, 1]


def default_look(name):
    """The same look every time for the same name."""
    seed = int(hashlib.md5(name.encode("utf-8")).hexdigest()[:8], 16)
    rng = random.Random(seed)
    hair = rng.choices(HAIRS, _HAIR_WEIGHTS)[0]
    natural = HAIR_COLORS[:5] if rng.random() < 0.9 else HAIR_COLORS
    return {"skin": rng.randrange(len(SKINS)), "hair": hair,
            "hair_color": HAIR_COLORS.index(rng.choice(natural)),
            "beard": rng.random() < 0.35, "trim": rng.randrange(len(TRIMS)) if rng.random() < 0.4 else 0,
            "tattoo": rng.choice(TATTOOS[1:]) if rng.random() < 0.3 else "none"}


def random_look(rng=random):
    return {"skin": rng.randrange(len(SKINS)), "hair": rng.choice(HAIRS),
            "hair_color": rng.randrange(len(HAIR_COLORS)), "beard": rng.random() < 0.4,
            "trim": rng.randrange(len(TRIMS)), "tattoo": rng.choice(TATTOOS)}


def look_of(profile):
    """The profile's look with the gaps filled in, as indexes and names."""
    look = default_look(profile.name)
    for k, v in (profile.look or {}).items():
        if k in look:
            look[k] = v
    if profile.look and "tattoo" not in profile.look:
        look["tattoo"] = "none"      # a look saved before tattoos existed
    look["skin"] = look["skin"] % len(SKINS)
    look["hair_color"] = look["hair_color"] % len(HAIR_COLORS)
    look["trim"] = look["trim"] % len(TRIMS)
    if look["hair"] not in HAIRS:
        look["hair"] = "short"
    if look["tattoo"] not in TATTOOS:
        look["tattoo"] = "none"
    return look


def colors(look):
    """The actual colours for a look: (skin, hair colour, trim or None)."""
    return SKINS[look["skin"]], HAIR_COLORS[look["hair_color"]], TRIMS[look["trim"]]
