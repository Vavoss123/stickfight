"""Training camp before title fights, retirement, and the hall of fame."""

import pygame

from engine.career import CAMPS
from engine.constants import STAT_MAX
from engine import legacy

from ..common import W, H, CX, RED, GOLD, WHITE, GREY, GREEN, text, text_block, panel, Button
from ..stickman import Figure
from .base import Scene


class CampScene(Scene):
    """Pick a camp: +1 to one stat for the coming title fight."""

    def __init__(self, app, career, then, back):
        super().__init__(app)
        self.c = career
        self.then = then
        self.back_to = back
        self.buttons = []
        for k, (stat, (name, blurb)) in enumerate(CAMPS.items()):
            b = Button((CX - 595 + k * 240, 260, 226, 200), name, sub=blurb, size=22,
                       color=(50, 56, 80))
            b.pick = stat
            self.buttons.append(b)
        self.back = Button((20, H - 56, 120, 40), "Back", size=18)
        self.focus = 0

    def _choose(self, stat):
        self.c.camp = stat
        self.c.save()
        self.app.sounds.play("levelup")
        self.then()

    def handle(self, e):
        for k, b in enumerate(self.buttons):
            if b.handle(e):
                self._choose(b.pick)
                return
            if e.type == pygame.MOUSEMOTION and b.hover:
                self.focus = k
        if self.back.handle(e) or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
            self.app.goto(self.back_to())
            return
        if e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_LEFT, pygame.K_a):
                self.focus = (self.focus - 1) % len(self.buttons)
            elif e.key in (pygame.K_RIGHT, pygame.K_d):
                self.focus = (self.focus + 1) % len(self.buttons)
            elif e.key == pygame.K_RETURN:
                self._choose(self.buttons[self.focus].pick)

    def draw(self, surf):
        surf.fill((14, 15, 22))
        text(surf, "TRAINING CAMP", (CX, 40), 52, WHITE, "midtop", display=True)
        opp = self.c.next_fight()[0]
        text(surf, f"Eight weeks out from {opp.name}. Where do you spend them?", (CX, 112), 19, GREY,
             "midtop")
        text(surf, "A stat camp adds 1 for this fight only, even past 10.", (CX, 140), 16, GOLD, "midtop")
        p = self.c.player
        for k, b in enumerate(self.buttons):
            b.selected = k == self.focus
            b.draw(surf)
            if b.pick == "film":
                note, sub = "A read and 45 momentum", "to start the fight"
            else:
                v = p.stats.get(b.pick)
                note = f"{b.pick.capitalize()} {v} > {v + 1}"
                sub = "past the usual max for this fight" if v >= STAT_MAX else "for this fight"
            text(surf, note, (b.rect.centerx, b.rect.bottom + 14), 17, GREEN, "midtop", bold=True)
            text(surf, sub, (b.rect.centerx, b.rect.bottom + 36), 13, GREY, "midtop")
        self.back.draw(surf)


class RetireScene(Scene):
    """The send off, then the hall of fame."""

    def __init__(self, app, entry):
        super().__init__(app)
        self.e = entry
        self.fig = Figure(250, 470, 1, tuple(entry["color"]), glove=RED, scale=1.4)
        self.fig.set_pose("victory" if entry["inducted"] else "stance",
                          idle="victory" if entry["inducted"] else "stance")
        self.next = Button((CX - 140, H - 86, 280, 54), "Hall of fame", color=(150, 110, 30), size=22)
        app.sounds.play("roar" if entry["inducted"] else "crowd", 0.8)

    def handle(self, e):
        if self.next.handle(e) or (e.type == pygame.KEYDOWN and e.key in (pygame.K_RETURN, pygame.K_SPACE)):
            from .menu import MenuScene
            self.app.goto(HallScene(self.app, lambda: MenuScene(self.app), highlight=self.e))

    def update(self, dt):
        self.fig.update(dt)

    def draw(self, surf):
        surf.fill((14, 15, 22))
        e = self.e
        self.fig.draw(surf)
        text(surf, "THE FINAL BELL", (CX + 120, 60), 24, GREY, "midtop", bold=True)
        text(surf, e["name"].upper(), (CX + 120, 96), 64, WHITE, "midtop", display=True, max_width=760)
        if e["nickname"]:
            text(surf, f'"{e["nickname"]}"', (CX + 120, 168), 22, GOLD, "midtop")
        rows = [("Record", e["record"]), ("Finishes", str(e["finishes"])),
                ("World titles", str(e["titles"])), ("Most defences", str(e["defenses"])),
                ("Best ranking", legacy.best_rank_label(e["best_rank"])),
                ("Legacy score", str(e["score"]))]
        y = 230
        for label, v in rows:
            text(surf, label, (CX - 40, y), 22, GREY)
            text(surf, v, (CX + 360, y), 22, WHITE, "topright", bold=True)
            y += 40
        if e["inducted"]:
            text(surf, "INDUCTED INTO THE HALL OF FAME", (CX + 120, y + 20), 30, GOLD, "midtop", display=True)
        else:
            text_block(surf, f"A career to be proud of. The hall of fame takes a world title or a legacy "
                             f"score of {legacy.INDUCT_SCORE}.", (CX + 120, y + 20), 18, 600, GREY)
        self.next.draw(surf)


class HallScene(Scene):
    def __init__(self, app, back, highlight=None):
        super().__init__(app)
        self.back_to = back
        self.hall = legacy.load()
        self.highlight = highlight
        self.scroll = 0
        self.back = Button((20, H - 56, 120, 40), "Back", size=18)

    def handle(self, e):
        if self.back.handle(e) or (e.type == pygame.KEYDOWN and e.key in (pygame.K_ESCAPE, pygame.K_RETURN)):
            self.app.goto(self.back_to())
            return
        rows = max(0, len(self.hall) - 12)
        if e.type == pygame.MOUSEWHEEL:
            self.scroll = max(0, min(rows, self.scroll - e.y))
        if e.type == pygame.KEYDOWN and e.key in (pygame.K_DOWN, pygame.K_s):
            self.scroll = min(rows, self.scroll + 1)
        if e.type == pygame.KEYDOWN and e.key in (pygame.K_UP, pygame.K_w):
            self.scroll = max(0, self.scroll - 1)

    def draw(self, surf):
        surf.fill((14, 15, 22))
        text(surf, "HALL OF FAME", (CX, 26), 52, GOLD, "midtop", display=True)
        if not self.hall:
            text(surf, "Nobody has retired yet. Finish a career and it shows up here.", (CX, 300), 20,
                 GREY, "midtop")
            self.back.draw(surf)
            return
        r = panel(surf, (CX - 560, 110, 1120, 530), (22, 24, 34))
        cols = [("", 40), ("Fighter", 80), ("Style", 470), ("Record", 600), ("Titles", 720),
                ("Defences", 820), ("Best", 930), ("Legacy", 1040)]
        for label, x in cols:
            text(surf, label, (r.x + x, r.y + 14), 15, GREY, bold=True)
        y = r.y + 46
        for k, e in enumerate(self.hall[self.scroll:self.scroll + 12]):
            n = self.scroll + k + 1
            me = self.highlight is not None and e == self.highlight
            if me:
                pygame.draw.rect(surf, (70, 50, 20), (r.x + 10, y - 4, r.w - 20, 38), border_radius=6)
            col = GOLD if e.get("inducted") else WHITE
            text(surf, str(n), (r.x + 40, y), 18, GREY, bold=True)
            name = e["name"] + (f' "{e["nickname"]}"' if e.get("nickname") else "")
            text(surf, name, (r.x + 80, y), 18, col, bold=e.get("inducted"), max_width=370)
            text(surf, e.get("archetype", ""), (r.x + 470, y), 17, GREY)
            text(surf, e.get("record", ""), (r.x + 600, y), 17, WHITE)
            text(surf, str(e.get("titles", 0)), (r.x + 720, y), 17, WHITE)
            text(surf, str(e.get("defenses", 0)), (r.x + 820, y), 17, WHITE)
            text(surf, legacy.best_rank_label(e.get("best_rank")), (r.x + 930, y), 17, WHITE)
            text(surf, str(e.get("score", 0)), (r.x + 1040, y), 17, col, bold=True)
            y += 40
        text(surf, "Gold names are inducted. Scroll for more.", (CX, r.bottom + 10), 14, GREY, "midtop")
        self.back.draw(surf)
