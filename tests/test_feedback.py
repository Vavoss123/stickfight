"""Playtest fixes: level 5 cards, new perks, the shop, money sinks and spare points."""

import os
import random
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.cards import CARDS, MAX_LEVEL, build_kit, leveled, perk_text
from engine.career import (Career, new_player, MAX_BONUS_DECK, POINTS_PER_DECK_POINT, POINTS_PER_PACK,
                           RESTOCK_PRICE, GLOVES, GLOVE_PRICE)
from engine.constants import STANDING, CLINCH
from engine.fighter import FighterState
from engine.moves import MOVES
from engine.resolve import resolve
from engine.roster import quick_fighters
from engine.state import FightState


def career():
    return Career(new_player("Test Fighter", "", "Striker", (200, 0, 0), ""), seed=1)


class LevelFive(unittest.TestCase):
    def test_every_perk_has_five_levels(self):
        for c in CARDS.values():
            if c.is_perk:
                self.assertEqual(len(c.perk), MAX_LEVEL, c.id)
                self.assertTrue(perk_text(c, MAX_LEVEL))

    def test_levels_keep_improving_but_taper(self):
        m = CARDS["superman"].move
        dmg = [leveled(m, lv).dmg for lv in range(1, MAX_LEVEL + 1)]
        self.assertEqual(dmg, sorted(dmg))
        self.assertGreater(dmg[2] - dmg[1], dmg[4] - dmg[3])   # 4 and 5 add less

    def test_level_three_unchanged(self):
        m = CARDS["superman"].move
        self.assertAlmostEqual(leveled(m, 3).dmg, m.dmg * 1.2)


class NewPerks(unittest.TestCase):
    def _pair(self, perks0=(), perks1=()):
        r = quick_fighters()
        a, b = r[0], r[1]
        a.perks, b.perks = list(perks0), list(perks1)
        for pid in list(perks0) + list(perks1):
            a.cards[pid] = b.cards[pid] = 3
        return FightState([FighterState(a), FighterState(b)])

    def test_slick_is_harder_to_hit(self):
        def landed(perks):
            n = 0
            for seed in range(300):
                st = self._pair(perks1=perks)
                n += resolve(st, ("cross", "takedown"), random.Random(seed)).landed[0]
            return n
        self.assertLess(landed(["slick"]), landed([]))

    def test_sprawl_stops_takedowns(self):
        def stuffed(perks):
            n = 0
            for seed in range(300):
                st = self._pair(perks1=perks)
                n += resolve(st, ("takedown", "block"), random.Random(seed)).stuffed[0]
            return n
        self.assertGreater(stuffed(["sprawl"]), stuffed([]))

    def test_iron_will_in_the_contest(self):
        from engine.resolve import sub_edge

        def edge(perks):
            st = self._pair(perks1=perks)
            st.pos = CLINCH
            return sub_edge(st.f[0], st.f[1], st.f[0].move("guillotine"))
        self.assertLess(edge(["ironwill"]), edge([]))

    def test_feint_master_drains(self):
        st = self._pair(perks0=["feintmaster"])
        st.f[1].stamina = 60
        resolve(st, ("feint", "block"), random.Random(1))
        self.assertLess(st.f[1].stamina, 60)


class Shop(unittest.TestCase):
    def test_maxed_cards_leave_the_shop(self):
        c = career()
        c.shop = ["twister", "slick"]
        c.player.cards["twister"] = MAX_LEVEL
        self.assertEqual(c.shop_cards(), ["slick"])
        c.money = 10 ** 6
        c.shop = ["twister"]
        self.assertIsNone(c.buy("twister"))

    def test_packs_skip_maxed_cards(self):
        c = career()
        for cid in CARDS:
            c.player.cards[cid] = MAX_LEVEL
        c.player.cards["slick"] = 1
        for _ in range(20):
            self.assertTrue(set(c.make_pack()) <= {"slick"})

    def test_in_deck(self):
        c = career()
        cid = next(iter(c.player.deck.values()))
        self.assertTrue(c.in_deck(cid))
        self.assertFalse(c.in_deck("twister"))


class Spending(unittest.TestCase):
    def test_training_points_get_dearer(self):
        c = career()
        c.money = 10 ** 7
        first = c.training_price()
        self.assertTrue(c.buy_training())
        self.assertGreater(c.training_price(), first)
        self.assertEqual(c.points, 1)

    def test_deck_points_are_capped(self):
        c = career()
        c.money = 10 ** 9
        base = c.budget()
        for _ in range(MAX_BONUS_DECK):
            self.assertTrue(c.buy_deck_point())
        self.assertFalse(c.buy_deck_point())
        self.assertIsNone(c.deck_point_price())
        self.assertEqual(c.budget(), base + MAX_BONUS_DECK)

    def test_restock_and_gloves(self):
        c = career()
        c.money = RESTOCK_PRICE + GLOVE_PRICE
        self.assertTrue(c.restock())
        self.assertTrue(c.buy_gloves("Gold"))
        self.assertEqual(c.player.gloves, GLOVES["Gold"])
        self.assertTrue(c.buy_gloves("Gold"))      # owned, free to put back on
        self.assertFalse(c.buy_gloves("Pink"))     # no money left

    def test_spare_training_points(self):
        c = career()
        c.points = POINTS_PER_DECK_POINT + POINTS_PER_PACK
        base = c.budget()
        self.assertTrue(c.trade_for_deck_point())
        self.assertEqual(c.budget(), base + 1)
        self.assertTrue(c.trade_for_pack())
        self.assertEqual(c.points, 0)
        self.assertFalse(c.trade_for_pack())

    def test_spending_survives_save(self):
        c = career()
        c.money = 10 ** 7
        c.buy_deck_point()
        c.buy_training()
        c.buy_gloves("Black")
        back = Career.from_dict(c.to_dict())
        self.assertEqual((back.bonus_deck, back.bought_training, back.gloves_owned),
                         (1, 1, ["Black"]))
        self.assertEqual(back.player.gloves, GLOVES["Black"])


if __name__ == "__main__":
    unittest.main()
