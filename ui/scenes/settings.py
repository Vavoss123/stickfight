"""Settings: volume, fullscreen, fight speed and walkouts."""

import pygame

from ..common import W, H, CX, GOLD, WHITE, GREY, text, panel, bar, Button
from ..settings import SPEEDS
from .base import Scene

ROWS = ["volume", "crowd", "fullscreen", "speed", "skip_walkouts"]
LABELS = {"volume": "Volume", "crowd": "Crowd noise", "fullscreen": "Fullscreen",
          "speed": "Fight speed", "skip_walkouts": "Skip walkouts"}
HELP = {"volume": "Every sound in the game.",
        "crowd": "The crowd, on top of the main volume.",
        "fullscreen": "F11 also switches it at any time.",
        "speed": "How fast exchanges play out. Knockout replays stay in slow motion.",
        "skip_walkouts": "Go straight to the fight instead of the ring announcer."}
TOP = 170
ROW_H = 74


class SettingsScene(Scene):
    def __init__(self, app, back):
        super().__init__(app)
        self.back_to = back
        self.s = app.settings
        self.focus = 0
        self.done = Button((CX - 120, H - 90, 240, 52), "Done", color=(40, 110, 60), size=22)
        self.controls = []   # (row, Button, value it sets or a step)
        for r, key in enumerate(ROWS):
            y = TOP + r * ROW_H + 14
            if key in ("volume", "crowd"):
                for k, step in enumerate((-10, 10)):
                    b = Button((CX + 20 + k * 300, y, 48, 44), "-" if step < 0 else "+", size=26)
                    self.controls.append((key, b, step))
            elif key == "speed":
                for k, (name, _) in enumerate(SPEEDS):
                    b = Button((CX + 20 + k * 118, y, 110, 44), name, size=18)
                    self.controls.append((key, b, k))
            else:
                for k, (name, v) in enumerate((("Off", False), ("On", True))):
                    b = Button((CX + 20 + k * 118, y, 110, 44), name, size=18)
                    self.controls.append((key, b, v))

    def _change(self, key, value):
        s = self.s
        if key in ("volume", "crowd"):
            s[key] = max(0, min(100, s[key] + value))
        else:
            s[key] = value
        self.app.apply_settings()
        s.save()
        self.app.sounds.play("punch" if key == "volume" else "roar" if key == "crowd" else "click",
                             0.6)

    def _nudge(self, key, d):
        """Arrow keys: step volume, or move to the next choice."""
        if key in ("volume", "crowd"):
            self._change(key, 10 * d)
        elif key == "speed":
            self._change(key, max(0, min(len(SPEEDS) - 1, self.s[key] + d)))
        else:
            self._change(key, d > 0)

    def _leave(self):
        self.s.save()
        self.app.goto(self.back_to())

    def handle(self, e):
        if self.done.handle(e):
            self._leave()
            return
        for key, b, v in self.controls:
            if b.handle(e):
                self.focus = ROWS.index(key)
                self._change(key, v)
                return
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE:
                self._leave()
            elif e.key in (pygame.K_DOWN, pygame.K_s):
                self.focus = (self.focus + 1) % len(ROWS)
            elif e.key in (pygame.K_UP, pygame.K_w):
                self.focus = (self.focus - 1) % len(ROWS)
            elif e.key in (pygame.K_LEFT, pygame.K_a):
                self._nudge(ROWS[self.focus], -1)
            elif e.key in (pygame.K_RIGHT, pygame.K_d):
                self._nudge(ROWS[self.focus], 1)
            elif e.key == pygame.K_RETURN:
                self._leave()

    def draw(self, surf):
        surf.fill((14, 15, 22))
        text(surf, "SETTINGS", (CX, 40), 52, WHITE, "midtop", display=True)
        text(surf, "Arrow keys or the mouse. Changes save straight away.", (CX, 106), 17, GREY,
             "midtop")
        for r, key in enumerate(ROWS):
            y = TOP + r * ROW_H
            row = pygame.Rect(CX - 440, y, 880, ROW_H - 8)
            panel(surf, row, (30, 33, 46) if r == self.focus else (22, 24, 34),
                  border=GOLD if r == self.focus else None)
            text(surf, LABELS[key], (row.x + 24, y + 12), 22, WHITE, bold=True)
            text(surf, HELP[key], (row.x + 24, y + 40), 14, GREY, max_width=420)
            if key in ("volume", "crowd"):
                v = self.s[key]
                bar(surf, (CX + 80, y + 28, 230, 16), v / 100, GOLD)
                text(surf, f"{v}%", (CX + 380, y + 36), 20, WHITE, "midleft", bold=True)
        for key, b, v in self.controls:
            if key not in ("volume", "crowd"):
                b.selected = self.s[key] == v
            b.draw(surf)
        self.done.draw(surf)
