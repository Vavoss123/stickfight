"""Choice cards: a crossroads between fights, dealt at the career hub."""

import pygame

from engine import story, choices

from ..common import W, H, CX, GOLD, WHITE, GREY, text, text_block, panel, Button
from ..stickman import Figure
from .base import Scene

OPTION_W = 560
OPTION_H = 64


class ChoiceScene(Scene):
    music = "keep"

    def __init__(self, app, career, cid, then):
        super().__init__(app)
        self.c = career
        self.cid = cid
        self.d = choices.CHOICES[cid]
        self.then = then
        self.response = None
        color, hands = story.CHARACTERS.get(self.d["speaker"], story.CHARACTERS[story.RAY])
        self.who = Figure(280, 560, 1, color, glove=hands, scale=1.5)
        self.who.set_pose("ref", idle="ref")
        self.me = Figure(W - 280, 560, -1, career.player.color,
                         glove=career.player.gloves or (214, 48, 49), scale=1.5).dress(career.player)
        self.me.set_pose("stance", idle="stance")
        self.buttons = []
        n = len(self.d["options"])
        top = 300 - (n * (OPTION_H + 14)) // 2
        for k, opt in enumerate(self.d["options"]):
            b = Button((CX - OPTION_W // 2, top + k * (OPTION_H + 14), OPTION_W, OPTION_H),
                       opt["label"], key=str(k + 1), sub=opt["blurb"], size=20)
            b.pick = k
            self.buttons.append(b)

    def _take(self, k):
        self.response = self.c.apply_choice(self.cid, k)
        self.c.save()
        self.app.sounds.play("click", 0.7)

    def handle(self, e):
        if self.response is not None:
            done = (e.type == pygame.KEYDOWN and e.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_ESCAPE))
            done = done or (e.type == pygame.MOUSEBUTTONDOWN and e.button == 1)
            if done:
                self.app.goto(self.then())
            return
        for b in self.buttons:
            if b.handle(e):
                self._take(b.pick)
                return
        if e.type == pygame.KEYDOWN and pygame.K_1 <= e.key <= pygame.K_1 + len(self.buttons) - 1:
            self._take(e.key - pygame.K_1)

    def update(self, dt):
        self.who.update(dt)
        self.me.update(dt)

    def draw(self, surf):
        surf.fill((12, 13, 18))
        pygame.draw.rect(surf, (30, 32, 40), (0, 560, W, H - 560))
        pygame.draw.line(surf, (70, 60, 50), (CX, 120), (CX, 260), 3)
        pygame.draw.rect(surf, (120, 40, 40), (CX - 34, 260, 68, 170), border_radius=24)
        self.who.draw(surf)
        self.me.draw(surf)
        text(surf, self.d["speaker"].upper(), (self.who.x, 580), 14, GOLD, "midtop", bold=True)
        first = self.c.player.name.split()[0] if self.c.player.name else "YOU"
        text(surf, first.upper(), (self.me.x, 580), 14, GREY, "midtop", bold=True)
        r = panel(surf, (CX - 440, 40, 880, 150), (20, 22, 32), alpha=240, border=GOLD)
        text(surf, self.d["title"].upper(), (r.x + 24, r.y + 16), 20, GOLD, bold=True)
        if self.response is None:
            text_block(surf, self.d["intro"], (r.x + 24, r.y + 50), 22, r.w - 48, WHITE, "topleft")
            for b in self.buttons:
                b.draw(surf)
            text(surf, "Press 1-3 or click", (CX, H - 40), 14, GREY, "midtop")
        else:
            text_block(surf, self.response, (r.x + 24, r.y + 50), 22, r.w - 48, WHITE, "topleft")
            text(surf, "SPACE to go on", (r.right - 20, r.bottom - 26), 13, GREY, "topright")
