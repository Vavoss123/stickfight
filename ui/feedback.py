"""Quick notes while playing. F1 opens a box on any screen, Enter saves the note.

Notes go to ~/.stickfight/feedback.txt with the game version and whatever the current
screen reports about itself (the fight screen adds the score, stamina and last moves),
so a note like "AI landed that while gassed" still makes sense later.
"""

import datetime
import os

import pygame

from version import VERSION

from .keyrepeat import KeyRepeat
from .common import W, H, CX, GOLD, WHITE, GREY, GREEN, text, panel, wrap

PATH = os.path.join(os.path.expanduser("~"), ".stickfight", "feedback.txt")
MAX_CHARS = 500


class Feedback:
    def __init__(self, app):
        self.app = app
        self.open = False
        self.note = ""
        self.context = []
        self.toast = 0.0
        self.toast_msg = ""
        self.rep = KeyRepeat()

    def _apply(self, act):
        self.note = self.note[:-1] if act[0] == "back" else (self.note + act[1])[:MAX_CHARS]

    def _start(self):
        self.open = True
        self.rep.clear()
        self.note = ""
        scene = self.app.scene
        ctx = getattr(scene, "feedback_context", None)
        try:
            self.context = ctx() if ctx else []
        except Exception:
            self.context = []
        self.context.insert(0, f"Screen: {type(scene).__name__}")
        pygame.key.start_text_input()

    def _close(self):
        self.open = False
        self.rep.clear()

    def handle(self, e):
        """True when the event belongs to the note box and the scene should not see it."""
        if not self.open:
            if e.type == pygame.KEYDOWN and e.key == pygame.K_F1:
                self._start()
                return True
            return False
        act = self.rep.feed(e)
        if act:
            self._apply(act)
        elif e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE:
                self._close()
            elif e.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                if self.note.strip():
                    self._save()
                self._close()
        return True

    def _save(self):
        stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        lines = [f"[{stamp}] v{VERSION}", f"  {self.note.strip()}"]
        lines += [f"    {c}" for c in self.context]
        try:
            os.makedirs(os.path.dirname(PATH), exist_ok=True)
            with open(PATH, "a", encoding="utf-8") as f:
                f.write("\n".join(lines) + "\n\n")
            self.toast_msg = "Note saved"
        except OSError as err:
            self.toast_msg = f"Could not save the note: {err}"
        self.toast = 2.0

    def update(self, dt):
        self.toast = max(0.0, self.toast - dt)
        if self.open:
            for act in self.rep.tick(dt):
                self._apply(act)

    def draw(self, surf):
        if self.toast > 0 and not self.open:
            r = panel(surf, (CX - 200, 20, 400, 44), (14, 15, 22), alpha=230, border=GREEN)
            text(surf, self.toast_msg, r.center, 18, WHITE, "center", bold=True, max_width=380)
        if not self.open:
            return
        panel(surf, (0, 0, W, H), (0, 0, 0), alpha=150, radius=0)
        r = panel(surf, (CX - 360, 200, 720, 250), (18, 20, 30), alpha=245, border=GOLD)
        text(surf, "QUICK NOTE", (r.x + 20, r.y + 16), 26, GOLD, display=True)
        text(surf, "What feels off? Enter saves, ESC cancels.", (r.x + 20, r.y + 54), 16, GREY)
        box = pygame.Rect(r.x + 20, r.y + 84, r.w - 40, 120)
        pygame.draw.rect(surf, (8, 9, 14), box, border_radius=6)
        cursor = "_" if (pygame.time.get_ticks() // 400) % 2 else " "
        lines = wrap(self.note + cursor, 18, box.w - 24) or [cursor]
        y = box.y + 10
        for ln in lines[-4:]:
            text(surf, ln, (box.x + 12, y), 18, WHITE, shadow=False)
            y += 26
        text(surf, f"Saved to {PATH}", (r.x + 20, r.bottom - 30), 13, GREY, max_width=r.w - 40)
