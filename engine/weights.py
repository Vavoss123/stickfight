"""Weight classes.

Inside a class it changes the feel of a fight: heavyweights hit harder and gas sooner,
lightweights are quicker and go longer. Across classes (quick fight and 2 player only,
career and tournaments keep everyone at one weight) the bigger fighter hits harder,
takes shots better and wins more scrambles. The smaller one keeps their speed and gas.
"""

CLASSES = {
    #               pounds, drawn size, damage, accuracy, stamina cost, knockout power
    "Lightweight":  dict(lbs=155, size=0.92, power=0.9, speed=0.03, gas=0.92, ko=0.85),
    "Welterweight": dict(lbs=170, size=1.0, power=1.0, speed=0.0, gas=1.0, ko=1.0),
    "Middleweight": dict(lbs=185, size=1.06, power=1.08, speed=-0.015, gas=1.05, ko=1.12),
    "Heavyweight":  dict(lbs=240, size=1.15, power=1.18, speed=-0.04, gas=1.12, ko=1.3),
}
NAMES = list(CLASSES)
DEFAULT = "Welterweight"

# Across classes, per 100 pounds of difference. Tuned so one class up wins about 55 to
# 60 percent and a heavyweight beats a lightweight about three times in four.
SIZE_DAMAGE = 1.0      # the bigger fighter hits this much harder
SIZE_GRAPPLE = 0.3     # and wins scrambles this much more often
SIZE_TOUGH = 0.8       # and takes this much less from each shot


def get(name):
    return CLASSES.get(name) or CLASSES[DEFAULT]


def short(name):
    """'Lightweight' -> 'LW'."""
    return {"Lightweight": "LW", "Welterweight": "WW", "Middleweight": "MW",
            "Heavyweight": "HW"}.get(name, "WW")


def gap(a, b):
    """How much heavier a is than b, in hundreds of pounds (negative if lighter)."""
    return (get(a)["lbs"] - get(b)["lbs"]) / 100
