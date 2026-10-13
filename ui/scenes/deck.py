"""Deck builder, card packs and the card shop for career mode."""

import pygame

from engine.cards import (CARDS, GROUPS, MAX_PERKS, PRICE, DECK_COST, deck_points, group_slots,
                          variants, warnings)
from engine.moves import MOVES

from ..cards import draw_card, RARITY_COLOR
from ..common import W, H, CX, GOLD, WHITE, GREY, GREEN, text, text_block, panel, Button, bar
from .base import Scene

TABS = [g for g, _ in GROUPS] + ["Perks"]
CW, CH = 186, 262


def money(n):
    return f"${n:,}"


class DeckScene(Scene):
    """career is a Career, or a Loadout for quick fight decks. Both have the same calls."""

    def __init__(self, app, career, back):
        super().__init__(app)
        self.c = career
        self.back_to = back
        self.tab = 0
        self.slot = None
        self.message = ""
        self.tab_buttons = []
        for k, name in enumerate(TABS):
            b = Button((20 + k * 160, 76, 152, 38), name, size=17)
            b.pick = k
            self.tab_buttons.append(b)
        self.back = Button((20, H - 56, 140, 42), "Done", color=(40, 110, 60), size=18)
        self.reset = Button((20, H - 104, 140, 38), "Reset deck", size=16)             if hasattr(career, "reset") else None
        self._pick_first_slot()

    def _slots(self):
        return group_slots(TABS[self.tab])

    def _pick_first_slot(self):
        if TABS[self.tab] == "Perks":
            self.slot = None
            return
        slots = self._slots()
        with_cards = [s for s in slots if variants(s)]
        self.slot = (with_cards or slots)[0]

    # Layout helpers

    def _slot_rects(self):
        out = []
        for k, base in enumerate(self._slots()):
            out.append((base, pygame.Rect(20, 132 + k * 34, 560, 30)))
        return out

    def _card_rects(self, ids):
        out = []
        per_row = 3
        for k, cid in enumerate(ids):
            x = 610 + (k % per_row) * (CW + 14)
            y = 132 + (k // per_row) * (CH + 14)
            out.append((cid, pygame.Rect(x, y, CW, CH)))
        return out

    def _perk_rects(self, ids):
        out = []
        for k, cid in enumerate(ids):
            x = 610 + (k % 2) * 330
            y = 132 + (k // 2) * 54
            out.append((cid, pygame.Rect(x, y, 320, 48)))
        return out

    def _choices(self):
        if TABS[self.tab] == "Perks":
            owned = [c.id for c in CARDS.values() if c.is_perk and c.id in self.c.player.cards]
            return owned
        if not self.slot:
            return []
        return [self.slot] + [c.id for c in variants(self.slot)]

    # Input

    def handle(self, e):
        if self.back.handle(e) or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
            self.c.save()
            self.app.goto(self.back_to())
            return
        if self.reset and self.reset.handle(e):
            self.c.reset()
            self.message = ""
            self.app.sounds.play("click")
            return
        for b in self.tab_buttons:
            if b.handle(e):
                self.tab = b.pick
                self.message = ""
                self._pick_first_slot()
                self.app.sounds.play("click")
                return
        if e.type != pygame.MOUSEBUTTONDOWN or e.button != 1:
            return
        if TABS[self.tab] != "Perks":
            for base, r in self._slot_rects():
                if r.collidepoint(e.pos):
                    self.slot = base
                    self.app.sounds.play("click")
                    return
        rects = self._perk_rects(self._choices()) if TABS[self.tab] == "Perks" else             self._card_rects(self._choices())
        for cid, r in rects:
            if r.collidepoint(e.pos):
                self._choose(cid)
                return

    def _choose(self, cid):
        p = self.c.player
        if TABS[self.tab] == "Perks":
            err = self.c.toggle_perk(cid)
        elif cid == self.slot:
            err = self.c.equip(self.slot, None)
        elif cid not in p.cards:
            err = "You do not own that card yet. Win packs or buy it in the shop."
        else:
            err = self.c.equip(self.slot, cid)
        self.message = err or ""
        self.app.sounds.play("click")
        if not err:
            self.c.save()

    # Drawing

    def draw(self, surf):
        surf.fill((14, 15, 22))
        c = self.c
        p = c.player
        text(surf, getattr(c, "title", "YOUR DECK"), (20, 18), 40, WHITE, display=True, max_width=700)
        pts, budget = deck_points(p), c.budget()
        text(surf, f"Deck points {pts} of {budget}", (W - 330, 22), 18, WHITE, bold=True)
        bar(surf, (W - 330, 48, 310, 12), pts / max(1, budget), GREEN if pts <= budget else (220, 60, 60))
        if c.money is not None:
            text(surf, money(c.money), (W - 20, 20), 18, GOLD, "topright", bold=True)
        for k, b in enumerate(self.tab_buttons):
            b.selected = k == self.tab
            b.draw(surf)

        if TABS[self.tab] == "Perks":
            self._draw_perks(surf)
        else:
            self._draw_slots(surf)

        y = H - 96
        for w in warnings(p):
            text(surf, w, (180, y), 16, (255, 170, 60), bold=True)
            y += 22
        if self.message:
            text(surf, self.message, (180, H - 44), 17, (255, 120, 100), bold=True)
        else:
            hint = getattr(c, "hint", "Common cards cost 1 point, rare 2, legendary 3. "
                                      "Win fights to raise your budget.")
            text(surf, hint, (180, H - 44), 15, GREY)
        self.back.draw(surf)
        if self.reset:
            self.reset.draw(surf)

    def _draw_slots(self, surf):
        p = self.c.player
        for base, r in self._slot_rects():
            cid = p.deck.get(base)
            sel = base == self.slot
            has = bool(variants(base))
            pygame.draw.rect(surf, (40, 44, 62) if sel else (26, 28, 38), r, border_radius=6)
            if sel:
                pygame.draw.rect(surf, GOLD, r, 2, border_radius=6)
            text(surf, MOVES[base].name, (r.x + 12, r.centery), 17, WHITE if has else GREY, "midleft")
            if cid:
                card = CARDS[cid]
                text(surf, f"{card.name}  L{p.cards.get(cid, 1)}", (r.right - 12, r.centery), 17,
                     RARITY_COLOR[card.rarity], "midright", bold=True)
            elif has:
                text(surf, "basic", (r.right - 12, r.centery), 15, GREY, "midright")
            else:
                text(surf, "no cards for this slot", (r.right - 12, r.centery), 13, (90, 90, 100), "midright")
        if self.slot:
            text(surf, f"Cards for the {MOVES[self.slot].name} slot", (610, 106), 16, GREY)
        for cid, r in self._card_rects(self._choices()):
            owned = cid == self.slot or cid in p.cards
            equipped = p.deck.get(self.slot) == cid or (cid == self.slot and self.slot not in p.deck)
            draw_card(surf, r, cid, p.cards.get(cid, 1), owned=owned, equipped=equipped)

    def _draw_perks(self, surf):
        p = self.c.player
        text(surf, f"Equipped perks ({len(p.perks)} of {MAX_PERKS})", (20, 132), 18, WHITE, bold=True)
        for k in range(MAX_PERKS):
            r = pygame.Rect(20, 166 + k * 50, 560, 42)
            pygame.draw.rect(surf, (26, 28, 38), r, border_radius=6)
            if k < len(p.perks):
                card = CARDS[p.perks[k]]
                text(surf, card.name, (r.x + 12, r.centery), 18, RARITY_COLOR[card.rarity], "midleft", bold=True)
                text(surf, f"L{p.cards.get(card.id, 1)}  {DECK_COST[card.rarity]} pt",
                     (r.right - 12, r.centery), 15, GREY, "midright")
            else:
                text(surf, "empty", (r.x + 12, r.centery), 15, (90, 90, 100), "midleft")
        text_block(surf, "Click a perk on the right to equip or remove it.", (20, 330), 15, 540, GREY,
                   "topleft")
        choices = self._choices()
        if not choices:
            text(surf, "No perks yet. Win packs or visit the shop.", (610, 140), 17, GREY)
        text(surf, "Your perks", (610, 106), 16, GREY)
        for cid, r in self._perk_rects(choices):
            card = CARDS[cid]
            on = cid in p.perks
            pygame.draw.rect(surf, (24, 74, 78) if on else (26, 28, 38), r, border_radius=6)
            pygame.draw.rect(surf, RARITY_COLOR[card.rarity], r, 2, border_radius=6)
            lvl = p.cards.get(cid, 1)
            text(surf, f"{card.name}  L{lvl}", (r.x + 10, r.y + 4), 16, WHITE, bold=True, max_width=230)
            text(surf, f"{DECK_COST[card.rarity]} pt" + ("  ON" if on else ""), (r.right - 10, r.y + 5), 13,
                 GOLD if on else GREY, "topright", bold=True)
            from engine.cards import perk_text
            text(surf, perk_text(card, lvl), (r.x + 10, r.y + 26), 12, (200, 210, 215), max_width=r.w - 20)


class PackScene(Scene):
    """Pick one of three cards after a win."""

    def __init__(self, app, career, quality, then):
        super().__init__(app)
        self.c = career
        self.then = then
        self.cards = career.make_pack(quality)
        self.quality = quality
        self.t = 0.0
        self.chosen = None
        self.result = None
        self.done = Button((CX - 120, H - 76, 240, 50), "Continue", color=(150, 110, 30), size=20)
        app.sounds.play("crowd", 0.5)

    def _rects(self):
        n = len(self.cards)
        w, h = 230, 324
        x0 = CX - (n * w + (n - 1) * 30) // 2
        return [pygame.Rect(x0 + k * (w + 30), 170, w, h) for k in range(n)]

    def handle(self, e):
        if self.chosen is None:
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and self.t > 0.8:
                for cid, r in zip(self.cards, self._rects()):
                    if r.collidepoint(e.pos):
                        self.chosen = cid
                        self.result = self.c.gain_card(cid)
                        self.c.save()
                        self.app.sounds.play("punch")
            if e.type == pygame.KEYDOWN and e.key in (pygame.K_1, pygame.K_2, pygame.K_3) and self.t > 0.8:
                k = e.key - pygame.K_1
                if k < len(self.cards):
                    self.chosen = self.cards[k]
                    self.result = self.c.gain_card(self.chosen)
                    self.c.save()
            if not self.cards:
                self.app.goto(self.then())
            return
        if self.done.handle(e) or (e.type == pygame.KEYDOWN and e.key in (pygame.K_RETURN, pygame.K_SPACE)):
            self.app.goto(self.then())

    def update(self, dt):
        self.t += dt

    def draw(self, surf):
        surf.fill((14, 15, 22))
        title = {"title": "CHAMPIONSHIP PACK", "finish": "FINISH BONUS PACK"}.get(self.quality, "CARD PACK")
        text(surf, title, (CX, 40), 48, GOLD, "midtop", display=True)
        sub = "Pick one card to keep. Duplicates level your card up." if self.chosen is None else ""
        text(surf, sub, (CX, 104), 18, GREY, "midtop")
        p = self.c.player
        for k, (cid, r) in enumerate(zip(self.cards, self._rects())):
            # Flip in one after another
            reveal = max(0.0, min(1.0, (self.t - k * 0.2) * 3))
            if reveal < 1.0:
                w = max(2, int(r.w * abs(reveal * 2 - 1)))
                back = pygame.Rect(0, 0, w, r.h)
                back.center = r.center
                pygame.draw.rect(surf, (40, 30, 60), back, border_radius=10)
                pygame.draw.rect(surf, GOLD, back, 3, border_radius=10)
                continue
            if self.chosen is not None and cid != self.chosen:
                dim = pygame.Surface(r.size, pygame.SRCALPHA)
                draw_card(dim, dim.get_rect(), cid, max(1, p.cards.get(cid, 0) or 1))
                dim.set_alpha(70)
                surf.blit(dim, r)
                continue
            have = p.cards.get(cid, 0)
            draw_card(surf, r, cid, max(1, have), selected=cid == self.chosen)
            if self.chosen is None:
                note = f"You have it at level {have}" if have else "New"
                text(surf, note, (r.centerx, r.bottom + 10), 15, GREEN if not have else GOLD, "midtop", bold=True)
                text(surf, str(k + 1), (r.centerx, r.bottom + 32), 14, GREY, "midtop")
        if self.chosen is not None:
            name = CARDS[self.chosen].name
            msg = {"new": f"{name} added to your collection.",
                   "level": f"{name} levelled up to level {p.cards[self.chosen]}!",
                   "refund": f"{name} is already maxed. Sold for {money(PRICE[CARDS[self.chosen].rarity] // 2)}."}[self.result]
            text(surf, msg, (CX, 540), 22, WHITE, "midtop", bold=True)
            text(surf, "Equip it from the Deck screen.", (CX, 574), 16, GREY, "midtop")
            self.done.draw(surf)


class ShopScene(Scene):
    def __init__(self, app, career, back):
        super().__init__(app)
        self.c = career
        self.back_to = back
        self.message = ""
        self.back = Button((20, H - 56, 140, 42), "Done", color=(40, 110, 60), size=18)
        self._build()

    def _build(self):
        self.buy = []
        n = len(self.c.shop)
        w = 230
        x0 = CX - (n * w + (n - 1) * 24) // 2
        for k, cid in enumerate(self.c.shop):
            b = Button((x0 + k * (w + 24), 530, w, 44), f"Buy {money(PRICE[CARDS[cid].rarity])}",
                       color=(150, 110, 30), size=18)
            b.pick = cid
            self.buy.append(b)

    def _rects(self):
        n = len(self.c.shop)
        w = 230
        x0 = CX - (n * w + (n - 1) * 24) // 2
        return [pygame.Rect(x0 + k * (w + 24), 150, w, 324) for k in range(n)]

    def handle(self, e):
        if self.back.handle(e) or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
            self.c.save()
            self.app.goto(self.back_to())
            return
        for b in self.buy:
            if b.handle(e):
                cid = b.pick
                res = self.c.buy(cid)
                if res is None:
                    self.message = "Not enough money."
                else:
                    name = CARDS[cid].name
                    self.message = {"new": f"Bought {name}.",
                                    "level": f"{name} is now level {self.c.player.cards[cid]}.",
                                    "refund": f"{name} was maxed, half refunded."}[res]
                    self.app.sounds.play("punch")
                    self.c.save()
                    self._build()
                return

    def draw(self, surf):
        surf.fill((14, 15, 22))
        text(surf, "CARD SHOP", (CX, 30), 48, WHITE, "midtop", display=True)
        text(surf, "New stock after every fight. Buying a card you own levels it up.", (CX, 92), 17,
             GREY, "midtop")
        text(surf, money(self.c.money), (W - 20, 24), 26, GOLD, "topright", bold=True)
        p = self.c.player
        if not self.c.shop:
            text(surf, "Sold out. Come back after your next fight.", (CX, 300), 22, GREY, "midtop")
        for cid, r, b in zip(self.c.shop, self._rects(), self.buy):
            have = p.cards.get(cid, 0)
            draw_card(surf, r, cid, max(1, have))
            note = f"Owned, level {have}" if have else "Not owned"
            text(surf, note, (r.centerx, r.bottom + 12), 15, GOLD if have else GREY, "midtop", bold=True)
            b.enabled = self.c.money >= PRICE[CARDS[cid].rarity]
            b.draw(surf)
        if self.message:
            text(surf, self.message, (CX, 610), 20, WHITE, "midtop", bold=True)
        self.back.draw(surf)
