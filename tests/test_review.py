import unittest

from engine import review
from engine.cpu import CPU
from engine.fight import Fight
from engine.roster import quick_fighters


def play(seed, level="hard"):
    r = quick_fighters()
    f = Fight(r[0], r[1], seed=seed)
    cpus = [CPU(level, seed=seed * 2 + 1), CPU(level, seed=seed * 2 + 2)]
    while not f.over:
        if f.between_rounds:
            f.start_next_round()
            continue
        st = f.state.clone()
        picks = (cpus[0].choose(f, 0), cpus[1].choose(f, 1))
        cpus[0].observe(st, 1, picks[1])
        cpus[1].observe(st, 0, picks[0])
        f.play(picks)
    return f


class ReviewTest(unittest.TestCase):
    def test_fights_review_cleanly(self):
        names = ("Reyes", "Petrov")
        turning = 0
        for seed in range(12):
            f = play(seed)
            t = review.turning_point(f, names)
            if t:
                turning += 1
                self.assertTrue(t.startswith("Round "), t)
            tips = review.tips(f, 0, names)
            self.assertLessEqual(len(tips), 2)
            for tip in tips:
                self.assertIsInstance(tip, str)
                self.assertTrue(tip)
        self.assertGreater(turning, 6)   # most fights have a moment worth naming

    def test_winner_matches_score(self):
        f = play(3)
        for ex in f.history:
            w = review.winner(ex)
            if ex.in_sub:
                self.assertIsNone(w)
                continue
            s = review.score(ex)
            if w is not None:
                self.assertGreaterEqual(s[w] - s[1 - w], review.EVEN)

    def test_round_and_clock(self):
        self.assertEqual(review.when(0), (1, "4:22"))
        self.assertEqual(review.when(7), (1, "0:00"))
        self.assertEqual(review.when(8), (2, "4:22"))


if __name__ == "__main__":
    unittest.main()
