"""AI personalities: how a computer fighter likes to fight, and what they say about it.

A personality is a small nudge on top of the AI's lookahead, so a pressure fighter
still blocks when blocking is clearly right, it just would rather not.
"""

from .constants import STANDING, CLINCH, STRIKE, GRAPPLE, DEFEND, SUB, HEAD, TOP
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
    "headhunter": dict(
        label="Headhunter", blurb="Only one target: your chin. Big shots, early and often.",
        quotes=["I am not here for a decision.", "Somebody is going to sleep tonight."],
        taunts=["Lights out!", "Your chin is mine!"]),
    "subartist": dict(
        label="Submission artist", blurb="Hunts for the tap from every position. Do not give up a limb.",
        quotes=["Every limb you have is a submission waiting to happen.", "Tap or nap. Your choice."],
        taunts=["Feel that squeeze?", "I'm hunting now."]),
    "trashtalk": dict(
        label="Trash talker", blurb="Never stops talking. Fights angry and wants you angry too.",
        quotes=["My grandma hits harder than you.", "After tonight nobody will remember your name."],
        taunts=["Is that it?! Pathetic!", "Too easy!"]),
}
NAMES = list(PERSONALITIES)

# What a computer fighter says when something happens, by personality. "any" is the fallback.
LINES = {
    "hurt": {
        "pressure": ["That all you got?", "Is that it?"], "counter": ["Lucky shot.", "Okay, you got one."],
        "grinder": ["I've been hit harder in practice."], "showboat": ["Ooh, nice one!", "Okay, now it's a show."],
        "any": ["Okay. Now we fight."]},
    "tired": {
        "pressure": ["Keep coming... I'm fine."], "counter": ["I only need one shot."],
        "grinder": ["Just hold on..."], "showboat": ["I'm just warming up!"], "any": ["Deep breaths..."]},
    "you_tired": {
        "pressure": ["You're breathing hard! I'm just getting started."], "counter": ["You're slowing down."],
        "grinder": ["You're tired. Good."], "showboat": ["Need a nap?"], "any": ["You're running on empty."]},
    "takedown": {
        "grinder": ["Welcome to my world.", "Get comfortable down there."], "pressure": ["Stay down!"],
        "any": ["Now you're mine."]},
    "taken_down": {
        "grinder": ["You think you can hold ME down?"], "showboat": ["Rude!"], "any": ["Get off me!"]},
    "sub": {"any": ["Tap!", "Nowhere to go now."], "grinder": ["Squeeze..."]},
    "escaped": {"any": ["Not today.", "You'll need more than that."], "showboat": ["Houdini!"]},
    "momentum": {"showboat": ["Hear that crowd? They love me!"], "pressure": ["Here I come!"],
                 "any": ["The crowd's with me now."]},
    "booed": {"showboat": ["Boo all you want, I'm still pretty."], "counter": ["Patience wins fights."],
              "any": ["Let them boo."]},
    "last_round": {"pressure": ["Five more minutes of hell for you."], "counter": ["One mistake. That's all I need."],
                   "grinder": ["Last round. I'm taking you down."], "showboat": ["Time for the finish!"],
                   "any": ["This is my round."]},
}


for _event, _lines in {
        "hurt": {"headhunter": ["You'll pay for that."], "subartist": ["Stand-up is not my game anyway."],
                 "trashtalk": ["That tickled!", "My little sister hits harder."]},
        "tired": {"trashtalk": ["I'm not tired, I'm bored."]},
        "you_tired": {"headhunter": ["Hands dropping... perfect."], "trashtalk": ["Already?! Weak!"]},
        "takedown": {"subartist": ["Now the fun starts."], "trashtalk": ["Lie down where you belong!"]},
        "taken_down": {"subartist": ["Thank you. This is my office."], "trashtalk": ["Lucky!"]},
        "sub": {"subartist": ["Got it.", "Tap. Now."], "trashtalk": ["Say goodnight!"]},
        "momentum": {"headhunter": ["One shot. That's all I need."], "trashtalk": ["Listen to them! They love me!"]},
        "booed": {"trashtalk": ["Boo louder, I can't hear you!"]},
        "last_round": {"headhunter": ["Somebody's going to sleep."], "subartist": ["I only need one limb."],
                       "trashtalk": ["Last round of your career."]},
}.items():
    LINES[_event].update(_lines)

# What each personality does for you in a career. A small perk, see career.py
CAREER_PERK = {
    "balanced": "Looks after themselves: hospital bills are 30% cheaper.",
    "pressure": "Tough as old boots: injuries heal a fight sooner.",
    "counter": "Hard to hurt: injuries are one step milder.",
    "grinder": "Judges like the work: decision wins pay 25% more.",
    "showboat": "Crowd favourite: every purse is 15% bigger.",
    "headhunter": "Knockout artist: KO and TKO bonuses are 50% bigger.",
    "subartist": "Tap or nap: submission bonuses are 50% bigger.",
    "trashtalk": "Sells the fight: grudge match bonuses are doubled.",
}


def line(name, event, rng):
    """Something fitting for this personality to say, or None."""
    by = LINES.get(event)
    if not by:
        return None
    return rng.choice(by.get(name) or by["any"])

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
    if name == "headhunter":
        head = c == STRIKE and move.target == HEAD
        return NUDGE * (0.7 * head + 0.4 * move.power - 0.3 * (c == DEFEND) - 0.3 * (c == GRAPPLE and feet))
    if name == "subartist":
        if move.cls == SUB:
            return NUDGE * 1.2
        if feet:
            return NUDGE * 0.6 * (c == GRAPPLE and move.to not in ("standing", None))
        return 0.0
    if name == "trashtalk":
        return NUDGE * (0.5 * (c == STRIKE) - 0.3 * (c == DEFEND))
    return 0.0
