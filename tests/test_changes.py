"""Gassed moves, escapes from under ground and pound, cross-slot cards and quick fight decks."""

import os
import random
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.cards import CARDS, PRESETS, build_kit, equip, validate
from engine.constants import STANDING, NEUTRAL, GUARD, MOUNT, BACK
from engine.fighter import FighterState
from engine.loadouts import Loadout, apply_saved, BUDGET
from engine.moves import MOVES, matchup
from engine.resolve import resolve
from engine.roster import quick_fighters, make
from engine.state import FightState


def fresh(pos=STANDING, top=None):
    r = quick_fighters()
    return FightState([FighterState(r[0]), FighterState(r[1])], pos, top)


class Gassed(unittest.TestCase):
    def test_effort(self):
        f = fresh().f[0]
        self.assertEqual(f.effort(MOVES["cross"]), 1.0)
        f.stamina = 0
        self.assertEqual(f.effort(MOVES["cross"]), 0.0)
        self.assertEqual(f.effort(MOVES["block"]), 1.0)  # resting is always free

    def _landed(self, stamina, n=300):
        hits = dmg = 0
        for seed in range(n):
            st = fresh()
            st.f[0].stamina = stamina
            st.f[1].stamina = 0   # same defence either way, only the attacker changes
            ex = resolve(st, ("jab", "clinch"), random.Random(seed))
            hits += ex.landed[0]
            dmg += ex.dmg[0]
        return hits / n, dmg / n

    def test_empty_tank_strikes_land_less_and_softer(self):
        fresh_hits, fresh_dmg = self._landed(100)
        empty_hits, empty_dmg = self._landed(0)
        self.assertLess(empty_hits, fresh_hits * 0.6)
        self.assertLess(empty_dmg, fresh_dmg * 0.4)

    def test_gassed_is_reported(self):
        st = fresh()
        st.f[1].stamina = 0
        ex = resolve(st, ("block", "cross"), random.Random(1))
        self.assertEqual(ex.gassed, [False, True])

    def test_gassed_strike_loses_the_race(self):
        # A power punch is slower than a jab, but a gassed jab is slower still
        firsts = 0
        for seed in range(200):
            st = fresh()
            st.f[0].stamina = 0
            ex = resolve(st, ("jab", "cross"), random.Random(seed))
            firsts += ex.landed[1]
        self.assertGreater(firsts, 80)


class BottomEscapes(unittest.TestCase):
    def test_counters_to_strikes_from_the_top(self):
        self.assertEqual(matchup(MOVES["bridge"], MOVES["melbows"]), 1)
        self.assertEqual(matchup(MOVES["shrimp"], MOVES["mgnp"]), 1)
        self.assertEqual(matchup(MOVES["turnin"], MOVES["bpunch"]), 1)
        self.assertEqual(matchup(CARDS["granby"].move, MOVES["mgnp"]), 1)  # cards inherit it
        # Guard is unchanged, escapes scramble out instead
        self.assertEqual(matchup(MOVES["gnp"], MOVES["sweep"]), 1)
        self.assertEqual(matchup(MOVES["gnp"], MOVES["triangle"]), 1)

    def test_scramble_out_from_under_ground_and_pound(self):
        swept = hit = 0
        for seed in range(400):
            st = fresh(GUARD, 0)
            ex = resolve(st, ("gnp", "sweep"), random.Random(seed))
            swept += ex.reversal_by == 1
            hit += ex.landed[0]
        # Sometimes, not always, and they still eat the punches
        self.assertGreater(swept, 20)
        self.assertLess(swept, 200)
        self.assertGreater(hit, 250)

    def test_no_scramble_into_a_submission(self):
        for seed in range(100):
            st = fresh(GUARD, 0)
            ex = resolve(st, ("gnp", "triangle"), random.Random(seed))
            if ex.landed[0]:   # a missed punch lets anything through, as before
                self.assertIsNone(ex.sub_start)

    def test_shrimp_under_punches_recovers_guard(self):
        out = 0
        for seed in range(200):
            st = fresh(MOUNT, 0)
            resolve(st, ("mgnp", "shrimp"), random.Random(seed))
            out += st.pos == GUARD
        self.assertGreater(out, 100)


class CrossSlotCards(unittest.TestCase):
    def test_slots(self):
        self.assertEqual(CARDS["guardpull"].move.slot, "body")
        self.assertEqual(CARDS["guardpull"].move.base, "clinch")
        self.assertEqual(CARDS["superman"].move.slot, "cross")

    def test_bjj_has_more_ways_to_the_mat(self):
        p = make("B", "", "BJJ")
        stand = build_kit(p).movesets[(STANDING, NEUTRAL)]
        self.assertIn("guardpull", stand)
        self.assertIn("singleleg", stand)
        self.assertNotIn("body", stand)
        self.assertEqual(validate(p, BUDGET), [])

    def test_guard_pull_puts_you_on_the_bottom(self):
        p0, p1 = make("A", "", "BJJ"), make("B", "", "Striker", cards=({}, [], 1))
        pulled = 0
        for seed in range(100):
            st = FightState([FighterState(p0), FighterState(p1)])
            resolve(st, ("guardpull", "block"), random.Random(seed))
            pulled += st.pos == GUARD and st.top == 1
        self.assertGreater(pulled, 70)

    def test_equip_checks_the_slot(self):
        p = make("A", "", "Striker", cards=({}, [], 1))
        p.cards["guardpull"] = 1
        self.assertIsNotNone(equip(p, "clinch", "guardpull", 10))
        self.assertIsNone(equip(p, "body", "guardpull", 10))
        self.assertEqual(p.deck["body"], "guardpull")


class QuickFightDecks(unittest.TestCase):
    def test_save_and_load(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "decks.json")
            p = quick_fighters()[0]
            lo = Loadout(p, (dict(p.deck), list(p.perks)), path=path)
            self.assertIsNone(lo.equip("kick", "showtime"))   # everything is unlocked
            lo.save()
            again = quick_fighters()
            apply_saved(again, path)
            self.assertEqual(again[0].deck.get("kick"), "showtime")
            lo.reset()
            again = quick_fighters()
            apply_saved(again, path)
            self.assertEqual(again[0].deck, dict(PRESETS["Striker"][0]))

    def test_budget(self):
        with tempfile.TemporaryDirectory() as d:
            p = quick_fighters()[0]
            lo = Loadout(p, ({}, []), path=os.path.join(d, "decks.json"))
            errs = [lo.equip(s, c) for s, c in (("kick", "showtime"), ("clinch", "imanari"),
                                                 ("standup", "necktie"), ("rnc", "twister"))]
            self.assertIn("Not enough deck points", errs)

    def test_broken_save_is_ignored(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "decks.json")
            with open(path, "w") as f:
                f.write('{"Dan Reyes": {"deck": {"jab": "twister"}, "perks": []}}')
            r = quick_fighters()
            before = dict(r[0].deck)
            apply_saved(r, path)
            self.assertEqual(r[0].deck, before)


if __name__ == "__main__":
    unittest.main()
