"""Holding a key in a text box: backspace keeps deleting and letters keep typing.

Operating systems and SDL disagree about repeating typed text, so this does it itself
and ignores any repeats that arrive on their own. Use one KeyRepeat per text box:
feed() each event, tick() each frame, and apply whatever actions come back.
"""

import pygame

DELAY = 0.4        # seconds before a held key starts repeating
INTERVAL = 0.035   # seconds between repeats after that


class KeyRepeat:
    def __init__(self):
        self.clear()

    def clear(self):
        self.key = None        # the key being held
        self.action = None     # what it does: ("text", "a") or ("back",)
        self.wait = 0.0
        self.pending = None    # a key went down and its text has not arrived yet

    def feed(self, e):
        """The action for an event now, or None. Starts, or stops, a repeat."""
        if e.type == pygame.KEYDOWN:
            if e.key == self.key:
                return None                      # a repeat from the system, ours takes over
            if e.key == pygame.K_BACKSPACE:
                self.key, self.action, self.wait, self.pending = e.key, ("back",), DELAY, None
                return self.action
            self.pending = e.key
            if self.key is not None and self.action[0] == "back":
                self.clear()
                self.pending = e.key
            return None
        if e.type == pygame.KEYUP:
            if e.key == self.key:
                self.clear()
            elif e.key == self.pending:
                self.pending = None
            return None
        if e.type == pygame.TEXTINPUT:
            if self.pending is None:
                if self.key is not None and self.action[0] == "text":
                    return None                  # the system repeating a held letter
                return ("text", e.text)          # a paste, or text that came with no key
            self.key, self.action, self.wait = self.pending, ("text", e.text), DELAY
            self.pending = None
            return self.action
        return None

    def tick(self, dt):
        """Repeats due since the last frame."""
        if self.key is None:
            return []
        if not pygame.key.get_pressed()[self.key]:
            self.clear()
            return []
        self.wait -= dt
        out = []
        while self.wait <= 0 and len(out) < 8:
            out.append(self.action)
            self.wait += INTERVAL
        return out
