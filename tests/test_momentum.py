"""Momentum, booing and going all in."""

import os
import random
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.constants import STANDING
from engine.fighter import FighterState
from engine.resolve import resolve, BOO_AFTER, SURGE_DMG
from engine.roster import quick_fighters
from engine.state import FightState


def fresh():
    r = quick_fighters()
    return FightState([FighterState(r[0]), FighterState(r[1])], STANDING)


class Momentum(unittest.TestCase):
    def test_landing_builds_hype(self):
        st = fresh()
        for seed in range(20):
            ex = resolve(st, ("cross", "takedown"), random.Random(seed))
            if ex.landed[0]:
                break
            st = fresh()
        self.assertGreater(st.f[0].hype, 0)
        self.assertEqual(st.f[1].hype, 0)

    def test_full_hype_surges_once(self):
        st = fresh()
        st.f[0].hype = 99.5
        ex = None
        for seed in range(50):
            st.f[0].hype = 99.5
            ex = resolve(st, ("cross", "takedown"), random.Random(seed))
            if ex.landed[0]:
                break
        self.assertTrue(st.f[0].surge)
        self.assertTrue(ex.surge_ready[0])
        # The next attack goes all in and spends it
        ex = resolve(st, ("jab", "jab"), random.Random(1))
        self.assertTrue(ex.surging[0])
        self.assertFalse(st.f[0].surge)
        self.assertEqual(st.f[0].hype, 0)

    def test_defending_does_not_spend_the_surge(self):
        st = fresh()
        st.f[0].surge = True
        ex = resolve(st, ("block", "jab"), random.Random(1))
        self.assertFalse(ex.surging[0])
        self.assertTrue(st.f[0].surge)

    def test_all_in_hits_harder(self):
        def avg(surge):
            total = 0.0
            for seed in range(300):
                st = fresh()
                st.f[0].surge = surge
                total += resolve(st, ("cross", "takedown"), random.Random(seed)).dmg[0]
            return total / 300
        self.assertGreater(avg(True), avg(False) * (SURGE_DMG - 0.1))

    def test_stalling_gets_booed(self):
        st = fresh()
        booed = []
        for k in range(BOO_AFTER + 1):
            st.f[0].hype = 50
            ex = resolve(st, ("block", "block"), random.Random(k))
            booed.append(ex.booed[0])
        self.assertEqual(booed[:BOO_AFTER - 1], [False] * (BOO_AFTER - 1))
        self.assertTrue(booed[BOO_AFTER - 1])
        self.assertLess(st.f[0].hype, 50)

    def test_attacking_resets_the_stall_count(self):
        st = fresh()
        for k in range(BOO_AFTER - 1):
            resolve(st, ("block", "block"), random.Random(k))
        resolve(st, ("jab", "block"), random.Random(9))
        self.assertEqual(st.f[0].passive, 0)

    def test_clone_keeps_momentum(self):
        st = fresh()
        st.f[0].hype, st.f[0].surge, st.f[0].passive = 40, True, 2
        c = st.clone()
        self.assertEqual((c.f[0].hype, c.f[0].surge, c.f[0].passive), (40, True, 2))


if __name__ == "__main__":
    unittest.main()
