"""The gym and the career's story beats."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine import story
from engine.career import Career, new_player, GYM_REPS, MAX_BONUS_DECK


def career():
    return Career(new_player("Sam Okoro", "", "Striker", (200, 0, 0), ""), seed=1)


def win(c):
    opp, *_ = c.next_fight()
    c.record_result(opp, True, False, "KO", "Power punch", 1)


def lose(c):
    opp, *_ = c.next_fight()
    c.record_result(opp, False, False, "KO", "Power punch", 1)


class Gym(unittest.TestCase):
    def test_the_gym_is_free_but_gets_harder_with_your_budget(self):
        c = career()
        easy = c.gym_level()
        money = c.money
        c.bonus_deck = 4
        self.assertGreater(c.gym_level(), easy)
        self.assertTrue(c.start_gym())
        self.assertEqual(c.money, money)

    def test_difficulty_is_capped(self):
        c = career()
        self.assertEqual(c.gym_level(), 0.0)
        c.bonus_deck = MAX_BONUS_DECK
        c.ladder.remove(c.player) if c.player in c.ladder else None
        self.assertLessEqual(c.gym_level(), 1.0)

    def test_one_session_between_fights(self):
        c = career()
        self.assertTrue(c.start_gym())
        self.assertIsNotNone(c.gym_open())
        self.assertFalse(c.start_gym())
        win(c)
        self.assertIsNone(c.gym_open())

    def test_rewards(self):
        c = career()
        before = c.budget()
        c.gym_reward(GYM_REPS)
        self.assertEqual(c.budget(), before + 1)
        self.assertEqual(c.points, 1)
        c.gym_reward(5)
        self.assertEqual(c.points, 3)
        c.gym_reward(0)
        self.assertEqual(c.points, 3)

    def test_maxed_deck_gives_points_instead(self):
        c = career()
        c.bonus_deck = MAX_BONUS_DECK
        c.gym_reward(GYM_REPS)
        self.assertEqual(c.bonus_deck, MAX_BONUS_DECK)
        self.assertEqual(c.points, 2)


class Story(unittest.TestCase):
    def test_intro_first(self):
        c = career()
        self.assertEqual(c.next_story(), "intro")
        self.assertIsNone(c.next_story())

    def test_first_win_and_loss_once(self):
        c = career()
        c.next_story()
        win(c)
        self.assertIn("first_win", c.story_queue)
        while c.next_story():
            pass
        win(c)
        lose(c)
        beats = []
        while True:
            b = c.next_story()
            if not b:
                break
            beats.append(b)
        self.assertIn("first_loss", beats)
        self.assertNotIn("first_win", beats)

    def test_ranked_beat(self):
        c = career()
        while c.rank() is None:
            win(c)
        self.assertIn("ranked", c.story_queue)

    def test_lines_fill_in_names(self):
        c = career()
        for who, line in story.lines("intro", c.player):
            self.assertNotIn("{", line)
        self.assertIn("Sam", " ".join(l for _, l in story.lines("intro", c.player)))

    def test_survives_save(self):
        c = career()
        c.next_story()
        c.gym_used = True
        back = Career.from_dict(c.to_dict())
        self.assertIn("intro", back.story_seen)
        self.assertTrue(back.gym_used)


if __name__ == "__main__":
    unittest.main()
