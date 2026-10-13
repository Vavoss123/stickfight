"""Weight classes and the shared card collection."""

import copy
import os
import random
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine import collection
from engine.career import Career, new_player
from engine.fighter import FighterState
from engine.loadouts import Loadout, apply_saved, own_cards
from engine.moves import MOVES
from engine.resolve import resolve
from engine.roster import quick_fighters, division
from engine.state import FightState
from engine.tournament import Tournament
from engine.weights import CLASSES, NAMES


def pair(w0, w1):
    a, b = copy.deepcopy(quick_fighters()[0]), copy.deepcopy(quick_fighters()[0])
    a.weight, b.weight = w0, w1
    return FightState([FighterState(a), FighterState(b)])


def avg_damage(w0, w1, n=300):
    total = 0.0
    for seed in range(n):
        st = pair(w0, w1)
        ex = resolve(st, ("cross", "takedown"), random.Random(seed))
        total += ex.dmg[0]
    return total / n


class WeightClasses(unittest.TestCase):
    def test_every_class_is_complete(self):
        for name, c in CLASSES.items():
            for k in ("lbs", "size", "power", "speed", "gas", "ko"):
                self.assertIn(k, c, name)
        lbs = [CLASSES[n]["lbs"] for n in NAMES]
        self.assertEqual(lbs, sorted(lbs))

    def test_heavier_hits_harder(self):
        self.assertGreater(avg_damage("Heavyweight", "Heavyweight"), avg_damage("Lightweight", "Lightweight"))
        # Against a smaller fighter the size counts on top
        self.assertGreater(avg_damage("Heavyweight", "Lightweight"), avg_damage("Heavyweight", "Heavyweight"))
        self.assertLess(avg_damage("Lightweight", "Heavyweight"), avg_damage("Lightweight", "Lightweight"))

    def test_heavier_gasses_faster(self):
        st = pair("Heavyweight", "Lightweight")
        self.assertGreater(st.f[0].cost_of(10), st.f[1].cost_of(10))

    def test_weight_survives_save(self):
        c = Career(new_player("Big Lad", "", "Brawler", (200, 0, 0), "", "Heavyweight"))
        back = Career.from_dict(c.to_dict())
        self.assertEqual(back.player.weight, "Heavyweight")

    def test_career_division_fights_at_your_weight(self):
        c = Career(new_player("Small Lad", "", "Striker", (200, 0, 0), "", "Lightweight"))
        self.assertTrue(all(p.weight == "Lightweight" for p in c.ladder))
        opp, *_ = c.next_fight()
        self.assertEqual(opp.weight, "Lightweight")

    def test_quick_fight_roster_has_every_class(self):
        weights = {p.weight for p in quick_fighters() + division()}
        self.assertEqual(weights, set(NAMES))

    def test_tournament_makes_weight(self):
        pool = quick_fighters() + division()
        me = pool[0]
        me.weight = "Middleweight"
        t = Tournament(me, pool[1:8], seed=1)
        self.assertTrue(all(p.weight == "Middleweight" for p in t.entrants))


class SharedCollection(unittest.TestCase):
    def test_careers_fill_the_collection(self):
        with tempfile.TemporaryDirectory() as d:
            c = Career(new_player("Test Fighter", "", "Striker", (200, 0, 0), ""))
            c.player.cards["twister"] = 2
            c.save(os.path.join(d, "career.json"))
            have = collection.load(os.path.join(d, "collection.json"))
            self.assertEqual(have.get("twister"), 2)
            # Levels only go up
            collection.add({"twister": 1}, os.path.join(d, "collection.json"))
            self.assertEqual(collection.load(os.path.join(d, "collection.json"))["twister"], 2)

    def test_collection_pool_only_has_your_cards(self):
        with tempfile.TemporaryDirectory() as d:
            cpath = os.path.join(d, "collection.json")
            collection.add({"necktie": 3}, cpath)
            p = quick_fighters()[0]   # Striker: Superman Punch, Calf Kick, Combination Puncher
            lo = Loadout(p, (dict(p.deck), list(p.perks)), path=os.path.join(d, "decks.json"),
                         pool="collection", collection_path=cpath)
            self.assertIn("necktie", p.cards)
            self.assertEqual(p.cards["necktie"], 3)
            self.assertIn("superman", p.cards)          # their own cards stay
            self.assertNotIn("twister", p.cards)        # not earned
            self.assertIsNotNone(lo.equip("rnc", "twister"))
            self.assertIsNone(lo.equip("standup", "necktie"))

    def test_switching_pools_drops_cards_you_do_not_have(self):
        with tempfile.TemporaryDirectory() as d:
            cpath = os.path.join(d, "collection.json")
            p = quick_fighters()[0]
            lo = Loadout(p, (dict(p.deck), list(p.perks)), path=os.path.join(d, "decks.json"),
                         pool="all", collection_path=cpath)
            self.assertIsNone(lo.equip("rnc", "twister"))
            lo.set_pool("collection")
            self.assertNotIn("rnc", p.deck)
            self.assertEqual(p.deck.get("cross"), "superman")   # their own card is kept

    def test_saved_deck_needs_the_cards(self):
        with tempfile.TemporaryDirectory() as d:
            dpath, cpath = os.path.join(d, "decks.json"), os.path.join(d, "collection.json")
            p = quick_fighters()[0]
            lo = Loadout(p, (dict(p.deck), list(p.perks)), path=dpath, collection_path=cpath)
            lo.equip("rnc", "twister")
            lo.save()
            r = quick_fighters()
            apply_saved(r, dpath, pool="collection", collection_path=cpath)
            self.assertNotIn("rnc", r[0].deck)          # you never earned the Twister
            r = quick_fighters()
            apply_saved(r, dpath, pool="all", collection_path=cpath)
            self.assertEqual(r[0].deck.get("rnc"), "twister")


if __name__ == "__main__":
    unittest.main()
