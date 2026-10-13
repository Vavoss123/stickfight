"""One night tournament: eight fighters, three rounds of the bracket, damage carries over.

The player fights their way through. Every other match is fought AI against AI. Whoever
wins goes into the next fight with part of the damage they took, so a war in the
quarterfinal leaves you hurt for the semifinal.
"""

import random

from .ai import AI
from .fight import Fight

STAGES = [("Quarterfinal", 3), ("Semifinal", 3), ("Final", 3)]   # name, rounds
SIZE = 8

# How much of each kind of damage is still there at the next fight
CARRY = {"hp": 0.5, "body": 0.5, "legs": 0.6, "cut": 0.75}


class Condition:
    """The wear a fighter brings into their next fight."""

    __slots__ = ("hp", "body", "legs", "cut")

    def __init__(self, hp=100.0, body=0.0, legs=0.0, cut=0.0):
        self.hp, self.body, self.legs, self.cut = hp, body, legs, cut

    @classmethod
    def after(cls, f):
        """What is left of a fight's damage once they get to the next one."""
        return cls(hp=100.0 - (100.0 - f.hp) * CARRY["hp"], body=f.body * CARRY["body"],
                   legs=f.legs * CARRY["legs"], cut=f.cut * CARRY["cut"])

    def start(self):
        return {"hp": self.hp, "body": self.body, "legs": self.legs, "cut": self.cut}

    def fresh(self):
        return self.hp >= 99.5 and self.body < 1 and self.legs < 1 and self.cut < 1


class Match:
    __slots__ = ("a", "b", "winner", "method", "detail", "round")

    def __init__(self, a, b):
        self.a, self.b = a, b          # entrant indices
        self.winner = None
        self.method = self.detail = ""
        self.round = 0

    @property
    def done(self):
        return self.winner is not None


class Tournament:
    def __init__(self, player, field, level="normal", seed=None):
        """player: the player's profile. field: seven opponents."""
        if len(field) != SIZE - 1:
            raise ValueError(f"a tournament needs {SIZE - 1} opponents")
        self.rng = random.Random(seed)
        self.level = level
        self.entrants = [player] + list(field)
        order = list(range(SIZE))
        self.rng.shuffle(order)
        self.cond = [Condition() for _ in range(SIZE)]
        self.stage = 0
        self.stages = [[Match(order[k], order[k + 1]) for k in range(0, SIZE, 2)]]
        self.player_out = False

    # Info

    @property
    def player(self):
        return self.entrants[0]

    @property
    def over(self):
        return self.stage >= len(STAGES)

    @property
    def champion(self):
        if not self.over:
            return None
        return self.stages[-1][0].winner

    def stage_name(self, k=None):
        k = self.stage if k is None else k
        return STAGES[min(k, len(STAGES) - 1)][0]

    def rounds(self, k=None):
        return STAGES[self.stage if k is None else k][1]

    def player_match(self):
        """The player's match in this stage, if they are still in and have not fought."""
        if self.over or self.player_out:
            return None
        for m in self.stages[self.stage]:
            if 0 in (m.a, m.b) and not m.done:
                return m
        return None

    def alive(self):
        if self.over:
            return {self.champion}
        out = set()
        for m in self.stages[self.stage]:
            out |= {m.a, m.b} if not m.done else {m.winner}
        return out

    # Playing

    def fight_for(self, m, seed=None):
        """A Fight for this match, with both fighters' carried damage."""
        a, b = self.entrants[m.a], self.entrants[m.b]
        return Fight(a, b, rounds=self.rounds(), seed=seed,
                     start=(self.cond[m.a].start(), self.cond[m.b].start()))

    def record(self, m, fight, sides=None):
        """Store how a match went. Draws go to whoever did more damage.
        sides: which entrant was red and which was blue, when it is not (m.a, m.b)."""
        sides = sides or (m.a, m.b)
        r = fight.result
        w = r.winner
        method, detail = r.method, r.detail
        if w is None:
            d0, d1 = fight.totals(0).dmg, fight.totals(1).dmg
            w = 0 if d0 >= d1 else 1
            method, detail = "Decision", "Draw, goes through on damage"
        m.winner = sides[w]
        m.method, m.detail, m.round = method, detail, r.round
        self.cond[m.winner] = Condition.after(fight.state.f[w])
        if 0 in (m.a, m.b) and m.winner != 0:
            self.player_out = True

    def sim(self, m):
        """Fight a match AI against AI."""
        fight = self.fight_for(m, seed=self.rng.random())
        ais = [AI(self.level, seed=self.rng.random()), AI(self.level, seed=self.rng.random())]
        while not fight.over:
            if fight.between_rounds:
                fight.start_next_round()
                continue
            st = fight.state
            picks = (ais[0].choose(fight, 0), ais[1].choose(fight, 1))
            ais[0].observe(st, 1, picks[1])
            ais[1].observe(st, 0, picks[0])
            fight.play(picks)
        self.record(m, fight)

    def finish_stage(self):
        """Sim every match the player is not in, then set up the next stage."""
        for m in self.stages[self.stage]:
            if not m.done and 0 not in (m.a, m.b):
                self.sim(m)
        if any(not m.done for m in self.stages[self.stage]):
            m = next(m for m in self.stages[self.stage] if not m.done)
            self.sim(m)   # the player walked away from it
        winners = [m.winner for m in self.stages[self.stage]]
        self.stage += 1
        if not self.over:
            self.stages.append([Match(winners[k], winners[k + 1]) for k in range(0, len(winners), 2)])
