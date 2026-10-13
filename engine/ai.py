"""Computer opponent.

For each move it could pick, the AI simulates the exchange against what it expects
the opponent to do, scores the result, and picks with some randomness. Higher levels
read the opponent's habits more and make fewer loose choices.
"""

import math
import random
from collections import defaultdict

from .constants import STANDING, CLINCH, GUARD, MOUNT, BACK, TOP
from .moves import base_class
from .resolve import resolve

LEVELS = {
    #          habit weight, temperature, samples, random pick chance
    "easy":   (0.0, 7.0, 2, 0.25),
    "normal": (0.5, 3.0, 4, 0.05),
    "hard":   (0.85, 1.4, 10, 0.0),
}


def position_value(st, me):
    """How much fighter `me` likes the current position, given both skill sets."""
    a, b = st.f[me].stats, st.f[1 - me].stats
    if st.pos == STANDING:
        return (a.striking - b.striking) * 1.5
    if st.pos == CLINCH:
        return (a.wrestling - b.wrestling) * 1.0 + (a.striking - b.striking) * 0.5
    top = st.top == me
    if st.pos == GUARD:
        if top:
            return 10 + (a.wrestling - b.wrestling) * 0.8 + (a.grappling - b.grappling) * 0.5
        return -10 + (a.grappling - b.grappling) * 2.0
    if st.pos == MOUNT:
        return 22 if top else -22
    if st.pos == BACK:
        return 24 + (a.grappling - b.grappling) if top else -24 + (a.grappling - b.grappling)
    return 0.0


def evaluate(st, ex, me):
    if ex.finish:
        return 1000.0 if ex.finish[0] == me else -1000.0
    m, o = st.f[me], st.f[1 - me]
    v = (m.hp - o.hp) + 0.15 * (m.stamina - o.stamina) + position_value(st, me)
    v += 0.12 * (o.body + o.legs - m.body - m.legs) + 0.15 * (o.cut - m.cut)
    if m.rocked:
        v -= 8
    if o.rocked:
        v += 8
    if st.sub:
        sign = 1 if st.sub.att == me else -1
        v += sign * st.sub.lock * 18
    return v


def _class_prior(opts, kit):
    """Spread the guess evenly over move classes, then over moves inside a class,
    so three strike options do not make strikes look three times as likely."""
    if opts[0] in kit.moves:
        groups = defaultdict(list)
        for k in opts:
            groups[base_class(kit.moves[k])].append(k)
        return {k: 1.0 / len(groups) / len(g) for g in groups.values() for k in g}
    return {k: 1.0 / len(opts) for k in opts}


class AI:
    def __init__(self, level="normal", seed=None):
        self.level = level
        self.habit_w, self.temp, self.samples, self.random_pick = LEVELS[level]
        self.rng = random.Random(seed)
        self.sim_rng = random.Random(self.rng.random())
        # (pos, role, in_sub) -> {move: weight}
        self.habits = defaultdict(lambda: defaultdict(float))

    def _context(self, st, i):
        return (st.pos, st.role(i), st.sub is not None and st.sub.att == i)

    def observe(self, st_before, opp, pick):
        """Remember what the opponent picked in this situation."""
        h = self.habits[self._context(st_before, opp)]
        for k in h:
            h[k] *= 0.85
        h[pick] += 1.0

    def predict(self, st, opp):
        opts = st.options(opp)
        uniform = _class_prior(opts, st.f[opp].kit)
        h = self.habits.get(self._context(st, opp))
        if not h or self.habit_w == 0:
            return uniform
        total = sum(h.get(k, 0) for k in opts)
        if total <= 0:
            return uniform
        trust = self.habit_w * total / (total + 2.0)
        return {k: (1 - trust) * uniform[k] + trust * h.get(k, 0) / total for k in opts}

    def choose(self, fight, me):
        st = fight.state
        opts = st.options(me)
        if len(opts) == 1:
            return opts[0]
        if self.rng.random() < self.random_pick:
            return self.rng.choice(opts)
        pred = self.predict(st, 1 - me)
        scores = {}
        for m in opts:
            ev = 0.0
            for o, p in pred.items():
                if p < 0.01:
                    continue
                total = 0.0
                for _ in range(self.samples):
                    sim = st.clone()
                    picks = (m, o) if me == 0 else (o, m)
                    ex = resolve(sim, picks, self.sim_rng)
                    total += evaluate(sim, ex, me)
                ev += p * total / self.samples
            scores[m] = ev
        best = max(scores.values())
        weights = [math.exp((scores[m] - best) / self.temp) for m in opts]
        return self.rng.choices(opts, weights)[0]
