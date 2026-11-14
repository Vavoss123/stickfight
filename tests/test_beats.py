"""The story beat engine: Act 1 (the rent, Lou, Dez), triggers and repeats."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine import story
from engine.career import Career, new_player


def career():
    return Career(new_player("Sam Cole", "The Hammer", "Striker", (200, 0, 0), "Leeds"), seed=1)


def win(c):
    opp, *_ = c.next_fight()
    c.record_result(opp, True, False, "KO", "Power punch", 1)


def lose(c):
    opp, *_ = c.next_fight()
    c.record_result(opp, False, False, "KO", "Power punch", 1)


def beats_shown(c):
    out = []
    while True:
        b = c.next_story()
        if b is None:
            return out
        out.append(b)


class ActOne(unittest.TestCase):
    def test_the_first_three_wins_tell_the_rent_story(self):
        c = career()
        self.assertEqual(c.next_story(), "intro")
        win(c)
        self.assertIn("first_win", beats_shown(c))
        win(c)
        self.assertIn("dez", beats_shown(c))
        win(c)
        self.assertIn("rent_paid", beats_shown(c))

    def test_getting_ranked_closes_the_act(self):
        c = career()
        seen = []
        for _ in range(30):
            if c.rank() is not None:
                break
            win(c)
            seen += beats_shown(c)
        self.assertIn("ranked", seen)

    def test_a_beat_shows_only_once(self):
        c = career()
        win(c)
        self.assertIn("first_win", beats_shown(c))
        win(c)
        self.assertNotIn("first_win", beats_shown(c))

    def test_losing_streak_comes_back(self):
        self.assertTrue(story.repeats("losing_streak"))
        self.assertFalse(story.repeats("first_win"))


class Scripts(unittest.TestCase):
    def test_every_script_formats_and_speaks(self):
        c = career()
        for beat, d in story.BEATS.items():
            for k in range(len(d["scripts"])):
                c.player.wins = k    # rotate the variants
                c.player.losses = 0
                got = story.lines(beat, c.player, rival="Vik Petrov", champ="Dante Vale")
                self.assertTrue(got, beat)
                for who, line in got:
                    self.assertIn(who, story.CHARACTERS, beat)
                    self.assertNotIn("{", line, beat)
                    self.assertLess(len(line), 110, beat)

    def test_name_is_filled_in(self):
        c = career()
        joined = " ".join(l for _, l in story.lines("intro", c.player))
        self.assertIn("Sam", joined)


if __name__ == "__main__":
    unittest.main()
