"""The move timer: run out of time and a move is picked for you."""

import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from ui.settings import Settings, DEFAULTS, PICK_TIMES


def scene(app, mode="cpu"):
    from engine.roster import quick_fighters
    from ui.scenes.fight import FightScene, FightConfig
    r = quick_fighters()
    s = FightScene(app, FightConfig(r[0], r[1], mode=mode))
    for _ in range(300):
        s.update(1 / 30)
        if s.phase == "pick":
            break
    return s


class PickTimerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import updater
        updater.check_async = lambda: None
        from main import App
        cls.app = App()
        cls.app.settings["skip_walkouts"] = True

    def test_default_and_clamp(self):
        self.assertEqual(DEFAULTS["pick_timer"], 15)
        s = Settings(path=os.path.join(os.path.dirname(__file__), "no_such_settings.json"))
        self.assertIn(s["pick_timer"], [t for _, t in PICK_TIMES])

    def test_counts_down_and_picks_for_you(self):
        self.app.settings["pick_timer"] = 15
        s = scene(self.app)
        self.assertEqual(s.pick_left, 15.0)
        s.update(1 / 30)
        self.assertLess(s.pick_left, 15.0)
        s.pick_left = 0.01
        s.update(1 / 30)
        self.assertIsNotNone(s.picks[0])
        self.assertEqual(s.phase, "reveal")
        self.assertTrue(any(p[0] == "TOO SLOW!" for p in s.popups))

    def test_both_players_auto_picked_in_versus(self):
        self.app.settings["pick_timer"] = 10
        s = scene(self.app, mode="2p")
        self.assertEqual(s.pick_left, 10.0)
        s.pick_left = 0.01
        s.update(1 / 30)
        self.assertIsNotNone(s.picks[0])
        self.assertIsNotNone(s.picks[1])
        self.assertEqual(s.phase, "reveal")

    def test_off_means_no_timer(self):
        self.app.settings["pick_timer"] = 0
        s = scene(self.app)
        self.assertIsNone(s.pick_left)

    def test_tutorial_has_no_timer(self):
        self.app.settings["pick_timer"] = 15
        from ui.scenes.tutorial import TutorialScene
        t = TutorialScene(self.app)
        self.assertEqual(t._pick_seconds(), 0)

    @classmethod
    def tearDownClass(cls):
        cls.app.settings["pick_timer"] = DEFAULTS["pick_timer"]


if __name__ == "__main__":
    unittest.main()
