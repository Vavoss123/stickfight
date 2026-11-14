import unittest

from main import window_size
from ui.common import W, H


class WindowSizeTest(unittest.TestCase):
    def test_fits_small_laptop(self):
        # 1366x768 at 125% scaling: Windows reports about 1093x614
        w, h = window_size((1093, 614))
        self.assertLessEqual(w, 1093)
        self.assertLessEqual(h, 614)

    def test_keeps_the_game_shape(self):
        for desk in ((1920, 1080), (2560, 1440), (1280, 1024), (3440, 1440), (1093, 614)):
            w, h = window_size(desk)
            self.assertAlmostEqual(w / h, W / H, places=2)

    def test_bigger_on_big_screens(self):
        self.assertGreater(window_size((2560, 1440))[0], W)


if __name__ == "__main__":
    unittest.main()
