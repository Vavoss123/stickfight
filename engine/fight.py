"""A full fight: rounds, the clock, stats for the judges, and the result."""

import random

from .constants import (EXCHANGES_PER_ROUND, ROUND_SECONDS, STANDING, MAX_STAMINA,
                        STRIKE)
from .fighter import FighterState
from .judges import RoundStats, score_fight
from .moves import MOVES
from .resolve import resolve
from .state import FightState


class Result:
    def __init__(self, winner, method, detail, round_no, time, cards=None):
        self.winner = winner      # 0, 1 or None for a draw
        self.method = method      # KO, TKO, Submission, Decision, Draw
        self.detail = detail
        self.round = round_no
        self.time = time          # "3:45"
        self.cards = cards or []


def fmt_time(seconds):
    seconds = max(0, int(round(seconds)))
    return f"{seconds // 60}:{seconds % 60:02d}"


class Fight:
    def __init__(self, p0, p1, rounds=3, seed=None, title=False):
        self.rng = random.Random(seed)
        self.profiles = (p0, p1)
        self.state = FightState([FighterState(p0), FighterState(p1)])
        self.rounds = rounds
        self.title = title
        self.round = 1
        self.exchange = 0
        self.stats = [(RoundStats(), RoundStats())]
        self.history = []
        self.result = None
        self.between_rounds = False

    # Info

    @property
    def over(self):
        return self.result is not None

    def options(self, i):
        return self.state.options(i)

    def elapsed(self):
        return self.exchange * ROUND_SECONDS / EXCHANGES_PER_ROUND

    def clock(self):
        return fmt_time(ROUND_SECONDS - self.elapsed())

    def totals(self, i):
        t = RoundStats()
        for pair in self.stats:
            s = pair[i]
            for k in RoundStats.__slots__:
                setattr(t, k, getattr(t, k) + getattr(s, k))
        return t

    # Flow

    def play(self, picks):
        if self.over or self.between_rounds:
            raise RuntimeError("fight is not accepting picks")
        ex = resolve(self.state, picks, self.rng)
        self._record(ex)
        self.history.append(ex)
        self.exchange += 1
        if ex.finish:
            w, method, detail = ex.finish
            # The finish happens during the exchange, so back the clock off a bit
            t = self.elapsed() - self.rng.uniform(5, ROUND_SECONDS / EXCHANGES_PER_ROUND - 5)
            self.result = Result(w, method, detail, self.round, fmt_time(t))
            return ex
        if self.exchange >= EXCHANGES_PER_ROUND:
            ex.round_over = True
            if self.round >= self.rounds:
                self._decision()
            else:
                self.between_rounds = True
        return ex

    def start_next_round(self):
        self.between_rounds = False
        self.round += 1
        self.exchange = 0
        self.stats.append((RoundStats(), RoundStats()))
        st = self.state
        st.pos, st.top, st.sub = STANDING, None, None
        for f in st.f:
            f.rocked = 0
            gain = (28 + f.stats.cardio * 2.5) * (1.0 - f.body / 200)
            f.stamina = min(MAX_STAMINA, f.stamina + gain)
            f.hp = min(100.0, f.hp + 4)
            f.body *= 0.8
            f.legs *= 0.85

    def _decision(self):
        winner, detail, cards = score_fight(self.stats, self.rng)
        method = "Decision" if winner is not None else "Draw"
        self.result = Result(winner, method, detail, self.round, "5:00", cards)

    def _record(self, ex):
        s = self.stats[-1]
        for i in (0, 1):
            r = s[i]
            if not ex.in_sub:
                m = MOVES[ex.picks[i]]
                if m.cls == STRIKE:
                    r.thrown += 1
                if ex.countered[i]:
                    r.thrown += 1
            if ex.landed[i]:
                r.landed += 1
            r.dmg += ex.dmg[i]
            if ex.takedown_by == i:
                r.takedowns += 1
            if ex.reversal_by == i:
                r.reversals += 1
            if ex.knockdown == 1 - i:
                r.knockdowns += 1
            if ex.sub_start == i:
                r.sub_attempts += 1
            if ex.in_sub and ex.sub_att == i and ex.sub_result == "tighter":
                r.sub_attempts += 0.5
            if ex.top == i:
                r.control += 1
