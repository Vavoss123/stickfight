"""All moves as data. Tweak numbers here to balance the game.

cls     strike / grapple / sub / defend (see the triangle in constants.py)
stat    which stat drives the move
cost    stamina cost (negative means the move recovers stamina)
dmg     base damage for strikes
acc     base chance a strike lands when it is not blocked
power   power shots can rock, drop and knock out
speed   when two strikes meet, the faster one lands first and disrupts the other
target  head (damage), body (drains stamina) or legs (saps power and movement)
to      where the fight goes if the move works:
        standing, clinch, guard_top, guard_bottom, mount_top (relative to the mover)
"""

from dataclasses import dataclass

from .constants import (STANDING, CLINCH, GUARD, MOUNT, BACK, NEUTRAL, TOP, BOTTOM,
                        STRIKE, GRAPPLE, SUB, DEFEND, HEAD, BODY, LEGS)


@dataclass(frozen=True)
class Move:
    key: str
    name: str
    cls: str
    stat: str
    cost: float
    dmg: float = 0.0
    acc: float = 0.8
    power: bool = False
    speed: int = 1
    target: str = HEAD
    cuts: float = 0.0   # chance a clean head shot opens a cut
    to: str = None
    desc: str = ""


_ALL = [
    # Standing
    Move("jab", "Jab", STRIKE, "striking", 3, dmg=4.5, acc=0.88, speed=3, cuts=0.03,
         desc="Quick and cheap. Beats power shots to the punch."),
    Move("cross", "Power punch", STRIKE, "striking", 10, dmg=10.5, acc=0.62, power=True, cuts=0.06,
         desc="Big right hand. Can drop them."),
    Move("body", "Body shot", STRIKE, "striking", 6, dmg=7, acc=0.78, target=BODY,
         desc="Hooks to the body. Drains their stamina."),
    Move("legkick", "Leg kick", STRIKE, "striking", 5, dmg=5, acc=0.8, speed=2, target=LEGS,
         desc="Goes under the guard. Chops down their power and movement."),
    Move("kick", "Head kick", STRIKE, "striking", 11, dmg=13.5, acc=0.6, power=True, speed=0, cuts=0.06,
         desc="Fight ender, but a block, takedown or clinch stops it."),
    Move("block", "Block and counter", DEFEND, "striking", -7,
         desc="Beats strikes and fires back. Loses to grappling."),
    Move("takedown", "Takedown", GRAPPLE, "wrestling", 10, to="guard_top",
         desc="Shoot for the legs. Beats jabs and kicks, eats power shots."),
    Move("clinch", "Clinch up", GRAPPLE, "wrestling", 5, to="clinch",
         desc="Tie up against the fence. Smothers power shots."),

    # Clinch
    Move("knees", "Knees", STRIKE, "striking", 8, dmg=9, acc=0.75, target=BODY,
         desc="Knees to the body. Drains their stamina."),
    Move("dirty", "Dirty boxing", STRIKE, "striking", 4, dmg=5.5, acc=0.85, speed=3, cuts=0.05,
         desc="Short shots in close."),
    Move("trip", "Trip", GRAPPLE, "wrestling", 10, to="guard_top",
         desc="Trip them to the mat."),
    Move("break", "Break away", GRAPPLE, "wrestling", 4, to="standing",
         desc="Push off and get back to range."),
    Move("frame", "Frame up", DEFEND, "wrestling", -6,
         desc="Tie up the arms and rest."),
    Move("guillotine", "Guillotine", SUB, "grappling", 12,
         desc="Lock the neck. If it fails you end up on your back."),

    # Guard, top
    Move("gnp", "Ground and pound", STRIKE, "wrestling", 6, dmg=7, acc=0.8, speed=2, cuts=0.06,
         desc="Punches from the top."),
    Move("elbows", "Elbows", STRIKE, "wrestling", 10, dmg=11, acc=0.65, power=True, cuts=0.16,
         desc="Nasty elbows. Opens cuts."),
    Move("pass", "Pass to mount", GRAPPLE, "grappling", 9, to="mount_top",
         desc="Pass the guard and take the mount."),
    Move("posture", "Posture up", DEFEND, "grappling", -6,
         desc="Stay heavy and safe, recover."),
    Move("standup", "Stand up", GRAPPLE, "wrestling", 5, to="standing",
         desc="Back to the feet."),

    # Guard, bottom
    Move("upkick", "Strikes off back", STRIKE, "striking", 6, dmg=5, acc=0.7,
         desc="Upkicks and elbows from the bottom."),
    Move("sweep", "Sweep", GRAPPLE, "grappling", 10, to="guard_top",
         desc="Flip them and come up on top."),
    Move("triangle", "Triangle choke", SUB, "grappling", 12,
         desc="Lock a triangle from guard."),
    Move("getup", "Get up", GRAPPLE, "wrestling", 8, to="standing",
         desc="Wall walk back to the feet."),
    Move("cover", "Cover up", DEFEND, "grappling", -5,
         desc="Tie them up and defend."),

    # Mount, top
    Move("mgnp", "Mounted punches", STRIKE, "wrestling", 6, dmg=9, acc=0.85, speed=2, cuts=0.06,
         desc="Rain down punches."),
    Move("melbows", "Mounted elbows", STRIKE, "wrestling", 10, dmg=13, acc=0.7, power=True, cuts=0.16,
         desc="Heavy elbows from mount. Opens cuts."),
    Move("armtri", "Arm triangle", SUB, "grappling", 12,
         desc="Squeeze the arm triangle."),
    Move("mposture", "Hold mount", DEFEND, "grappling", -6,
         desc="Keep the position and recover."),
    Move("takeback", "Take the back", GRAPPLE, "grappling", 8, to="back_top",
         desc="Slide behind them for the choke."),

    # Back control, top
    Move("bpunch", "Punches from back", STRIKE, "wrestling", 6, dmg=7, acc=0.8, speed=2, cuts=0.04,
         desc="Punch around the side of the head."),
    Move("rnc", "Rear naked choke", SUB, "grappling", 11,
         desc="The most dangerous choke there is."),
    Move("bhold", "Body triangle", DEFEND, "grappling", -6,
         desc="Lock your legs and recover."),

    # Back control, bottom
    Move("bcover", "Hand fight", DEFEND, "grappling", -4,
         desc="Protect the neck and wait."),
    Move("turnin", "Turn in", GRAPPLE, "grappling", 8, to="guard_bottom",
         desc="Turn to face them, back to guard."),
    Move("bstand", "Stand up", GRAPPLE, "wrestling", 9, to="standing",
         desc="Fight the hooks and get up."),

    # Mount, bottom
    Move("mcover", "Cover up", DEFEND, "grappling", -4,
         desc="Protect the face."),
    Move("bridge", "Bridge and roll", GRAPPLE, "wrestling", 10, to="guard_top",
         desc="Explode and reverse the position."),
    Move("shrimp", "Shrimp to guard", GRAPPLE, "grappling", 7, to="guard_bottom",
         desc="Recover guard."),
]

MOVES = {m.key: m for m in _ALL}

MOVESETS = {
    (STANDING, NEUTRAL): ["jab", "cross", "body", "legkick", "kick", "block", "takedown", "clinch"],
    (CLINCH, NEUTRAL): ["knees", "dirty", "trip", "break", "frame", "guillotine"],
    (GUARD, TOP): ["gnp", "elbows", "pass", "posture", "standup"],
    (GUARD, BOTTOM): ["upkick", "sweep", "triangle", "getup", "cover"],
    (MOUNT, TOP): ["mgnp", "melbows", "armtri", "takeback", "mposture"],
    (MOUNT, BOTTOM): ["mcover", "bridge", "shrimp"],
    (BACK, TOP): ["bpunch", "rnc", "bhold"],
    (BACK, BOTTOM): ["bcover", "turnin", "bstand"],
}

# Pairs where the normal triangle does not apply. (a, b): +1 a wins, -1 b wins.
OVERRIDES = {
    ("kick", "takedown"): -1,   # kick gets caught
    ("jab", "takedown"): -1,    # a jab does not stop a committed shot
    ("cross", "clinch"): -1,    # closing the distance smothers a wide power shot
    ("legkick", "block"): 1,    # a high guard does nothing for the legs
    ("legkick", "takedown"): -1,  # kick gets caught
    ("body", "takedown"): -1,   # dipping to the body opens up the shot
    ("kick", "clinch"): -1,
}

# Triangle: who beats whom by class. Subs count as grappling.
_BEATS = {STRIKE: GRAPPLE, GRAPPLE: DEFEND, DEFEND: STRIKE}


def base_class(move):
    return GRAPPLE if move.cls == SUB else move.cls


def matchup(a, b):
    """+1 if move a beats move b, -1 if b beats a, 0 if neither does."""
    if (a.key, b.key) in OVERRIDES:
        return OVERRIDES[(a.key, b.key)]
    if (b.key, a.key) in OVERRIDES:
        return -OVERRIDES[(b.key, a.key)]
    ca, cb = base_class(a), base_class(b)
    if ca == cb:
        return 0
    if _BEATS[ca] == cb:
        return 1
    if _BEATS[cb] == ca:
        return -1
    return 0
