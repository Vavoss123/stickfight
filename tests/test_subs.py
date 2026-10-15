"""The submission contest: no dice, so the same picks always give the same result."""

import random
import unittest

from engine.constants import GUARD, SUB_MAX_ANGLE, SUB_OPTIONS, SUB_TAP
from engine.fighter import FighterState
from engine.resolve import resolve, sub_edge
from engine.roster import quick_fighters
from engine.state import FightState, SubState

POWER, ANGLE, CALM = SUB_OPTIONS


def state(lock=1, angle=0, move="triangle"):
    r = quick_fighters()
    for p in r:
        p.deck, p.perks = {}, []
    st = FightState([FighterState(r[0]), FighterState(r[1])], GUARD, 1)
    st.f[0].stats.grappling = st.f[1].stats.grappling      # equal, so only the picks matter
    st.sub = SubState(0, move, lock, angle)
    return st


def play(picks, **kw):
    st = state(**kw)
    ex = resolve(st, picks, random.Random(0))
    return st, ex


class Matrix(unittest.TestCase):
    def test_no_dice(self):
        for picks in [(a, d) for a in SUB_OPTIONS for d in SUB_OPTIONS]:
            results = {play(picks)[1].sub_result for _ in range(5)}
            different_seeds = set()
            for seed in range(20):
                st = state()
                different_seeds.add(resolve(st, picks, random.Random(seed)).sub_result)
            self.assertEqual(len(results), 1, picks)
            self.assertEqual(len(different_seeds), 1, picks)

    def test_squeeze_beats_explode_and_breathe(self):
        for d in (POWER, CALM):
            st, ex = play((POWER, d))
            self.assertEqual((ex.sub_result, st.sub.lock), ("tighter", 2), d)

    def test_hand_fighting_stops_a_squeeze(self):
        st, ex = play((POWER, ANGLE))
        self.assertEqual((ex.sub_result, st.sub.lock), ("defended", 1))

    def test_an_angle_gets_a_squeeze_through_a_hand_fight(self):
        st, ex = play((POWER, ANGLE), angle=1)
        self.assertEqual((ex.sub_result, st.sub.lock, st.sub.angle), ("tighter", 2, 0))

    def test_adjust_builds_the_angle_and_beats_a_hand_fight(self):
        for d in (ANGLE, CALM):
            st, ex = play((ANGLE, d))
            self.assertEqual((ex.sub_result, st.sub.angle), ("angle", 1), d)

    def test_the_angle_is_capped(self):
        st, ex = play((ANGLE, CALM), angle=SUB_MAX_ANGLE)
        self.assertEqual(st.sub.angle, SUB_MAX_ANGLE)

    def test_explode_beats_an_adjust(self):
        st, ex = play((ANGLE, POWER), lock=2)
        self.assertEqual((ex.sub_result, st.sub.lock), ("loosened", 1))
        st, ex = play((ANGLE, POWER), lock=1)
        self.assertEqual(ex.sub_result, "escaped")
        self.assertIsNone(st.sub)

    def test_a_locked_in_angle_cannot_be_exploded_out_of(self):
        st, ex = play((ANGLE, POWER), angle=SUB_MAX_ANGLE)
        self.assertEqual((ex.sub_result, st.sub.lock), ("defended", 1))

    def test_easing_off_holds_against_an_explosion(self):
        st, ex = play((CALM, POWER))
        self.assertEqual((ex.sub_result, st.sub.lock), ("defended", 1))

    def test_a_tap_ends_the_fight(self):
        st, ex = play((POWER, CALM), lock=SUB_TAP - 1)
        self.assertEqual(ex.sub_result, "tap")
        self.assertEqual(ex.finish[:2], (0, "Submission"))


class Gas(unittest.TestCase):
    def test_you_cannot_squeeze_on_empty(self):
        st = state()
        st.f[0].stamina = 3
        ex = resolve(st, (POWER, CALM), random.Random(0))
        self.assertTrue(ex.gassed[0])
        self.assertEqual((ex.sub_result, st.sub.lock), ("angle", 1))   # it came out as an adjust

    def test_you_cannot_explode_on_empty(self):
        st = state()
        st.f[1].stamina = 3
        ex = resolve(st, (POWER, POWER), random.Random(0))
        self.assertTrue(ex.gassed[1])
        self.assertEqual(ex.sub_result, "tighter")      # it came out as a breather

    def test_exploding_and_squeezing_cost_gas(self):
        st = state()
        a, d = st.f[0].stamina, st.f[1].stamina
        resolve(st, (POWER, POWER), random.Random(0))
        self.assertLess(st.f[0].stamina, a)
        self.assertLess(st.f[1].stamina, d)

    def test_breathing_and_easing_off_recover(self):
        st = state()
        st.f[0].stamina = st.f[1].stamina = 50
        resolve(st, (CALM, CALM), random.Random(0))
        self.assertGreater(st.f[0].stamina, 50)
        self.assertGreater(st.f[1].stamina, 50)


class Skill(unittest.TestCase):
    def test_a_better_grappler_makes_ground_against_a_hand_fight(self):
        st = state()
        st.f[0].stats.grappling = st.f[1].stats.grappling + 3
        ex = resolve(st, (POWER, ANGLE), random.Random(0))
        self.assertEqual(ex.sub_result, "angle")

    def test_a_far_better_grappler_squeezes_through_a_hand_fight(self):
        st = state()
        st.f[0].stats.grappling = st.f[1].stats.grappling + 7
        ex = resolve(st, (POWER, ANGLE), random.Random(0))
        self.assertEqual((ex.sub_result, st.sub.lock), ("tighter", 2))

    def test_a_much_better_defender_scrambles_out_of_a_crush(self):
        st = state()
        st.f[1].stats.grappling = st.f[0].stats.grappling + 4
        ex = resolve(st, (POWER, POWER), random.Random(0))
        self.assertEqual((ex.sub_result, st.sub.lock), ("held", 1))

    def test_edge_counts_the_hold_and_perks(self):
        st = state()
        base = sub_edge(st.f[0], st.f[1], st.f[0].move("triangle"))
        self.assertGreater(sub_edge(st.f[0], st.f[1], st.f[0].move("rnc")), base - 10)   # runs
        st.f[1].stamina = 10
        self.assertGreater(sub_edge(st.f[0], st.f[1], st.f[0].move("triangle")), base)


if __name__ == "__main__":
    unittest.main()
