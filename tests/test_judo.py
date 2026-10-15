import random
import unittest

from engine.cards import CARDS, STARTERS
from engine.career import Career, new_player
from engine.constants import CLINCH, GUARD, MOUNT
from engine.fighter import FighterState
from engine.moves import zone
from engine.resolve import resolve
from engine.roster import quick_fighters
from engine.state import FightState

THROWS = ("osoto", "seoi", "tomoe", "uchimata", "hiptoss")


def clinch(card=None, perks=()):
    r = quick_fighters()
    for p in r:
        p.deck, p.perks = {}, []
    if card:
        r[0].deck = {"trip": card}
        r[0].cards = {card: 1}
    r[0].perks = list(perks)
    for p in perks:
        r[0].cards[p] = 1
    return FightState([FighterState(r[0]), FighterState(r[1])], CLINCH)


class Judo(unittest.TestCase):
    def test_throws_are_wrestling_moves_from_the_clinch(self):
        for cid in THROWS:
            m = CARDS[cid].move
            self.assertEqual((m.base, m.stat), ("trip", "wrestling"), cid)
            self.assertGreater(m.slam, 0, cid)

    def test_a_throw_takes_them_down(self):
        for cid in THROWS:
            landed = 0
            for seed in range(60):
                st = clinch(cid)
                resolve(st, (cid, "frame"), random.Random(seed))
                landed += st.pos in (GUARD, MOUNT) and st.top == 0
            self.assertGreater(landed, 20, cid)

    def test_uchi_mata_and_the_hip_toss_land_in_mount(self):
        for cid in ("uchimata", "hiptoss"):
            self.assertEqual(CARDS[cid].move.to, "mount_top")

    def test_the_judo_black_belt_helps_throws(self):
        def landed(perks):
            n = 0
            for seed in range(400):
                st = clinch("osoto", perks)
                resolve(st, ("osoto", "frame"), random.Random(seed))
                n += st.pos != CLINCH
            return n
        self.assertGreater(landed(["judoka"]), landed([]))

    def test_career_wrestlers_start_with_a_throw(self):
        self.assertEqual(STARTERS["Wrestler"][0].get("trip"), "osoto")
        c = Career(new_player("Test", "", "Wrestler", (60, 190, 110), ""), seed=1)
        self.assertEqual(c.player.deck.get("trip"), "osoto")

    def test_most_throws_are_not_shown_as_leg_attacks(self):
        self.assertEqual(zone(CARDS["seoi"].move), "position")
        self.assertEqual(zone(CARDS["osoto"].move), "legs")


if __name__ == "__main__":
    unittest.main()
