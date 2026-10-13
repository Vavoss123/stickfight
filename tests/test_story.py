"""Rivals, training camp and the hall of fame."""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine import legacy
from engine.career import Career, new_player, GRUDGE_EVERY, RIVALRY_WINS


def career():
    return Career(new_player("Test Fighter", "", "Striker", (200, 0, 0), ""), seed=1)


def win(c):
    opp, *_ = c.next_fight()
    return opp, c.record_result(opp, True, False, "KO", "Power punch", 1)


def lose(c):
    opp, *_ = c.next_fight()
    return opp, c.record_result(opp, False, False, "KO", "Power punch", 1)


def get_ranked(c):
    while c.rank() is None:
        win(c)


class Rival(unittest.TestCase):
    def test_rival_calls_you_out_once_ranked(self):
        c = career()
        get_ranked(c)
        self.assertIsNotNone(c.rival)
        self.assertTrue(c.news and c.rival in c.news[0])
        rival = c.rival_profile()
        self.assertLess(c.ladder.index(rival), c.rank())   # someone above you

    def test_whoever_beats_you_becomes_the_rival(self):
        c = career()
        get_ranked(c)
        win(c)
        win(c)            # high enough that a loss keeps you ranked
        c.rival = None
        opp, _ = lose(c)
        self.assertEqual(c.rival, opp.name)
        self.assertEqual(c.rival_record, [0, 1])

    def test_grudge_match_comes_round(self):
        c = career()
        get_ranked(c)
        rival = c.rival
        labels = []
        for _ in range(GRUDGE_EVERY + 1):
            opp, *_, label = c.next_fight()
            labels.append(label)
            if label == "Grudge match":
                self.assertEqual(opp.name, rival)
                break
            win(c)
        self.assertIn("Grudge match", labels)

    def test_fighting_your_rival_in_the_rankings_is_a_grudge_match(self):
        c = career()
        get_ranked(c)
        for _ in range(10):
            opp, *_, label = c.next_fight()
            if c.rival and opp.name == c.rival:
                self.assertEqual(label, "Grudge match")
                return
            win(c)

    def test_grudge_win_pays_more_and_settles(self):
        c = career()
        get_ranked(c)
        win(c)
        rival = c.rival
        wins = 0
        for _ in range(30):
            opp, *_rest, label = c.next_fight()
            normal_purse = None
            _, reward = win(c)
            if label == "Grudge match":
                wins += 1
                self.assertGreater(reward["bonus"], reward["purse"])
                if wins >= RIVALRY_WINS:
                    break
        self.assertEqual(wins, RIVALRY_WINS)
        self.assertIsNone(c.rival)
        self.assertTrue(any("settled" in n for n in c.news))
        self.assertNotEqual(rival, None)

    def test_rival_survives_save(self):
        c = career()
        get_ranked(c)
        lose(c)
        back = Career.from_dict(c.to_dict())
        self.assertEqual(back.rival, c.rival)
        self.assertEqual(back.rival_record, c.rival_record)


class Camp(unittest.TestCase):
    def _title_shot(self):
        c = career()
        for _ in range(40):
            if c.next_fight()[2]:
                return c
            win(c)
        self.fail("never got a title shot")

    def test_camp_before_title_fight(self):
        c = self._title_shot()
        self.assertTrue(c.camp_due())
        before = c.player.stats.striking
        c.camp = "striking"
        self.assertFalse(c.camp_due())
        boosted = c.fighter_for_fight()
        self.assertEqual(boosted.stats.striking, min(10, before + 1))
        self.assertEqual(c.player.stats.striking, before)   # only for this fight
        win(c)
        self.assertIsNone(c.camp)

    def test_no_camp_for_normal_fights(self):
        c = career()
        self.assertFalse(c.camp_due())
        self.assertIs(c.fighter_for_fight(), c.player)


class HallOfFame(unittest.TestCase):
    def test_champion_is_inducted(self):
        c = career()
        for _ in range(40):
            win(c)
            if c.is_champ():
                break
        self.assertEqual(c.titles_won, 1)
        self.assertEqual(c.best_rank, 0)
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "hall.json")
            e = legacy.retire(c, path)
            self.assertTrue(e["inducted"])
            hall = legacy.load(path)
            self.assertEqual(hall[0]["name"], "Test Fighter")

    def test_short_career_is_remembered_not_inducted(self):
        c = career()
        lose(c)
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "hall.json")
            e = legacy.retire(c, path)
            self.assertFalse(e["inducted"])
            self.assertEqual(len(legacy.load(path)), 1)

    def test_hall_is_sorted_by_legacy(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "hall.json")
            weak = career()
            lose(weak)
            legacy.retire(weak, path)
            strong = career()
            for _ in range(8):
                win(strong)
            legacy.retire(strong, path)
            hall = legacy.load(path)
            self.assertGreater(hall[0]["score"], hall[1]["score"])

    def test_broken_hall_file(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "hall.json")
            with open(path, "w") as f:
                f.write("not json")
            self.assertEqual(legacy.load(path), [])


if __name__ == "__main__":
    unittest.main()
