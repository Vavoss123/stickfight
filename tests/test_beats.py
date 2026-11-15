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


class Reactive(unittest.TestCase):
    def test_a_first_round_finish_gets_a_scene_with_a_cooldown(self):
        c = career()
        win(c)
        beats_shown(c)
        win(c)
        self.assertIn("fast_finish", beats_shown(c))   # a round 1 KO is worth a word
        win(c)
        self.assertNotIn("fast_finish", beats_shown(c))   # but not after every single one

    def test_winning_while_hurt_gets_lou_talking(self):
        c = career()
        win(c)
        beats_shown(c)
        c.injury = {"name": "Broken hand", "stats": {"striking": 1}, "fights": 3}
        win(c)
        self.assertIn("won_hurt", beats_shown(c))
        joined = " ".join(l for _, l in story.lines("won_hurt", c.player, injury="Broken hand"))
        self.assertIn("broken hand", joined)

    def test_permanent_damage_gets_the_scar_scene(self):
        c = career()
        c.new_scar = True
        self.assertIn("scar", story.after_fight(c, False, False, False, False, 1))
        c.new_scar = False
        self.assertNotIn("scar", story.after_fight(c, False, False, False, False, 1))


class Callouts(unittest.TestCase):
    def test_a_rival_remembers_beating_you(self):
        import random
        c = career()
        rival = c.ladder[1]
        got = story.callout("Sam Cole", rival, random.Random(1),
                            last={"result": "Loss", "method": "KO"})
        self.assertIn("knocked", got)
        self.assertIn(rival.name, got)

    def test_a_rival_remembers_a_close_decision(self):
        import random
        c = career()
        got = story.callout("Sam Cole", c.ladder[1], random.Random(1),
                            last={"result": "Win", "method": "Decision"})
        self.assertIn("judges", got)

    def test_a_new_rival_speaks_in_their_own_voice(self):
        import random
        c = career()
        for rival in c.ladder[1:4]:
            got = story.callout("Sam Cole", rival, random.Random(1))
            self.assertIn("Sam Cole", got)
            self.assertIn(rival.name, got)

    def test_the_career_callout_uses_the_last_meeting(self):
        c = career()
        while c.rank() is None or c.rank() > 4:
            win(c)
        c.rival = None
        opp, *_ = c.next_fight()
        c.record_result(opp, False, False, "KO", "Power punch", 1)   # they knock you out
        self.assertEqual(c.rival, opp.name)
        self.assertTrue(any("knocked" in n for n in c.news), c.news)


class Endings(unittest.TestCase):
    def pick(self, titles=0, loyalty=50, fame=50, health=50):
        c = career()
        c.titles_won = titles
        c.loyalty, c.fame, c.health = loyalty, fame, health
        return story.ending(c)

    def test_the_meters_decide_the_ending(self):
        self.assertEqual(self.pick(), "end_quiet")
        self.assertEqual(self.pick(health=70), "end_walked_away")
        self.assertEqual(self.pick(titles=1, loyalty=60), "end_redemption")
        self.assertEqual(self.pick(titles=1, loyalty=75, health=65), "end_reconciled")
        self.assertEqual(self.pick(fame=70, loyalty=30), "end_famous")
        self.assertEqual(self.pick(titles=3, loyalty=90, health=20), "end_one_too_many")

    def test_every_ending_has_a_scene_and_a_hall_line(self):
        for eid, line in story.ENDINGS.items():
            self.assertIn(eid, story.BEATS)
            self.assertTrue(line)
        c = career()
        self.assertIn(story.ending(c), story.ENDINGS)

    def test_the_hall_entry_remembers_the_ending(self):
        from engine import legacy
        c = career()
        c.health = 20
        e = legacy.entry_for(c)
        self.assertEqual(e["ending"], story.ENDINGS["end_one_too_many"])

    def test_endings_never_queue_from_fights(self):
        c = career()
        for _ in range(6):
            win(c)
            for b in beats_shown(c):
                self.assertFalse(b.startswith("end_"), b)


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
