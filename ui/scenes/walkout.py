"""Walkouts and the announcer before the fight. Any key skips."""

import pygame

from ..arena import Arena
from ..common import W, H, CX, FLOOR_Y, RED, BLUE, GOLD, WHITE, GREY, text, panel
from ..choreo import SCALE
from ..stickman import Figure
from .base import Scene


def intro_lines(p, corner):
    nick = f' "{p.nickname}" ' if p.nickname else " "
    first, *rest = p.name.split(" ", 1)
    full = f"{first}{nick}{rest[0] if rest else ''}".strip()
    lines = [f"Fighting out of the {corner} corner",
             f"Standing {p.height}, with a record of {p.record()}"]
    if p.hometown:
        lines.append(f"Out of {p.hometown}")
    lines.append(full.upper())
    return lines


class WalkoutScene(Scene):
    def __init__(self, app, cfg, label=""):
        super().__init__(app)
        self.cfg = cfg
        self.label = label
        self.arena = Arena()
        self.figs = [Figure(-80, FLOOR_Y, 1, cfg.p0.color, glove=RED, scale=SCALE),
                     Figure(W + 80, FLOOR_Y, -1, cfg.p1.color, glove=BLUE, scale=SCALE)]
        self.ref = Figure(CX, FLOOR_Y - 14, 1, (25, 25, 30), glove=(120, 125, 140),
                          body=(120, 125, 140), scale=0.9 * SCALE)
        self.ref.set_pose("ref", idle="ref")
        self.t = 0.0
        self.step = -1
        self.lines = []
        self.shown = 0.0
        self.spot = None
        self.events = []
        self._script()
        self.app.sounds.ambience(True)

    def _script(self):
        walk = [("walk1", 0.2), ("walk2", 0.2)] * 6
        title = "This is the main event of the evening" if not self.cfg.title else \
            "This is for the championship of the world"
        s = [
            (0.2, lambda: self._say(["Ladies and gentlemen", title], None)),
            (2.6, lambda: (self._say(intro_lines(self.cfg.p1, "blue"), 1),
                           self.figs[1].play(walk, idle="stance"),
                           self.figs[1].move_to(CX + 230, dur=2.2))),
            (5.6, lambda: (self.figs[1].play([("victory", 0.3), ("victory", 0.6), ("stance", 0.3)]),
                           self.app.sounds.play("crowd", 0.6), self.arena.cheer(1.2))),
            (6.8, lambda: (self._say(intro_lines(self.cfg.p0, "red"), 0),
                           self.figs[0].play(walk, idle="stance"),
                           self.figs[0].move_to(CX - 230, dur=2.2))),
            (9.8, lambda: (self.figs[0].play([("victory", 0.3), ("victory", 0.6), ("stance", 0.3)]),
                           self.app.sounds.play("crowd", 0.8), self.arena.cheer(1.5))),
            (11.0, lambda: (self._say(["Touch gloves", "and let's get it on"], None),
                            self.figs[0].move_to(CX - 85, dur=0.8), self.figs[1].move_to(CX + 85, dur=0.8),
                            self.ref.play([("ref_fight", 0.3)], idle="ref_fight"))),
            (12.2, lambda: (self.figs[0].play([("jab", 0.15), ("jab", 0.3), ("stance", 0.2)]),
                            self.figs[1].play([("jab", 0.15), ("jab", 0.3), ("stance", 0.2)]))),
            (13.4, self._done),
        ]
        for t, fn in s:
            self.events.append([t, fn])

    def _say(self, lines, spot):
        self.lines = lines
        self.shown = 0.0
        self.spot = spot

    def _done(self):
        from .fight import FightScene
        self.app.goto(FightScene(self.app, self.cfg))

    def handle(self, e):
        if (e.type == pygame.KEYDOWN and e.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_ESCAPE)) \
                or (e.type == pygame.MOUSEBUTTONDOWN and e.button == 1):
            self.events = []
            self._done()

    def update(self, dt):
        self.t += dt
        self.shown += dt
        due = [ev for ev in self.events if ev[0] <= self.t]
        self.events = [ev for ev in self.events if ev[0] > self.t]
        for ev in due:
            ev[1]()
        for f in self.figs:
            f.update(dt)
        self.ref.update(dt)
        self.arena.update(dt)

    def draw(self, surf):
        self.arena.draw(surf)
        dim = pygame.Surface((W, H), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 120))
        surf.blit(dim, (0, 0))
        if self.spot is not None:
            f = self.figs[self.spot]
            cone = pygame.Surface((W, H), pygame.SRCALPHA)
            x = int(f.x)
            pygame.draw.polygon(cone, (255, 245, 210, 40),
                                [(x - 30, 0), (x + 30, 0), (x + 140, FLOOR_Y + 10), (x - 140, FLOOR_Y + 10)])
            pygame.draw.ellipse(cone, (255, 245, 210, 60), (x - 140, FLOOR_Y - 14, 280, 34))
            surf.blit(cone, (0, 0))
        self.ref.draw(surf)
        for f in self.figs:
            f.draw(surf)
        # Announcer text, typed out
        if self.lines:
            chars = int(self.shown * 45)
            y = 150
            for k, ln in enumerate(self.lines):
                last = k == len(self.lines) - 1 and self.spot is not None
                vis = ln[:max(0, chars)]
                chars -= len(ln) + 6
                if not vis:
                    break
                color = (RED if self.spot == 0 else BLUE if self.spot == 1 else WHITE)
                if last:
                    text(surf, vis, (CX, y + 10), 54, GOLD, "midtop", display=True)
                else:
                    text(surf, vis, (CX, y), 26, WHITE if not last else color, "midtop")
                y += 40
        if self.label:
            text(surf, self.label.upper(), (CX, 40), 22, GOLD, "midtop", bold=True)
        text(surf, "SPACE to skip", (W - 20, H - 20), 15, GREY, "bottomright")
