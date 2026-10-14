"""A full fight: rounds, the clock, stats for the judges, and the result."""

import random

from .constants import (EXCHANGES_PER_ROUND, ROUND_SECONDS, STANDING, MAX_STAMINA,
                        STRIKE, ROUND_RECOVERY)
from .fighter import FighterState
from .judges import RoundStats, score_fight
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
    def __init__(self, p0, p1, rounds=3, seed=None, title=False, start=None):
        """start: optional (dict, dict) of hp, stamina, body, legs and cut for fighters who
        are not fresh, like the later rounds of a tournament."""
        self.rng = random.Random(seed)
        self.profiles = (p0, p1)
        start = start or (None, None)
        self.state = FightState([FighterState(p, **(s or {})) for p, s in zip((p0, p1), start)])
        self.rounds = rounds
        self.title = title
        self.round = 1
        self.exchange = 0
        self.stats = [(RoundStats(), RoundStats())]
        self.history = []
        self.result = None
        self.between_rounds = False

    def refit(self, i, profile):
        """Give fighter i a new deck mid fight, keeping their damage and stamina."""
        from .cards import build_kit
        f = self.state.f[i]
        f.profile = profile
        f.kit = build_kit(profile)
        f.stats = f.kit.stats
        f.wc = f.kit.weight
        profiles = list(self.profiles)
        profiles[i] = profile
        self.profiles = tuple(profiles)

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
        st.pos, st.top, st.sub, st.idle = STANDING, None, None, 0
        for f in st.f:
            f.rocked = 0
            gain = (ROUND_RECOVERY + f.stats.cardio * 2) * (1.0 - f.body / 200) + f.perk("secondwind")
            f.combo = 0
            f.opening = None
            f.stamina = min(MAX_STAMINA, f.stamina + gain)
            f.hp = min(100.0, f.hp + 4)
            f.body *= 0.8
            f.legs *= 0.85
            f.cut = max(0.0, f.cut - 15 - f.perk("cutman"))  # the cutman goes to work

    def _decision(self):
        winner, detail, cards = score_fight(self.stats, self.rng)
        method = "Decision" if winner is not None else "Draw"
        self.result = Result(winner, method, detail, self.round, "5:00", cards)

    def _record(self, ex):
        s = self.stats[-1]
        for i in (0, 1):
            r = s[i]
            if not ex.in_sub:
                m = ex.moves[i]
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
            if ex.foul and ex.foul[0] == i and ex.foul[2] == "point":
                r.deductions += 1
