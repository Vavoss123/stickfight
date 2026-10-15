"""Where fighters stand and how each move is animated."""

from engine.constants import STANDING, CLINCH, GUARD, MOUNT, BACK
from .common import CX, FLOOR_Y
from .stickman import joints, concrete

# Fighters are drawn this much bigger than the authored poses
SCALE = 1.45
STAND_GAP = 50 * SCALE
CLINCH_GAP = 34 * SCALE

# (pose, seconds) for each move, and when the blow lands
ACTION = {
    "jab": [("jab", 0.10), ("jab", 0.10)],
    "cross": [("cross_wind", 0.14), ("cross", 0.10), ("cross", 0.10)],
    "kick": [("kick_wind", 0.14), ("kick", 0.14), ("kick", 0.12)],
    "body": [("bodyshot", 0.13), ("bodyshot", 0.12)],
    "legkick": [("legkick_wind", 0.1), ("legkick", 0.1), ("legkick", 0.1)],
    "block": [("block", 0.12), ("block", 0.28)],
    "takedown": [("shoot", 0.22), ("shoot", 0.12)],
    "clinch": [("clinch_in", 0.2), ("clinch_in", 0.1)],
    "knees": [("knee", 0.14), ("knee", 0.1)],
    "dirty": [("dirty", 0.1), ("dirty", 0.1)],
    "trip": [("trip", 0.2), ("trip", 0.12)],
    "break": [("frame", 0.15), ("frame", 0.15)],
    "frame": [("frame", 0.2), ("frame", 0.2)],
    "guillotine": [("guillotine", 0.25), ("guillotine", 0.1)],
    "gnp": [("gnp_wind", 0.12), ("gnp", 0.08), ("gnp", 0.1)],
    "elbows": [("gnp_wind", 0.14), ("elbow", 0.08), ("elbow", 0.1)],
    "pass": [("pass", 0.25), ("pass", 0.1)],
    "posture": [("posture", 0.3)],
    "standup": [("getup", 0.25)],
    "upkick": [("guard_bot_strike", 0.15), ("guard_bot_strike", 0.1)],
    "sweep": [("sweep", 0.25), ("sweep", 0.1)],
    "triangle": [("triangle", 0.25), ("triangle", 0.1)],
    "getup": [("getup", 0.25)],
    "cover": [("guard_bot_cover", 0.3)],
    "mgnp": [("mount_gnp", 0.1), ("mount_strike", 0.08), ("mount_strike", 0.1)],
    "melbows": [("mount_gnp", 0.14), ("mount_strike", 0.08), ("mount_strike", 0.1)],
    "armtri": [("arm_tri", 0.25), ("arm_tri", 0.1)],
    "mposture": [("mount_top", 0.3)],
    "mcover": [("mount_bot", 0.3)],
    "bridge": [("bridge", 0.25), ("bridge", 0.1)],
    "shrimp": [("guard_bot", 0.25)],
    "takeback": [("pass", 0.25), ("pass", 0.1)],
    "bpunch": [("back_top", 0.1), ("back_punch", 0.1), ("back_punch", 0.1)],
    "rnc": [("rnc", 0.25), ("rnc", 0.1)],
    "bhold": [("back_top", 0.3)],
    "bcover": [("rnc_def", 0.3)],
    "turnin": [("guard_bot", 0.25)],
    "bstand": [("getup", 0.25)],
    "imanari": [("shoot", 0.15), ("sweep", 0.2)],
    "feint": [("cross_wind", 0.1), ("stance", 0.12), ("jab", 0.06), ("stance", 0.1)],
    "check": [("legkick_wind", 0.12), ("legkick_wind", 0.18), ("stance", 0.1)],
    "weave": [("sprawl", 0.1), ("sprawl", 0.14), ("stance", 0.12)],
    # Signature moves, each with its own animation
    "superman": [("superman_wind", 0.12), ("superman", 0.12), ("superman", 0.08)],
    "spinfist": [("spin_wind", 0.14), ("spinfist", 0.1), ("spinfist", 0.1)],
    "spinelbow": [("spin_wind", 0.12), ("spinelbow", 0.1), ("spinelbow", 0.1)],
    "showtime": [("showtime_wind", 0.16), ("showtime", 0.14), ("showtime", 0.1)],
    "flyknee": [("flyknee_wind", 0.14), ("flyknee", 0.12), ("flyknee", 0.1)],
    "calfkick": [("legkick_wind", 0.1), ("calfkick", 0.1), ("calfkick", 0.1)],
    "liver": [("liver_wind", 0.1), ("liver", 0.1), ("liver", 0.1)],
    "checkhook": [("block", 0.1), ("checkhook", 0.12), ("checkhook", 0.2)],
    "doubleleg": [("shoot", 0.18), ("doubleleg", 0.14), ("doubleleg", 0.1)],
    "singleleg": [("shoot", 0.16), ("singleleg", 0.16)],
    "guardpull": [("clinch_in", 0.15), ("guardpull", 0.2)],
    "plum": [("plum", 0.14), ("plum_knee", 0.1), ("plum_knee", 0.1)],
    "hammer": [("hammer_wind", 0.12), ("hammer", 0.08), ("hammer", 0.1)],
    "kimura": [("kimura", 0.25), ("kimura", 0.1)],
    "gogo": [("gogo", 0.25), ("gogo", 0.1)],
    # Judo throws
    "osoto": [("osoto_step", 0.14), ("osoto", 0.16), ("osoto", 0.14)],
    "seoi": [("seoi_turn", 0.2), ("seoi", 0.18), ("seoi", 0.14)],
    "hiptoss": [("hiptoss_load", 0.18), ("hiptoss", 0.18), ("hiptoss", 0.14)],
    "uchimata": [("uchimata_load", 0.18), ("uchimata", 0.18), ("uchimata", 0.16)],
    "tomoe": [("tomoe_sit", 0.2), ("tomoe", 0.16), ("tomoe", 0.14)],
}

IMPACT = {"superman": 0.24, "spinfist": 0.24, "spinelbow": 0.22, "showtime": 0.3, "flyknee": 0.26,
          "calfkick": 0.2, "liver": 0.2, "plum": 0.24, "hammer": 0.2,
          "jab": 0.10, "cross": 0.24, "kick": 0.28, "knees": 0.14, "dirty": 0.1,
          "body": 0.13, "legkick": 0.2, "bpunch": 0.2,
          "gnp": 0.2, "elbows": 0.22, "upkick": 0.15, "mgnp": 0.18, "melbows": 0.22}

SUB_POSES = {
    # move: (attacker pose, defender pose)
    "guillotine": ("guillotine", "guillotined"),
    "triangle": ("triangle", "pass"),
    "armtri": ("arm_tri", "mount_bot"),
    "rnc": ("rnc", "rnc_def"),
    "imanari": ("sweep", "guard_top"),   # rolled under them, they come down with it
    "kimura": ("kimura", "kimura_def"),
    "gogo": ("gogo", "guard_top"),
}


# Standing strikes: which poses hold the blow at its furthest, and which limb is doing the hitting
STRIKE_LIMBS = {
    "jab": (("jab",), ("fhand",)),
    "cross": (("cross",), ("bhand",)),
    "body": (("bodyshot",), ("bhand",)),
    "kick": (("kick",), ("bfoot",)),
    "legkick": (("legkick",), ("bfoot",)),
    "knees": (("knee",), ("bknee", "bfoot")),
    "dirty": (("dirty",), ("fhand", "bhand")),
    "counter": (("counter",), ("fhand",)),
    "superman": (("superman",), ("bhand",)),
    "spinfist": (("spinfist",), ("fhand",)),
    "spinelbow": (("spinelbow",), ("felbow",)),
    "showtime": (("showtime",), ("bfoot",)),
    "flyknee": (("flyknee",), ("bknee",)),
    "calfkick": (("calfkick",), ("bfoot",)),
    "liver": (("liver",), ("fhand",)),
}

# How far from a fighter's hip, towards whoever is hitting them, the part being hit starts
FRONT = {"head": 25, "neck": 22, "body": 13, "legs": 14, "arms": 36}
MAX_LUNGE = 46
_reach = {}


def reach(anim):
    """How far forward of the hip the hitting limb gets at the end of the blow (authored units)."""
    if anim not in _reach:
        poses, limbs = STRIKE_LIMBS[anim]
        best = 0.0
        for pose in poses:
            j = joints(concrete(pose), 0, 0, 1, 1.0)
            best = max(best, *(j[limb][0] - j["hip"][0] for limb in limbs))
        _reach[anim] = best
    return _reach[anim]


def lunge(anim, target, dist, att_scale, def_scale):
    """How far, in pixels, the attacker steps in so the blow reaches its target instead of
    swinging at air. dist is the gap between the two fighters' hips in pixels."""
    if anim not in STRIKE_LIMBS:
        return 0.0
    need = dist - FRONT.get(target, 20) * def_scale - reach(anim) * att_scale + 4 * att_scale
    return max(0.0, min(need, MAX_LUNGE * att_scale))


# Throws: how the one being thrown flies. (pose in the air, how high in authored units,
# how far they travel towards where they land at the top of the arc, 0 to 1)
THROWS = {
    "osoto": ("thrown_back", 10, 0.5),
    "seoi": ("thrown_up", 34, 0.6),
    "hiptoss": ("thrown_up", 26, 0.6),
    "uchimata": ("thrown_up", 42, 0.6),
    "tomoe": ("thrown_up", 46, 0.7),
    "doubleleg": ("lifted", 14, 0.5),
    "trip": ("thrown_back", 4, 0.5),
}


def facing(i):
    return 1 if i == 0 else -1


def layout(st):
    """Anchor x, idle pose and facing for both fighters in this state."""
    xs = [0, 0]
    idle = ["stance", "stance"]
    faces = [facing(0), facing(1)]
    pos, top_i = st.pos, st.top
    if st.sub and st.pos in (STANDING, CLINCH):
        pos, top_i = GUARD, 1 - st.sub.att   # a flying sub ends up as a guard on the mat
    if pos == STANDING:
        xs = [CX - STAND_GAP, CX + STAND_GAP]
    elif pos == CLINCH:
        xs = [CX - CLINCH_GAP, CX + CLINCH_GAP]
        idle = ["clinch", "clinch"]
    else:
        top = top_i
        bot = 1 - top
        fb = facing(bot)
        if pos == BACK:
            # Both face the same way, the top fighter sits behind
            ft = facing(top)
            faces[bot] = ft
            gap = (16, 16) if st.sub else (28, 20)  # pull in tight for the choke
            xs[top] = CX - ft * gap[0] * SCALE
            xs[bot] = CX + ft * gap[1] * SCALE
            idle[top], idle[bot] = "back_top", "back_bot"
        elif pos == GUARD:
            bx = CX - fb * 30 * SCALE
            xs[bot] = bx
            xs[top] = bx + fb * 62 * SCALE
            idle[top], idle[bot] = "guard_top", "guard_bot"
        else:
            bx = CX + fb * 10 * SCALE
            xs[bot] = bx
            xs[top] = bx - fb * 28 * SCALE
            idle[top], idle[bot] = "mount_top", "mount_bot"
    if st.sub:
        a, d = SUB_POSES[st.f[st.sub.att].move(st.sub.move).anim]
        idle[st.sub.att] = a
        idle[1 - st.sub.att] = d
    for i in (0, 1):
        f = st.f[i]
        if idle[i] == "stance":
            if f.rocked:
                idle[i] = "rocked"
            elif f.legs >= 60:
                idle[i] = "limp"
            elif f.stamina < 22:
                idle[i] = "tired"
    return xs, idle, faces


def hit_pose(st_before_pos, role_bottom, target):
    if st_before_pos in (STANDING, CLINCH):
        return {"body": "body_hit", "legs": "leg_hit"}.get(target, "hit")
    if st_before_pos == BACK:
        return "back_bot_hit" if role_bottom else "back_top"
    return "mount_bot_hit" if role_bottom else "posture"


__all__ = ["ACTION", "IMPACT", "THROWS", "layout", "facing", "hit_pose", "lunge", "reach", "FLOOR_Y",
           "SCALE"]
