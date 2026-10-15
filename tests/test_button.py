import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from ui.common import Button


def move(pos):
    return pygame.event.Event(pygame.MOUSEMOTION, pos=pos)


class Hover(unittest.TestCase):
    def test_hover_clears_when_the_mouse_leaves_a_disabled_button(self):
        b = Button((10, 10, 40, 30), "+")
        b.handle(move((20, 20)))
        self.assertTrue(b.hover)
        b.enabled = False              # the last point was spent under the mouse
        b.handle(move((300, 300)))
        self.assertFalse(b.hover)

    def test_disabled_buttons_do_not_click(self):
        b = Button((10, 10, 40, 30), "+", enabled=False)
        e = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(20, 20))
        self.assertFalse(b.handle(e))


if __name__ == "__main__":
    unittest.main()
