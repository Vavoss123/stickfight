"""Feints, reads and follow ups."""

import os
import random
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.constants import STANDING
from engine.fighter import FighterState
from engine.moves import MOVES, MOVESETS, matchup
from engine.resolve import resolve
from engine.roster import quick_fighters
from engine.state import FightState


def fresh():
    r = quick_fighters()
    return FightState([FighterState(r[0]), FighterState(r[1])], STANDING)


class Feints(unittest.TestCase):
    def test_matchups(self):
        f = MOVES["feint"]
        self.assertEqual(matchup(f, MOVES["block"]), 1)
        self.assertEqual(matchup(f, MOVES["jab"]), -1)
        self.assertEqual(matchup(f, MOVES["takedown"]), -1)
        self.assertEqual(matchup(MOVES["jab"], f), 1)
        self.assertEqual(matchup(f, f), 0)
        self.assertIn("feint", MOVESETS[(STANDING, "neutral")])

    def test_feint_freezes_a_blocker(self):
        st = fresh()
        st.f[1].stamina = 50
        ex = resolve(st, ("feint", "block"), random.Random(1))
        self.assertTrue(ex.feinted[0])
        self.assertTrue(ex.frozen[1])
        self.assertLessEqual(st.f[1].stamina, 50)      # no rest behind the guard
        self.assertEqual(st.f[0].opening, "read")
        self.assertFalse(ex.landed[1] or ex.countered[1])

    def test_feint_into_a_strike_gets_you_hit(self):
        hit = 0
        for seed in range(100):
            st = fresh()
            ex = resolve(st, ("feint", "jab"), random.Random(seed))
            hit += ex.landed[1]
            self.assertIsNone(st.f[0].opening)
        self.assertGreater(hit, 80)

    def test_a_read_wins_the_race(self):
        # A power punch is slower than a jab. After a read it keeps up.
        def clean(opening):
            n = 0
            for seed in range(200):
                st = fresh()
                st.f[0].opening = opening
                ex = resolve(st, ("cross", "jab"), random.Random(seed))
                n += ex.landed[0] and not ex.landed[1]
            return n
        self.assertGreater(clean("read"), clean(None) * 1.3)

    def test_landing_clean_sets_up_a_follow_up(self):
        for seed in range(50):
            st = fresh()
            ex = resolve(st, ("cross", "takedown"), random.Random(seed))
            if ex.landed[0] and not ex.finish:
                self.assertEqual(st.f[0].opening, "follow")
                ex2 = resolve(st, ("block", "block"), random.Random(seed))
                self.assertIsNone(st.f[0].opening)      # it only lasts one exchange
                return
        self.fail("never landed")

    def test_openings_clone(self):
        st = fresh()
        st.f[0].opening = "read"
        self.assertEqual(st.clone().f[0].opening, "read")


if __name__ == "__main__":
    unittest.main()
