"""Advice from the corner between rounds.

The coach looks at what the opponent keeps doing, what the fighter keeps doing (the
AI is reading that too), injuries on both sides, and how the round went.
"""

from collections import Counter

from .constants import STANDING, GUARD, MOUNT, BACK, BOTTOM, TOP

# What to do about an opponent who keeps throwing the same thing on the feet
COUNTERS = {
    "takedown": "He keeps shooting. Throw the power punch when he changes levels.",
    "cross": "He's loading up on the right hand. Block and counter, or clinch up on him.",
    "jab": "He's living on the jab. Shoot a takedown under it.",
    "block": "He's shelling up. Leg kicks and takedowns go right through that guard.",
    "body": "He keeps going to the body. Time the takedown when he dips.",
    "legkick": "He's chopping your legs. Catch the next one with a takedown.",
    "kick": "He's throwing head kicks. Keep the guard up or shoot under it.",
    "clinch": "He wants the clinch. Stick the jab in his face on the way in.",
}

# What the opponent keeps doing on the ground
GROUND = {
    ("getup", BOTTOM): "When he's on his back he tries to get up. Pass as he turns and take the back.",
    ("sweep", BOTTOM): "He's hunting sweeps from the bottom. Hit him and make him cover up.",
    ("triangle", BOTTOM): "Watch the triangle from his guard. Strike first, don't sit there.",
    ("cover", BOTTOM): "He just covers up down there. Pass the guard or go for the choke.",
    ("gnp", TOP): "He's pounding you from the top. Cover up, then get up when he lets off.",
    ("elbows", TOP): "Those elbows are hurting you. Cover up and look for the sweep.",
    ("pass", TOP): "He wants to pass. Don't just lie there, sweep him or get up.",
    ("posture", TOP): "He's stalling on top. Get up or sweep, he's not doing anything.",
}

TELLS = {
    "takedown": "You're shooting every time. He's waiting with the right hand.",
    "cross": "You keep loading up the right hand. He's reading it, mix it up.",
    "block": "You're shelling up too much. He's going to take you down.",
    "jab": "You're only throwing the jab. Change it up.",
    "kick": "Too many head kicks. He's going to catch one.",
    "legkick": "He's timing the leg kick. Go upstairs or shoot.",
    "body": "You're going to the body every time. He sees it coming.",
    "clinch": "You're clinching every exchange. He's ready for it.",
}


def _picks(fight, who, pos=None, role=None, last_round_only=True):
    """Moves fighter `who` picked, optionally only in one position and role."""
    hist = fight.history
    if last_round_only:
        hist = hist[-8:]
    out = []
    for ex in hist:
        if ex.in_sub:
            continue
        if pos and ex.pos_before != pos:
            continue
        if role:
            if ex.top_before is None:
                continue
            mine = TOP if ex.top_before == who else BOTTOM
            if mine != role:
                continue
        m = ex.moves[who]
        out.append(m.base if m else ex.picks[who])  # signature cards count as their basic move
    return out


def _habit(picks, min_count=3, share=0.4):
    if len(picks) < min_count:
        return None
    k, n = Counter(picks).most_common(1)[0]
    return k if n / len(picks) >= share else None


def _round_points(fight, i):
    s = fight.stats[-1][i]
    return s.points((1, 1, 1))


def advice(fight, me):
    """Two or three short tips for fighter `me`, most useful first."""
    opp = 1 - me
    m, o = fight.state.f[me], fight.state.f[opp]
    tips = []

    # Injuries come first, they change what you can do
    if m.cut >= 40:
        tips.append((9, "That cut is bad. One more big shot and the doctor stops it. Keep your guard tight."))
    elif m.cut > 0:
        tips.append((5, "We closed the cut, but protect it."))
    if o.cut >= 25:
        tips.append((8, "He's cut and bleeding. Go after that eye with elbows and punches."))
    if m.legs >= 45:
        tips.append((8, "Your leg is hurt. Stop shooting off it, keep the fight tight."))
    if o.legs >= 40:
        tips.append((7, "His lead leg is going. Keep kicking it."))
    if o.body >= 40:
        tips.append((6, "The body shots are working. He's breathing hard, keep digging."))

    # Opponent habits
    stand = _habit(_picks(fight, opp, STANDING))
    if stand in COUNTERS:
        tips.append((7, COUNTERS[stand]))
    for role in (BOTTOM, TOP):
        g = _habit(_picks(fight, opp, role=role), min_count=2, share=0.5)
        if (g, role) in GROUND:
            tips.append((6, GROUND[(g, role)]))
            break

    # Your own tells
    mine = _habit(_picks(fight, me, STANDING), min_count=3, share=0.5)
    if mine in TELLS:
        tips.append((6, TELLS[mine]))

    # Gas tank
    if m.stamina < 35:
        tips.append((6, "You're gassed. Block and recover, pick your moments."))
    elif o.stamina < 35:
        tips.append((6, "He's tired. Push the pace and make him work."))

    # How the round went
    diff = _round_points(fight, me) - _round_points(fight, opp)
    if diff > 15:
        tips.append((4, "You won that round. Stay smart, don't give him anything."))
    elif diff < -15:
        tips.append((5, "You lost that round. You need to make something happen."))
    else:
        tips.append((3, "That round was close. Win the next exchange and you win the round."))

    tips.sort(key=lambda t: -t[0])
    seen, out = set(), []
    for _, t in tips:
        if t not in seen:
            out.append(t)
            seen.add(t)
    return out[:3]
