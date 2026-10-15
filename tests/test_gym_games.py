import os
import random
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from engine.career import GYM_REPS
from ui import gym_games
from ui.gym_games import PadWork, CatchBalls, Mitts, Reaction, Combos, DRILLS

DT = 1 / 60


def key(k):
    return pygame.event.Event(pygame.KEYDOWN, key=k)


def click(pos):
    return pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos)


def run(drill, bot=None, limit=60 * 120):
    for _ in range(limit):
        if bot:
            bot(drill)
        drill.update(DT)
        drill.events = []
        if drill.finished:
            return drill.hits
    raise AssertionError(f"{type(drill).__name__} never finished")


def pad_bot(d):
    if d.live and abs(d.marker() - d.centre) < d.width * 0.3:
        d.handle(key(pygame.K_SPACE))


def catch_bot(d):
    if d.ball:
        d.x = d.ball["x"]


def mitt_bot(d):
    if d.pad:
        d.handle(click((d.pad["x"], d.pad["y"])))


def reaction_bot(d):
    if d.phase == "go" and d.t > 0.15:
        d.handle(key(pygame.K_SPACE))


def combo_bot(d):
    if d.phase == "input":
        d.handle(key(pygame.K_1 + d.seq[len(d.got)]))


BOTS = {PadWork: pad_bot, CatchBalls: catch_bot, Mitts: mitt_bot, Reaction: reaction_bot, Combos: combo_bot}


class Drills(unittest.TestCase):
    def test_every_drill_can_be_won_at_every_level(self):
        for cls in DRILLS:
            for level in (0.0, 0.5, 1.0):
                for seed in range(3):
                    d = cls(random.Random(seed), level)
                    self.assertEqual(run(d, BOTS[cls]), GYM_REPS, (cls.__name__, level, seed))

    def test_doing_nothing_scores_nothing_but_still_ends(self):
        for cls in DRILLS:
            d = cls(random.Random(1), 0.5)
            self.assertEqual(run(d), 0, cls.__name__)

    def test_pressing_too_early_in_the_bell_drill_is_a_miss(self):
        d = Reaction(random.Random(1), 0.0)
        d.handle(key(pygame.K_SPACE))
        self.assertEqual(d.hits, 0)
        self.assertEqual(d.rep, 1)

    def test_a_wrong_combo_move_is_a_miss(self):
        d = Combos(random.Random(1), 0.0)
        while d.phase != "input":
            d.update(DT)
        wrong = (d.seq[0] + 1) % 4
        d.handle(key(pygame.K_1 + wrong))
        self.assertEqual((d.hits, d.rep), (0, 1))

    def test_harder_levels_are_tighter(self):
        easy, hard = PadWork(random.Random(1), 0.0), PadWork(random.Random(1), 1.0)
        self.assertGreater(easy.width, hard.width)
        self.assertLess(easy.speed, hard.speed)
        self.assertGreater(CatchBalls(None, 0.0).reach, CatchBalls(None, 1.0).reach)
        self.assertGreater(Mitts(None, 0.0).radius, Mitts(None, 1.0).radius)
        e, h = Reaction(random.Random(1), 0.0), Reaction(random.Random(1), 1.0)
        self.assertGreater(e.limit, h.limit)
        self.assertGreater(Combos(None, 0.0).show, Combos(None, 1.0).show)

    def test_pick_avoids_the_last_drill(self):
        for _ in range(30):
            self.assertNotIsInstance(gym_games.pick(random.Random(), PadWork), PadWork)

    def test_drills_draw(self):
        pygame.init()
        surf = pygame.display.set_mode((1280, 720))
        for cls in DRILLS:
            d = cls(random.Random(2), 0.5)
            for _ in range(120):
                d.update(DT)
            d.draw(surf)


if __name__ == "__main__":
    unittest.main()
