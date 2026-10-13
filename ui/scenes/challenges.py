"""Challenges: the daily challenge, achievements and the secret fighters."""

from datetime import date

import pygame

from engine import achievements, daily
from engine.roster import quick_fighters, division, UNLOCKABLES

from ..common import W, H, CX, RED, BLUE, GOLD, WHITE, GREY, GREEN, text, text_block, panel, Button
from .base import Scene
from .fight import FightConfig


def start_daily(app):
    ch = daily.today(quick_fighters() + division())

    def done(app, fight):
        score = ch.score(fight)
        best = daily.record(ch.day, score)
        got = []
        if score > 0:
            got.append("daily")
            if daily.streak(ch.day) >= 3:
                got.append("streak")
        app.award(got)
        msg = (f"Scored {score:,}. Your best today is {best:,}." if score else
               "No score this time. You can try again as often as you like.")
        app.goto(ChallengesScene(app, msg))

    cfg = FightConfig(ch.me, ch.opp, mode="ai", level=ch.level, rounds=ch.rounds, on_done=done,
                      event="Daily challenge", start=ch.start())
    from .walkout import WalkoutScene
    app.goto(WalkoutScene(app, cfg, f"Daily challenge: {ch.twist[1]}"))


class ChallengesScene(Scene):
    def __init__(self, app, message=""):
        super().__init__(app)
        self.message = message
        self.ch = daily.today(quick_fighters() + division())
        self.best = daily.load().get(self.ch.day.isoformat(), 0)
        self.streak = daily.streak(date.today())
        self.fight = Button((60, 520, 340, 56), "FIGHT", color=(170, 40, 40), size=26)
        self.back = Button((20, H - 56, 120, 40), "Back", size=18)

    def handle(self, e):
        if self.fight.handle(e) or (e.type == pygame.KEYDOWN and e.key == pygame.K_RETURN):
            self.app.sounds.play("click")
            start_daily(self.app)
            return
        if self.back.handle(e) or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
            from .menu import MenuScene
            self.app.goto(MenuScene(self.app))

    def draw(self, surf):
        surf.fill((14, 15, 22))
        text(surf, "CHALLENGES", (CX, 18), 46, WHITE, "midtop", display=True)
        self._draw_daily(surf)
        self._draw_achievements(surf)
        self._draw_secrets(surf)
        self.back.draw(surf)

    def _draw_daily(self, surf):
        ch = self.ch
        r = panel(surf, (30, 84, 400, 560), (22, 24, 34), border=GOLD)
        text(surf, "DAILY CHALLENGE", (r.centerx, r.y + 14), 18, GOLD, "midtop", bold=True)
        text(surf, ch.day.strftime("%A %d %B"), (r.centerx, r.y + 38), 15, GREY, "midtop")
        text(surf, ch.me.name.upper(), (r.centerx, r.y + 72), 26, RED, "midtop", display=True,
             max_width=r.w - 30)
        text(surf, f"{ch.me.weight} {ch.me.archetype}", (r.centerx, r.y + 104), 15, GREY, "midtop")
        text(surf, "VS", (r.centerx, r.y + 128), 20, GOLD, "midtop", display=True)
        text(surf, ch.opp.name.upper(), (r.centerx, r.y + 156), 26, BLUE, "midtop", display=True,
             max_width=r.w - 30)
        text(surf, f"{ch.opp.weight} {ch.opp.archetype}", (r.centerx, r.y + 188), 15, GREY, "midtop")
        tw = panel(surf, (r.x + 20, r.y + 222, r.w - 40, 110), (40, 34, 14), alpha=230)
        text(surf, ch.twist[1].upper(), (tw.centerx, tw.y + 12), 20, GOLD, "midtop", bold=True)
        text_block(surf, ch.twist[2], (tw.centerx, tw.y + 42), 15, tw.w - 30, WHITE)
        text(surf, f"{ch.rounds} rounds, hard AI. Win to score.", (r.centerx, r.y + 346), 15, GREY, "midtop")
        text(surf, f"Best today: {self.best:,}" if self.best else "Not won yet today",
             (r.centerx, r.y + 376), 18, GREEN if self.best else WHITE, "midtop", bold=True)
        text(surf, f"Streak: {self.streak} day{'s' if self.streak != 1 else ''}", (r.centerx, r.y + 402),
             16, GOLD if self.streak else GREY, "midtop")
        self.fight.rect.x = r.x + 30
        self.fight.rect.y = r.y + 436
        self.fight.draw(surf)
        if self.message:
            text_block(surf, self.message, (r.centerx, r.y + 502), 14, r.w - 30, WHITE, bold=True)

    def _draw_achievements(self, surf):
        rec = self.app.record
        r = panel(surf, (450, 84, 800, 400), (22, 24, 34))
        got = len(rec.unlocked)
        text(surf, f"ACHIEVEMENTS  {got} / {len(achievements.LIST)}", (r.x + 20, r.y + 14), 18, GOLD, bold=True)
        for k, (aid, name, desc) in enumerate(achievements.LIST):
            col, row = k % 2, k // 2
            x, y = r.x + 20 + col * 390, r.y + 46 + row * 38
            have = rec.has(aid)
            pygame.draw.circle(surf, GOLD if have else (60, 62, 74), (x + 8, y + 12), 7)
            text(surf, name, (x + 24, y), 15, WHITE if have else GREY, bold=have, max_width=350)
            text(surf, desc, (x + 24, y + 18), 12, (200, 200, 210) if have else (110, 112, 124),
                 max_width=350)

    def _draw_secrets(self, surf):
        rec = self.app.record
        r = panel(surf, (450, 498, 800, 146), (22, 24, 34))
        text(surf, "SECRET FIGHTERS", (r.x + 20, r.y + 12), 18, GOLD, bold=True)
        for k, (aid, build) in enumerate(UNLOCKABLES):
            x = r.x + 20 + k * 192
            box = pygame.Rect(x, r.y + 44, 180, 88)
            have = rec.has(aid)
            pygame.draw.rect(surf, (36, 40, 56) if have else (26, 28, 38), box, border_radius=8)
            if have:
                p = build()
                text(surf, p.name, (box.centerx, box.y + 12), 16, GOLD, "midtop", bold=True, max_width=170)
                text(surf, f"{p.weight} {p.archetype}", (box.centerx, box.y + 36), 13, GREY, "midtop",
                     max_width=170)
                text(surf, "Unlocked", (box.centerx, box.y + 60), 13, GREEN, "midtop", bold=True)
            else:
                text(surf, "???", (box.centerx, box.y + 10), 22, GREY, "midtop", display=True)
                text_block(surf, achievements.NAMES[aid], (box.centerx, box.y + 46), 13, 170, GREY)
