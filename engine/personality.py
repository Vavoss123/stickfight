"""AI personalities: how a computer fighter likes to fight, and what they say about it.

A personality is a small nudge on top of the AI's lookahead, so a pressure fighter
still blocks when blocking is clearly right, it just would rather not.
"""

from .constants import STANDING, CLINCH, STRIKE, GRAPPLE, DEFEND, TOP
from .moves import base_class

PERSONALITIES = {
    "balanced": dict(
        label="Balanced", blurb="Does whatever the fight needs.",
        quotes=["I respect everyone. Then I beat them.", "Whatever you bring, I have an answer."],
        taunts=["Steady work.", "Right on schedule."]),
    "pressure": dict(
        label="Pressure fighter", blurb="Always coming forward. Rarely takes a step back.",
        quotes=["I am going to walk you down for fifteen minutes.", "There is nowhere to run in a cage."],
        taunts=["Keep backing up!", "You cannot hide from me!"]),
    "counter": dict(
        label="Counter puncher", blurb="Waits behind the guard and makes you pay for every mistake.",
        quotes=["Come forward. That is what I want.", "Every shot you throw is a gift to me."],
        taunts=["Too slow.", "I saw that coming a mile away."]),
    "grinder": dict(
        label="Grinder", blurb="Takes you down and keeps you there. Ugly, effective.",
        quotes=["You will spend this whole fight on your back.", "Pretty does not win fights. Pressure does."],
        taunts=["Welcome to my world.", "Get used to the mat."]),
    "showboat": dict(
        label="Showboat", blurb="Loves the big moment. Spinning stuff, head kicks, highlight reels.",
        quotes=["Tonight I make the highlight reel. You are just in it.", "Bring your camera phones, people."],
        taunts=["Did you see that?!", "That is going on the poster!"]),
}
NAMES = list(PERSONALITIES)

# The usual personality for each style when a fighter does not have their own
BY_STYLE = {"Striker": "counter", "Wrestler": "grinder", "BJJ": "balanced", "Brawler": "pressure"}

# Score nudges, in the AI's points (about one point of health each)
NUDGE = 2.5


def of(profile):
    p = getattr(profile, "personality", "") or BY_STYLE.get(getattr(profile, "archetype", ""), "balanced")
    return p if p in PERSONALITIES else "balanced"


def label(profile):
    return PERSONALITIES[of(profile)]["label"]


def bias(name, move, st, me):
    """How much this personality likes a move right now."""
    if move is None:
        return 0.0
    c = base_class(move)
    feet = st.pos in (STANDING, CLINCH)
    top = not feet and st.role(me) == TOP
    if name == "pressure":
        return NUDGE * (0.8 * (c == STRIKE) - 0.6 * (c == DEFEND) + 0.3 * move.power)
    if name == "counter":
        if feet:
            return NUDGE * ((c == DEFEND) * 0.8 - 0.4 * (c == STRIKE and move.speed < 2))
        return 0.0
    if name == "grinder":
        if feet:
            return NUDGE * ((c == GRAPPLE and move.to not in ("standing", None)) - 0.5 * (c == STRIKE))
        if top:
            return NUDGE * ((c == DEFEND) * 0.8 - 1.5 * (move.to == "standing"))
        return 0.0
    if name == "showboat":
        flashy = move.power or move.key != move.base or move.base in ("kick",)
        return NUDGE * (flashy * 0.8 - 0.4 * (c == DEFEND))
    return 0.0
