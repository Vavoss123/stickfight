"""The gym: a drill with Coach Ray.

The gym is free, one session between fights. Coach Ray picks one of several drills at
random (pad work, catching balls, mitt work, a bell drill, combos, see ui/gym_games.py).
Every one is eight reps and scores hits out of eight, so a good session earns a deck
point whichever drill comes up. The bigger your deck budget (your rank plus any bonus
points), the harder the drills get.
"""

import random

import pygame

from engine.career import GYM_REPS

from .. import gym_games
from ..common import W, H, CX, GOLD, WHITE, GREY, GREEN, RED, text, text_block, panel, Button
from ..stickman import Figure
from .base import Scene

LAST = [None]     # the drill you did last time, so it is not the same one twice running


class GymScene(Scene):
    def __init__(self, app, career, back):
        super().__init__(app)
        self.c = career
        self.back_to = back
        self.rng = random.Random()
        self.state = "ready"          # ready, play, done
        self.drill = None
        self.finish_wait = 0.0
        self.result = ""
        self.me = Figure(CX - 120, 400, 1, career.player.color, glove=career.player.gloves or RED,
                         scale=1.3).dress(career.player)
        self.me.set_pose("stance", idle="stance")
        self.coach = Figure(CX + 120, 400, -1, (60, 60, 70), glove=(230, 200, 60), scale=1.3)
        self.coach.set_pose("block", idle="block")   # holding the pads up
        self.start_btn = Button((CX - 150, H - 110, 300, 56), "", size=20, color=(150, 110, 30))
        self.back = Button((20, H - 56, 120, 40), "Back", size=18)

    def _start(self):
        self.drill = gym_games.pick(self.rng, LAST[0], self.c.gym_level())
        LAST[0] = type(self.drill)
        self.state = "play"
        self.app.sounds.play("bell", 0.5)

    def _events(self):
        """What the drill wants shown: punches, the coach's moves and the sounds."""
        d = self.drill
        for kind, what in d.events:
            if kind == "hit":
                self.me.play([("cross_wind", 0.08), ("cross", 0.12), ("stance", 0.2)], idle="stance")
                self.coach.hit(0.6 if what else 0.2)
                self.app.sounds.play("punch" if what else "jab")
            elif kind == "coach":
                self.coach.play([(what, 0.12), (what, 0.18), ("block", 0.2)], idle="block")
            elif kind == "me":
                self.me.play([(what, 0.1), (what, 0.14), ("stance", 0.2)], idle="stance")
        d.events = []

    def handle(self, e):
        if self.back.handle(e) or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
            if self.state in ("ready", "done"):
                self.app.goto(self.back_to())
            return
        press = gym_games.pressed(e) and not (e.type == pygame.MOUSEBUTTONDOWN
                                              and self.back.rect.collidepoint(e.pos))
        if self.state == "ready":
            if (self.start_btn.handle(e) or press) and self.c.start_gym():
                self.c.save()
                self._start()
        elif self.state == "play":
            self.drill.handle(e)
        elif self.state == "done" and press:
            self.app.goto(self.back_to())

    def update(self, dt):
        self.me.update(dt)
        self.coach.update(dt)
        if self.state != "play":
            return
        d = self.drill
        d.update(dt)
        self._events()
        if d.finished:
            self.finish_wait += dt
            if self.finish_wait > 1.0:
                self.result = self.c.gym_reward(d.hits)
                self.c.save()
                self.state = "done"
                self.app.sounds.play("levelup" if d.hits >= 5 else "boo", 0.6)

    def draw(self, surf):
        surf.fill((12, 13, 18))
        pygame.draw.rect(surf, (30, 32, 40), (0, 400, W, H - 400))
        text(surf, "THE GYM", (CX, 20), 46, WHITE, "midtop", display=True)
        d = self.drill
        sub = f"{d.name}: {d.blurb}" if d else "Coach Ray picks a drill at random."
        text(surf, sub, (CX, 78), 17, GREY, "midtop", max_width=W - 80)
        self.me.draw(surf)
        self.coach.draw(surf)
        c = self.c
        if self.state == "ready":
            r = panel(surf, (CX - 300, 120, 600, 170), (20, 22, 32), alpha=235, border=GOLD)
            text(surf, f"Free session. Difficulty: {c.gym_tier()}", (r.centerx, r.y + 16), 22, GOLD, "midtop",
                 bold=True)
            text_block(surf, f"Coach Ray picks a drill at random. {GYM_REPS} reps, score out of {GYM_REPS}. "
                             f"7 or more is a deck point (all {GYM_REPS} adds a training point too), 5 or 6 is "
                             "two training points, 3 or 4 is one. The bigger your deck budget, rank and bonus "
                             "points, the tougher the drills.", (r.centerx, r.y + 52), 15, r.w - 40, WHITE)
            why = c.gym_open()
            self.start_btn.label = why or "Start the session"
            self.start_btn.enabled = why is None
            self.start_btn.draw(surf)
        else:
            text(surf, d.status(), (CX, 120), 22, WHITE, "midtop", bold=True)
            if d.shout:
                text(surf, d.shout, (CX + 120, 180), 30, GOLD, "midtop", display=True)
            d.draw(surf)
            if self.state == "done":
                r = panel(surf, (CX - 320, 540, 640, 110), (20, 22, 32), alpha=240, border=GREEN)
                text(surf, f"COACH RAY: {d.hits} out of {GYM_REPS}.", (r.x + 20, r.y + 14), 18, GOLD, bold=True)
                text_block(surf, self.result, (r.x + 20, r.y + 44), 16, r.w - 40, WHITE, "topleft")
                text(surf, "SPACE to go back", (r.right - 16, r.bottom - 22), 13, GREY, "topright")
        if self.state in ("ready", "done"):
            self.back.draw(surf)
