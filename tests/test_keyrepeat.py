import os
import unittest
from unittest import mock

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from ui.keyrepeat import KeyRepeat, DELAY, INTERVAL


def down(key):
    return pygame.event.Event(pygame.KEYDOWN, key=key)


def up(key):
    return pygame.event.Event(pygame.KEYUP, key=key)


def typed(s):
    return pygame.event.Event(pygame.TEXTINPUT, text=s)


class Held(unittest.TestCase):
    def setUp(self):
        self.down = {pygame.K_BACKSPACE: True, pygame.K_a: True}
        p = mock.patch("pygame.key.get_pressed", lambda: mock.MagicMock(__getitem__=lambda s, k: self.down.get(k, False)))
        p.start()
        self.addCleanup(p.stop)

    def test_holding_backspace_keeps_deleting(self):
        r = KeyRepeat()
        self.assertEqual(r.feed(down(pygame.K_BACKSPACE)), ("back",))
        self.assertEqual(r.tick(DELAY - 0.01), [])
        self.assertEqual(len(r.tick(0.01 + INTERVAL * 3.5)), 4)
        self.assertIsNone(r.feed(down(pygame.K_BACKSPACE)))        # the system's own repeat is ignored

    def test_holding_a_letter_keeps_typing_it(self):
        r = KeyRepeat()
        self.assertIsNone(r.feed(down(pygame.K_a)))
        self.assertEqual(r.feed(typed("a")), ("text", "a"))
        self.assertIsNone(r.feed(typed("a")))                       # a repeat the system sent
        self.assertEqual(r.tick(DELAY + INTERVAL)[0], ("text", "a"))

    def test_letting_go_stops_it(self):
        r = KeyRepeat()
        r.feed(down(pygame.K_BACKSPACE))
        r.feed(up(pygame.K_BACKSPACE))
        self.assertEqual(r.tick(5), [])

    def test_a_key_that_is_no_longer_down_stops_it(self):
        r = KeyRepeat()
        r.feed(down(pygame.K_a))
        r.feed(typed("a"))
        self.down[pygame.K_a] = False                               # a missed key up
        self.assertEqual(r.tick(5), [])

    def test_pasted_text_just_types(self):
        r = KeyRepeat()
        self.assertEqual(r.feed(typed("hello")), ("text", "hello"))
        self.assertEqual(r.tick(5), [])


if __name__ == "__main__":
    unittest.main()
