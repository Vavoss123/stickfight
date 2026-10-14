"""Checks, weaves, knees, arm damage, limbs giving out and perks past a maxed stat."""

import os
import random
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.cards import build_kit
from engine.constants import STANDING, GUARD, MOUNT, STAT_LIMIT
from engine.fighter import FighterState
from engine.moves import MOVES, MOVESETS, matchup, zone
from engine.resolve import resolve
from engine.roster import quick_fighters
from engine.state import FightState, SubState


def fresh(pos=STANDING, top=None):
    r = quick_fighters()
    for p in r:
        p.deck, p.perks = {}, []
    return FightState([FighterState(r[0]), FighterState(r[1])], pos, top)


class Check(unittest.TestCase):
    def test_matchups(self):
        c = MOVES["check"]
        self.assertEqual(matchup(c, MOVES["legkick"]), 1)
        for m in ("jab", "cross", "body", "kick", "knee", "takedown"):
            self.assertEqual(matchup(c, MOVES[m]), -1, m)
        self.assertEqual(matchup(MOVES["legkick"], MOVES["block"]), 1)   # the guard does nothing low

    def test_checked_kick_hurts_the_kicker(self):
        st = fresh()
        ex = resolve(st, ("check", "legkick"), random.Random(1))
        self.assertTrue(ex.checked[0])
        self.assertGreater(st.f[1].legs, 0)
        self.assertEqual(st.f[0].legs, 0)

    def test_check_hurts_more_than_the_kick(self):
        kick = check = 0.0
        for seed in range(100):
            st = fresh()
            resolve(st, ("legkick", "clinch"), random.Random(seed))   # the kick lands
            kick += st.f[1].legs
            st = fresh()
            resolve(st, ("check", "legkick"), random.Random(seed))
            check += st.f[1].legs
        self.assertGreater(check, kick)


class Weave(unittest.TestCase):
    def test_slip_or_eat_it(self):
        slips = eats = 0
        clean_dmg = eaten = 0.0
        for seed in range(400):
            st = fresh()
            ex = resolve(st, ("weave", "cross"), random.Random(seed))
            if ex.slipped[0]:
                slips += 1
                self.assertEqual(ex.dmg[1], 0)
            elif ex.walked_in[0]:
                eats += 1
                eaten += ex.dmg[1]
            st = fresh()
            clean_dmg += resolve(st, ("cross", "takedown"), random.Random(seed)).dmg[0]
        self.assertGreater(slips, 100)
        self.assertGreater(eats, 100)

    def test_weave_costs_stamina(self):
        st = fresh()
        resolve(st, ("weave", "jab"), random.Random(1))
        self.assertLess(st.f[0].stamina, 100)


class Knee(unittest.TestCase):
    def test_knee_beats_a_takedown_and_jab_does_not(self):
        self.assertEqual(matchup(MOVES["knee"], MOVES["takedown"]), 1)
        self.assertEqual(matchup(MOVES["jab"], MOVES["takedown"]), -1)

    def test_knee_catch_hits_hard(self):
        knee = body = 0.0
        for seed in range(200):
            st = fresh()
            knee += resolve(st, ("knee", "takedown"), random.Random(seed)).dmg[0]
            st = fresh()
            body += resolve(st, ("body", "clinch"), random.Random(seed)).dmg[0]
        self.assertGreater(knee, body)


class Limbs(unittest.TestCase):
    def test_cracked_ribs(self):
        for seed in range(50):
            st = fresh()
            st.f[1].body = 99
            ex = resolve(st, ("body", "clinch"), random.Random(seed))
            if ex.landed[0]:
                self.assertEqual(ex.finish[1], "TKO")
                self.assertEqual(ex.broken, (1, "ribs"))
                return
        self.fail("never landed")

    def test_broken_leg(self):
        for seed in range(50):
            st = fresh()
            st.f[1].legs = 99
            ex = resolve(st, ("legkick", "clinch"), random.Random(seed))
            if ex.landed[0]:
                self.assertEqual(ex.broken, (1, "leg"))
                self.assertIn("Broken leg", ex.finish[2])
                return
        self.fail("never landed")

    def test_blocking_hurts_the_arms_and_they_leak(self):
        st = fresh()
        resolve(st, ("block", "cross"), random.Random(1))
        self.assertGreater(st.f[0].arms, 0)
        light, heavy = fresh(), fresh()
        heavy.f[0].arms = 90
        resolve(light, ("block", "cross"), random.Random(2))
        resolve(heavy, ("block", "cross"), random.Random(2))
        self.assertGreater(100 - heavy.f[0].hp, 100 - light.f[0].hp)

    def test_hurt_arms_help_the_armbar(self):
        def tighter(arms):
            n = 0
            for seed in range(300):
                st = fresh(GUARD, 1)
                st.f[1].arms = arms
                st.sub = SubState(0, "armbar", 1)
                n += resolve(st, ("left", "right"), random.Random(seed)).sub_result == "tighter"
            return n
        self.assertGreater(tighter(80), tighter(0))


class Zones(unittest.TestCase):
    def test_everything_has_a_zone(self):
        for m in MOVES.values():
            self.assertIn(zone(m), ("head", "body", "legs", "arms", "neck", "position", "defence", "trick"))
        self.assertEqual(zone(MOVES["armbar"]), "arms")
        self.assertEqual(zone(MOVES["takedown"]), "legs")
        self.assertEqual(zone(MOVES["rnc"]), "neck")
        self.assertIn("armbar", MOVESETS[(GUARD, "bottom")])
        self.assertIn("marmbar", MOVESETS[(MOUNT, "top")])


class StatsPastTen(unittest.TestCase):
    def test_perk_on_a_maxed_stat_still_counts(self):
        p = quick_fighters()[0]
        p.stats.striking = 10
        p.perks = ["heavyhands"]
        p.cards["heavyhands"] = 5
        self.assertGreater(build_kit(p).stats.striking, 10)
        self.assertLessEqual(build_kit(p).stats.striking, STAT_LIMIT)
        self.assertEqual(p.stats.striking, 10)   # training stays at 10


if __name__ == "__main__":
    unittest.main()
