"""After the fight: the official result, scorecards and fight stats."""

import pygame

from ..arena import Arena
from ..common import W, H, CX, FLOOR_Y, RED, BLUE, GOLD, WHITE, GREY, CORNER, text, panel, Button
from ..choreo import SCALE
from ..stickman import Figure
from .base import Scene


class ResultScene(Scene):
    def __init__(self, app, fight, cfg):
        super().__init__(app)
        self.fight = fight
        self.cfg = cfg
        self.r = fight.result
        self.arena = Arena()
        self.t = 0.0
        profiles = (cfg.p0, cfg.p1)
        self.figs = []
        for i, p in enumerate(profiles):
            from .fight import size_of, gloves_of
            f = Figure(CX - 440 if i == 0 else CX + 440, FLOOR_Y, 1 if i == 0 else -1, p.color,
                       glove=gloves_of(p, CORNER[i]), scale=SCALE * size_of(p)).dress(p)
            if self.r.winner == i:
                f.set_pose("victory", idle="victory")
            elif self.r.winner is None:
                f.set_pose("stance", idle="stance")
            else:
                f.set_pose("tired", idle="tired")
            self.figs.append(f)
        self.buttons = []
        y = 650
        if cfg.on_done is None:
            b = Button((CX - 270, y, 260, 50), "Rematch")
            b.pick = "rematch"
            self.buttons.append(b)
            b = Button((CX + 10, y, 260, 50), "Main menu")
            b.pick = "menu"
            self.buttons.append(b)
        else:
            b = Button((CX - 130, y, 260, 50), "Continue", color=(150, 110, 30))
            b.pick = "continue"
            self.buttons.append(b)
        if self.r.winner is not None:
            app.sounds.play("crowd", 0.8)
        if cfg.mode == "ai" and not cfg.practice and hasattr(app, "award"):
            from engine import achievements
            app.award(achievements.for_fight(fight, 0, cfg.level, app.record))

    def _go(self, pick):
        if pick == "rematch":
            from .walkout import WalkoutScene
            self.app.goto(WalkoutScene(self.app, self.cfg))
        elif pick == "menu":
            from .menu import MenuScene
            self.app.goto(MenuScene(self.app))
        else:
            self.cfg.on_done(self.app, self.fight)

    def handle(self, e):
        for b in self.buttons:
            if b.handle(e):
                self._go(b.pick)
                return
        if e.type == pygame.KEYDOWN and e.key in (pygame.K_RETURN, pygame.K_SPACE) and self.t > 0.6:
            self._go(self.buttons[-1].pick if self.cfg.on_done else "menu")

    def update(self, dt):
        self.t += dt
        for f in self.figs:
            f.update(dt)
        self.arena.update(dt)

    def draw(self, surf):
        self.arena.draw(surf)
        if not hasattr(self, "dim"):
            self.dim = pygame.Surface((W, H), pygame.SRCALPHA)
            self.dim.fill((0, 0, 0, 140))
        surf.blit(self.dim, (0, 0))
        for f in self.figs:
            f.draw(surf)
        r = self.r
        p = (self.cfg.p0, self.cfg.p1)
        if r.winner is None:
            text(surf, "IT'S A DRAW", (CX, 40), 70, GOLD, "midtop", display=True)
        else:
            w = p[r.winner]
            text(surf, "AND THE WINNER", (CX, 30), 22, GREY, "midtop", bold=True)
            text(surf, w.name.upper(), (CX, 58), 70, CORNER[r.winner], "midtop", display=True,
                 max_width=W - 80)
        method = r.method if r.method in ("KO", "TKO", "Submission") else r.detail
        sub = f"{r.detail}" if r.method in ("KO", "TKO", "Submission") else ""
        line = f"{method}, round {r.round} at {r.time}" if r.method != "Decision" and r.method != "Draw" \
            else f"{method} after {r.round} rounds"
        text(surf, line, (CX, 140), 26, WHITE, "midtop", bold=True)
        if sub:
            text(surf, sub, (CX, 172), 20, GREY, "midtop")
        if self.fight.title and r.winner is not None:
            text(surf, "CHAMPION OF THE WORLD", (CX, 200), 22, GOLD, "midtop", bold=True)

        y = 236
        if r.cards:
            rect = panel(surf, (CX - 300, y, 600, 142), (12, 13, 20), alpha=230)
            text(surf, "SCORECARDS", (CX, y + 8), 16, GOLD, "midtop", bold=True)
            rounds = getattr(r, "by_round", []) or []
            for k, (a, b) in enumerate(r.cards):
                yy = y + 34 + k * 26
                text(surf, f"Judge {k + 1}", (CX - 280, yy), 17, GREY)
                if k < len(rounds):
                    for n, (ra, rb) in enumerate(rounds[k]):
                        rc = CORNER[0] if ra > rb else CORNER[1] if rb > ra else WHITE
                        text(surf, f"{ra}-{rb}", (CX - 170 + n * 62, yy + 2), 15, rc, bold=True)
                col = CORNER[0] if a > b else CORNER[1] if b > a else WHITE
                text(surf, f"{a} - {b}", (CX + 240, yy), 19, col, "midtop", bold=True)
            text(surf, "Each round goes on damage and strikes first, then takedowns and control.",
                 (CX, y + 116), 13, GREY, "midtop")
            y += 154

        f = self.fight
        t0, t1 = f.totals(0), f.totals(1)
        rows = [
            ("Strikes landed", f"{t0.landed}/{t0.thrown}", f"{t1.landed}/{t1.thrown}"),
            ("Damage dealt", f"{t0.dmg:.0f}", f"{t1.dmg:.0f}"),
            ("Takedowns", t0.takedowns, t1.takedowns),
            ("Knockdowns", t0.knockdowns, t1.knockdowns),
            ("Sub attempts", int(t0.sub_attempts), int(t1.sub_attempts)),
        ]
        rect = panel(surf, (CX - 230, y, 460, 40 + len(rows) * 28), (12, 13, 20), alpha=230)
        text(surf, p[0].name.split()[-1].upper(), (CX - 150, y + 10), 16, RED, "midtop", bold=True)
        text(surf, "FIGHT STATS", (CX, y + 10), 16, GOLD, "midtop", bold=True)
        text(surf, p[1].name.split()[-1].upper(), (CX + 150, y + 10), 16, BLUE, "midtop", bold=True)
        yy = y + 38
        for label, a, b in rows:
            text(surf, str(a), (CX - 150, yy), 19, WHITE, "midtop")
            text(surf, label, (CX, yy), 16, GREY, "midtop")
            text(surf, str(b), (CX + 150, yy), 19, WHITE, "midtop")
            yy += 28
        for b in self.buttons:
            b.draw(surf)
