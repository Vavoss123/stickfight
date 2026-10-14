"""Tournament mode: pick a fighter, then fight through an eight fighter bracket in one night."""

import copy
import random

import pygame

from engine.cards import signature_names
from engine.constants import STAT_NAMES
from engine.loadouts import Loadout, apply_saved
from engine.roster import quick_fighters, division, ARCHETYPE_BLURB
from engine.tournament import Tournament, STAGES, SIZE

from ..common import (W, H, CX, RED, BLUE, GOLD, WHITE, GREY, GREEN, CORNER, text, text_block,
                      wrap, panel, bar, Button)
from ..stickman import Figure
from .base import Scene
from .fight import FightConfig

LEVELS = ["easy", "normal", "hard"]


class TournamentSetupScene(Scene):
    def __init__(self, app):
        super().__init__(app)
        from engine.roster import unlocked
        self.roster = quick_fighters() + division() + unlocked(set(app.record.unlocked))
        self.defaults = [(dict(p.deck), list(p.perks)) for p in self.roster]
        apply_saved(self.roster, pool=app.settings["card_pool"])
        self.sel = 0
        self.level = 1
        self.list = []
        step = min(34, 540 // len(self.roster))
        for k, p in enumerate(self.roster):
            b = Button((40, 110 + k * step, 300, step - 4), p.name, size=16 if step >= 30 else 14)
            b.pick = k
            self.list.append(b)
        self.levels = []
        for k, lv in enumerate(LEVELS):
            b = Button((820 + k * 120, 300, 110, 44), lv.capitalize(), size=18)
            b.pick = k
            self.levels.append(b)
        self.deck = Button((420, 560, 300, 40), "Edit deck", size=17, color=(60, 50, 110))
        self.start = Button((820, 470, 350, 60), "START TOURNAMENT", color=(170, 40, 40), size=24)
        self.back = Button((20, H - 56, 120, 40), "Back", size=18)
        self.fig = Figure(570, 330, 1, (0, 0, 0), glove=RED, scale=0.8)
        self.fig.set_pose("stance", idle="stance")

    def _begin(self):
        rng = random.Random()
        me = copy.deepcopy(self.roster[self.sel])
        others = [copy.deepcopy(p) for k, p in enumerate(self.roster) if k != self.sel]
        # The other fighters keep their own preset decks
        from engine.roster import unlocked
        fresh = {p.name: p for p in quick_fighters() + division() + unlocked(set(self.app.record.unlocked))}
        others = [fresh[p.name] for p in rng.sample(others, SIZE - 1)]
        t = Tournament(me, others, level=LEVELS[self.level], seed=rng.random())
        self.app.sounds.play("crowd", 0.6)
        self.app.goto(BracketScene(self.app, t, "Eight fighters, one night. Win three fights to take it."))

    def handle(self, e):
        for b in self.list:
            if b.handle(e):
                self.sel = b.pick
                self.app.sounds.play("click")
        for b in self.levels:
            if b.handle(e):
                self.level = b.pick
                self.app.sounds.play("click")
        if self.deck.handle(e):
            from .deck import DeckScene
            k = self.sel
            lo = Loadout(self.roster[k], self.defaults[k], pool=self.app.settings["card_pool"])
            self.app.goto(DeckScene(self.app, lo, lambda: self))
            return
        if self.start.handle(e) or (e.type == pygame.KEYDOWN and e.key == pygame.K_RETURN):
            self._begin()
            return
        if self.back.handle(e) or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
            from .menu import MenuScene
            self.app.goto(MenuScene(self.app))
            return
        if e.type == pygame.KEYDOWN and e.key in (pygame.K_UP, pygame.K_w, pygame.K_DOWN, pygame.K_s):
            d = -1 if e.key in (pygame.K_UP, pygame.K_w) else 1
            self.sel = (self.sel + d) % len(self.roster)

    def update(self, dt):
        for b in self.list:
            b.selected = b.pick == self.sel
        for b in self.levels:
            b.selected = b.pick == self.level
        self.fig.shorts = self.roster[self.sel].color
        from engine.weights import get
        self.fig.scale = 0.8 * get(self.roster[self.sel].weight)["size"]
        self.fig.update(dt)

    def draw(self, surf):
        surf.fill((14, 15, 22))
        text(surf, "TOURNAMENT", (CX, 20), 48, WHITE, "midtop", display=True)
        text(surf, "Pick your fighter. Damage carries over from one fight to the next.", (CX, 76), 17,
             GREY, "midtop")
        for b in self.list:
            b.draw(surf)
        p = self.roster[self.sel]
        rect = panel(surf, (380, 110, 380, 500), (22, 24, 34), border=RED)
        text(surf, p.name.upper(), (rect.centerx, rect.y + 12), 26, WHITE, "midtop", display=True,
             max_width=rect.w - 24)
        text(surf, f'"{p.nickname}"  {p.weight} {p.archetype}, {p.record()}', (rect.centerx, rect.y + 46),
             16, GOLD, "midtop", max_width=rect.w - 24)
        self.fig.x, self.fig.y = rect.centerx, rect.y + 220
        self.fig.draw(surf)
        yy = rect.y + 238
        for s in STAT_NAMES:
            text(surf, s.capitalize(), (rect.x + 30, yy), 15, GREY)
            bar(surf, (rect.x + 130, yy + 3, 200, 12), p.stats.get(s) / 10, RED)
            yy += 24
        yy = text_block(surf, ARCHETYPE_BLURB.get(p.archetype, ""), (rect.centerx, yy + 6), 14,
                        rect.w - 40, GREY, line_gap=1)
        sigs = signature_names(p)
        if sigs:
            for ln in wrap("Cards: " + ", ".join(sigs), 14, rect.w - 40)[:2]:
                yy = text(surf, ln, (rect.centerx, yy + 4), 14, (210, 190, 255), "midtop").bottom
        self.deck.draw(surf)
        text(surf, "Difficulty", (820, 272), 16, GREY)
        for b in self.levels:
            b.draw(surf)
        text_block(surf, "Quarterfinal, semifinal and final, three rounds each, everyone at your weight. "
                         "About half the damage you take stays with you, and cuts stay open.",
                   (820, 360), 15, 360, WHITE, "topleft")
        self.start.draw(surf)
        self.back.draw(surf)


# Bracket layout
COL_X = [30, 300, 570]
BOX_W, BOX_H = 250, 64
QF_Y0, QF_GAP = 120, 128


def _box_y(stage, k):
    """Top of match box k in a stage, centred between the two matches that feed it."""
    if stage == 0:
        return QF_Y0 + k * QF_GAP
    a, b = _box_y(stage - 1, 2 * k), _box_y(stage - 1, 2 * k + 1)
    return (a + b) // 2


class BracketScene(Scene):
    def __init__(self, app, t, message=""):
        super().__init__(app)
        self.t = t
        self.message = message
        self.fight_btn = Button((900, 470, 340, 56), "FIGHT", color=(170, 40, 40), size=26)
        self.deck_btn = Button((900, 536, 166, 40), "Edit deck", size=17, color=(60, 50, 110))
        self.quit_btn = Button((1074, 536, 166, 40), "Leave", size=17, color=(90, 40, 40))
        self.next_btn = Button((900, 470, 340, 56), "NEXT ROUND", color=(40, 90, 150), size=24)
        self.menu_btn = Button((900, 470, 340, 56), "MAIN MENU", color=(40, 110, 60), size=24)
        self.confirm_quit = False
        app.sounds.ambience(False)

    # Actions

    def _fight(self):
        t = self.t
        m = t.player_match()
        opp_i = m.b if m.a == 0 else m.a
        me, opp = t.player, t.entrants[opp_i]
        opp_view = opp
        if opp.color == me.color:
            opp_view = copy.copy(opp)
            opp_view.color = tuple(255 - x for x in opp.color)
        start = (t.cond[0].start(), t.cond[opp_i].start())
        name = t.stage_name()

        def done(app, fight):
            t.record(m, fight, sides=(0, opp_i))   # the player is always red
            won = m.winner == 0
            final = t.stage == len(STAGES) - 1
            t.finish_stage()
            if won and final:
                msg = "TOURNAMENT CHAMPION! Three fights, three wins, one night."
                app.sounds.play("roar")
                app.award(["tournament"])
            elif won:
                msg = f"Through to the {t.stage_name().lower()}. Mind the damage you are carrying."
            else:
                msg = f"Out in the {name.lower()}. See how the rest of the night plays out."
            app.goto(BracketScene(app, t, msg))

        cfg = FightConfig(me, opp_view, mode="ai", level=t.level, rounds=t.rounds(),
                          on_done=done, event=f"Tournament {name.lower()}", start=start)
        from .walkout import WalkoutScene
        self.app.goto(WalkoutScene(self.app, cfg, f"Tournament {name}"))

    def _deck(self):
        from .deck import DeckScene
        me = self.t.player
        default = (dict(me.deck), list(me.perks))
        lo = Loadout(me, default, pool=self.app.settings["card_pool"])
        lo.save = lambda: None   # only for this tournament
        lo.reset = lambda: (setattr(me, "deck", dict(default[0])), setattr(me, "perks", list(default[1])))
        self.app.goto(DeckScene(self.app, lo, lambda: BracketScene(self.app, self.t, self.message)))

    def handle(self, e):
        t = self.t
        enter = e.type == pygame.KEYDOWN and e.key in (pygame.K_RETURN, pygame.K_SPACE)
        if t.over:
            if self.menu_btn.handle(e) or enter or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
                from .menu import MenuScene
                self.app.goto(MenuScene(self.app))
            return
        if t.player_match():
            if self.fight_btn.handle(e) or enter:
                self._fight()
                return
            if self.deck_btn.handle(e):
                self._deck()
                return
        else:
            if self.next_btn.handle(e) or enter:
                t.finish_stage()
                self.app.sounds.play("crowd", 0.6)
                champ = t.entrants[t.champion].name if t.over else None
                self.message = f"{champ} wins the tournament." if champ else \
                    f"On to the {t.stage_name().lower()}."
                return
        if self.quit_btn.handle(e) or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
            if self.confirm_quit or not t.player_match():
                from .menu import MenuScene
                self.app.goto(MenuScene(self.app))
            else:
                self.confirm_quit = True
                self.quit_btn.label = "Sure? Again"

    # Drawing

    def draw(self, surf):
        surf.fill((14, 15, 22))
        t = self.t
        title = "TOURNAMENT" if not t.over else "TOURNAMENT RESULTS"
        text(surf, title, (440, 20), 44, WHITE, "midtop", display=True)
        for k, (name, _) in enumerate(STAGES):
            col = GOLD if k == t.stage and not t.over else GREY
            text(surf, name.upper(), (COL_X[k] + BOX_W // 2, 86), 16, col, "midtop", bold=True)
        self._draw_lines(surf)
        for k, stage in enumerate(t.stages):
            for j, m in enumerate(stage):
                self._draw_match(surf, m, COL_X[k], _box_y(k, j))
        self._draw_side(surf)

    def _draw_lines(self, surf):
        for k in range(1, len(STAGES)):
            for j in range(SIZE >> (k + 1)):
                y = _box_y(k, j) + BOX_H // 2
                xa = COL_X[k - 1] + BOX_W
                for src in (2 * j, 2 * j + 1):
                    ys = _box_y(k - 1, src) + BOX_H // 2
                    pygame.draw.lines(surf, (60, 62, 80), False,
                                      [(xa, ys), (xa + 10, ys), (xa + 10, y), (COL_X[k], y)], 2)

    def _draw_match(self, surf, m, x, y):
        t = self.t
        mine = 0 in (m.a, m.b)
        panel(surf, (x, y, BOX_W, BOX_H), (30, 33, 46) if mine else (22, 24, 34),
              border=GOLD if mine and not m.done else None)
        for row, i in enumerate((m.a, m.b)):
            p = t.entrants[i]
            yy = y + 6 + row * 26
            won = m.winner == i
            lost = m.done and not won
            col = GOLD if i == 0 else WHITE
            if lost:
                col = (110, 110, 120)
            text(surf, p.name, (x + 12, yy), 16, col, bold=won, max_width=150)
            if not m.done:
                c = t.cond[i]
                bar(surf, (x + 170, yy + 6, 68, 8), c.hp / 100, GREEN if c.hp > 70 else (240, 170, 60))
        if m.done:
            how = m.method if m.method != "Decision" else "Dec"
            text(surf, f"{how} R{m.round}", (x + BOX_W - 10, y + BOX_H - 4), 12, GREY, "bottomright")

    def _draw_side(self, surf):
        t = self.t
        r = panel(surf, (880, 20, 380, 580), (22, 24, 34), border=BLUE)
        m = t.player_match()
        if t.over:
            champ = t.entrants[t.champion]
            text(surf, "CHAMPION", (r.centerx, r.y + 20), 20, GOLD, "midtop", bold=True)
            text(surf, champ.name.upper(), (r.centerx, r.y + 50), 32, GOLD if t.champion == 0 else WHITE,
                 "midtop", display=True, max_width=r.w - 30)
            if t.champion == 0:
                self._trophy(surf, r.centerx, r.y + 140)
        elif m:
            opp_i = m.b if m.a == 0 else m.a
            text(surf, f"YOUR {t.stage_name().upper()}", (r.centerx, r.y + 16), 18, GOLD, "midtop", bold=True)
            text(surf, f"{t.rounds()} rounds", (r.centerx, r.y + 40), 14, GREY, "midtop")
            yy = r.y + 72
            for i, color in ((0, RED), (opp_i, BLUE)):
                p = t.entrants[i]
                text(surf, p.name.upper(), (r.x + 20, yy), 22, color, display=True, max_width=r.w - 40)
                text(surf, f"{p.archetype}, {p.record()}", (r.right - 20, yy + 4), 14, GREY, "topright")
                yy = self._draw_condition(surf, t.cond[i], r.x + 20, yy + 34, r.w - 40) + 18
            from engine import coach
            expect, _ = coach.scout(t.entrants[opp_i], t.player, 0)
            if expect:
                text_block(surf, "Expect: " + expect[0], (r.centerx, yy), 14, r.w - 40, (150, 200, 255))
        else:
            text(surf, "YOU ARE OUT", (r.centerx, r.y + 20), 22, (255, 120, 100), "midtop", bold=True)
            text_block(surf, "Watch how the rest of the bracket plays out.", (r.centerx, r.y + 56), 16,
                       r.w - 40, GREY)
        if self.message:
            text_block(surf, self.message, (r.centerx, r.y + 360), 17, r.w - 40, WHITE, bold=True)
        if t.over:
            self.menu_btn.draw(surf)
        elif m:
            self.fight_btn.draw(surf)
            self.deck_btn.draw(surf)
            self.quit_btn.draw(surf)
        else:
            self.next_btn.draw(surf)
            self.quit_btn.draw(surf)

    def _draw_condition(self, surf, c, x, y, w):
        if c.fresh():
            text(surf, "Fresh", (x, y), 15, GREEN, bold=True)
            return y + 20
        rows = [("Health", c.hp / 100, GREEN if c.hp > 70 else (240, 170, 60), f"{c.hp:.0f}%")]
        for label, v in (("Body", c.body), ("Legs", c.legs), ("Cut", c.cut)):
            if v >= 1:
                rows.append((label, v / 100, (240, 120, 60), f"{v:.0f}%"))
        for label, frac, col, val in rows:
            text(surf, label, (x, y), 14, GREY)
            bar(surf, (x + 70, y + 4, w - 130, 10), frac, col)
            text(surf, val, (x + w, y), 14, WHITE, "topright")
            y += 22
        return y

    def _trophy(self, surf, x, y):
        pygame.draw.polygon(surf, GOLD, [(x - 50, y), (x + 50, y), (x + 34, y + 70), (x - 34, y + 70)])
        pygame.draw.rect(surf, GOLD, (x - 8, y + 70, 16, 40))
        pygame.draw.rect(surf, (180, 140, 30), (x - 40, y + 110, 80, 18), border_radius=4)
        pygame.draw.arc(surf, GOLD, (x - 80, y + 4, 50, 50), 1.5, 4.7, 6)
        pygame.draw.arc(surf, GOLD, (x + 30, y + 4, 50, 50), -1.6, 1.6, 6)
