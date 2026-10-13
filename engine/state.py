"""The minimal fight state the rules operate on. Cheap to clone for AI lookahead."""

from .constants import STANDING, CLINCH, NEUTRAL, TOP, BOTTOM, SUB_OPTIONS
from .moves import MOVESETS


class SubState:
    __slots__ = ("att", "move", "lock")

    def __init__(self, att, move, lock):
        self.att = att
        self.move = move
        self.lock = lock

    def clone(self):
        return SubState(self.att, self.move, self.lock)


class FightState:
    __slots__ = ("f", "pos", "top", "sub")

    def __init__(self, fighters, pos=STANDING, top=None, sub=None):
        self.f = fighters
        self.pos = pos
        self.top = top
        self.sub = sub

    def clone(self):
        return FightState([self.f[0].clone(), self.f[1].clone()], self.pos, self.top,
                          self.sub.clone() if self.sub else None)

    def role(self, i):
        if self.pos in (STANDING, CLINCH):
            return NEUTRAL
        return TOP if self.top == i else BOTTOM

    def options(self, i):
        """Legal picks for fighter i right now."""
        if self.sub:
            return list(SUB_OPTIONS)
        return list(MOVESETS[(self.pos, self.role(i))])
