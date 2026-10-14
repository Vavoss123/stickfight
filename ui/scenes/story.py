"""Story scenes: Coach Ray talks you through the big moments of a career."""

import pygame

from engine import story

from ..common import W, H, CX, GOLD, WHITE, GREY, text, text_block, panel
from ..stickman import Figure
from .base import Scene

TYPE_SPEED = 45   # characters a second


class StoryScene(Scene):
    def __init__(self, app, career, beat, then):
        super().__init__(app)
        self.c = career
        self.lines = story.lines(beat, career.player, rival=career.rival)
        self.then = then
        self.k = 0
        self.shown = 0.0
        self.coach = Figure(300, 560, 1, (60, 60, 70), glove=(120, 120, 130), scale=1.5)
        self.coach.set_pose("ref", idle="ref")
        self.me = Figure(W - 300, 560, -1, career.player.color, glove=career.player.gloves or (214, 48, 49),
                         scale=1.5)
        self.me.set_pose("stance", idle="stance")

    def _advance(self):
        who, line = self.lines[self.k]
        if self.shown * TYPE_SPEED < len(line):
            self.shown = len(line) / TYPE_SPEED   # finish typing first
            return
        self.k += 1
        self.shown = 0.0
        if self.k >= len(self.lines):
            self.app.goto(self.then())
        else:
            self.app.sounds.play("click", 0.5)

    def handle(self, e):
        go = (e.type == pygame.KEYDOWN and e.key in (pygame.K_SPACE, pygame.K_RETURN))
        go = go or (e.type == pygame.MOUSEBUTTONDOWN and e.button == 1)
        if go:
            self._advance()
        elif e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
            self.app.goto(self.then())

    def update(self, dt):
        self.shown += dt
        self.coach.update(dt)
        self.me.update(dt)

    def draw(self, surf):
        surf.fill((12, 13, 18))
        # A gym: a heavy bag and a mat line
        pygame.draw.rect(surf, (30, 32, 40), (0, 560, W, H - 560))
        pygame.draw.line(surf, (70, 60, 50), (CX, 120), (CX, 260), 3)
        pygame.draw.rect(surf, (120, 40, 40), (CX - 34, 260, 68, 170), border_radius=24)
        self.coach.draw(surf)
        self.me.draw(surf)
        if self.k >= len(self.lines):
            return
        who, line = self.lines[self.k]
        r = panel(surf, (CX - 440, 40, 880, 150), (20, 22, 32), alpha=240, border=GOLD)
        text(surf, who.upper(), (r.x + 24, r.y + 16), 20, GOLD, bold=True)
        typed = line[:int(self.shown * TYPE_SPEED)]
        text_block(surf, typed, (r.x + 24, r.y + 50), 22, r.w - 48, WHITE, "topleft")
        text(surf, f"{self.k + 1} / {len(self.lines)}   SPACE to go on, ESC to skip", (r.right - 20, r.bottom - 26),
             13, GREY, "topright")
