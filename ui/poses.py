"""Stick figure poses.

Each pose gives world angles in degrees for every bone, authored facing right.
0 points forward, 90 points down, -90 points up (screen y grows downward).
"hip" is the hip offset from the fighter's anchor point on the mat. When "ground"
is True the hip height is worked out so the lowest foot touches the mat.

Bones: torso (hip to neck), head, front arm (fua upper, ffa fore), back arm (bua, bfa),
front leg (fth thigh, fsh shin), back leg (bth, bsh).
"""

BONES = ("torso", "head", "fua", "ffa", "bua", "bfa", "fth", "fsh", "bth", "bsh")

LEN = {"torso": 50, "neck": 8, "head_r": 11, "ua": 26, "fa": 24, "th": 31, "sh": 31}


def P(hip=(0, 0), ground=True, **angles):
    d = {"hip": hip, "ground": ground}
    d.update(angles)
    return d


STANCE = P(torso=-78, head=-80, fua=55, ffa=-62, bua=78, bfa=-78,
           fth=68, fsh=100, bth=112, bsh=94)
STANCE_B = P(hip=(2, 0), torso=-80, head=-82, fua=58, ffa=-58, bua=80, bfa=-74,
             fth=72, fsh=98, bth=110, bsh=92)

POSES = {
    "stance": STANCE,
    "stance_b": STANCE_B,
    "walk1": P(torso=-84, head=-86, fua=80, ffa=60, bua=100, bfa=110,
               fth=60, fsh=95, bth=115, bsh=105),
    "walk2": P(torso=-84, head=-86, fua=100, ffa=110, bua=80, bfa=60,
               fth=100, fsh=105, bth=80, bsh=95),
    "jab": P(hip=(6, 0), torso=-74, head=-76, fua=-4, ffa=-2, bua=78, bfa=-80,
             fth=62, fsh=98, bth=116, bsh=96),
    "cross_wind": P(hip=(-4, 0), torso=-92, head=-88, fua=60, ffa=-70, bua=130, bfa=-40,
                    fth=70, fsh=100, bth=118, bsh=96),
    "cross": P(hip=(12, 0), torso=-62, head=-66, fua=75, ffa=-75, bua=-6, bfa=-4,
               fth=58, fsh=96, bth=124, bsh=100),
    "kick_wind": P(hip=(-2, 0), torso=-95, head=-90, fua=55, ffa=-60, bua=110, bfa=70,
                   fth=80, fsh=100, bth=70, bsh=150),
    "kick": P(hip=(4, 0), torso=-118, head=-100, fua=40, ffa=-70, bua=150, bfa=120,
              fth=92, fsh=94, bth=-30, bsh=-20),
    "block": P(hip=(-4, 0), torso=-84, head=-70, fua=10, ffa=-110, bua=25, bfa=-105,
               fth=62, fsh=110, bth=116, bsh=88),
    "counter": P(hip=(4, 0), torso=-70, head=-74, fua=-10, ffa=-12, bua=40, bfa=-100,
                 fth=62, fsh=100, bth=118, bsh=96),
    "shoot": P(hip=(34, 0), torso=-15, head=-5, fua=30, ffa=20, bua=40, bfa=10,
               fth=40, fsh=125, bth=150, bsh=172),
    "sprawl": P(hip=(-12, 0), torso=5, head=40, fua=80, ffa=100, bua=90, bfa=110,
                fth=150, fsh=170, bth=160, bsh=178),
    "clinch_in": P(hip=(18, 0), torso=-60, head=-50, fua=0, ffa=25, bua=10, bfa=30,
                   fth=66, fsh=102, bth=120, bsh=98),
    "clinch": P(torso=-66, head=-40, fua=-15, ffa=40, bua=0, bfa=45,
                fth=70, fsh=100, bth=118, bsh=96),
    "knee": P(torso=-62, head=-40, fua=-20, ffa=50, bua=-5, bfa=55,
              fth=80, fsh=95, bth=-20, bsh=80),
    "dirty": P(torso=-66, head=-44, fua=-15, ffa=40, bua=-20, bfa=-35,
               fth=70, fsh=100, bth=118, bsh=96),
    "frame": P(hip=(-6, 0), torso=-80, head=-70, fua=-5, ffa=10, bua=10, bfa=20,
               fth=72, fsh=102, bth=112, bsh=94),
    "trip": P(hip=(10, 0), torso=-45, head=-30, fua=10, ffa=40, bua=20, bfa=50,
              fth=40, fsh=40, bth=118, bsh=96),
    "hit": P(hip=(-10, 0), torso=-108, head=-130, fua=110, ffa=150, bua=130, bfa=80,
             fth=66, fsh=96, bth=118, bsh=92),
    "body_hit": P(hip=(-6, 0), torso=-55, head=-30, fua=80, ffa=40, bua=70, bfa=20,
                  fth=70, fsh=100, bth=115, bsh=95),
    "rocked": P(hip=(-4, 0), torso=-98, head=-120, fua=95, ffa=100, bua=88, bfa=95,
                fth=55, fsh=115, bth=125, bsh=78),
    "victory": P(torso=-90, head=-95, fua=-115, ffa=-105, bua=-65, bfa=-75,
                 fth=80, fsh=92, bth=100, bsh=88),
    "tired": P(torso=-60, head=-50, fua=80, ffa=85, bua=85, bfa=90,
               fth=70, fsh=105, bth=110, bsh=88),
    "getup": P(hip=(0, 0), torso=-30, head=-10, fua=80, ffa=95, bua=110, bfa=100,
               fth=40, fsh=120, bth=120, bsh=170),
    "ref": P(torso=-90, head=-90, fua=100, ffa=80, bua=80, bfa=100,
             fth=80, fsh=92, bth=100, bsh=88),
    "ref_stop": P(hip=(8, 0), torso=-70, head=-70, fua=10, ffa=0, bua=-40, bfa=-60,
                  fth=60, fsh=98, bth=116, bsh=96),
    "ref_fight": P(torso=-90, head=-90, fua=-30, ffa=-70, bua=20, bfa=10,
                   fth=80, fsh=92, bth=100, bsh=88),

    # On the mat. Hip y is set by hand here.
    "ko": P(hip=(0, -6), ground=False, torso=182, head=186, fua=165, ffa=195,
            bua=200, bfa=175, fth=-4, fsh=2, bth=4, bsh=0),
    "guard_bot": P(hip=(0, -9), ground=False, torso=178, head=170, fua=-55, ffa=-15,
                   bua=-75, bfa=-30, fth=-45, fsh=15, bth=-30, bsh=25),
    "guard_bot_strike": P(hip=(0, -9), ground=False, torso=178, head=168, fua=-30, ffa=-20,
                          bua=-75, bfa=-30, fth=-70, fsh=-30, bth=-30, bsh=25),
    "guard_bot_cover": P(hip=(0, -9), ground=False, torso=178, head=172, fua=-80, ffa=-160,
                         bua=-70, bfa=-150, fth=-40, fsh=20, bth=-25, bsh=30),
    "triangle": P(hip=(0, -12), ground=False, torso=178, head=165, fua=-50, ffa=-10,
                  bua=-60, bfa=0, fth=-80, fsh=-160, bth=-60, bsh=-110),
    "sweep": P(hip=(0, -14), ground=False, torso=200, head=200, fua=-80, ffa=-40,
               bua=-40, bfa=0, fth=-100, fsh=-60, bth=-20, bsh=40),
    "guard_top": P(hip=(0, -30), ground=False, torso=-62, head=-55, fua=45, ffa=60,
                   bua=55, bfa=70, fth=82, fsh=178, bth=96, bsh=182),
    "gnp_wind": P(hip=(-2, -30), ground=False, torso=-80, head=-70, fua=45, ffa=60,
                  bua=-60, bfa=150, fth=82, fsh=178, bth=96, bsh=182),
    "gnp": P(hip=(2, -30), ground=False, torso=-50, head=-40, fua=40, ffa=55,
             bua=55, bfa=70, fth=82, fsh=178, bth=96, bsh=182),
    "elbow": P(hip=(2, -30), ground=False, torso=-40, head=-30, fua=40, ffa=55,
               bua=10, bfa=150, fth=82, fsh=178, bth=96, bsh=182),
    "posture": P(hip=(0, -30), ground=False, torso=-85, head=-80, fua=70, ffa=80,
                 bua=80, bfa=85, fth=82, fsh=178, bth=96, bsh=182),
    "pass": P(hip=(10, -26), ground=False, torso=-20, head=-10, fua=60, ffa=80,
              bua=80, bfa=90, fth=60, fsh=170, bth=110, bsh=178),
    "mount_top": P(hip=(0, -24), ground=False, torso=-88, head=-82, fua=60, ffa=70,
                   bua=70, bfa=80, fth=70, fsh=175, bth=110, bsh=178),
    "mount_gnp": P(hip=(0, -24), ground=False, torso=-60, head=-50, fua=55, ffa=60,
                   bua=-70, bfa=160, fth=70, fsh=175, bth=110, bsh=178),
    "mount_strike": P(hip=(0, -24), ground=False, torso=-45, head=-35, fua=50, ffa=60,
                      bua=60, bfa=70, fth=70, fsh=175, bth=110, bsh=178),
    "arm_tri": P(hip=(0, -20), ground=False, torso=-10, head=10, fua=60, ffa=140,
                 bua=70, bfa=150, fth=60, fsh=175, bth=150, bsh=180),
    "mount_bot": P(hip=(0, -8), ground=False, torso=180, head=178, fua=-70, ffa=-150,
                   bua=-60, bfa=-140, fth=-40, fsh=40, bth=-30, bsh=50),
    "mount_bot_hit": P(hip=(0, -7), ground=False, torso=182, head=195, fua=-120, ffa=-200,
                       bua=200, bfa=180, fth=-30, fsh=40, bth=-20, bsh=40),
    "bridge": P(hip=(0, -22), ground=False, torso=200, head=190, fua=-80, ffa=-100,
                bua=-60, bfa=-80, fth=-60, fsh=80, bth=-50, bsh=85),
    "guillotine": P(torso=-50, head=-60, fua=40, ffa=150, bua=60, bfa=170,
                    fth=70, fsh=105, bth=115, bsh=95),
    "guillotined": P(hip=(10, 0), torso=-5, head=30, fua=50, ffa=90, bua=70, bfa=110,
                     fth=55, fsh=120, bth=140, bsh=170),
    # Targeted strikes and their reactions
    "legkick_wind": P(hip=(-2, 0), torso=-96, head=-90, fua=55, ffa=-60, bua=105, bfa=70,
                      fth=82, fsh=100, bth=95, bsh=150),
    "legkick": P(hip=(6, 0), torso=-112, head=-96, fua=45, ffa=-65, bua=125, bfa=85,
                 fth=92, fsh=95, bth=35, bsh=55),
    "bodyshot": P(hip=(10, 0), torso=-52, head=-58, fua=50, ffa=-75, bua=20, bfa=-5,
                  fth=50, fsh=110, bth=128, bsh=96),
    "leg_hit": P(hip=(-6, 0), torso=-96, head=-100, fua=95, ffa=60, bua=115, bfa=140,
                 fth=82, fsh=150, bth=106, bsh=90),
    "limp": P(torso=-88, head=-86, fua=68, ffa=-50, bua=85, bfa=-60,
              fth=74, fsh=118, bth=108, bsh=90),
    "limp_b": P(hip=(1, 0), torso=-90, head=-88, fua=70, ffa=-46, bua=86, bfa=-56,
                fth=76, fsh=122, bth=106, bsh=90),

    # Back control, both fighters facing the same way, top fighter behind
    "back_bot": P(hip=(0, -10), ground=False, torso=-98, head=-92, fua=60, ffa=-120,
                  bua=72, bfa=-128, fth=4, fsh=6, bth=10, bsh=4),
    "back_bot_hit": P(hip=(0, -10), ground=False, torso=-80, head=-50, fua=50, ffa=-100,
                      bua=60, bfa=-110, fth=0, fsh=10, bth=8, bsh=6),
    "rnc_def": P(hip=(0, -10), ground=False, torso=-110, head=-70, fua=-70, ffa=-170,
                 bua=-50, bfa=-150, fth=-12, fsh=20, bth=6, bsh=0),
    "back_top": P(hip=(0, -10), ground=False, torso=-62, head=-52, fua=10, ffa=-20,
                  bua=30, bfa=0, fth=-6, fsh=32, bth=8, bsh=40),
    "back_punch": P(hip=(0, -10), ground=False, torso=-55, head=-48, fua=-40, ffa=-30,
                    bua=40, bfa=10, fth=-6, fsh=32, bth=8, bsh=40),
    "rnc": P(hip=(0, -10), ground=False, torso=-70, head=-60, fua=-20, ffa=175,
             bua=-45, bfa=200, fth=-10, fsh=28, bth=6, bsh=38),

    "tapping": P(hip=(0, -9), ground=False, torso=178, head=168, fua=-60, ffa=-40,
                 bua=-120, bfa=-90, fth=-35, fsh=20, bth=-25, bsh=25),
}
