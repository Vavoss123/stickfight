"""The scouting report before a fight: who they are, what to expect, what to bring."""

import pygame

from engine import coach, personality
from engine.cards import CARDS, deck_points, signature_names
from engine.constants import STAT_NAMES

from ..common import W, H, CX, BLUE, GOLD, WHITE, GREY, GREEN, text, text_block, panel, bar, Button
from ..stickman import Figure
from .base import Scene


class ScoutScene(Scene):
    def __init__(self, app, opp, owner, back):
        """owner: a Career or Loadout, whose player gets the cards."""
        super().__init__(app)
        self.opp = opp
        self.c = owner
        self.back_to = back
        self.message = ""
        self.fig = Figure(250, 380, -1, opp.color, glove=BLUE, scale=1.0)
        self.fig.set_pose("stance", idle="stance")
        self.deck = Button((CX + 40, H - 80, 220, 48), "Edit deck", size=19, color=(60, 50, 110))
        self.done = Button((CX + 280, H - 80, 220, 48), "Done", size=19, color=(40, 110, 60))
        self._build()

    def _build(self):
        self.expect, ideas = coach.scout(self.opp, self.c.player, self.c.budget())
        self.ideas = []
        for k, s in enumerate(ideas):
            b = Button((CX - 60, 360 + k * 70, 680, 60), f"Put in {CARDS[s.card].name}", sub=s.why, size=18,
                       color=(40, 70, 50))
            b.pick = s
            self.ideas.append(b)

    def _apply(self, s):
        c = self.c
        if s.kind == "move":
            err = c.equip(s.slot, s.card)
        else:
            if s.out in c.player.perks:
                c.toggle_perk(s.out)
            err = c.toggle_perk(s.card)
            if err and s.out:
                c.toggle_perk(s.out)   # put it back
        if err:
            self.message = err
            return
        c.save()
        self.message = f"{CARDS[s.card].name} is in your deck."
        self.app.sounds.play("levelup", 0.6)
        self._build()

    def handle(self, e):
        for b in self.ideas:
            if b.handle(e):
                self._apply(b.pick)
                return
        if self.deck.handle(e):
            from .deck import DeckScene
            self.app.goto(DeckScene(self.app, self.c, lambda: ScoutScene(self.app, self.opp, self.c,
                                                                        self.back_to)))
            return
        if self.done.handle(e) or (e.type == pygame.KEYDOWN and e.key in (pygame.K_ESCAPE, pygame.K_RETURN)):
            self.app.goto(self.back_to())

    def update(self, dt):
        self.fig.update(dt)

    def draw(self, surf):
        surf.fill((14, 15, 22))
        o = self.opp
        text(surf, "SCOUTING REPORT", (CX, 18), 44, WHITE, "midtop", display=True)
        r = panel(surf, (30, 84, 420, 560), (22, 24, 34), border=BLUE)
        text(surf, o.name.upper(), (r.centerx, r.y + 14), 28, WHITE, "midtop", display=True, max_width=r.w - 30)
        if o.nickname:
            text(surf, f'"{o.nickname}"', (r.centerx, r.y + 50), 16, GOLD, "midtop")
        text(surf, f"{o.weight} {o.archetype}, {o.record()}", (r.centerx, r.y + 72), 15, GREY, "midtop")
        pers = personality.PERSONALITIES[personality.of(o)]
        text(surf, pers["label"], (r.centerx, r.y + 96), 18, (150, 200, 255), "midtop", bold=True)
        text_block(surf, pers["blurb"], (r.centerx, r.y + 120), 14, r.w - 40, GREY)
        self.fig.x, self.fig.y = r.centerx, r.y + 320
        self.fig.draw(surf)
        yy = r.y + 340
        for s in STAT_NAMES:
            text(surf, s.capitalize(), (r.x + 30, yy), 15, GREY)
            bar(surf, (r.x + 130, yy + 3, 220, 12), o.stats.get(s) / 10, BLUE)
            text(surf, str(o.stats.get(s)), (r.right - 30, yy), 15, WHITE, "topright")
            yy += 24
        sigs = signature_names(o)
        text_block(surf, "Cards: " + (", ".join(sigs) if sigs else "none"), (r.centerx, yy + 8), 14,
                   r.w - 40, (210, 190, 255))

        text(surf, "WHAT TO EXPECT", (CX - 60, 96), 18, GOLD, bold=True)
        y = 126
        for line in self.expect:
            pygame.draw.circle(surf, GOLD, (CX - 50, y + 10), 4)
            y = text_block(surf, line, (CX - 36, y), 17, 640, WHITE, "topleft") + 6
        text(surf, "THE COACH SAYS BRING", (CX - 60, 326), 18, GREEN, bold=True)
        p = self.c.player
        text(surf, f"Deck {deck_points(p)} of {self.c.budget()} points", (CX + 620, 328), 15, GREY, "topright")
        if not self.ideas:
            text_block(surf, "Your deck already has what you need for this one, or you do not own the "
                             "cards for it yet.", (CX - 60, 362), 16, 680, GREY, "topleft")
        for b in self.ideas:
            b.draw(surf)
        if self.message:
            text(surf, self.message, (CX - 60, H - 120), 16, WHITE, bold=True)
        self.deck.draw(surf)
        self.done.draw(surf)
