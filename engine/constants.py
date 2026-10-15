"""Shared names used across the engine."""

# Positions
STANDING = "standing"
CLINCH = "clinch"
GUARD = "guard"
MOUNT = "mount"
BACK = "back"

# Strike targets
HEAD = "head"
BODY = "body"
LEGS = "legs"

# Roles a fighter can have in a position
NEUTRAL = "neutral"
TOP = "top"
BOTTOM = "bottom"

# Move classes. Strike beats grapple, grapple beats defend, defend beats strike.
# A feint beats a defend (they freeze) and loses to everything else.
STRIKE = "strike"
GRAPPLE = "grapple"
SUB = "sub"
DEFEND = "defend"
FEINT = "feint"

EXCHANGES_PER_ROUND = 8
ROUND_SECONDS = 300
MAX_HP = 100.0
MAX_STAMINA = 100.0
# Stamina tuning. Higher cost and lower recovery make every big move a decision.
STAMINA_COST = 1.3        # multiplier on every move's stamina cost
STAMINA_FLOOR = 0.5       # how hard an empty tank hits power and accuracy
ROUND_RECOVERY = 22.0     # stamina back between rounds, plus 2 per cardio point
TIRED_DAMAGE = 0.4        # an empty fighter takes this much extra damage

STAT_NAMES = ("striking", "wrestling", "grappling", "cardio", "chin")
STAT_MAX = 10      # as high as training goes
STAT_LIMIT = 12    # perks and training camp can go past training, up to this

# What one more point in each stat does, for the screens that let you raise them
STAT_INFO = {
    "striking": "Punches and kicks. Each point: about 2.5% more accurate, 7% more damage, "
                "and better counters.",
    "wrestling": "Takedowns, trips, ground and pound. Each point: about 3% better takedowns "
                 "and takedown defence, and harder shots from the top.",
    "grappling": "Submissions, sweeps and escapes. Each point: about 5% more likely to win "
                 "each turn of a submission, and better sweeps and passes.",
    "cardio": "Your gas tank. Each point: every move costs about 6% less stamina, and you "
              "get 2 more back between rounds.",
    "chin": "Taking a shot. Each point: head shots hurt about 6% less and you are less "
            "likely to be rocked or knocked out.",
}
STAT_MIN = 1

# The submission contest. Both fighters pick one of three each exchange and there are no
# dice: the same picks always give the same result, so it is a read of your opponent, a
# check on the gas tank and a build up of angle, see resolve._resolve_sub.
SUB_POWER, SUB_ANGLE, SUB_CALM = "power", "angle", "calm"
SUB_OPTIONS = (SUB_POWER, SUB_ANGLE, SUB_CALM)
SUB_ATTACK_LABELS = {SUB_POWER: "Squeeze", SUB_ANGLE: "Adjust angle", SUB_CALM: "Ease off"}
SUB_DEFEND_LABELS = {SUB_POWER: "Explode", SUB_ANGLE: "Hand fight", SUB_CALM: "Breathe"}
SUB_ATTACK_HINTS = {SUB_POWER: "Crank it. Hand fighting stops it",
                    SUB_ANGLE: "Set up the angle. Explode beats it",
                    SUB_CALM: "Recover. Safe, but no progress"}
SUB_DEFEND_HINTS = {SUB_POWER: "Burst out. Costs gas. Squeeze beats it",
                    SUB_ANGLE: "Stop the squeeze. Adjust beats it",
                    SUB_CALM: "Recover, but squeeze gets through"}
SUB_TAP = 3
SUB_START = 1
SUB_MAX_ANGLE = 2
