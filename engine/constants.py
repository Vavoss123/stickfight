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
STRIKE = "strike"
GRAPPLE = "grapple"
SUB = "sub"
DEFEND = "defend"

EXCHANGES_PER_ROUND = 8
ROUND_SECONDS = 300
MAX_HP = 100.0
MAX_STAMINA = 100.0
# Stamina tuning. Higher cost and lower recovery make every big move a decision.
STAMINA_COST = 1.3        # multiplier on every move's stamina cost
STAMINA_FLOOR = 0.5       # how hard an empty tank hits power and accuracy
ROUND_RECOVERY = 22.0     # stamina back between rounds, plus 2 per cardio point

STAT_NAMES = ("striking", "wrestling", "grappling", "cardio", "chin")
STAT_MAX = 10
STAT_MIN = 1

# Submission contest options. The defender escapes by matching the attacker.
SUB_OPTIONS = ("left", "squeeze", "right")
SUB_ATTACK_LABELS = {"left": "Crank left", "squeeze": "Squeeze", "right": "Crank right"}
SUB_DEFEND_LABELS = {"left": "Turn left", "squeeze": "Hand fight", "right": "Turn right"}
SUB_TAP = 3
SUB_START = 1
