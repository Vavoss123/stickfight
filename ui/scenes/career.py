"""Career: create a fighter, then a hub with training, rankings and the next fight."""

import pygame

from engine.career import Career, new_player, train_cost, delete_save
from engine.constants import STAT_NAMES, STAT_MAX
from engine.roster import ARCHETYPES, ARCHETYPE_BLURB, COLORS

from ..common import (W, H, CX, RED, BLUE, GOLD, WHITE, GREY, GREEN, text, panel, Button, bar,
                      font)
from ..stickman import Figure
from .base import Scene
from .fight import FightConfig

LEVEL_NAME = {"easy": "Easy", "normal": "Normal", "hard": "Hard"}


def open_career(app):
    c = Career.load()
    if c is None:
        app.goto(CreateScene(app))
    else:
        app.goto(HubScene(app, c))


class TextField:
    def __init__(self, rect, label, value="", limit=22):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.value = value
        self.limit = limit
        self.focus = False

    def handle(self, e):
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            self.focus = self.rect.collidepoint(e.pos)
        if not self.focus:
            return
        if e.type == pygame.TEXTINPUT:
            if len(self.value) < self.limit:
                self.value += e.text
        elif e.type == pygame.KEYDOWN and e.key == pygame.K_BACKSPACE:
            self.value = self.value[:-1]

    def draw(self, surf):
        text(surf, self.label, (self.rect.x, self.rect.y - 22), 15, GREY)
        pygame.draw.rect(surf, (30, 33, 46), self.rect, border_radius=6)
        pygame.draw.rect(surf, GOLD if self.focus else (0, 0, 0), self.rect, 2, border_radius=6)
        v = self.value + ("|" if self.focus and pygame.time.get_ticks() // 500 % 2 else "")
        text(surf, v, (self.rect.x + 10, self.rect.centery), 20, WHITE, "midleft", shadow=False)


class CreateScene(Scene):
    def __init__(self, app):
        super().__init__(app)
        self.fields = [
            TextField((90, 150, 360, 40), "Name", "", 22),
            TextField((90, 226, 360, 40), "Nickname", "", 18),
            TextField((90, 302, 360, 40), "Hometown", "", 28),
        ]
        self.fields[0].focus = True
        self.arch = "Striker"
        self.color = 0
        self.arch_buttons = []
        for k, a in enumerate(ARCHETYPES):
            b = Button((90 + (k % 2) * 184, 390 + (k // 2) * 56, 176, 48), a, size=20)
            b.pick = a
            self.arch_buttons.append(b)
        self.swatches = [pygame.Rect(90 + k * 45, 552, 36, 36) for k in range(len(COLORS))]
        self.start = Button((CX + 140, H - 80, 280, 54), "Start career", color=(170, 40, 40), size=24)
        self.back = Button((20, H - 70, 120, 40), "Back", size=18)
        self.fig = Figure(870, 470, 1, COLORS[0], glove=RED, scale=1.5)
        self.fig.set_pose("stance", idle="stance")
        self.error = ""
        pygame.key.start_text_input()

    def handle(self, e):
        for f in self.fields:
            f.handle(e)
        if e.type == pygame.KEYDOWN and e.key == pygame.K_TAB:
            k = next((i for i, f in enumerate(self.fields) if f.focus), -1)
            for f in self.fields:
                f.focus = False
            self.fields[(k + 1) % len(self.fields)].focus = True
        for b in self.arch_buttons:
            if b.handle(e):
                self.arch = b.pick
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            for k, r in enumerate(self.swatches):
                if r.collidepoint(e.pos):
                    self.color = k
        if self.start.handle(e) or (e.type == pygame.KEYDOWN and e.key == pygame.K_RETURN):
            self._create()
        if self.back.handle(e) or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
            from .menu import MenuScene
            self.app.goto(MenuScene(self.app))

    def _create(self):
        name = self.fields[0].value.strip()
        if len(name.split()) < 1 or len(name) < 2:
            self.error = "Give your fighter a name"
            return
        nick = self.fields[1].value.strip()
        town = self.fields[2].value.strip()
        p = new_player(name.title(), nick, self.arch, COLORS[self.color], town)
        c = Career(p)
        c.save()
        self.app.goto(HubScene(self.app, c, "Welcome to the show. Win two prospect fights to get ranked."))

    def update(self, dt):
        self.fig.shorts = COLORS[self.color]
        self.fig.update(dt)

    def draw(self, surf):
        surf.fill((14, 15, 22))
        text(surf, "CREATE YOUR FIGHTER", (CX, 26), 44, WHITE, "midtop", display=True)
        for f in self.fields:
            f.draw(surf)
        text(surf, "Style", (90, 368), 15, GREY)
        for b in self.arch_buttons:
            b.selected = b.pick == self.arch
            b.draw(surf)
        text(surf, ARCHETYPE_BLURB[self.arch], (90, 500), 16, WHITE, max_width=360)
        text(surf, "Shorts", (90, 530), 15, GREY)
        for k, r in enumerate(self.swatches):
            pygame.draw.rect(surf, COLORS[k], r, border_radius=6)
            pygame.draw.rect(surf, GOLD if k == self.color else (0, 0, 0), r, 3, border_radius=6)
        rect = panel(surf, (640, 110, 520, 500), (22, 24, 34))
        name = self.fields[0].value.strip() or "Your Name"
        text(surf, name.upper(), (rect.centerx, rect.y + 16), 32, WHITE, "midtop", display=True,
             max_width=rect.w - 30)
        if self.fields[1].value.strip():
            text(surf, f'"{self.fields[1].value.strip()}"', (rect.centerx, rect.y + 56), 18, GOLD, "midtop")
        self.fig.x, self.fig.y = rect.x + 140, rect.y + 400
        self.fig.draw(surf)
        base = {k: v - 1 for k, v in ARCHETYPES[self.arch].items()}
        yy = rect.y + 140
        for s in STAT_NAMES:
            text(surf, s.capitalize(), (rect.x + 260, yy), 16, GREY)
            bar(surf, (rect.x + 360, yy + 4, 130, 12), base[s] / 10, RED)
            yy += 32
        text(surf, "You start 0-0, a little below the", (rect.x + 260, yy + 20), 15, GREY)
        text(surf, "ranked fighters. Train to catch up.", (rect.x + 260, yy + 40), 15, GREY)
        if self.error:
            text(surf, self.error, (CX + 280, H - 104), 16, (255, 120, 100), "midbottom")
        self.start.draw(surf)
        self.back.draw(surf)


class HubScene(Scene):
    def __init__(self, app, career, message=""):
        super().__init__(app)
        self.c = career
        self.message = message
        self.fig = Figure(200, 330, 1, career.player.color, glove=RED, scale=1.2)
        self.fig.set_pose("victory" if career.is_champ() else "stance",
                          idle="victory" if career.is_champ() else "stance")
        self.opp_fig = None
        self.confirm_retire = False
        self._build()
        app.sounds.ambience(False)

    def _build(self):
        self.plus = []
        for k, s in enumerate(STAT_NAMES):
            b = Button((380, 400 + k * 34, 36, 28), "+", size=18, color=(40, 120, 70))
            b.pick = s
            self.plus.append(b)
        self.fight_btn = Button((CX - 150, 560, 300, 60), "FIGHT", color=(170, 40, 40), size=28)
        self.menu_btn = Button((20, H - 56, 150, 40), "Main menu", size=17)
        self.retire_btn = Button((180, H - 56, 150, 40), "Retire", size=17, color=(90, 40, 40))
        opp, *_ = self.c.next_fight()
        self.opp_fig = Figure(CX, 470, -1, opp.color, glove=BLUE, scale=1.0)
        self.opp_fig.set_pose("stance", idle="stance")

    def handle(self, e):
        for b in self.plus:
            if b.handle(e):
                if self.c.train(b.pick):
                    self.app.sounds.play("click")
                    self.c.save()
        if self.fight_btn.handle(e) or (e.type == pygame.KEYDOWN and e.key == pygame.K_RETURN):
            self._fight()
        if self.menu_btn.handle(e) or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
            from .menu import MenuScene
            self.app.goto(MenuScene(self.app))
        if self.retire_btn.handle(e):
            if self.confirm_retire:
                delete_save()
                from .menu import MenuScene
                self.app.goto(MenuScene(self.app))
            else:
                self.confirm_retire = True
                self.retire_btn.label = "Sure? Click again"

    def _fight(self):
        c = self.c
        opp, rounds, title, level, label = c.next_fight()
        c.save()
        p = c.player
        opp_view = opp
        if opp.color == p.color:
            import copy
            opp_view = copy.copy(opp)
            opp_view.color = tuple(255 - x for x in opp.color)

        def done(app, fight):
            r = fight.result
            won = r.winner == 0
            draw = r.winner is None
            before = c.rank_label()
            was_champ = c.is_champ()
            c.record_result(opp, won, draw, r.method, r.detail, r.round)
            c.save()
            after = c.rank_label()
            if c.is_champ() and not was_champ:
                msg = "AND NEW! You are the champion of the world."
            elif was_champ and c.is_champ():
                msg = f"Title defended. That is {c.defenses} successful defence{'s' if c.defenses != 1 else ''}."
            elif was_champ:
                msg = "You lost the belt. Climb back up."
            elif before != after:
                msg = f"You moved from {before} to {after}."
            elif won:
                msg = "Good win. Keep it going."
            else:
                msg = "Tough night. Train up and go again."
            app.goto(HubScene(app, c, msg))

        cfg = FightConfig(p, opp_view, mode="ai", level=level, rounds=rounds, title=title,
                          on_done=done, event=label)
        from .walkout import WalkoutScene
        self.app.goto(WalkoutScene(self.app, cfg, label))

    def update(self, dt):
        self.fig.update(dt)
        if self.opp_fig:
            self.opp_fig.update(dt)

    def draw(self, surf):
        surf.fill((14, 15, 22))
        c = self.c
        p = c.player
        # Your card
        rect = panel(surf, (20, 20, 420, 600), (22, 24, 34), border=RED)
        text(surf, p.name.upper(), (rect.x + 20, rect.y + 14), 32, WHITE, display=True, max_width=240)
        if p.nickname:
            text(surf, f'"{p.nickname}"', (rect.x + 22, rect.y + 54), 17, GOLD)
        text(surf, f"{p.archetype}, {p.record()}", (rect.x + 22, rect.y + 78), 17, GREY)
        rank = c.rank_label()
        rc = GOLD if c.is_champ() else WHITE
        text(surf, rank.upper(), (rect.right - 20, rect.y + 18), 30, rc, "topright", display=True)
        if c.is_champ():
            self._belt(surf, rect.right - 90, rect.y + 70)
        self.fig.x, self.fig.y = rect.x + 120, rect.y + 340
        self.fig.draw(surf)
        text(surf, "TRAINING", (rect.x + 20, rect.y + 352), 16, GOLD, bold=True)
        pts = c.points
        text(surf, f"{pts} point{'s' if pts != 1 else ''} to spend", (rect.right - 20, rect.y + 352), 16,
             GREEN if pts else GREY, "topright")
        for k, s in enumerate(STAT_NAMES):
            yy = 400 + k * 34
            v = p.stats.get(s)
            text(surf, s.capitalize(), (rect.x + 20, yy + 4), 16, WHITE)
            bar(surf, (rect.x + 120, yy + 8, 200, 14), v / 10, RED)
            text(surf, str(v), (rect.x + 330, yy + 4), 16, WHITE)
            b = self.plus[k]
            b.enabled = v < STAT_MAX and pts >= train_cost(v)
            b.draw(surf)
        text(surf, "Stats under 7 cost 1 point, 7 and up cost 2", (rect.x + 20, rect.bottom - 26), 13, GREY)

        # Next fight
        opp, rounds, title, level, label = c.next_fight()
        r2 = panel(surf, (460, 20, 380, 520), (22, 24, 34), border=GOLD if title else BLUE)
        text(surf, "NEXT FIGHT", (r2.centerx, r2.y + 14), 16, GOLD, "midtop", bold=True)
        text(surf, label.upper(), (r2.centerx, r2.y + 36), 26, GOLD if title else WHITE, "midtop", display=True,
             max_width=r2.w - 30)
        text(surf, opp.name.upper(), (r2.centerx, r2.y + 80), 30, WHITE, "midtop", display=True,
             max_width=r2.w - 30)
        if opp.nickname:
            text(surf, f'"{opp.nickname}"', (r2.centerx, r2.y + 116), 16, GOLD, "midtop")
        text(surf, f"{opp.archetype}, {opp.record()}", (r2.centerx, r2.y + 138), 16, GREY, "midtop")
        self.opp_fig.shorts = opp.color
        self.opp_fig.x, self.opp_fig.y = r2.centerx, r2.y + 330
        self.opp_fig.draw(surf)
        yy = r2.y + 350
        for s in STAT_NAMES:
            v = opp.stats.get(s)
            mine = p.stats.get(s)
            text(surf, s.capitalize(), (r2.x + 30, yy), 15, GREY)
            bar(surf, (r2.x + 130, yy + 3, 170, 12), v / 10, BLUE)
            diff = v - mine
            col = (255, 120, 100) if diff > 0 else GREEN if diff < 0 else GREY
            text(surf, f"{v}", (r2.x + 320, yy), 15, col)
            yy += 24
        text(surf, f"{rounds} rounds, {LEVEL_NAME[level]} AI", (r2.centerx, r2.bottom - 30), 15, GREY, "midtop")
        self.fight_btn.label = "FIGHT FOR THE BELT" if title and not c.is_champ() else "FIGHT"
        self.fight_btn.draw(surf)

        # Rankings
        r3 = panel(surf, (860, 20, 400, 600), (22, 24, 34))
        text(surf, "RANKINGS", (r3.centerx, r3.y + 14), 26, WHITE, "midtop", display=True)
        yy = r3.y + 56
        for i, f in enumerate(c.ladder):
            me = f is p
            if me:
                pygame.draw.rect(surf, (90, 30, 30), (r3.x + 10, yy - 4, r3.w - 20, 40), border_radius=6)
            label_r = "C" if i == 0 else str(i)
            text(surf, label_r, (r3.x + 34, yy), 20, GOLD if i == 0 else GREY, "midtop", bold=True)
            text(surf, f.name, (r3.x + 64, yy), 18, WHITE if not me else GOLD, bold=me, max_width=250)
            text(surf, f.record(), (r3.right - 20, yy), 16, GREY, "topright")
            yy += 48
        if c.rank() is None:
            text(surf, f"You: unranked, {c.unranked_wins} of 2 prospect wins", (r3.centerx, r3.bottom - 30), 15,
                 GOLD, "midtop")

        if self.message:
            panel(surf, (460, 640, 800, 50), (40, 34, 14), alpha=230, border=GOLD)
            text(surf, self.message, (860, 665), 18, WHITE, "center", bold=True)
        self.menu_btn.draw(surf)
        self.retire_btn.draw(surf)

    def _belt(self, surf, x, y):
        pygame.draw.rect(surf, (30, 26, 18), (x - 60, y + 10, 120, 22), border_radius=8)
        pygame.draw.ellipse(surf, GOLD, (x - 26, y, 52, 42))
        pygame.draw.ellipse(surf, (180, 140, 30), (x - 18, y + 7, 36, 28), 3)
        pygame.draw.circle(surf, (200, 40, 40), (x, y + 21), 6)
