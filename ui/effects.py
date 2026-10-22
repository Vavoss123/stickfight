"""What the words that pop up in a fight mean.

The fight screen explains each one the first few times it shows up (Settings can turn
that off), and How to play lists the main ones.
"""

# Popup word (without the "!") -> (title, what it means)
EFFECTS = {
    "ROCKED": ("Rocked", "Hurt and wobbly. Easier to hit, hits softer, and one more big shot can drop "
                         "them. Clears after an exchange."),
    "KNOCKDOWN": ("Knockdown", "Dropped by a big shot. Huge on the judges' cards, and a hurt fighter can "
                               "be finished."),
    "CUT": ("Cut", "Blood in the eyes makes strikes miss more. A bad cut and the doctor stops it."),
    "LIMPING": ("Limping", "Leg damage past 60%. Slower, weaker power shots and takedowns. At 100% the "
                           "leg breaks."),
    "GASSED": ("Gassed", "Not enough stamina for that move. It came out slow and weak. Defend or rest "
                         "to get some back."),
    "CAUGHT": ("Caught", "Shot in for a takedown and ran onto a strike. Extra damage."),
    "CHECKED": ("Checked", "The leg kick was checked with the shin. It hurt the kicker's leg instead."),
    "COUNTER": ("Counter", "Blocked the strike and fired back straight away."),
    "BLOCKED": ("Blocked", "The guard took it. Blocking heavy shots slowly hurts the arms."),
    "SLIPPED": ("Slipped", "Weaved under the strike. Nothing landed, and the next strike is faster."),
    "WALKED INTO IT": ("Walked into it", "Tried to weave and ate the shot, at one and a half times the "
                                         "damage."),
    "STUFFED": ("Stuffed", "The takedown or sweep was stopped. It cost stamina for nothing."),
    "FEINT": ("Feint", "A fake. Anyone waiting to defend freezes."),
    "FROZEN": ("Frozen", "Bit on the feint. No stamina back, and the feinter's next strike gets a read: "
                         "faster, more accurate and harder."),
    "ALL IN": ("All in", "Full momentum spent: this attack is more accurate and hits harder."),
    "MOMENTUM": ("Momentum", "The purple bar is full. The next attack goes all in."),
    "BOOO": ("Booed", "The crowd is bored. Stalling drains momentum."),
    "MISS": ("Miss", "A power shot that found nothing. It still cost stamina."),
    "FOUL": ("Foul", "An illegal shot. The first is a warning, after that it costs a point."),
    "BREAK": ("Break", "Nothing was happening, so the referee split them up."),
    "TIGHTER": ("Tighter", "The submission sank in deeper. Fill the meter and they tap."),
    "LOOSENED": ("Loosened", "The defender made space. One more and they are out."),
    "ANGLE": ("Angle", "The hold has a better angle. The next squeeze gets through a hand fight."),
    "DEFENDED": ("Defended", "The defender stopped that part of the submission."),
    "ESCAPED": ("Escaped", "Out of the submission."),
    "CRACKED RIBS": ("Cracked ribs", "Body damage reached 100%. The fight is stopped."),
    "BROKEN LEG": ("Broken leg", "Leg damage reached 100%. The fight is stopped."),
}

# The ones How to play shows, in order
MAIN = ["ROCKED", "CUT", "LIMPING", "GASSED", "CAUGHT", "CHECKED", "COUNTER", "SLIPPED", "STUFFED",
        "FROZEN", "ALL IN", "ANGLE"]
TIMES_EXPLAINED = 2    # explain each effect this many times before trusting you know it


def key(word):
    """'ROCKED!' -> 'ROCKED'. None if it is not an effect, like a damage number."""
    k = word.strip().rstrip("!").strip()
    return k if k in EFFECTS else None
