"""The gym drills. Coach Ray picks one at random each session.

Every drill is eight reps and scores hits out of GYM_REPS, so the rewards in
engine/career.py do not care which one you played. The gym is free, so the drills
get harder instead: `level` runs from 0 (a rookie deck) to 1 (a champion with every
bonus point) and makes things faster, smaller and shorter.

A drill has:

    name, blurb     what it is called and how to play it
    status()        the line above the drill ("Rep 3 of 8   Hits 2")
    handle(e)       mouse and keyboard
    update(dt)
    draw(surf)
    finished, hits  done when finished is True
    shout, events   a word from the coach after a rep, and things for the scene to show
"""

import math
import random

import pygame

from engine.career import GYM_REPS

from .common import W, CX, GOLD, WHITE, GREEN, RED, text

SHOUTS_HIT = ["Good!", "Again!", "There it is!", "Sharp!", "Yes!"]
SHOUTS_MISS = ["Late!", "Early!", "Focus!", "Come on!", "Watch the pad!"]
PRESS = (pygame.K_SPACE, pygame.K_RETURN)


def pressed(e):
    """SPACE, ENTER or a left click."""
    return (e.type == pygame.KEYDOWN and e.key in PRESS) or \
           (e.type == pygame.MOUSEBUTTONDOWN and e.button == 1)


class Drill:
    name = ""
    blurb = ""

    def __init__(self, rng=None, level=0.0):
        self.rng = rng or random.Random()
        self.level = level
        self.rep = 0
        self.hits = 0
        self.finished = False
        self.shout = ""
        self.events = []       # ("hit", good), ("coach", pose), ("me", pose)

    def status(self):
        return f"Rep {min(self.rep + 1, GYM_REPS)} of {GYM_REPS}    Hits {self.hits}"

    def score(self, good):
        """One rep is over."""
        self.hits += bool(good)
        self.rep += 1
        self.shout = self.rng.choice(SHOUTS_HIT if good else SHOUTS_MISS)
        self.events.append(("hit", bool(good)))
        if self.rep >= GYM_REPS:
            self.finished = True

    def handle(self, e):
        pass

    def update(self, dt):
        pass

    def draw(self, surf):
        pass


class PadWork(Drill):
    """A marker sweeps along a bar. Press when it is inside the gold zone."""
    name = "Pad work"
    blurb = "Hit SPACE (or click) when the marker is in the gold zone."
    BAR = pygame.Rect(CX - 360, 470, 720, 40)

    def __init__(self, rng=None, level=0.0):
        super().__init__(rng, level)
        self.wait = 0.0
        self._target()

    def _target(self):
        """A little smaller and faster every rep, and more so the higher the level."""
        k, lv = self.rep, self.level
        self.width = max(0.09, 0.30 - 0.10 * lv - k * (0.022 + 0.006 * lv))
        self.centre = self.rng.uniform(0.15 + self.width, 0.85 - self.width)
        self.speed = 0.38 + 0.25 * lv + k * (0.05 + 0.03 * lv)     # sweeps a second
        self.pos = 0.0
        self.live = True

    def marker(self):
        return 0.5 - 0.5 * math.cos(self.pos * math.pi * 2)   # back and forth

    def handle(self, e):
        if self.live and not self.finished and pressed(e):
            self.live = False
            self.wait = 0.8
            self.score(abs(self.marker() - self.centre) <= self.width / 2)

    def update(self, dt):
        if self.live:
            self.pos += dt * self.speed
            if self.pos >= 2.0:                 # let it go past twice and the rep is lost
                self.live = False
                self.wait = 0.8
                self.score(False)
        elif not self.finished:
            self.wait -= dt
            if self.wait <= 0:
                self._target()

    def draw(self, surf):
        bar = self.BAR
        pygame.draw.rect(surf, (40, 42, 54), bar, border_radius=8)
        zx = bar.x + int((self.centre - self.width / 2) * bar.w)
        pygame.draw.rect(surf, GOLD, (zx, bar.y, int(self.width * bar.w), bar.h), border_radius=6)
        if self.live:
            mx = bar.x + int(self.marker() * bar.w)
            pygame.draw.rect(surf, WHITE, (mx - 4, bar.y - 10, 8, bar.h + 20), border_radius=3)
        pygame.draw.rect(surf, (0, 0, 0), bar, 2, border_radius=8)


class CatchBalls(Drill):
    """Balls drop from the ceiling. Move the mouse (or the arrow keys) to catch each one."""
    name = "Catch the balls"
    blurb = "Move the mouse left and right (or use the arrow keys) to catch every ball before it lands."
    FLOOR = 520
    TOP = 150

    def __init__(self, rng=None, level=0.0):
        super().__init__(rng, level)
        self.reach = 58 - 14 * level          # how far from the glove still counts
        self.x = float(CX)
        self.target_x = None                  # the mouse, once it has moved
        self.held = set()
        self.ball = None
        self.gap = 0.6
        self.fall = 2.0
        self.splat = None                     # (x, time left) where a missed ball landed
        self.puff = None                      # (x, time left) where a ball was caught

    def _spawn(self):
        k, lv = self.rep, self.level
        self.fall = max(0.9, 2.0 - 0.6 * lv - k * (0.1 + 0.02 * lv))   # seconds to fall
        x = self.rng.uniform(130, W - 130)
        # Never ask for more than the glove can cover in time
        reach = 600 * self.fall
        x = min(max(x, self.x - reach), self.x + reach)
        self.ball = {"x": x, "t": 0.0}

    def handle(self, e):
        if e.type == pygame.MOUSEMOTION:
            self.target_x = e.pos[0]
        elif e.type == pygame.KEYDOWN and e.key in (pygame.K_LEFT, pygame.K_a, pygame.K_RIGHT, pygame.K_d):
            self.held.add(e.key)
            self.target_x = None
        elif e.type == pygame.KEYUP:
            self.held.discard(e.key)

    def update(self, dt):
        if self.finished:
            return
        for name in ("splat", "puff"):
            v = getattr(self, name)
            if v:
                setattr(self, name, (v[0], v[1] - dt) if v[1] - dt > 0 else None)
        step = 620 * dt
        if self.target_x is not None:
            self.x += max(-1.6 * step, min(1.6 * step, self.target_x - self.x))
        else:
            left = bool(self.held & {pygame.K_LEFT, pygame.K_a})
            right = bool(self.held & {pygame.K_RIGHT, pygame.K_d})
            self.x += step * (right - left)
        self.x = max(60, min(W - 60, self.x))
        if self.ball is None:
            self.gap -= dt
            if self.gap <= 0:
                self._spawn()
            return
        b = self.ball
        b["t"] += dt
        if b["t"] >= self.fall:
            caught = abs(b["x"] - self.x) <= self.reach
            if caught:
                self.puff = (b["x"], 0.3)
            else:
                self.splat = (b["x"], 0.6)
            self.ball = None
            self.gap = 0.7
            self.score(caught)

    def draw(self, surf):
        pygame.draw.line(surf, (60, 62, 76), (40, self.FLOOR + 36), (W - 40, self.FLOOR + 36), 2)
        if self.ball:
            b = self.ball
            f = b["t"] / self.fall
            y = self.TOP + (self.FLOOR - self.TOP) * (f * f * 0.35 + f * 0.65)
            pygame.draw.circle(surf, (230, 200, 60), (int(b["x"]), int(y)), 17)
            pygame.draw.circle(surf, (0, 0, 0), (int(b["x"]), int(y)), 17, 2)
            pygame.draw.arc(surf, (255, 255, 255), (b["x"] - 12, y - 12, 24, 24), 0.6, 2.2, 2)
            # A faint line down to where it will land
            pygame.draw.line(surf, (70, 70, 40), (b["x"], y + 20), (b["x"], self.FLOOR + 30), 1)
        if self.splat:
            x, t = self.splat
            pygame.draw.ellipse(surf, (230, 200, 60), (x - 20, self.FLOOR + 22, 40, 14))
        if self.puff:
            x, t = self.puff
            pygame.draw.circle(surf, GREEN, (int(x), self.FLOOR - 6), int(30 * (1 - t / 0.3)) + 10, 3)
        # The glove, as wide as the reach so what you see is what counts
        gx, gy, hw = int(self.x), self.FLOOR, int(self.reach)
        pygame.draw.rect(surf, RED, (gx - hw, gy, hw * 2, 30), border_radius=10)
        pygame.draw.rect(surf, (0, 0, 0), (gx - hw, gy, hw * 2, 30), 2, border_radius=10)
        pygame.draw.rect(surf, (230, 230, 230), (gx - hw, gy + 22, hw * 2, 8), border_radius=4)


class Mitts(Drill):
    """The coach holds up a pad somewhere. Click it before it lowers."""
    name = "Mitt work"
    blurb = "Click each pad the coach holds up before it drops. The shrinking ring means hurry."

    def __init__(self, rng=None, level=0.0):
        super().__init__(rng, level)
        self.radius = 46 - 10 * level
        self.pad = None
        self.wait = 0.7
        self.life = 2.4

    def _spawn(self):
        k, lv = self.rep, self.level
        self.life = max(0.8, 2.5 - 0.8 * lv - k * (0.12 + 0.02 * lv))
        side = self.rng.choice((0, 1))
        x = self.rng.uniform(120, CX - 260) if side == 0 else self.rng.uniform(CX + 260, W - 120)
        self.pad = {"x": x, "y": self.rng.uniform(170, 360), "t": 0.0}

    def handle(self, e):
        if self.pad and e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            d = math.hypot(e.pos[0] - self.pad["x"], e.pos[1] - self.pad["y"])
            if d <= self.radius:
                self.pad = None
                self.wait = 0.5
                self.score(True)

    def update(self, dt):
        if self.finished:
            return
        if self.pad is None:
            self.wait -= dt
            if self.wait <= 0:
                self._spawn()
            return
        self.pad["t"] += dt
        if self.pad["t"] >= self.life:
            self.pad = None
            self.wait = 0.5
            self.score(False)

    def draw(self, surf):
        if not self.pad:
            return
        p = self.pad
        left = 1 - p["t"] / self.life
        x, y, r = int(p["x"]), int(p["y"]), int(self.radius)
        pygame.draw.circle(surf, (230, 190, 50), (x, y), r)
        pygame.draw.circle(surf, (150, 110, 20), (x, y), r, 4)
        pygame.draw.circle(surf, (255, 235, 150), (x, y), r // 2, 3)
        col = GREEN if left > 0.5 else (255, 170, 60) if left > 0.25 else RED
        pygame.draw.circle(surf, col, (x, y), int(r + 6 + 40 * left), 3)


class Reaction(Drill):
    """Wait for the bell, then press as fast as you can."""
    name = "Bell drill"
    blurb = "Wait for the light to go green, then press SPACE (or click). Too early counts against you."
    say = ""

    def __init__(self, rng=None, level=0.0):
        super().__init__(rng, level)
        self._next()

    def _next(self):
        self.phase = "wait"        # wait, go, rest
        self.t = 0.0
        self.delay = self.rng.uniform(1.0, 2.6)
        self.limit = max(0.3, 0.8 - 0.25 * self.level - self.rep * 0.04)   # seconds once it goes green

    def handle(self, e):
        if self.finished or not pressed(e):
            return
        if self.phase == "wait":
            self.phase, self.t, self.say = "rest", 0.0, "Too early!"
            self.score(False)
        elif self.phase == "go":
            took = self.t
            self.phase, self.t, self.say = "rest", 0.0, f"{int(took * 1000)} ms"
            self.score(took <= self.limit)

    def update(self, dt):
        if self.finished:
            return
        self.t += dt
        if self.phase == "wait" and self.t >= self.delay:
            self.phase, self.t = "go", 0.0
        elif self.phase == "go" and self.t > self.limit:
            self.phase, self.t, self.say = "rest", 0.0, "Too slow!"
            self.score(False)
        elif self.phase == "rest" and self.t > 0.9:
            self._next()

    def draw(self, surf):
        c = (CX, 250)
        col = {"wait": (190, 50, 50), "go": (60, 210, 90), "rest": (70, 72, 86)}[self.phase]
        pygame.draw.circle(surf, col, c, 58)
        pygame.draw.circle(surf, (0, 0, 0), c, 58, 4)
        label = {"wait": "WAIT", "go": "NOW!", "rest": self.say}[self.phase]
        text(surf, label, c, 26, WHITE, "center", display=True, max_width=100)
        if self.phase == "go":
            frac = max(0.0, 1 - self.t / self.limit)
            pygame.draw.rect(surf, (40, 42, 54), (CX - 150, 450, 300, 12), border_radius=5)
            pygame.draw.rect(surf, GOLD, (CX - 150, 450, int(300 * frac), 12), border_radius=5)


class Combos(Drill):
    """The coach throws a combination. Throw it back."""
    name = "Combos"
    blurb = "Watch Coach Ray's combination, then repeat it with the buttons or the keys 1 to 4."
    MOVES = [("Jab", "jab"), ("Cross", "cross"), ("Kick", "kick"), ("Knee", "knee")]

    def __init__(self, rng=None, level=0.0):
        super().__init__(rng, level)
        self.show = 0.8 - 0.3 * level          # seconds per move shown
        self.buttons = [pygame.Rect(CX - 330 + k * 170, 470, 160, 56) for k in range(4)]
        self.flash = {}
        self._start_rep()

    def _start_rep(self):
        n = 2 + (self.rep + int(self.level * 6)) // 3          # longer as you go and as the level rises
        self.seq = [self.rng.randrange(4) for _ in range(n)]
        self.phase = "show"
        self.t = -0.5
        self.shown = 0
        self.got = []

    def handle(self, e):
        if self.finished or self.phase != "input":
            return
        pick = None
        if e.type == pygame.KEYDOWN and pygame.K_1 <= e.key <= pygame.K_4:
            pick = e.key - pygame.K_1
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            pick = next((k for k, r in enumerate(self.buttons) if r.collidepoint(e.pos)), None)
        if pick is None:
            return
        self.flash[pick] = 0.2
        self.events.append(("me", self.MOVES[pick][1]))
        self.got.append(pick)
        if self.got[-1] != self.seq[len(self.got) - 1]:
            self.phase, self.t = "rest", 0.0
            self.score(False)
        elif len(self.got) == len(self.seq):
            self.phase, self.t = "rest", 0.0
            self.score(True)

    def update(self, dt):
        for k in list(self.flash):
            self.flash[k] -= dt
            if self.flash[k] <= 0:
                del self.flash[k]
        if self.finished:
            return
        self.t += dt
        if self.phase == "show":
            n = int(self.t / self.show) + 1 if self.t >= 0 else 0
            while self.shown < min(n, len(self.seq)):
                move = self.seq[self.shown]
                self.events.append(("coach", self.MOVES[move][1]))
                self.flash[move] = 0.4
                self.shown += 1
            if self.t >= self.show * len(self.seq) + 0.2:
                self.phase, self.t = "input", 0.0
        elif self.phase == "input" and self.t > 3.0 + 1.5 * len(self.seq):
            self.phase, self.t = "rest", 0.0       # froze up
            self.score(False)
        elif self.phase == "rest" and self.t > 0.8:
            self._start_rep()

    def draw(self, surf):
        msg = {"show": "Watch...", "input": "Your turn!", "rest": ""}[self.phase]
        text(surf, msg, (CX, 420), 22, GOLD, "midtop", bold=True)
        # The combination so far, as dots
        for k in range(len(self.seq)):
            done = k < len(self.got)
            ok = done and self.got[k] == self.seq[k]
            col = GREEN if ok else RED if done else (70, 72, 86)
            pygame.draw.circle(surf, col, (CX - 12 * (len(self.seq) - 1) + k * 24, 452), 7)
        for k, (label, _) in enumerate(self.MOVES):
            r = self.buttons[k]
            lit = k in self.flash
            pygame.draw.rect(surf, GOLD if lit else (52, 58, 78), r, border_radius=8)
            pygame.draw.rect(surf, (0, 0, 0), r, 2, border_radius=8)
            text(surf, label, r.center, 22, (20, 20, 20) if lit else WHITE, "center", bold=True)
            text(surf, str(k + 1), (r.x + 8, r.y + 4), 14, (20, 20, 20) if lit else GOLD, bold=True)


DRILLS = [PadWork, CatchBalls, Mitts, Reaction, Combos]


def pick(rng=None, avoid=None, level=0.0):
    """A random drill at this level, and not the one you just did if there is a choice."""
    rng = rng or random.Random()
    options = [d for d in DRILLS if d is not avoid] or DRILLS
    return rng.choice(options)(rng, level)
