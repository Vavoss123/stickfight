import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from ui import gamepad


class PlayStationTest(unittest.TestCase):
    def test_names(self):
        for n in ("DualSense Wireless Controller", "PS4 Controller", "Wireless Controller",
                  "Sony DualShock 3"):
            self.assertTrue(gamepad.is_playstation(n), n)
        for n in ("Xbox Series X Controller", "Controller (XBOX 360 For Windows)", "", None):
            self.assertFalse(gamepad.is_playstation(n), n)

    def test_labels(self):
        pygame.init()
        pads = gamepad.Pads.__new__(gamepad.Pads)
        pads.order = [7, 8]
        pads.playstation = {7}
        ps = pads.labels(0)
        self.assertEqual(len(ps), len(gamepad.PICK_LABELS))
        self.assertEqual(ps[0], gamepad.PS_SHAPES[0])
        self.assertEqual(ps[8:10], ["L1", "R1"])
        self.assertEqual(pads.labels(1), gamepad.PICK_LABELS)
        self.assertEqual(pads.labels(None), gamepad.PICK_LABELS)


class FollowsInputTest(unittest.TestCase):
    """With a pad plugged in, the move buttons show pad buttons only after the pad is used."""

    def test_switches(self):
        import updater
        updater.check_async = lambda: None
        from main import App
        from engine.roster import quick_fighters
        from ui.scenes.fight import FightScene, FightConfig, LABEL_SOLO
        app = App()
        app.settings["skip_walkouts"] = True
        app.pads.order = [42]          # pretend a PlayStation pad is plugged in
        app.pads.playstation = {42}
        r = quick_fighters()
        scene = FightScene(app, FightConfig(r[0], r[1]))
        for _ in range(300):
            scene.update(1 / 30)
            if scene.phase == "pick":
                break
        app.using_pad = False
        scene.update(1 / 30)
        self.assertEqual(scene.buttons[0][0].key, LABEL_SOLO[0])
        app.using_pad = True
        scene.update(1 / 30)
        self.assertEqual(scene.buttons[0][0].key, gamepad.ps_labels()[0])


if __name__ == "__main__":
    unittest.main()
