"""The gym: pad work with Coach Ray.

A marker sweeps along a bar. Hit SPACE (or click, or A on a pad) while it is inside the
target. Eight reps, each one faster with a smaller target. Good sessions earn a deck
point. A session costs money, more the bigger your deck already is.
"""

import math
import random

import pygame

from engine.career import GYM_REPS

from ..common import W, H, CX, GOLD, WHITE, GREY, GREEN, RED, text, text_block, panel, Button
from ..stickman import Figure
from .base import Scene

BAR = pygame.Rect(CX - 360, 470, 720, 40)
SHOUTS_HIT = ["Good!", "Again!", "There it is!", "Sharp!", "Yes!"]
SHOUTS_MISS = ["Late!", "Early!", "Focus!", "Come on!", "Watch the pad!"]


class GymScene(Scene):
    def __init__(self, app, career, back):
        super().__init__(app)
        self.c = career
        self.back_to = back
        self.rng = random.Random()
        self.state = "ready"          # ready, rep, between, done
        self.rep = 0
        self.hits = 0
        self.t = 0.0
        self.shout = ""
        self.result = ""
        self.me = Figure(CX - 120, 400, 1, career.player.color, glove=career.player.gloves or RED,
                         scale=1.3).dress(career.player)
        self.me.set_pose("stance", idle="stance")
        self.coach = Figure(CX + 120, 400, -1, (60, 60, 70), glove=(230, 200, 60), scale=1.3)
        self.coach.set_pose("block", idle="block")   # holding the pads up
        self.start_btn = Button((CX - 150, H - 110, 300, 56), "", size=20, color=(150, 110, 30))
        self.back = Button((20, H - 56, 120, 40), "Back", size=18)
        self._new_target()

    def _new_target(self):
        """Smaller and faster every rep."""
        k = self.rep
        self.width = max(0.07, 0.22 - k * 0.02)
        self.centre = self.rng.uniform(0.2 + self.width, 0.8 - self.width)
        self.speed = 0.55 + k * 0.12          # sweeps a second
        self.pos = 0.0

    def _marker(self):
        return 0.5 - 0.5 * math.cos(self.pos * math.pi * 2)   # back and forth

    def _hit(self):
        x = self._marker()
        good = abs(x - self.centre) <= self.width / 2
        self.hits += good
        self.shout = self.rng.choice(SHOUTS_HIT if good else SHOUTS_MISS)
        self.me.play([("cross_wind", 0.08), ("cross", 0.12), ("stance", 0.2)], idle="stance")
        self.coach.hit(0.6 if good else 0.2)
        self.app.sounds.play("punch" if good else "jab")
        self.rep += 1
        if self.rep >= GYM_REPS:
            self.result = self.c.gym_reward(self.hits)
            self.c.save()
            self.state = "done"
            self.app.sounds.play("levelup" if self.hits >= 5 else "boo", 0.6)
        else:
            self.state = "between"
            self.t = 0.0

    def handle(self, e):
        press = e.type == pygame.KEYDOWN and e.key in (pygame.K_SPACE, pygame.K_RETURN)
        press = press or (e.type == pygame.MOUSEBUTTONDOWN and e.button == 1
                          and not self.back.rect.collidepoint(e.pos))
        if self.back.handle(e) or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
            if self.state in ("ready", "done"):
                self.app.goto(self.back_to())
            return
        if self.state == "ready":
            if (self.start_btn.handle(e) or press) and self.c.start_gym():
                self.c.save()
                self.state = "rep"
                self.app.sounds.play("bell", 0.5)
        elif self.state == "rep" and press:
            self._hit()
        elif self.state == "done" and press:
            self.app.goto(self.back_to())

    def update(self, dt):
        self.me.update(dt)
        self.coach.update(dt)
        if self.state == "rep":
            self.pos += dt * self.speed
        elif self.state == "between":
            self.t += dt
            if self.t > 0.7:
                self._new_target()
                self.state = "rep"

    def draw(self, surf):
        surf.fill((12, 13, 18))
        pygame.draw.rect(surf, (30, 32, 40), (0, 400, W, H - 400))
        text(surf, "THE GYM", (CX, 20), 46, WHITE, "midtop", display=True)
        text(surf, "Pad work with Coach Ray. Hit SPACE when the marker is in the gold zone.", (CX, 78), 17,
             GREY, "midtop")
        self.me.draw(surf)
        self.coach.draw(surf)
        c = self.c
        if self.state == "ready":
            r = panel(surf, (CX - 300, 120, 600, 150), (20, 22, 32), alpha=235, border=GOLD)
            text(surf, f"A session costs ${c.gym_price():,}", (r.centerx, r.y + 16), 22, GOLD, "midtop", bold=True)
            text_block(surf, f"{GYM_REPS} reps. Hit 7 or more for a deck point (all {GYM_REPS} adds a "
                             "training point too), 5 or 6 for two training points, 3 or 4 for one. "
                             "The price goes up as your deck budget grows.", (r.centerx, r.y + 52), 15,
                       r.w - 40, WHITE)
            why = c.gym_open()
            self.start_btn.label = why or "Start the session"
            self.start_btn.enabled = why is None
            self.start_btn.draw(surf)
        else:
            text(surf, f"Rep {min(self.rep + 1, GYM_REPS)} of {GYM_REPS}    Hits {self.hits}", (CX, 120), 22,
                 WHITE, "midtop", bold=True)
            if self.shout:
                text(surf, self.shout, (CX + 120, 180), 30, GOLD, "midtop", display=True)
            pygame.draw.rect(surf, (40, 42, 54), BAR, border_radius=8)
            zx = BAR.x + int((self.centre - self.width / 2) * BAR.w)
            pygame.draw.rect(surf, GOLD, (zx, BAR.y, int(self.width * BAR.w), BAR.h), border_radius=6)
            if self.state == "rep":
                mx = BAR.x + int(self._marker() * BAR.w)
                pygame.draw.rect(surf, WHITE, (mx - 4, BAR.y - 10, 8, BAR.h + 20), border_radius=3)
            pygame.draw.rect(surf, (0, 0, 0), BAR, 2, border_radius=8)
            if self.state == "done":
                r = panel(surf, (CX - 320, 540, 640, 110), (20, 22, 32), alpha=240, border=GREEN)
                text(surf, f"COACH RAY: {self.hits} out of {GYM_REPS}.", (r.x + 20, r.y + 14), 18, GOLD, bold=True)
                text_block(surf, self.result, (r.x + 20, r.y + 44), 16, r.w - 40, WHITE, "topleft")
                text(surf, "SPACE to go back", (r.right - 16, r.bottom - 22), 13, GREY, "topright")
        if self.state in ("ready", "done"):
            self.back.draw(surf)
