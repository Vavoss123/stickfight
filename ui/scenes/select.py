"""Pick both fighters, the difficulty and the number of rounds."""

import pygame

import copy

from engine.constants import STAT_NAMES
from engine import sharecode
from engine.career import Career
from engine.cards import signature_names
from engine import personality
from engine.loadouts import Loadout, apply_saved
from engine.weights import get as get_weight, gap as weight_gap
from engine.roster import quick_fighters, division, ARCHETYPE_BLURB

from ..common import (W, H, CX, RED, BLUE, GOLD, WHITE, GREY, CORNER, text, text_block, wrap,
                      panel, Button, bar)
from ..stickman import Figure
from .base import Scene
from .fight import FightConfig

LEVELS = ["easy", "normal", "hard"]


class SelectScene(Scene):
    def __init__(self, app, mode, pick=None):
        super().__init__(app)
        self.mode = mode
        from engine.roster import unlocked
        # Your career fighter and friends' fighters from codes come first, with their own decks
        self.own = {}                 # roster index -> "you" or "code"
        mine = []
        career = Career.load()
        if career is not None:
            mine.append((copy.deepcopy(career.player), "you"))
        mine += [(p, "code") for _, p in sharecode.load_friends()]
        rest = quick_fighters() + division() + unlocked(set(app.record.unlocked))
        apply_saved(rest, pool=app.settings["card_pool"])
        self.roster = [p for p, _ in mine] + rest
        self.own = {k: tag for k, (_, tag) in enumerate(mine)}
        self.defaults = [(dict(p.deck), list(p.perks)) for p in self.roster]
        self.sel = [0, 1]
        if pick:
            # Just added by code: put them in blue
            k = next((k for k, p in enumerate(self.roster) if p.name == pick), None)
            if k is not None:
                self.sel = [0 if k != 0 else 1, k]
        self.level = 1
        self.rounds = 3
        self.figs = [Figure(250, 400, 1, (0, 0, 0), glove=RED, scale=0.72),
                     Figure(W - 250, 400, -1, (0, 0, 0), glove=BLUE, scale=0.72)]
        for f in self.figs:
            f.set_pose("stance", idle="stance")
        self.lists = [[], []]
        for side in (0, 1):
            x = 20 if side == 0 else W - 20 - 300
            step = min(34, 560 // len(self.roster))
            for k, p in enumerate(self.roster):
                tag = {"you": "  (you)", "code": "  (code)"}.get(self.own.get(k), "")
                b = Button((x, 96 + k * step, 300, step - 4), f"{p.name}{tag}", size=16 if step >= 30 else 14,
                           color=(40, 70, 60) if tag else (52, 58, 78))
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
        self.code_btn = Button((W - 320, H - 56, 300, 40), "Add fighter by code", size=17, color=(40, 90, 130))
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
        if k in self.own:
            return                    # career and code fighters bring their own deck
        self.app.sounds.play("click")
        lo = Loadout(self.roster[k], self.defaults[k], pool=self.app.settings["card_pool"])
        self.app.goto(DeckScene(self.app, lo, lambda: self))

    def _refresh(self):
        for side in (0, 1):
            for b in self.lists[side]:
                b.selected = b.pick == self.sel[side]
        for b in self.opts:
            kind, v = b.pick
            b.selected = (kind == "level" and v == self.level) or (kind == "rounds" and v == self.rounds)
        for i in (0, 1):
            p = self.roster[self.sel[i]]
            self.figs[i].dress(p)
            self.figs[i].scale = 0.64 * get_weight(p.weight)["size"]

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
        if self.code_btn.handle(e):
            from .share import CodeScene
            mode, app = self.mode, self.app
            self.app.sounds.play("click")
            self.app.goto(CodeScene(app, lambda p: app.goto(SelectScene(app, mode, pick=p.name)),
                                    lambda: SelectScene(app, mode)))
            return
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
            "Red uses Q W E R A S D F Z, blue uses U I O P J K L ; M"
        if self.mode != "ai" and self.app.pads.count:
            sub = ("Controller 1 is red, controller 2 is blue" if self.app.pads.count >= 2 else
                   "Red uses Q W E R A S D F Z, the controller plays blue")
        a, b = self.roster[self.sel[0]], self.roster[self.sel[1]]
        if a.weight != b.weight:
            heavy = a if weight_gap(a.weight, b.weight) > 0 else b
            lbs = abs(get_weight(a.weight)["lbs"] - get_weight(b.weight)["lbs"])
            text(surf, f"Catchweight bout: {heavy.name} is {lbs} lbs heavier", (CX, 70), 17,
                 (255, 170, 60), "midtop", bold=True)
        else:
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
            text(surf, f'"{p.nickname}"  {personality.label(p)}', (rect.centerx, rect.y + 44), 16, GOLD,
                 "midtop", max_width=inner)
            text(surf, f"{p.weight} {p.archetype}, {p.record()}", (rect.centerx, rect.y + 66), 16, GREY,
                 "midtop", max_width=inner)
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
            from engine import coach
            expect, _ = coach.scout(self.roster[self.sel[1]], self.roster[self.sel[0]], 0)
            if expect:
                text(surf, "Expect: " + expect[0], (CX + 20 + 140, 520), 13, (150, 200, 255), "midtop",
                     max_width=260)
        if self.mode == "ai":
            text(surf, "Difficulty", (CX - 230, 570), 16, GREY, "topright")
        text(surf, "Length", (CX - 120, 618), 16, GREY, "topright")
        for b in self.opts:
            b.draw(surf)
        for b in self.deck_buttons:
            own = self.own.get(self.sel[b.pick])
            b.enabled = own is None
            b.label = "Edit deck" if own is None else "Their own deck"
            b.draw(surf)
        self.start.draw(surf)
        self.back.draw(surf)
        self.code_btn.draw(surf)
