import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

pygame.init()
pygame.display.set_mode((100, 100))

from ui.choreo import STRIKE_LIMBS, FRONT, MAX_LUNGE, SCALE, STAND_GAP, lunge, reach


class Strikes(unittest.TestCase):
    def test_every_standing_strike_reaches_after_the_step(self):
        dist = 2 * STAND_GAP
        for anim in STRIKE_LIMBS:
            for target in ("head", "body", "legs"):
                step = lunge(anim, target, dist, SCALE, SCALE)
                gap_left = dist - step
                touching = reach(anim) * SCALE + 4 * SCALE >= gap_left - FRONT[target] * SCALE - 0.5
                # Capped lunges (a leg kick from far away) can still fall short, nothing else may
                self.assertTrue(touching or step >= MAX_LUNGE * SCALE - 0.5, (anim, target))

    def test_no_step_when_already_in_range(self):
        self.assertEqual(lunge("jab", "head", 60, SCALE, SCALE), 0.0)

    def test_steps_are_capped(self):
        self.assertLessEqual(lunge("legkick", "legs", 400, SCALE, SCALE), MAX_LUNGE * SCALE)

    def test_unknown_moves_do_not_move(self):
        self.assertEqual(lunge("takedown", "body", 150, SCALE, SCALE), 0.0)

    def test_the_longer_the_limb_the_smaller_the_step(self):
        self.assertLess(lunge("cross", "head", 150, SCALE, SCALE), lunge("jab", "head", 150, SCALE, SCALE))


if __name__ == "__main__":
    unittest.main()
