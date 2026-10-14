"""Deck builder, card packs and the card shop for career mode."""

import pygame

from engine.cards import (CARDS, GROUPS, MAX_PERKS, MAX_LEVEL, PRICE, deck_points,
                          group_of, group_slots, variants, warnings)
from engine.career import GLOVES, GLOVE_PRICE, RESTOCK_PRICE
from engine.moves import MOVES

from ..cards import draw_card, RARITY_COLOR, CLASS_BG, PERK_BG
from ..common import W, H, CX, GOLD, WHITE, GREY, GREEN, text, text_block, panel, Button, bar
from .base import Scene

TABS = [g for g, _ in GROUPS] + ["Perks"]
CW, CH = 150, 232          # card size for the choices, four to a row
STRIP_Y = 462              # where the active deck strip starts
CHIP_W, CHIP_H = 196, 44


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
        self.reset = (Button((20, H - 104, 140, 38), "Reset deck", size=16)
                      if hasattr(career, "reset") else None)
        # Quick fight decks can use every card or only the ones earned in careers
        self.pool_btn = (Button((W - 330, 66, 310, 34), "", size=15, color=(60, 50, 110))
                         if hasattr(career, "set_pool") else None)
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
        slots = self._slots()
        step = min(34, (STRIP_Y - 10 - 132) // max(1, len(slots)))
        for k, base in enumerate(slots):
            out.append((base, pygame.Rect(20, 132 + k * step, 560, step - 4)))
        return out

    def _card_rects(self, ids):
        out = []
        per_row = 4
        for k, cid in enumerate(ids):
            x = 610 + (k % per_row) * (CW + 12)
            y = 132 + (k // per_row) * (CH + 12)
            out.append((cid, pygame.Rect(x, y, CW, CH)))
        return out

    def _perk_rects(self, ids):
        out = []
        for k, cid in enumerate(ids):
            x = 610 + (k % 3) * 216
            y = 132 + (k // 3) * 40
            out.append((cid, pygame.Rect(x, y, 208, 36)))
        return out

    def _active(self):
        """Everything in the deck right now: (kind, slot or perk id, card id)."""
        p = self.c.player
        out = []
        for group, _ in GROUPS:
            for slot in group_slots(group):
                if slot in p.deck:
                    out.append(("move", slot, p.deck[slot]))
        out += [("perk", pid, pid) for pid in p.perks]
        return out

    def _chip_rects(self):
        out = []
        for k, item in enumerate(self._active()):
            x = 34 + (k % 6) * (CHIP_W + 8)
            y = STRIP_Y + 34 + (k // 6) * (CHIP_H + 8)
            out.append((item, pygame.Rect(x, y, CHIP_W, CHIP_H)))
        return out

    def _open(self, item):
        """Clicking a card in the active deck opens what can replace it."""
        kind, key, cid = item
        if kind == "perk":
            self.tab = TABS.index("Perks")
            self.slot = None
        else:
            self.tab = TABS.index(group_of(key))
            self.slot = key
        self.message = ""
        self.app.sounds.play("click")

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
        if self.pool_btn and self.pool_btn.handle(e):
            new = "collection" if self.c.pool == "all" else "all"
            self.c.set_pool(new)
            self.c.save()
            self.app.settings["card_pool"] = new
            self.app.settings.save()
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
        for item, r in self._chip_rects():
            if r.collidepoint(e.pos):
                self._open(item)
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
        text(surf, f"Deck points {pts} of {budget}", (W - 330, 14), 18, WHITE, bold=True)
        bar(surf, (W - 330, 40, 310, 12), pts / max(1, budget), GREEN if pts <= budget else (220, 60, 60))
        if self.pool_btn:
            self.pool_btn.label = ("Cards: all unlocked (switch to my collection)" if c.pool == "all"
                                   else "Cards: my collection (switch to all)")
            self.pool_btn.draw(surf)
        if c.money is not None:
            text(surf, money(c.money), (W - 20, 20), 18, GOLD, "topright", bold=True)
        for k, b in enumerate(self.tab_buttons):
            b.selected = k == self.tab
            b.draw(surf)

        if TABS[self.tab] == "Perks":
            self._draw_perks(surf)
        else:
            self._draw_slots(surf)
        self._draw_active(surf)

        y = H - 96
        for w in warnings(p):
            text(surf, w, (180, y), 16, (255, 170, 60), bold=True)
            y += 22
        if self.message:
            text(surf, self.message, (180, H - 44), 17, (255, 120, 100), bold=True)
        else:
            hint = getattr(c, "hint", "Cards cost 1 to 3 points by how strong they are. "
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

    def _draw_active(self, surf):
        p = self.c.player
        r = panel(surf, (20, STRIP_Y, W - 40, 142), (18, 30, 22), alpha=230, border=GREEN)
        text(surf, "ACTIVE DECK", (r.x + 14, r.y + 8), 17, GREEN, bold=True)
        text(surf, "Click a card to see what can replace it", (r.x + 140, r.y + 10), 14, GREY)
        chips = self._chip_rects()
        if not chips:
            text(surf, "Nothing equipped yet. Pick a slot above and choose a card.", (r.centerx, r.y + 64),
                 16, GREY, "midtop")
        for (kind, key, cid), c in chips:
            card = CARDS[cid]
            open_now = (kind == "move" and key == self.slot and TABS[self.tab] != "Perks") or \
                       (kind == "perk" and TABS[self.tab] == "Perks")
            bg = PERK_BG if kind == "perk" else CLASS_BG[card.move.cls]
            pygame.draw.rect(surf, bg, c, border_radius=8)
            pygame.draw.rect(surf, WHITE if open_now else RARITY_COLOR[card.rarity], c,
                             3 if open_now else 2, border_radius=8)
            text(surf, card.name, (c.x + 10, c.y + 5), 15, WHITE, bold=True, max_width=c.w - 54)
            lvl = p.cards.get(cid, 1)
            text(surf, f"L{lvl}", (c.right - 10, c.y + 6), 14, GOLD, "topright", bold=True)
            sub = "Perk" if kind == "perk" else f"Replaces {MOVES[key].name}"
            text(surf, f"{sub}, {card.points} pt", (c.x + 10, c.y + 25), 12, (200, 205, 215),
                 max_width=c.w - 20)

    def _draw_perks(self, surf):
        p = self.c.player
        text(surf, f"Equipped perks ({len(p.perks)} of {MAX_PERKS})", (20, 132), 18, WHITE, bold=True)
        for k in range(MAX_PERKS):
            r = pygame.Rect(20, 166 + k * 50, 560, 42)
            pygame.draw.rect(surf, (26, 28, 38), r, border_radius=6)
            if k < len(p.perks):
                card = CARDS[p.perks[k]]
                text(surf, card.name, (r.x + 12, r.centery), 18, RARITY_COLOR[card.rarity], "midleft", bold=True)
                text(surf, f"L{p.cards.get(card.id, 1)}  {card.points} pt",
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
            text(surf, f"{card.name}  L{lvl}", (r.x + 8, r.y + 2), 14, WHITE, bold=True, max_width=150)
            text(surf, f"{card.points} pt" + (" ON" if on else ""), (r.right - 8, r.y + 3), 12,
                 GOLD if on else GREY, "topright", bold=True)
            from engine.cards import perk_text
            text(surf, perk_text(card, lvl), (r.x + 8, r.y + 19), 11, (200, 210, 215), max_width=r.w - 16)


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
        self.chosen_t = 0.0
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
                        self._picked_sound()
            if e.type == pygame.KEYDOWN and e.key in (pygame.K_1, pygame.K_2, pygame.K_3) and self.t > 0.8:
                k = e.key - pygame.K_1
                if k < len(self.cards):
                    self.chosen = self.cards[k]
                    self.result = self.c.gain_card(self.chosen)
                    self.c.save()
                    self._picked_sound()
            if not self.cards:
                self.app.goto(self.then())
            return
        if self.done.handle(e) or (e.type == pygame.KEYDOWN and e.key in (pygame.K_RETURN, pygame.K_SPACE)):
            self.app.goto(self.then())

    def _picked_sound(self):
        self.chosen_t = 0.0
        self.app.sounds.play({"new": "levelup", "level": "levelup", "refund": "cash"}[self.result])
        if self.result == "new" and CARDS[self.chosen].rarity == "legendary":
            self.app.sounds.play("roar", 0.8)

    def _legendary(self, cid):
        return CARDS[cid].rarity == "legendary"

    def update(self, dt):
        # A flick for each card as it turns over, and a roar when a legendary shows up
        for k, cid in enumerate(self.cards):
            flip_at = k * 0.2 + 1 / 6
            shown_at = k * 0.2 + 1 / 3
            if self.t < flip_at <= self.t + dt:
                self.app.sounds.play("flip")
            if self._legendary(cid) and self.t < shown_at <= self.t + dt:
                self.app.sounds.play("boom", 0.6)
                self.app.sounds.play("roar", 0.7)
        self.t += dt
        self.chosen_t += dt

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
            if self._legendary(cid):
                self._glow(surf, r, self.t - (k * 0.2 + 1 / 3))
            draw_card(surf, r, cid, max(1, have), selected=cid == self.chosen)
            if self._legendary(cid) and self.chosen is None:
                text(surf, "LEGENDARY!", (r.centerx, r.y - 30), 26, GOLD, "midtop", display=True)
            if self.chosen is None:
                note, col = card_note(self.c, cid)
                if self.c.in_deck(cid):
                    pygame.draw.rect(surf, GOLD, r.inflate(10, 10), 3, border_radius=12)
                text(surf, note, (r.centerx, r.bottom + 10), 15, col, "midtop", bold=True)
                text(surf, str(k + 1), (r.centerx, r.bottom + 32), 14, GREY, "midtop")
        if self.chosen is not None and self.result == "new":
            self._new_card_banner(surf)
        if self.chosen is not None:
            name = CARDS[self.chosen].name
            msg = {"new": f"{name} added to your collection.",
                   "level": f"{name} levelled up to level {p.cards[self.chosen]}!",
                   "refund": f"{name} is already maxed. Sold for {money(PRICE[CARDS[self.chosen].rarity] // 2)}."}[self.result]
            text(surf, msg, (CX, 540), 22, WHITE, "midtop", bold=True)
            tip = "It is in your deck, so it is already working for you." if self.c.in_deck(self.chosen) \
                else "Equip it from the Deck screen."
            text(surf, tip, (CX, 574), 16, GREY, "midtop")
            self.done.draw(surf)


    def _glow(self, surf, r, age):
        """Gold rays behind a legendary card. They burst out, then keep pulsing."""
        import math
        if age < 0:
            return
        burst = min(1.0, age * 3)
        pulse = 0.75 + 0.25 * math.sin(self.t * 5)
        size = int(max(r.w, r.h) * (0.9 + 0.5 * burst))
        g = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
        c = (size, size)
        for k in range(16):
            a = self.t * 0.6 + k * math.pi / 8
            tip = (c[0] + math.cos(a) * size, c[1] + math.sin(a) * size)
            left = (c[0] + math.cos(a - 0.08) * size * 0.2, c[1] + math.sin(a - 0.08) * size * 0.2)
            right = (c[0] + math.cos(a + 0.08) * size * 0.2, c[1] + math.sin(a + 0.08) * size * 0.2)
            pygame.draw.polygon(g, (240, 196, 60, int(70 * pulse * burst)), [left, tip, right])
        pygame.draw.circle(g, (255, 220, 120, int(28 * pulse * burst)), c, int(size * 0.42))
        surf.blit(g, (r.centerx - size, r.centery - size))

    def _new_card_banner(self, surf):
        """NEW CARD! slams in over the pack, then settles."""
        t = self.chosen_t
        if t > 2.2:
            return
        scale = 1.0 + max(0.0, 0.4 - t) * 2.5     # starts big and lands
        alpha = 255 if t < 1.6 else int(255 * (2.2 - t) / 0.6)
        size = int(46 * scale)
        legend = self._legendary(self.chosen)
        label = "NEW LEGENDARY!" if legend else "NEW CARD!"
        text(surf, label, (CX, 140), size, GOLD if legend else WHITE, "center", display=True,
             alpha=max(0, alpha))


def card_note(c, cid):
    """Owned or not, in the active deck or not, and what the next copy does."""
    p = c.player
    have = p.cards.get(cid, 0)
    deck = c.in_deck(cid)
    if not have:
        return "New card", GREEN
    if have >= MAX_LEVEL:
        return "Maxed", GREY
    where = "IN YOUR DECK" if deck else "Not in your deck"
    return f"{where}  L{have} > L{have + 1}", GOLD if deck else (200, 200, 210)


class ShopScene(Scene):
    def __init__(self, app, career, back):
        super().__init__(app)
        self.c = career
        self.back_to = back
        self.message = ""
        self.back = Button((20, H - 56, 140, 42), "Done", color=(40, 110, 60), size=18)
        self.glove_pick = 0
        self._build()

    def _build(self):
        self.buy = []
        cards = self.c.shop_cards()
        n = len(cards)
        w = 230
        x0 = CX - (n * w + (n - 1) * 24) // 2
        for k, cid in enumerate(cards):
            b = Button((x0 + k * (w + 24), 500, w, 40), f"Buy {money(PRICE[CARDS[cid].rarity])}",
                       color=(150, 110, 30), size=17)
            b.pick = cid
            self.buy.append(b)
        # Other ways to spend
        self.extras = []
        for k, pick in enumerate(("training", "deck", "restock", "gloves")):
            b = Button((180 + k * 270, 580, 258, 56), "", sub="", size=17, color=(52, 58, 92))
            b.pick = pick
            self.extras.append(b)

    def _rects(self):
        n = len(self.c.shop)
        w = 230
        x0 = CX - (n * w + (n - 1) * 24) // 2
        return [pygame.Rect(x0 + k * (w + 24), 130, w, 324) for k in range(n)]

    def _glove_name(self):
        return list(GLOVES)[self.glove_pick % len(GLOVES)]

    def _extra(self, pick):
        c = self.c
        if pick == "training":
            ok = c.buy_training()
            return "One extra training point. Spend it on the hub." if ok else "Not enough money."
        if pick == "deck":
            if c.deck_point_price() is None:
                return "You already have every extra deck point."
            ok = c.buy_deck_point()
            return f"Deck budget is now {c.budget()} points." if ok else "Not enough money."
        if pick == "restock":
            ok = c.restock()
            if ok:
                self._build()
            return "Fresh stock." if ok else "Not enough money."
        name = self._glove_name()
        owned = name in c.gloves_owned
        ok = c.buy_gloves(name)
        if not ok:
            return "Not enough money."
        self.glove_pick += 1 if owned else 0
        return f"{name} gloves on." if not owned else f"{name} gloves on. Click again for the next colour."

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
                    lv = self.c.player.cards[cid]
                    deck = " It is in your deck." if self.c.in_deck(cid) else " Equip it from the Deck screen."
                    self.message = (f"Bought {name}." if res == "new" else f"{name} is now level {lv}.") + deck
                    self.app.sounds.play("cash")
                    self.c.save()
                    self._build()
                return
        for b in self.extras:
            if b.handle(e):
                self.message = self._extra(b.pick)
                self.app.sounds.play("cash" if not self.message.startswith("Not") else "click")
                self.c.save()
                return

    def draw(self, surf):
        surf.fill((14, 15, 22))
        c = self.c
        text(surf, "CARD SHOP", (CX, 20), 44, WHITE, "midtop", display=True)
        text(surf, self.message or "New stock after every fight. Buying a card you own levels it up.",
             (CX, 76), 17, WHITE if self.message else GREY, "midtop", bold=bool(self.message))
        text(surf, money(c.money), (W - 20, 24), 26, GOLD, "topright", bold=True)
        cards = c.shop
        if not cards:
            text(surf, "Sold out. Restock below or come back after your next fight.", (CX, 280), 20,
                 GREY, "midtop")
        p = c.player
        for cid, r, b in zip(cards, self._rects(), self.buy):
            have = p.cards.get(cid, 0)
            if c.in_deck(cid):
                pygame.draw.rect(surf, GOLD, r.inflate(10, 10), 3, border_radius=12)
            draw_card(surf, r, cid, max(1, have))
            note, col = card_note(c, cid)
            text(surf, note, (r.centerx, r.bottom + 10), 15, col, "midtop", bold=True)
            b.enabled = c.money >= PRICE[CARDS[cid].rarity]
            b.draw(surf)
        text(surf, "MORE WAYS TO SPEND", (180, 556), 15, GOLD, bold=True)
        for b in self.extras:
            if b.pick == "training":
                b.label, b.sub = "Extra training point", f"{money(c.training_price())}, {c.points} now"
                b.enabled = c.money >= c.training_price()
            elif b.pick == "deck":
                price = c.deck_point_price()
                b.label = "Extra deck point"
                b.sub = f"{money(price)}, budget {c.budget()}" if price else f"Maxed, budget {c.budget()}"
                b.enabled = price is not None and c.money >= price
            elif b.pick == "restock":
                b.label, b.sub = "Restock the shop", money(RESTOCK_PRICE)
                b.enabled = c.money >= RESTOCK_PRICE
            else:
                name = self._glove_name()
                owned = name in c.gloves_owned
                b.label = f"{name} gloves"
                b.sub = "Owned, click to wear" if owned else f"{money(GLOVE_PRICE)}, just for looks"
                b.enabled = owned or c.money >= GLOVE_PRICE
            b.draw(surf)
            if b.pick == "gloves":
                pygame.draw.circle(surf, GLOVES[self._glove_name()], (b.rect.right - 20, b.rect.centery), 9)
        self.back.draw(surf)
