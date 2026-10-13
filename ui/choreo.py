"""Where fighters stand and how each move is animated."""

from engine.constants import STANDING, CLINCH, GUARD, MOUNT, BACK
from .common import CX, FLOOR_Y

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
}

IMPACT = {"jab": 0.10, "cross": 0.24, "kick": 0.28, "knees": 0.14, "dirty": 0.1,
          "body": 0.13, "legkick": 0.2, "bpunch": 0.2,
          "gnp": 0.2, "elbows": 0.22, "upkick": 0.15, "mgnp": 0.18, "melbows": 0.22}

SUB_POSES = {
    # move: (attacker pose, defender pose)
    "guillotine": ("guillotine", "guillotined"),
    "triangle": ("triangle", "pass"),
    "armtri": ("arm_tri", "mount_bot"),
    "rnc": ("rnc", "rnc_def"),
    "imanari": ("sweep", "leg_hit"),
}


def facing(i):
    return 1 if i == 0 else -1


def layout(st):
    """Anchor x, idle pose and facing for both fighters in this state."""
    xs = [0, 0]
    idle = ["stance", "stance"]
    faces = [facing(0), facing(1)]
    if st.pos == STANDING:
        xs = [CX - STAND_GAP, CX + STAND_GAP]
    elif st.pos == CLINCH:
        xs = [CX - CLINCH_GAP, CX + CLINCH_GAP]
        idle = ["clinch", "clinch"]
    else:
        top = st.top
        bot = 1 - top
        fb = facing(bot)
        if st.pos == BACK:
            # Both face the same way, the top fighter sits behind
            ft = facing(top)
            faces[bot] = ft
            gap = (16, 16) if st.sub else (28, 20)  # pull in tight for the choke
            xs[top] = CX - ft * gap[0] * SCALE
            xs[bot] = CX + ft * gap[1] * SCALE
            idle[top], idle[bot] = "back_top", "back_bot"
        elif st.pos == GUARD:
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


__all__ = ["ACTION", "IMPACT", "layout", "facing", "hit_pose", "FLOOR_Y", "SCALE"]
