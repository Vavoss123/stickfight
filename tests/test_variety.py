"""Fouls, point deductions and the referee breaking them up."""

import os
import random
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine import resolve as R
from engine.constants import STANDING, CLINCH, GUARD
from engine.fighter import FighterState
from engine.judges import Judge, RoundStats
from engine.roster import quick_fighters
from engine.state import FightState


def fresh(pos=STANDING, top=None):
    r = quick_fighters()
    return FightState([FighterState(r[0]), FighterState(r[1])], pos, top)


class Fouls(unittest.TestCase):
    def setUp(self):
        self.old = R.FOUL_CHANCE
        R.FOUL_CHANCE = 1.0   # every strike is a foul

    def tearDown(self):
        R.FOUL_CHANCE = self.old

    def test_warning_then_point(self):
        st = fresh()
        ex = R.resolve(st, ("jab", "clinch"), random.Random(1))
        self.assertEqual(ex.foul[0], 0)
        self.assertEqual(ex.foul[2], "warning")
        self.assertFalse(ex.landed[0])
        ex = R.resolve(st, ("jab", "clinch"), random.Random(2))
        self.assertEqual(ex.foul[2], "point")

    def test_low_blow_and_ground_fouls(self):
        st = fresh()
        self.assertEqual(R.resolve(st, ("legkick", "block"), random.Random(1)).foul[1], "Low blow")
        st = fresh(GUARD, 0)
        ex = R.resolve(st, ("gnp", "sweep"), random.Random(1))
        self.assertEqual(ex.foul[1], "Shot to the back of the head")
        self.assertEqual(st.pos, STANDING)       # restarted on the feet

    def test_victim_gets_a_breather(self):
        st = fresh()
        st.f[1].stamina = 40
        R.resolve(st, ("jab", "clinch"), random.Random(1))
        self.assertGreater(st.f[1].stamina, 40)

    def test_deduction_on_the_scorecard(self):
        a, b = RoundStats(), RoundStats()
        a.dmg = 30
        a.deductions = 1
        j = Judge(random.Random(1))
        self.assertEqual(j.score_round(a, b), (9, 9))


class Referee(unittest.TestCase):
    def test_breaks_a_quiet_clinch(self):
        st = fresh(CLINCH)
        broke = None
        for k in range(R.IDLE_LIMIT[CLINCH]):
            ex = R.resolve(st, ("frame", "frame"), random.Random(k))
            broke = ex.ref_break
        self.assertEqual(broke, "clinch")
        self.assertEqual(st.pos, STANDING)

    def test_stands_up_a_quiet_ground_fight(self):
        st = fresh(GUARD, 0)
        for k in range(R.IDLE_LIMIT[GUARD]):
            ex = R.resolve(st, ("posture", "cover"), random.Random(k))
        self.assertEqual(ex.ref_break, "ground")
        self.assertEqual(st.pos, STANDING)

    def test_action_keeps_them_down(self):
        st = fresh(GUARD, 0)
        for k in range(R.IDLE_LIMIT[GUARD] + 2):
            st.f[1].hp = 100
            R.resolve(st, ("gnp", "upkick"), random.Random(k))   # trading shots, never idle
            if st.pos != GUARD:
                break
        self.assertEqual(st.idle, 0)


if __name__ == "__main__":
    unittest.main()
