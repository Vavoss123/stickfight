"""Banners that slide in over any screen: achievements and unlocked fighters."""

import pygame

from .common import W, CX, GOLD, WHITE, GREY, text, panel

SHOW = 3.0


class Toasts:
    def __init__(self, app):
        self.app = app
        self.queue = []      # [title, line, seconds left]

    def push(self, title, line):
        self.queue.append([title, line, SHOW])
        if len(self.queue) == 1:
            self.app.sounds.play("levelup", 0.7)

    def update(self, dt):
        if not self.queue:
            return
        self.queue[0][2] -= dt
        if self.queue[0][2] <= 0:
            self.queue.pop(0)
            if self.queue:
                self.app.sounds.play("levelup", 0.7)

    def draw(self, surf):
        if not self.queue:
            return
        title, line, left = self.queue[0]
        slide = min(1.0, (SHOW - left) * 5, left * 5)
        y = int(-70 + 90 * slide)
        r = panel(surf, (CX - 260, y, 520, 64), (40, 34, 14), alpha=240, border=GOLD)
        text(surf, title, (r.x + 18, r.y + 9), 15, GOLD, bold=True)
        text(surf, line, (r.x + 18, r.y + 32), 19, WHITE, bold=True, max_width=r.w - 36)
        if len(self.queue) > 1:
            text(surf, f"+{len(self.queue) - 1}", (r.right - 14, r.y + 9), 14, GREY, "topright")
