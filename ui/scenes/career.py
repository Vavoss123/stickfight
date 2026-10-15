"""Career: create a fighter, then a hub with training, rankings and the next fight."""

import pygame

from engine.career import Career, new_player, train_cost, delete_save
from engine.constants import STAT_NAMES, STAT_MAX
from engine.fighter import Profile
from engine.looks import random_look
from engine import personality
from engine.roster import ARCHETYPES, ARCHETYPE_BLURB, COLORS
from engine.weights import NAMES as WEIGHTS, get as get_weight

from engine.cards import deck_points, signature_names

from ..common import (W, H, CX, RED, BLUE, GOLD, WHITE, GREY, GREEN, text, text_block, panel, Button,
                      bar, font)
from ..keyrepeat import KeyRepeat
from ..stickman import Figure
from .base import Scene
from .fight import FightConfig

LEVEL_NAME = {"easy": "Easy", "normal": "Normal", "hard": "Hard"}


def open_career(app):
    c = Career.load()
    if c is None:
        app.goto(CreateScene(app))
    else:
        app.goto(HubScene(app, c, " ".join(c.news)))


class TextField:
    def __init__(self, rect, label, value="", limit=22):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.value = value
        self.limit = limit
        self.focus = False
        self.rep = KeyRepeat()

    def _apply(self, act):
        if act[0] == "back":
            self.value = self.value[:-1]
        else:
            self.value = (self.value + act[1])[:self.limit]

    def handle(self, e):
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            self.focus = self.rect.collidepoint(e.pos)
        if not self.focus:
            self.rep.clear()
            return
        act = self.rep.feed(e)
        if act:
            self._apply(act)

    def update(self, dt):
        if self.focus:
            for act in self.rep.tick(dt):
                self._apply(act)

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
        self.draft = Profile(name="", color=COLORS[0], look=random_look())   # the look being picked
        self.look_btn = Button((90, 548, 360, 40), "Change look: hair, skin, shorts  >", size=17,
                               color=(60, 50, 110))
        self.arch_buttons = []
        for k, a in enumerate(ARCHETYPES):
            b = Button((90 + (k % 2) * 184, 390 + (k // 2) * 56, 176, 48), a, size=20)
            b.pick = a
            self.arch_buttons.append(b)
        self.weight = 1   # Welterweight
        self.weight_btn = Button((90, 600, 360, 38), "", size=17, color=(52, 58, 78))
        self.pers = None   # None follows the style, until you pick one
        self.pers_btn = Button((900, 506, 244, 36), "", size=15, color=(110, 60, 40))
        self.start = Button((CX + 140, H - 80, 280, 54), "Start career", color=(170, 40, 40), size=24)
        self.back = Button((20, H - 70, 120, 40), "Back", size=18)
        self.hall = Button((150, H - 70, 160, 40), "Hall of fame", size=17, color=(150, 110, 30))
        self.fig = Figure(870, 470, 1, COLORS[0], glove=RED, scale=1.5)
        self.fig.set_pose("stance", idle="stance")
        self.error = ""
        pygame.key.start_text_input()
        self.text_entry = True    # so typing an m does not mute the sound

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
        if self.weight_btn.handle(e):
            self.weight = (self.weight + 1) % len(WEIGHTS)
            self.app.sounds.play("click")
        if self.pers_btn.handle(e):
            names = personality.NAMES
            self.pers = names[(names.index(self._pers()) + 1) % len(names)]
            self.app.sounds.play("click")
        if self.look_btn.handle(e):
            from .look import LookScene
            self.draft.name = self.fields[0].value.strip().title()
            self.app.sounds.play("click")
            self.app.goto(LookScene(self.app, self.draft, lambda: self.app.goto(self)))
            return
        if self.start.handle(e) or (e.type == pygame.KEYDOWN and e.key == pygame.K_RETURN):
            self._create()
        if self.back.handle(e) or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
            from .menu import MenuScene
            self.app.goto(MenuScene(self.app))
        if self.hall.handle(e):
            from .legacy import HallScene
            self.app.goto(HallScene(self.app, lambda: CreateScene(self.app)))

    def _pers(self):
        return self.pers or personality.BY_STYLE.get(self.arch, "balanced")

    def _create(self):
        name = self.fields[0].value.strip()
        if len(name.split()) < 1 or len(name) < 2:
            self.error = "Give your fighter a name"
            return
        nick = self.fields[1].value.strip()
        town = self.fields[2].value.strip()
        p = new_player(name.title(), nick, self.arch, self.draft.color, town, WEIGHTS[self.weight])
        p.look = dict(self.draft.look)
        p.personality = self._pers()
        c = Career(p)
        c.save()
        self.app.goto(HubScene(self.app, c, "Welcome to the show. Win two prospect fights to get ranked."))

    def update(self, dt):
        self.fig.dress(self.draft)
        for f in self.fields:
            f.update(dt)
        self.fig.scale = 1.5 * get_weight(WEIGHTS[self.weight])["size"]
        w = WEIGHTS[self.weight]
        self.weight_btn.label = f"Weight class: {w} ({get_weight(w)['lbs']} lbs)  >"
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
        self.look_btn.draw(surf)
        self.weight_btn.draw(surf)
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
        pers = personality.PERSONALITIES[self._pers()]
        text(surf, "Personality", (rect.x + 260, 484), 15, GREY)
        self.pers_btn.label = f"{pers['label']}  >"
        self.pers_btn.draw(surf)
        text_block(surf, personality.CAREER_PERK[self._pers()], (rect.x + 260, 550), 13, 244, GOLD, "topleft")
        if self.error:
            text(surf, self.error, (CX + 280, H - 104), 16, (255, 120, 100), "midbottom")
        self.start.draw(surf)
        self.back.draw(surf)
        self.hall.draw(surf)


class HubScene(Scene):
    def __init__(self, app, career, message=""):
        super().__init__(app)
        self.c = career
        self.message = message
        self.fig = Figure(200, 330, 1, career.player.color, glove=career.player.gloves or RED,
                          scale=1.2).dress(career.player)
        self.fig.set_pose("victory" if career.is_champ() else "stance",
                          idle="victory" if career.is_champ() else "stance")
        self.opp_fig = None
        self.confirm_retire = False
        self._tip = None
        self._story_checked = False
        self._build()
        app.sounds.ambience(False)

    def _build(self):
        self.trade_deck = Button((40, 572, 190, 32), "+1 deck point (5 pts)", size=14, color=(60, 50, 110))
        self.trade_pack = Button((240, 572, 180, 32), "Card pack (3 pts)", size=14, color=(150, 110, 30))
        self.plus = []
        for k, s in enumerate(STAT_NAMES):
            b = Button((380, 400 + k * 34, 36, 28), "+", size=18, color=(40, 120, 70))
            b.pick = s
            self.plus.append(b)
        self.fight_btn = Button((CX - 150, 560, 300, 60), "FIGHT", color=(170, 40, 40), size=28)
        self.menu_btn = Button((20, H - 56, 150, 40), "Main menu", size=17)
        self.retire_btn = Button((180, H - 56, 150, 40), "Retire", size=17, color=(90, 40, 40))
        self.hall_btn = Button((340, H - 56, 140, 40), "Hall of fame", size=16, color=(150, 110, 30))
        self.deck_btn = Button((CX - 150, 624, 72, 38), "Deck", size=16, color=(60, 50, 110))
        self.scout_btn = Button((CX - 74, 624, 72, 38), "Scout", size=16, color=(40, 90, 130))
        self.gym_btn = Button((CX + 2, 624, 72, 38), "Gym", size=16, color=(40, 110, 60))
        self.shop_btn = Button((CX + 78, 624, 72, 38), "Shop", size=16, color=(150, 110, 30))
        self.trophy_btn = Button((488, H - 56, 110, 40), "Trophies", size=16, color=(110, 90, 30))
        self.look_btn = Button((606, H - 56, 90, 40), "Look", size=16, color=(60, 50, 110))
        self.rehab_btn = Button((250, 262, 170, 32), "", size=14, color=(40, 90, 130))
        opp, *_ = self.c.next_fight()
        self.grudge_text = self.c.grudge_line() if self.c.next_fight()[4] == "Grudge match" else ""
        self.opp_fig = Figure(CX, 470, -1, opp.color, glove=BLUE, scale=1.0).dress(opp)
        self.opp_fig.set_pose("stance", idle="stance")

    def handle(self, e):
        if self.trade_deck.handle(e):
            if self.c.trade_for_deck_point():
                self.app.sounds.play("levelup")
                self.message = f"Traded 5 training points. Your deck budget is now {self.c.budget()}."
                self.c.save()
            return
        if self.trade_pack.handle(e):
            if self.c.trade_for_pack():
                self.c.save()
                from .deck import PackScene
                c = self.c
                self.app.goto(PackScene(self.app, c, "normal", lambda: HubScene(self.app, c)))
            return
        if self.c.injury and self.rehab_btn.handle(e):
            if self.c.rehab():
                self.app.sounds.play("cash")
                self.c.save()
                self.message = "Physio worked. You are fit to fight."
            else:
                self.message = "Not enough money for physio."
            return
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
        if self.gym_btn.handle(e) or (e.type == pygame.KEYDOWN and e.key == pygame.K_g):
            from .gym import GymScene
            self.app.goto(GymScene(self.app, self.c, lambda: HubScene(self.app, self.c, self.message)))
            return
        if self.look_btn.handle(e):
            from .look import LookScene
            self.app.sounds.play("click")
            back = lambda: self.app.goto(HubScene(self.app, self.c, self.message))

            def saved():
                self.c.save()
                back()
            self.app.goto(LookScene(self.app, self.c.player, saved, back))
            return
        if self.trophy_btn.handle(e):
            from .challenges import TrophiesScene
            self.app.goto(TrophiesScene(self.app, lambda: HubScene(self.app, self.c, self.message)))
            return
        if self.scout_btn.handle(e) or (e.type == pygame.KEYDOWN and e.key == pygame.K_s):
            from .scout import ScoutScene
            opp = self.c.next_fight()[0]
            self.app.goto(ScoutScene(self.app, opp, self.c, lambda: HubScene(self.app, self.c, self.message)))
            return
        if self.deck_btn.handle(e) or (e.type == pygame.KEYDOWN and e.key == pygame.K_d):
            from .deck import DeckScene
            self.app.goto(DeckScene(self.app, self.c, lambda: HubScene(self.app, self.c)))
            return
        if self.shop_btn.handle(e):
            from .deck import ShopScene
            self.app.goto(ShopScene(self.app, self.c, lambda: HubScene(self.app, self.c)))
            return
        if self.hall_btn.handle(e):
            from .legacy import HallScene
            self.app.goto(HallScene(self.app, lambda: HubScene(self.app, self.c, self.message)))
            return
        if self.retire_btn.handle(e):
            if self.confirm_retire:
                from engine import legacy
                from .legacy import RetireScene
                entry = legacy.retire(self.c)
                delete_save()
                if entry["inducted"]:
                    self.app.award(["hall"])
                self.app.goto(RetireScene(self.app, entry))
            else:
                self.confirm_retire = True
                self.retire_btn.label = "Sure? Click again"

    def _fight(self):
        c = self.c
        if c.camp_due():
            from .legacy import CampScene
            self.app.goto(CampScene(self.app, c, then=lambda: HubScene(self.app, c)._fight(),
                                    back=lambda: HubScene(self.app, c, self.message)))
            return
        opp, rounds, title, level, label = c.next_fight()
        c.save()
        p = c.fighter_for_fight()
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
            reward = c.record_result(opp, won, draw, r.method, r.detail, r.round)
            c.save()
            from engine import achievements
            app.award(achievements.for_career(c))
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
            msg += f" You made ${reward['purse'] + reward['bonus']:,}."
            if reward.get("bill"):
                msg += f" The hospital bill came to ${reward['bill']:,}."
            if reward.get("injury"):
                msg += f" {reward['injury']}."
            if reward.get("permanent"):
                msg += " That knockout cost you a point of chin for good."
            if reward["story"]:
                msg += " " + " ".join(reward["story"])
            if reward["pack"]:
                from .deck import PackScene
                app.goto(PackScene(app, c, reward["pack"], lambda: HubScene(app, c, msg)))
            else:
                app.goto(HubScene(app, c, msg))

        if label == "Grudge match" and title:
            label = "Grudge match for the title"
        cfg = FightConfig(p, opp_view, mode="ai", level=level, rounds=rounds, title=title,
                          start=(c.camp_start(), None), deck_budget=c.budget(),
                          on_done=done, event=label)
        from .walkout import WalkoutScene
        self.app.goto(WalkoutScene(self.app, cfg, label))

    def update(self, dt):
        if not self._story_checked:
            # A story beat waiting from the last fight (or the start of the career)
            self._story_checked = True
            beat = self.c.next_story()
            if beat:
                self.c.save()
                from .story import StoryScene
                c, msg = self.c, self.message
                self.app.goto(StoryScene(self.app, c, beat, lambda: HubScene(self.app, c, msg)))
                return
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
        text(surf, f"{p.weight} {p.archetype}, {p.record()}, {personality.label(p)}", (rect.x + 22, rect.y + 78),
             17, GREY, max_width=rect.w - 40)
        text(surf, f"${c.money:,}", (rect.x + 22, rect.y + 102), 18, GOLD, bold=True)
        text(surf, f"Deck {deck_points(p)} of {c.budget()} points", (rect.right - 20, rect.y + 104), 15,
             GREY, "topright")
        rank = c.rank_label()
        rc = GOLD if c.is_champ() else WHITE
        text(surf, rank.upper(), (rect.right - 20, rect.y + 18), 30, rc, "topright", display=True)
        if c.is_champ():
            self._belt(surf, rect.right - 90, rect.y + 70)
        self.fig.x, self.fig.y = rect.x + 120, rect.y + 340
        self.fig.draw(surf)
        if c.injury:
            self._draw_injury(surf, pygame.Rect(rect.x + 230, rect.y + 136, 176, 166))
        text(surf, "TRAINING", (rect.x + 20, rect.y + 352), 16, GOLD, bold=True)
        pts = c.points
        text(surf, f"{pts} point{'s' if pts != 1 else ''} to spend", (rect.right - 20, rect.y + 352), 16,
             GREEN if pts else GREY, "topright")
        from engine.cards import build_kit
        eff = build_kit(c.fighter_for_fight()).stats   # camp boost and injuries included
        mouse = pygame.mouse.get_pos()
        hover = None
        for k, s in enumerate(STAT_NAMES):
            yy = 400 + k * 34
            v = p.stats.get(s)
            row = pygame.Rect(rect.x + 10, yy, 360, 30)
            if row.collidepoint(mouse) or self.plus[k].hover:
                hover = (s, yy)
                pygame.draw.rect(surf, (36, 40, 56), row, border_radius=6)
            text(surf, s.capitalize(), (rect.x + 20, yy + 4), 16, WHITE)
            bar(surf, (rect.x + 120, yy + 8, 200, 14), v / 10, RED)
            text(surf, str(v), (rect.x + 326, yy + 4), 16, WHITE)
            extra = eff.get(s) - v
            if extra > 0:
                text(surf, f"+{extra}", (rect.x + 344, yy + 6), 12, GOLD, bold=True)
            elif extra < 0:
                text(surf, f"{extra}", (rect.x + 344, yy + 6), 12, (255, 110, 100), bold=True)
            b = self.plus[k]
            b.enabled = v < STAT_MAX and pts >= train_cost(v)
            b.draw(surf)

        from engine.career import POINTS_PER_DECK_POINT, POINTS_PER_PACK, MAX_BONUS_DECK
        self.trade_deck.enabled = pts >= POINTS_PER_DECK_POINT and c.bonus_deck < MAX_BONUS_DECK
        self.trade_pack.enabled = pts >= POINTS_PER_PACK
        self.trade_deck.draw(surf)
        self.trade_pack.draw(surf)
        self._tip = (hover, p, eff) if hover else None
        text(surf, "Hover a stat to see what it does. Under 7 costs 1 point, 7 and up 2",
             (rect.centerx, rect.bottom - 4), 11, GREY, "midbottom")

        # Next fight
        opp, rounds, title, level, label = c.next_fight()
        r2 = panel(surf, (460, 20, 380, 520), (22, 24, 34),
                   border=(220, 60, 60) if label == "Grudge match" else GOLD if title else BLUE)
        text(surf, "NEXT FIGHT", (r2.centerx, r2.y + 14), 16, GOLD, "midtop", bold=True)
        lc = (255, 90, 80) if label == "Grudge match" else GOLD if title else WHITE
        text(surf, label.upper(), (r2.centerx, r2.y + 36), 26, lc, "midtop", display=True,
             max_width=r2.w - 30)
        text(surf, opp.name.upper(), (r2.centerx, r2.y + 80), 30, WHITE, "midtop", display=True,
             max_width=r2.w - 30)
        if opp.nickname:
            text(surf, f'"{opp.nickname}"', (r2.centerx, r2.y + 116), 16, GOLD, "midtop")
        text(surf, f"{opp.archetype}, {opp.record()}, {personality.label(opp).lower()}",
             (r2.centerx, r2.y + 138), 16, GREY, "midtop", max_width=r2.w - 30)
        self.opp_fig.dress(opp)
        self.opp_fig.x, self.opp_fig.y = r2.centerx, r2.y + 318
        self.opp_fig.draw(surf)
        yy = r2.y + 334
        for s in STAT_NAMES:
            v = opp.stats.get(s)
            mine = p.stats.get(s)
            text(surf, s.capitalize(), (r2.x + 30, yy), 15, GREY)
            bar(surf, (r2.x + 130, yy + 3, 170, 12), v / 10, BLUE)
            diff = v - mine
            col = (255, 120, 100) if diff > 0 else GREEN if diff < 0 else GREY
            text(surf, f"{v}", (r2.x + 320, yy), 15, col)
            yy += 24
        sigs = signature_names(opp)
        if sigs:
            text_block(surf, "Cards: " + ", ".join(sigs), (r2.centerx, r2.y + 462), 13, r2.w - 40,
                       (210, 190, 255))
        text(surf, f"{rounds} rounds, {LEVEL_NAME[level]} AI", (r2.centerx, r2.bottom - 24), 15, GREY, "midtop")
        grudge = label == "Grudge match"
        if grudge and self.grudge_text:
            text_block(surf, self.grudge_text, (r2.centerx, r2.y + 162), 15, r2.w - 40, (255, 120, 100),
                       bold=True)
        if c.camp:
            from engine.career import CAMPS
            text(surf, f"{CAMPS[c.camp][0]}: +1 {c.camp}", (r2.centerx, r2.y + 196), 15, GREEN, "midtop",
                 bold=True)
        elif title:
            text(surf, "Training camp before this one", (r2.centerx, r2.y + 196), 15, GOLD, "midtop")
        self.fight_btn.label = "FIGHT FOR THE BELT" if title and not c.is_champ() else "FIGHT"
        if title and c.camp_due():
            self.fight_btn.label = "GO TO CAMP"
        self.fight_btn.draw(surf)
        self.deck_btn.draw(surf)
        self.scout_btn.draw(surf)
        self.gym_btn.draw(surf)
        self.shop_btn.draw(surf)
        self.trophy_btn.draw(surf)
        self.look_btn.draw(surf)

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
            rival = not me and f.name == c.rival
            text(surf, f.name, (r3.x + 64, yy), 18, (255, 120, 100) if rival else WHITE if not me else GOLD,
                 bold=me or rival, max_width=200 if rival else 250)
            if rival:
                w, l = c.rival_record
                text(surf, f"RIVAL {w}-{l}", (r3.right - 20, yy + 20), 12, (255, 120, 100), "topright", bold=True)
            text(surf, f.record(), (r3.right - 20, yy), 16, GREY, "topright")
            yy += 48
        if c.rank() is None:
            text(surf, f"You: unranked, {c.unranked_wins} of 2 prospect wins", (r3.centerx, r3.bottom - 30), 15,
                 GOLD, "midtop")

        if self.message:
            panel(surf, (860, 628, 400, 84), (40, 34, 14), alpha=230, border=GOLD)
            text_block(surf, self.message, (1060, 638), 16, 380, WHITE, "midtop", bold=True)
        self.menu_btn.draw(surf)
        self.retire_btn.draw(surf)
        self.hall_btn.draw(surf)
        if self._tip:   # drawn last so it sits on top of the next fight panel
            (stat, y), p, eff = self._tip
            self._stat_tip(surf, stat, y, p, eff)

    def _stat_tip(self, surf, stat, y, p, eff):
        """What a point in this stat does, and where the number comes from."""
        from engine.constants import STAT_INFO, STAT_LIMIT
        v, e = p.stats.get(stat), eff.get(stat)
        r = panel(surf, (446, y - 10, 400, 112), (20, 24, 36), alpha=245, border=GOLD)
        text(surf, f"{stat.upper()}  {v}" + (f"  (+{e - v} from perks = {e})" if e > v else ""),
             (r.x + 14, r.y + 10), 15, GOLD, bold=True, max_width=r.w - 28)
        y2 = text_block(surf, STAT_INFO[stat], (r.x + 14, r.y + 34), 14, r.w - 28, WHITE, "topleft")
        if v >= STAT_MAX:
            note = f"Maxed by training. Perks and camp can still take it to {STAT_LIMIT}."
        else:
            note = f"Next point costs {train_cost(v)} training point{'s' if train_cost(v) > 1 else ''}."
        text(surf, note, (r.x + 14, min(y2 + 2, r.bottom - 20)), 12, GREY, max_width=r.w - 28)

    def _draw_injury(self, surf, r):
        inj = self.c.injury
        panel(surf, r, (50, 20, 22), alpha=240, border=(220, 70, 60))
        text(surf, "INJURED", (r.x + 10, r.y + 8), 15, (255, 110, 100), bold=True)
        text(surf, inj["name"], (r.x + 10, r.y + 28), 15, WHITE, bold=True, max_width=r.w - 20)
        y = r.y + 50
        for st, v in inj["stats"].items():
            text(surf, f"{st.capitalize()} -{v}", (r.x + 10, y), 14, (255, 170, 160))
            y += 18
        n = inj["fights"]
        text(surf, "Heals after the next fight" if n == 1 else f"Heals after {n} fights", (r.x + 10, r.y + 102),
             12, GREY)
        price = self.c.rehab_price()
        self.rehab_btn.rect = pygame.Rect(r.x + 8, r.bottom - 40, r.w - 16, 32)
        self.rehab_btn.label = f"Physio now: ${price:,}"
        self.rehab_btn.enabled = self.c.money >= price
        self.rehab_btn.draw(surf)

    def _belt(self, surf, x, y):
        pygame.draw.rect(surf, (30, 26, 18), (x - 60, y + 10, 120, 22), border_radius=8)
        pygame.draw.ellipse(surf, GOLD, (x - 26, y, 52, 42))
        pygame.draw.ellipse(surf, (180, 140, 30), (x - 18, y + 7, 36, 28), 3)
        pygame.draw.circle(surf, (200, 40, 40), (x, y + 21), 6)
