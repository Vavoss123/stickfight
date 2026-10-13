import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.fight import Fight
from engine.fighter import FighterState
from engine.roster import quick_fighters, division
from engine.tournament import Tournament, Condition, STAGES, CARRY


def field():
    pool = quick_fighters() + division()
    return pool[0], pool[1:8]


def play_out(t):
    while not t.over:
        m = t.player_match()
        if m:
            t.sim(m)
        t.finish_stage()


class Bracket(unittest.TestCase):
    def test_full_bracket(self):
        me, others = field()
        t = Tournament(me, others, seed=1)
        play_out(t)
        self.assertEqual([len(s) for s in t.stages], [4, 2, 1])
        self.assertIsNotNone(t.champion)
        for k in range(1, len(STAGES)):
            winners = [m.winner for m in t.stages[k - 1]]
            entrants = [i for m in t.stages[k] for i in (m.a, m.b)]
            self.assertEqual(winners, entrants)

    def test_player_is_in_the_first_stage(self):
        me, others = field()
        t = Tournament(me, others, seed=2)
        m = t.player_match()
        self.assertIn(0, (m.a, m.b))

    def test_needs_eight(self):
        me, others = field()
        with self.assertRaises(ValueError):
            Tournament(me, others[:3])


class CarryOver(unittest.TestCase):
    def test_damage_carries_partly(self):
        me, others = field()
        f = FighterState(me, hp=40, body=50, legs=80, cut=30)
        c = Condition.after(f)
        self.assertAlmostEqual(c.hp, 100 - 60 * CARRY["hp"])
        self.assertAlmostEqual(c.legs, 80 * CARRY["legs"])
        self.assertFalse(c.fresh())
        self.assertTrue(Condition().fresh())

    def test_next_fight_starts_hurt(self):
        me, others = field()
        t = Tournament(me, others, seed=3)
        m = t.player_match()
        t.cond[m.a] = Condition(hp=70, legs=30, cut=20)
        fight = t.fight_for(m)
        self.assertEqual(fight.state.f[0].hp, 70)
        self.assertEqual(fight.state.f[0].legs, 30)
        self.assertEqual(fight.state.f[1].hp, 100)

    def test_record_with_player_as_red(self):
        # The UI always puts the player in red, even when they are b in the bracket
        me, others = field()
        t = Tournament(me, others, seed=4)
        m = t.player_match()
        opp = m.b if m.a == 0 else m.a
        fight = Fight(t.entrants[0], t.entrants[opp], seed=1)
        fight.state.f[0].hp = 55
        fight.state.f[1].hp = 0
        fight.play(tuple(fight.options(i)[0] for i in (0, 1)))
        t.record(m, fight, sides=(0, opp))
        self.assertEqual(m.winner, 0)
        self.assertLess(t.cond[0].hp, 100)
        self.assertFalse(t.player_out)

    def test_draws_still_have_a_winner(self):
        me, others = field()
        t = Tournament(me, others, seed=5)
        m = t.stages[0][0]
        fight = t.fight_for(m)
        fight.result = type("R", (), {"winner": None, "method": "Draw", "detail": "Split draw",
                                      "round": 3})()
        t.record(m, fight)
        self.assertIn(m.winner, (m.a, m.b))
        self.assertTrue(m.detail.startswith("Draw"))


if __name__ == "__main__":
    unittest.main()
