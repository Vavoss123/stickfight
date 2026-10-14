"""The coach's card ideas between rounds, and the swap limit."""

import copy
import os
import random
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine import coach
from engine.cards import deck_points
from engine.corner import advice
from engine.fight import Fight
from engine.roster import quick_fighters


def fight_where(red_picks, blue_picks, own=(), red=None):
    """A round of the same picks over and over, then the break."""
    r = quick_fighters()
    p0 = red or r[0]
    for cid in own:
        p0.cards[cid] = 1
    f = Fight(p0, r[1], seed=1)
    while not f.between_rounds and not f.over:
        def pick(i, wanted):
            # By the basic move, so a card like Double Leg Blast counts as a takedown
            opts = f.options(i)
            bases = {f.state.f[i].move(k).base: k for k in opts} if not f.state.sub else {}
            return next((bases[w] for w in wanted if w in bases), opts[0])
        f.play((pick(0, red_picks), pick(1, blue_picks)))
    return f


class Coach(unittest.TestCase):
    def test_sprawl_against_a_wrestler(self):
        f = fight_where(["jab"], ["takedown", "posture", "gnp"], own=["sprawl"])
        ideas = coach.suggest(f, 0, budget=20)
        self.assertTrue(any(s.card == "sprawl" for s in ideas), [s.text() for s in ideas])

    def test_only_cards_you_own(self):
        f = fight_where(["jab"], ["takedown", "posture", "gnp"])
        p = f.profiles[0]
        for s in coach.suggest(f, 0, budget=20):
            self.assertIn(s.card, p.cards)

    def test_respects_the_budget(self):
        f = fight_where(["jab"], ["takedown", "posture", "gnp"], own=["sprawl", "ironlungs"])
        tight = deck_points(f.profiles[0])
        for s in coach.suggest(f, 0, budget=tight):
            trial = copy.deepcopy(f.profiles[0])
            s.apply(trial)
            self.assertLessEqual(deck_points(trial), tight)

    def test_full_perks_name_one_to_drop(self):
        f = fight_where(["jab"], ["takedown", "posture", "gnp"], own=["sprawl", "base", "gastank"])
        f.profiles[0].perks = ["combo", "base", "gastank"]
        for cid in f.profiles[0].perks:
            f.profiles[0].cards[cid] = 1
        ideas = [s for s in coach.suggest(f, 0, budget=30) if s.card == "sprawl"]
        self.assertTrue(ideas)
        self.assertIn(ideas[0].out, ("combo", "base", "gastank"))
        p = copy.deepcopy(f.profiles[0])
        ideas[0].apply(p)
        self.assertEqual(len(p.perks), 3)
        self.assertIn("sprawl", p.perks)

    def test_changes_count(self):
        r = quick_fighters()
        a = copy.deepcopy(r[0])
        b = copy.deepcopy(a)
        self.assertEqual(coach.changes(a, b), 0)
        b.deck["kick"] = "showtime"
        self.assertEqual(coach.changes(a, b), 1)
        b.perks = ["sprawl"]          # swapped the one perk for another
        self.assertEqual(coach.changes(a, b), 2)

    def test_refit_changes_the_moves_mid_fight(self):
        f = fight_where(["jab"], ["jab"])
        p = f.profiles[0]
        hp = f.state.f[0].hp
        p.cards["showtime"] = 1
        p.deck["kick"] = "showtime"
        f.refit(0, p)
        f.start_next_round()
        self.assertIn("showtime", f.options(0))
        self.assertLessEqual(f.state.f[0].hp, 100)
        self.assertGreaterEqual(f.state.f[0].hp, hp)   # damage kept, only the break heals

    def test_corner_talks_neutrally(self):
        f = fight_where(["jab"], ["takedown", "posture", "gnp"])
        for tip in advice(f, 0) + advice(f, 1):
            for word in (" he ", " his ", " him ", "He's", "He "):
                self.assertNotIn(word, f" {tip} ")


class Dialogue(unittest.TestCase):
    def test_every_personality_has_something_to_say(self):
        import random
        from engine import personality
        for event in personality.LINES:
            for name in personality.NAMES:
                self.assertTrue(personality.line(name, event, random.Random(1)), (name, event))

    def test_scouting_report(self):
        from engine.roster import division
        me = quick_fighters()[0]
        for cid in ("sprawl", "ironwill", "checkhook"):
            me.cards[cid] = 1
        grinder = division()[0]       # Marcus Cole
        expect, ideas = coach.scout(grinder, me, budget=20)
        self.assertTrue(any("takedown" in e for e in expect))
        self.assertTrue(any(s.card == "sprawl" for s in ideas))


if __name__ == "__main__":
    unittest.main()
