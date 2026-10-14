"""Three judges score each round on the 10 point must system."""


class RoundStats:
    __slots__ = ("dmg", "landed", "thrown", "takedowns", "control", "sub_attempts",
                 "knockdowns", "reversals", "deductions")

    def __init__(self):
        for k in self.__slots__:
            setattr(self, k, 0)

    # How much each thing counts. Like real MMA judging, damage and effective striking
    # come first; takedowns and control count, but holding someone down without doing
    # anything does not win a round on its own.
    WEIGHTS = {"dmg": 1.0, "landed": 0.6, "takedowns": 4.0, "control": 1.1, "sub_attempts": 2.5,
               "knockdowns": 12.0, "reversals": 2.0}

    def points(self, w):
        k = self.WEIGHTS
        return (self.dmg * k["dmg"] * w[0] + self.landed * k["landed"] * w[0]
                + self.takedowns * k["takedowns"] * w[1] + self.control * k["control"] * w[1]
                + self.sub_attempts * k["sub_attempts"] * w[2] + self.knockdowns * k["knockdowns"]
                + self.reversals * k["reversals"] * w[1])

    def why(self, other):
        """What won this round on paper, for showing the player: (label, mine, theirs) best first."""
        rows = [("damage", self.dmg, other.dmg), ("strikes landed", self.landed, other.landed),
                ("takedowns", self.takedowns, other.takedowns), ("control", self.control, other.control),
                ("knockdowns", self.knockdowns, other.knockdowns),
                ("submission attempts", self.sub_attempts, other.sub_attempts)]
        k = {"damage": "dmg", "strikes landed": "landed", "takedowns": "takedowns", "control": "control",
             "knockdowns": "knockdowns", "submission attempts": "sub_attempts"}
        rows.sort(key=lambda r: -(r[1] - r[2]) * self.WEIGHTS[k[r[0]]])
        return rows


class Judge:
    def __init__(self, rng):
        # Each judge leans a little: (striking, wrestling, grappling) weights
        self.w = tuple(rng.uniform(0.8, 1.2) for _ in range(3))
        self.rng = rng

    def score_round(self, s0, s1):
        p0 = s0.points(self.w) + self.rng.uniform(-2, 2)
        p1 = s1.points(self.w) + self.rng.uniform(-2, 2)
        diff = p0 - p1
        if abs(diff) < 0.15:
            return (10 - s0.deductions, 10 - s1.deductions)
        win = 0 if diff > 0 else 1
        ws, ls = (s0, s1) if win == 0 else (s1, s0)
        # 10-8 is for real beatdowns: huge margin, or knockdowns on top of a big margin
        big = abs(diff) > 65 or ws.knockdowns >= 2 or (ws.knockdowns and abs(diff) > 40)
        lose_score = 8 if big else 9
        if ls.knockdowns >= 1 and ws.knockdowns == 0:
            lose_score = 9
        a, b = (10, lose_score) if win == 0 else (lose_score, 10)
        return a - s0.deductions, b - s1.deductions


def score_fight(rounds, rng):
    """rounds: list of (RoundStats, RoundStats).
    Returns (winner or None, detail, cards, by_round): cards are each judge's totals,
    by_round each judge's score for every round."""
    judges = [Judge(rng) for _ in range(3)]
    cards = []
    by_round = []   # each judge's (red, blue) score for every round
    for j in judges:
        t = [0, 0]
        mine = []
        for s0, s1 in rounds:
            a, b = j.score_round(s0, s1)
            t[0] += a
            t[1] += b
            mine.append((a, b))
        cards.append(tuple(t))
        by_round.append(mine)
    votes = [0 if a > b else 1 if b > a else None for a, b in cards]
    v0, v1 = votes.count(0), votes.count(1)
    if v0 == 3 or v1 == 3:
        return (0 if v0 == 3 else 1), "Unanimous decision", cards, by_round
    if v0 == 2 and v1 == 1 or v1 == 2 and v0 == 1:
        return (0 if v0 == 2 else 1), "Split decision", cards, by_round
    if v0 == 2 or v1 == 2:
        return (0 if v0 == 2 else 1), "Majority decision", cards, by_round
    return None, "Draw", cards, by_round
