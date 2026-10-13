"""Achievements, the daily challenge and secret fighters."""

import os
import random
import sys
import tempfile
import unittest
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine import achievements, daily
from engine.ai import AI
from engine.fight import Fight
from engine.roster import quick_fighters, division, unlocked, UNLOCKABLES


def win_a_fight(p0, p1, seed=1, rounds=3, start=None):
    """Play AI against a helpless opponent until red wins."""
    f = Fight(p0, p1, rounds=rounds, seed=seed, start=start)
    ai = AI("hard", seed=seed)
    while not f.over:
        if f.between_rounds:
            f.start_next_round()
            continue
        f.play((ai.choose(f, 0), f.options(1)[-1]))
    return f


class Achievements(unittest.TestCase):
    def test_list_is_unique(self):
        ids = [a for a, _, _ in achievements.LIST]
        self.assertEqual(len(ids), len(set(ids)))
        for aid, _ in UNLOCKABLES:
            self.assertIn(aid, achievements.NAMES)

    def test_a_win_earns_something(self):
        r = quick_fighters()
        for seed in range(10):
            f = win_a_fight(r[0], r[1], seed)
            if f.result.winner == 0:
                got = achievements.for_fight(f, 0, "hard")
                self.assertIn("first_win", got)
                self.assertIn("hard", got)
                return
        self.fail("never won")

    def test_a_loss_earns_nothing(self):
        r = quick_fighters()
        f = win_a_fight(r[0], r[1], 1)
        f.result.winner = 1
        self.assertEqual(achievements.for_fight(f, 0), [])

    def test_record_saves_and_counts(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "a.json")
            rec = achievements.Record(path)
            self.assertEqual(rec.give(["ko", "ko", "nonsense"]), ["ko"])
            self.assertEqual(rec.give(["ko"]), [])
            for _ in range(10):
                rec.add("ko_wins")
            rec.save()
            back = achievements.Record(path)
            self.assertTrue(back.has("ko"))
            self.assertEqual(back.counts["ko_wins"], 10)

    def test_ten_knockouts(self):
        rec = achievements.Record(os.path.join(tempfile.mkdtemp(), "a.json"))
        rec.counts["ko_wins"] = 9
        r = quick_fighters()
        for seed in range(30):
            f = win_a_fight(r[3], r[1], seed)
            if f.result.winner == 0 and f.result.method in ("KO", "TKO"):
                self.assertIn("ko10", achievements.for_fight(f, 0, "normal", rec))
                return
        self.skipTest("no knockout in 30 fights")


class Daily(unittest.TestCase):
    def test_same_day_same_challenge(self):
        roster = quick_fighters() + division()
        a = daily.for_day(date(2026, 10, 13), roster)
        b = daily.for_day(date(2026, 10, 13), quick_fighters() + division())
        self.assertEqual((a.me.name, a.opp.name, a.twist), (b.me.name, b.opp.name, b.twist))
        self.assertNotEqual(a.me.name, a.opp.name)

    def test_days_differ(self):
        roster = quick_fighters() + division()
        seen = {daily.for_day(date(2026, 1, 1) + timedelta(days=k), roster).twist[0] for k in range(40)}
        self.assertGreater(len(seen), 4)

    def test_twists_apply(self):
        roster = quick_fighters() + division()
        for k in range(200):
            ch = daily.for_day(date(2026, 1, 1) + timedelta(days=k), roster)
            if ch.twist[0] == "heavy":
                self.assertEqual(ch.opp.weight, "Heavyweight")
                self.assertNotEqual(ch.me.weight, "Heavyweight")
            if ch.twist[0] == "cut":
                self.assertGreater(ch.start()[0]["cut"], 0)
            if ch.twist[0] == "five":
                self.assertEqual(ch.rounds, 5)
            f = Fight(ch.me, ch.opp, rounds=ch.rounds, start=ch.start())   # always builds
            if ch.twist[0] == "hype":
                self.assertGreater(f.state.f[1].hype, 50)

    def test_finish_only(self):
        roster = quick_fighters() + division()
        ch = next(daily.for_day(date(2026, 1, 1) + timedelta(days=k), roster) for k in range(400)
                  if daily.for_day(date(2026, 1, 1) + timedelta(days=k), roster).twist[0] == "finish")
        r = type("R", (), {"winner": 0, "method": "Decision"})()
        self.assertFalse(ch.won(r))
        r.method = "KO"
        self.assertTrue(ch.won(r))

    def test_best_score_and_streak(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "daily.json")
            today = date(2026, 10, 13)
            for k in (2, 1):
                daily.record(today - timedelta(days=k), 1200, path)
            self.assertEqual(daily.streak(today, path), 2)      # today not played yet
            daily.record(today, 900, path)
            daily.record(today, 1500, path)
            self.assertEqual(daily.load(path)[today.isoformat()], 1500)
            self.assertEqual(daily.streak(today, path), 3)
            daily.record(today - timedelta(days=5), 0, path)
            self.assertEqual(daily.streak(today, path), 3)


class Secrets(unittest.TestCase):
    def test_unlocked_fighters(self):
        self.assertEqual(unlocked(set()), [])
        names = [p.name for p in unlocked({a for a, _ in UNLOCKABLES})]
        self.assertEqual(len(names), len(UNLOCKABLES))
        regular = {p.name for p in quick_fighters() + division()}
        self.assertFalse(regular & set(names))


if __name__ == "__main__":
    unittest.main()
