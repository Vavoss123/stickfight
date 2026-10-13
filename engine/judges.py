"""Three judges score each round on the 10 point must system."""


class RoundStats:
    __slots__ = ("dmg", "landed", "thrown", "takedowns", "control", "sub_attempts",
                 "knockdowns", "reversals", "deductions")

    def __init__(self):
        for k in self.__slots__:
            setattr(self, k, 0)

    def points(self, w):
        return (self.dmg * w[0] + self.landed * 0.6 * w[0] + self.takedowns * 5 * w[1]
                + self.control * 1.5 * w[1] + self.sub_attempts * 2.5 * w[2]
                + self.knockdowns * 12 + self.reversals * 3 * w[1])


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
    """rounds: list of (RoundStats, RoundStats). Returns (winner or None, detail, cards)."""
    judges = [Judge(rng) for _ in range(3)]
    cards = []
    for j in judges:
        t = [0, 0]
        for s0, s1 in rounds:
            a, b = j.score_round(s0, s1)
            t[0] += a
            t[1] += b
        cards.append(tuple(t))
    votes = [0 if a > b else 1 if b > a else None for a, b in cards]
    v0, v1 = votes.count(0), votes.count(1)
    if v0 == 3 or v1 == 3:
        return (0 if v0 == 3 else 1), "Unanimous decision", cards
    if v0 == 2 and v1 == 1 or v1 == 2 and v0 == 1:
        return (0 if v0 == 2 else 1), "Split decision", cards
    if v0 == 2 or v1 == 2:
        return (0 if v0 == 2 else 1), "Majority decision", cards
    return None, "Draw", cards
