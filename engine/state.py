"""The minimal fight state the rules operate on. Cheap to clone for AI lookahead."""

from .constants import STANDING, CLINCH, NEUTRAL, TOP, BOTTOM, SUB_OPTIONS


class SubState:
    __slots__ = ("att", "move", "lock", "angle")

    def __init__(self, att, move, lock, angle=0):
        self.att = att
        self.move = move
        self.lock = lock      # 0 is escaped, SUB_TAP is a tap
        self.angle = angle    # set up by Adjust, spent by a squeeze that gets through a defence

    def clone(self):
        return SubState(self.att, self.move, self.lock, self.angle)


class FightState:
    __slots__ = ("f", "pos", "top", "sub", "idle")

    def __init__(self, fighters, pos=STANDING, top=None, sub=None, idle=0):
        self.f = fighters
        self.pos = pos
        self.top = top
        self.sub = sub
        self.idle = idle    # quiet exchanges in a row in the clinch or on the ground

    def clone(self):
        return FightState([self.f[0].clone(), self.f[1].clone()], self.pos, self.top,
                          self.sub.clone() if self.sub else None, self.idle)

    def role(self, i):
        if self.pos in (STANDING, CLINCH):
            return NEUTRAL
        return TOP if self.top == i else BOTTOM

    def options(self, i):
        """Legal picks for fighter i right now."""
        if self.sub:
            return list(SUB_OPTIONS)
        return list(self.f[i].kit.movesets[(self.pos, self.role(i))])
