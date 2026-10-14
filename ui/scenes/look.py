"""Change how your fighter looks: skin, hair, beard, tattoos and shorts."""

import random

import pygame

from engine.looks import (SKINS, HAIRS, HAIR_NAMES, HAIR_COLORS, SHORTS, TRIMS, TATTOOS, TATTOO_NAMES,
                          look_of, random_look)

from ..common import W, H, CX, RED, GOLD, WHITE, GREY, text, panel, Button
from ..stickman import Figure
from .base import Scene

# The preview shows off a few moves so you see the look from every angle
SHOWCASE = [("stance", 1.4), ("jab", 0.5), ("stance", 0.6), ("kick", 0.6), ("stance", 0.6),
            ("victory", 1.4)]
SW = 38        # swatch size
COL_X = 600    # where the options start


class LookScene(Scene):
    """target has .name, .color and .look (a Profile works). done() runs after Save."""

    def __init__(self, app, target, done, cancel=None):
        super().__init__(app)
        self.target = target
        self.done = done
        self.cancel = cancel or done
        self.look = look_of(target)
        self.color = tuple(target.color)
        if self.color not in SHORTS:
            self.color = SHORTS[0]
        self.fig = Figure(290, 520, 1, self.color, glove=getattr(target, "gloves", None) or RED, scale=1.7)
        self.fig.dress(look=self.look)
        self.show = 0
        self.show_t = 0.0
        self.rows = []      # (label, y) for the headings
        self.swatches = []  # (rect, key, value, colour)
        y = 112
        self._swatch_row("Skin", y, "skin", SKINS)
        y += 68
        self.rows.append(("Hair", y))
        self.hair_buttons = []
        for k, h in enumerate(HAIRS):
            b = Button((COL_X + (k % 4) * 152, y + 24 + (k // 4) * 44, 144, 38), HAIR_NAMES[h], size=17)
            b.pick = h
            self.hair_buttons.append(b)
        y += 114
        self._swatch_row("Hair colour", y, "hair_color", HAIR_COLORS)
        y += 68
        self.rows.append(("Beard", y))
        self.beard_buttons = [Button((COL_X + k * 152, y + 24, 144, 36), label, size=16)
                              for k, label in enumerate(("No beard", "Beard"))]
        y += 68
        self.rows.append(("Tattoos", y))
        self.tattoo_buttons = []
        for k, t in enumerate(TATTOOS):
            b = Button((COL_X + k * 102, y + 24, 96, 36), TATTOO_NAMES[t], size=14)
            b.pick = t
            self.tattoo_buttons.append(b)
        y += 68
        self._swatch_row("Shorts", y, "shorts", SHORTS)
        y += 68
        self._swatch_row("Stripe", y, "trim", TRIMS)
        self.random_btn = Button((190, H - 120, 200, 42), "Random look", size=18, color=(60, 50, 110))
        self.save_btn = Button((W - 240, H - 70, 220, 50), "Save look", color=(40, 110, 60), size=22)
        self.back_btn = Button((20, H - 70, 140, 42), "Cancel", size=18)

    def _swatch_row(self, label, y, key, values):
        self.rows.append((label, y))
        for k, v in enumerate(values):
            r = pygame.Rect(COL_X + k * (SW + 10), y + 26, SW, SW)
            self.swatches.append((r, key, k, v))

    def _selected(self, key, k):
        if key == "shorts":
            return SHORTS[k] == self.color
        return self.look[key] == k

    def _apply(self):
        self.fig.shorts = self.color
        self.fig.dress(look=self.look)

    def _save(self):
        self.target.color = self.color
        self.target.look = dict(self.look)
        self.app.sounds.play("click")
        self.done()

    def handle(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE:
                self.cancel()
                return
            if e.key == pygame.K_RETURN:
                self._save()
                return
        if self.save_btn.handle(e):
            self._save()
            return
        if self.back_btn.handle(e):
            self.cancel()
            return
        if self.random_btn.handle(e):
            self.look = random_look()
            self.color = random.choice(SHORTS)
            self.app.sounds.play("click")
        for b in self.hair_buttons:
            if b.handle(e):
                self.look["hair"] = b.pick
                self.app.sounds.play("click")
        for k, b in enumerate(self.beard_buttons):
            if b.handle(e):
                self.look["beard"] = k == 1
                self.app.sounds.play("click")
        for b in self.tattoo_buttons:
            if b.handle(e):
                self.look["tattoo"] = b.pick
                self.app.sounds.play("click")
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            for r, key, k, _ in self.swatches:
                if r.collidepoint(e.pos):
                    if key == "shorts":
                        self.color = SHORTS[k]
                    else:
                        self.look[key] = k
                    self.app.sounds.play("click")
        self._apply()

    def update(self, dt):
        self.show_t += dt
        pose, secs = SHOWCASE[self.show]
        if self.show_t >= secs:
            self.show_t = 0.0
            self.show = (self.show + 1) % len(SHOWCASE)
            nxt = SHOWCASE[self.show][0]
            self.fig.play([(nxt, 0.15)], idle=nxt)
        self.fig.update(dt)

    def draw(self, surf):
        surf.fill((14, 15, 22))
        text(surf, "YOUR LOOK", (CX, 26), 44, WHITE, "midtop", display=True)
        rect = panel(surf, (60, 110, 460, 470), (22, 24, 34))
        text(surf, self.target.name.upper() if self.target.name else "YOUR FIGHTER", (rect.centerx, rect.y + 16),
             26, WHITE, "midtop", display=True, max_width=rect.w - 30)
        self.fig.draw(surf)
        for label, y in self.rows:
            text(surf, label, (COL_X, y), 16, GREY, bold=True)
        for r, key, k, col in self.swatches:
            if col is None:
                pygame.draw.rect(surf, (40, 42, 52), r, border_radius=6)
                pygame.draw.line(surf, (150, 60, 60), (r.x + 8, r.bottom - 8), (r.right - 8, r.y + 8), 3)
            else:
                pygame.draw.rect(surf, col, r, border_radius=6)
            on = self._selected(key, k)
            pygame.draw.rect(surf, GOLD if on else (0, 0, 0), r, 3, border_radius=6)
        for b in self.hair_buttons:
            b.selected = b.pick == self.look["hair"]
            b.draw(surf)
        for k, b in enumerate(self.beard_buttons):
            b.selected = self.look["beard"] == (k == 1)
            b.draw(surf)
        for b in self.tattoo_buttons:
            b.selected = b.pick == self.look["tattoo"]
            b.draw(surf)
        self.random_btn.draw(surf)
        self.save_btn.draw(surf)
        self.back_btn.draw(surf)
        text(surf, "Free to change any time from the career screen", (W - 260, H - 45), 14, GREY, "midright")
