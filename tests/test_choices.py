"""Choice cards: the three meters, the cadence, and what each option really does."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine import choices
from engine.career import Career, new_player, PURSES


def career():
    return Career(new_player("Sam Cole", "The Hammer", "Striker", (200, 0, 0), "Leeds"), seed=1)


def win(c):
    opp, *_ = c.next_fight()
    return c.record_result(opp, True, False, "KO", "Power punch", 1)


class Cadence(unittest.TestCase):
    def test_no_card_at_the_very_start(self):
        self.assertIsNone(career().next_choice())

    def test_a_card_every_few_fights(self):
        c = career()
        dealt = 0
        for _ in range(12):
            win(c)
            cid = c.next_choice()
            if cid:
                dealt += 1
                self.assertIsNone(c.next_choice() if c.apply_choice(cid, 0) is None else None)
        self.assertGreaterEqual(dealt, 2)

    def test_answering_puts_the_cards_away(self):
        c = career()
        for _ in range(4):
            win(c)
        cid = c.next_choice()
        self.assertIsNotNone(cid)
        c.apply_choice(cid, 0)
        self.assertIsNone(c.next_choice())


class Effects(unittest.TestCase):
    def test_short_notice_doubles_the_purse_once(self):
        c = career()
        for _ in range(3):
            win(c)
        c.apply_choice("short_notice", 0)
        self.assertEqual(c.pending_purse, 2.0)
        self.assertEqual(c.camp_start()["stamina"], 65.0)
        kind = c.fight_kind()
        reward = win(c)
        self.assertEqual(reward["purse"], PURSES[kind][0] * 2)
        self.assertEqual(c.pending_purse, 1.0)
        self.assertEqual(c.pending_start, {})

    def test_turning_dez_down_builds_loyalty(self):
        c = career()
        before = c.loyalty
        c.apply_choice("short_notice", 1)
        self.assertGreater(c.loyalty, before)

    def test_the_doctor_can_heal_you(self):
        c = career()
        c.injury = {"name": "Broken hand", "stats": {"striking": 1}, "fights": 3}
        c.apply_choice("doctor", 0)
        self.assertIsNone(c.injury)

    def test_meters_stay_on_the_scale(self):
        c = career()
        c.health = 2
        c.apply_choice("doctor", 1)      # -8 health
        self.assertEqual(c.health, 0)
        c.fame = 98
        c.apply_choice("media_day", 0)   # +8 fame
        self.assertEqual(c.fame, 100)


class Presser(unittest.TestCase):
    def test_the_title_presser_always_happens(self):
        c = career()
        dealt = None
        for _ in range(40):
            if c.next_fight()[2]:
                break
            win(c)
            cid = c.next_choice()
            if cid == "presser":
                dealt = c.apply_choice("presser", 0)   # trash talk
            elif cid:
                c.apply_choice(cid, 0)
        self.assertTrue(c.next_fight()[2], "never reached a title shot")
        self.assertIsNotNone(dealt, "no presser before the title fight")
        self.assertEqual(c.camp_start()["hype"], 60.0)
        self.assertIsNone(c.next_choice())   # and it only happens once


class Saving(unittest.TestCase):
    def test_meters_and_cadence_survive_a_save(self):
        c = career()
        for _ in range(3):
            win(c)
        c.apply_choice("appearance", 1)
        d = Career.from_dict(c.to_dict())
        self.assertEqual((d.loyalty, d.fame, d.health), (c.loyalty, c.fame, c.health))
        self.assertEqual(d.last_choice, c.last_choice)
        self.assertEqual(d.choice_last, c.choice_last)
        self.assertIsNone(d.next_choice())


class Lines(unittest.TestCase):
    def test_every_option_has_the_pieces(self):
        for cid, d in choices.CHOICES.items():
            self.assertIn(d["speaker"], ("Coach Ray", "Lou", "Dez Harlan"), cid)
            self.assertTrue(d["title"] and d["intro"], cid)
            self.assertGreaterEqual(len(d["options"]), 2, cid)
            for opt in d["options"]:
                self.assertTrue(opt["label"] and opt["blurb"] and opt["response"], cid)
                self.assertTrue(opt["effects"], cid)


if __name__ == "__main__":
    unittest.main()
