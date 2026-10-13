"""Pick both fighters, the difficulty and the number of rounds."""

import pygame

from engine.constants import STAT_NAMES
from engine.cards import signature_names
from engine.loadouts import Loadout, apply_saved
from engine.roster import quick_fighters, division, ARCHETYPE_BLURB

from ..common import (W, H, CX, RED, BLUE, GOLD, WHITE, GREY, CORNER, text, text_block, wrap,
                      panel, Button, bar)
from ..stickman import Figure
from .base import Scene
from .fight import FightConfig

LEVELS = ["easy", "normal", "hard"]


class SelectScene(Scene):
    def __init__(self, app, mode):
        super().__init__(app)
        self.mode = mode
        self.roster = quick_fighters() + division()
        self.defaults = [(dict(p.deck), list(p.perks)) for p in self.roster]
        apply_saved(self.roster)
        self.sel = [0, 1]
        self.level = 1
        self.rounds = 3
        self.figs = [Figure(250, 400, 1, (0, 0, 0), glove=RED, scale=0.72),
                     Figure(W - 250, 400, -1, (0, 0, 0), glove=BLUE, scale=0.72)]
        for f in self.figs:
            f.set_pose("stance", idle="stance")
        self.lists = [[], []]
        for side in (0, 1):
            x = 20 if side == 0 else W - 20 - 300
            for k, p in enumerate(self.roster):
                b = Button((x, 96 + k * 34, 300, 30), f"{p.name}", size=16)
                b.pick = k
                self.lists[side].append(b)
        self.opts = []
        y = 560
        if mode == "ai":
            for k, lv in enumerate(LEVELS):
                b = Button((CX - 165 + k * 112, y, 104, 40), lv.capitalize(), size=18)
                b.pick = ("level", k)
                self.opts.append(b)
        for k, n in enumerate((3, 5)):
            b = Button((CX - 110 + k * 112, y + 50, 104, 36), f"{n} rounds", size=16)
            b.pick = ("rounds", n)
            self.opts.append(b)
        self.start = Button((CX - 130, H - 62, 260, 50), "FIGHT", color=(170, 40, 40), size=26)
        self.back = Button((20, H - 56, 120, 40), "Back", size=18)
        # The computer picks its own cards, so in quick fight only red gets a deck button
        self.deck_buttons = []
        for i in ((0,) if mode == "ai" else (0, 1)):
            x = 340 if i == 0 else CX + 20
            b = Button((x + 30, 514, 220, 30), "Edit deck", size=16, color=(60, 50, 110))
            b.pick = i
            self.deck_buttons.append(b)

    def _edit_deck(self, side):
        from .deck import DeckScene
        k = self.sel[side]
        self.app.sounds.play("click")
        self.app.goto(DeckScene(self.app, Loadout(self.roster[k], self.defaults[k]), lambda: self))

    def _refresh(self):
        for side in (0, 1):
            for b in self.lists[side]:
                b.selected = b.pick == self.sel[side]
        for b in self.opts:
            kind, v = b.pick
            b.selected = (kind == "level" and v == self.level) or (kind == "rounds" and v == self.rounds)
        for i in (0, 1):
            self.figs[i].shorts = self.roster[self.sel[i]].color

    def _start(self):
        import copy
        p0 = copy.deepcopy(self.roster[self.sel[0]])
        p1 = copy.deepcopy(self.roster[self.sel[1]])
        if p0.color == p1.color:
            p1.color = tuple(255 - c for c in p1.color)
        cfg = FightConfig(p0, p1, mode=self.mode, level=LEVELS[self.level], rounds=self.rounds,
                          event="Main event")
        from .walkout import WalkoutScene
        self.app.goto(WalkoutScene(self.app, cfg))

    def handle(self, e):
        for side in (0, 1):
            for b in self.lists[side]:
                if b.handle(e):
                    self.sel[side] = b.pick
                    self.app.sounds.play("click")
        for b in self.opts:
            if b.handle(e):
                kind, v = b.pick
                if kind == "level":
                    self.level = v
                else:
                    self.rounds = v
                self.app.sounds.play("click")
        for b in self.deck_buttons:
            if b.handle(e):
                self._edit_deck(b.pick)
                return
        if self.start.handle(e):
            self._start()
        if self.back.handle(e) or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
            from .menu import MenuScene
            self.app.goto(MenuScene(self.app))
        if e.type == pygame.KEYDOWN:
            n = len(self.roster)
            if e.key == pygame.K_RETURN:
                self._start()
            elif e.key == pygame.K_w:
                self.sel[0] = (self.sel[0] - 1) % n
            elif e.key == pygame.K_s:
                self.sel[0] = (self.sel[0] + 1) % n
            elif e.key == pygame.K_UP:
                self.sel[1] = (self.sel[1] - 1) % n
            elif e.key == pygame.K_DOWN:
                self.sel[1] = (self.sel[1] + 1) % n

    def update(self, dt):
        self._refresh()
        for f in self.figs:
            f.update(dt)

    def draw(self, surf):
        surf.fill((14, 15, 22))
        title = "QUICK FIGHT" if self.mode == "ai" else "LOCAL 2 PLAYER"
        text(surf, title, (CX, 20), 44, WHITE, "midtop", display=True)
        sub = "You are red. Pick your opponent in blue." if self.mode == "ai" else \
            "Red uses Q W E A S D, blue uses U I O J K L"
        text(surf, sub, (CX, 70), 17, GREY, "midtop")
        for side in (0, 1):
            for b in self.lists[side]:
                b.draw(surf)
        # Fighter cards in the middle
        for i in (0, 1):
            p = self.roster[self.sel[i]]
            x = 340 if i == 0 else CX + 20
            rect = panel(surf, (x, 104, 280, 446), (22, 24, 34), border=CORNER[i])
            inner = rect.w - 24
            text(surf, p.name.upper(), (rect.centerx, rect.y + 12), 24, WHITE, "midtop", display=True,
                 max_width=inner)
            text(surf, f'"{p.nickname}"', (rect.centerx, rect.y + 44), 16, GOLD, "midtop", max_width=inner)
            text(surf, f"{p.archetype}, {p.record()}", (rect.centerx, rect.y + 66), 16, GREY, "midtop",
                 max_width=inner)
            self.figs[i].x = rect.centerx
            self.figs[i].y = rect.y + 196
            self.figs[i].draw(surf)
            yy = rect.y + 214
            for s in STAT_NAMES:
                v = p.stats.get(s)
                text(surf, s.capitalize(), (rect.x + 16, yy), 15, GREY)
                bar(surf, (rect.x + 110, yy + 3, 150, 12), v / 10, CORNER[i])
                yy += 22
            blurb = ARCHETYPE_BLURB.get(p.archetype, "")
            yy = text_block(surf, blurb, (rect.centerx, yy + 4), 13, inner, GREY, line_gap=1)
            sigs = signature_names(p)
            if sigs:
                lines = wrap("Cards: " + ", ".join(sigs), 13, inner)
                if len(lines) > 2:
                    lines = lines[:2]
                    lines[1] = lines[1].rstrip(",") + "..."
                yy += 4
                for ln in lines:
                    yy = text(surf, ln, (rect.centerx, yy), 13, (210, 190, 255), "midtop").bottom + 1
        text(surf, "VS", (CX, 300), 40, GOLD, "center", display=True)
        if self.mode == "ai":
            text(surf, "Difficulty", (CX - 230, 570), 16, GREY, "topright")
        text(surf, "Length", (CX - 120, 618), 16, GREY, "topright")
        for b in self.opts:
            b.draw(surf)
        for b in self.deck_buttons:
            b.draw(surf)
        self.start.draw(surf)
        self.back.draw(surf)
