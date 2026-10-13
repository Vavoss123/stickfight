"""Main menu with a little sparring session going on behind it."""

import random

import pygame

import updater
from engine.career import Career
from version import VERSION

from ..arena import Arena
from ..common import (W, H, CX, FLOOR_Y, RED, BLUE, GOLD, WHITE, GREY, GREEN, text, panel,
                      bar, Button)
from ..choreo import SCALE
from ..stickman import Figure
from .base import Scene

SPAR = ["jab", "cross", "block", "kick", "counter"]
SEQ = {
    "jab": [("jab", 0.1), ("jab", 0.1), ("stance", 0.2)],
    "cross": [("cross_wind", 0.14), ("cross", 0.1), ("stance", 0.25)],
    "block": [("block", 0.12), ("block", 0.3), ("stance", 0.2)],
    "kick": [("kick_wind", 0.14), ("kick", 0.14), ("stance", 0.3)],
    "counter": [("block", 0.1), ("counter", 0.1), ("stance", 0.2)],
}


class MenuScene(Scene):
    def __init__(self, app):
        super().__init__(app)
        self.arena = Arena()
        self.figs = [Figure(CX + 110 - 72, FLOOR_Y, 1, (200, 40, 40), glove=RED, scale=SCALE),
                     Figure(CX + 110 + 72, FLOOR_Y, -1, (40, 90, 220), glove=BLUE, scale=SCALE)]
        self.rng = random.Random()
        self.next_move = 1.0
        self.t = 0.0
        has_save = Career.load() is not None
        items = [
            ("Quick fight", "Fight the computer", "quick"),
            ("Local 2 player", "Same keyboard, hidden picks", "versus"),
            ("Career", "Continue your career" if has_save else "Start from the bottom", "career"),
            ("How to play", "Rules and controls", "help"),
            ("Quit", "", "quit"),
        ]
        self.buttons = []
        for k, (label, sub, pick) in enumerate(items):
            b = Button((60, 250 + k * 78, 340, 64), label, sub=sub, size=24,
                       color=(150, 40, 40) if k == 0 else (40, 44, 62))
            b.pick = pick
            self.buttons.append(b)
        self.focus = 0
        app.sounds.ambience(False)

    def _go(self, pick):
        self.app.sounds.play("click")
        if pick == "quick":
            from .select import SelectScene
            self.app.goto(SelectScene(self.app, "ai"))
        elif pick == "versus":
            from .select import SelectScene
            self.app.goto(SelectScene(self.app, "2p"))
        elif pick == "career":
            from .career import open_career
            open_career(self.app)
        elif pick == "help":
            from .howto import HowToScene
            self.app.goto(HowToScene(self.app))
        elif pick == "quit":
            self.app.running = False

    def handle(self, e):
        for b in self.buttons:
            if b.handle(e):
                self._go(b.pick)
                return
        if e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_DOWN, pygame.K_s):
                self.focus = (self.focus + 1) % len(self.buttons)
            elif e.key in (pygame.K_UP, pygame.K_w):
                self.focus = (self.focus - 1) % len(self.buttons)
            elif e.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._go(self.buttons[self.focus].pick)
            elif e.key == pygame.K_ESCAPE:
                self.app.running = False
            elif e.key == pygame.K_u and updater.state["status"] in ("available", "failed"):
                if updater.state["status"] == "failed":
                    updater.state["status"] = "available"
                self.app.sounds.play("click")
                updater.start_update()
        for k, b in enumerate(self.buttons):
            b.selected = k == self.focus
            if b.hover:
                self.focus = k

    def update(self, dt):
        self.t += dt
        self.next_move -= dt
        if self.next_move <= 0:
            self.next_move = self.rng.uniform(0.7, 1.6)
            i = self.rng.randint(0, 1)
            mv = self.rng.choice(SPAR)
            self.figs[i].play(list(SEQ[mv]), idle="stance")
            if mv in ("cross", "kick") and self.rng.random() < 0.5:
                o = self.figs[1 - i]
                o.play([("stance", 0.15), ("block", 0.1), ("block", 0.2), ("stance", 0.2)])
        for f in self.figs:
            f.update(dt)
        self.arena.update(dt)

    def draw(self, surf):
        self.arena.draw(surf)
        shade = pygame.Surface((480, H), pygame.SRCALPHA)
        for x in range(480):
            a = int(200 * (1 - x / 480) ** 1.4)
            pygame.draw.line(shade, (0, 0, 0, a), (x, 0), (x, H))
        surf.blit(shade, (0, 0))
        for f in self.figs:
            f.draw(surf)
        text(surf, "STICKFIGHT", (56, 70), 96, WHITE, display=True)
        text(surf, "TURN BASED MMA", (62, 178), 24, GOLD, bold=True)
        for b in self.buttons:
            b.draw(surf)
        text(surf, "M mutes sound, ESC pauses in a fight", (W - 20, H - 16), 14, GREY, "bottomright")
        text(surf, f"v{VERSION}", (20, H - 16), 14, GREY, "bottomleft")
        self._draw_update(surf)

    def _draw_update(self, surf):
        st = updater.state
        status = st["status"]
        if status not in ("available", "downloading", "restarting", "failed"):
            return
        r = panel(surf, (W - 380, 20, 360, 74), border=GOLD if status == "available" else None)
        if status == "available":
            text(surf, f"Update available: {st['latest']}", (r.x + 16, r.y + 12), 20, GOLD,
                 bold=True)
            how = "Press U to update and restart" if updater.FROZEN and st["asset"] \
                else "Press U to open the download page"
            text(surf, how, (r.x + 16, r.y + 42), 16, WHITE)
        elif status == "downloading":
            text(surf, f"Downloading {st['latest']}...", (r.x + 16, r.y + 12), 20, WHITE,
                 bold=True)
            bar(surf, (r.x + 16, r.y + 44, r.w - 32, 14), st["progress"], GREEN)
        elif status == "restarting":
            text(surf, "Restarting...", (r.x + 16, r.y + 24), 20, GREEN, bold=True)
        else:
            text(surf, "Update failed", (r.x + 16, r.y + 12), 20, RED, bold=True)
            text(surf, "Press U to try again", (r.x + 16, r.y + 42), 16, WHITE)
