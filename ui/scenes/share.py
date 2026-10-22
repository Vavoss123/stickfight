"""Fighter codes: show yours to copy, or enter a friend's to fight them in local games."""

import pygame

from engine import sharecode

from ..common import W, H, CX, RED, GOLD, WHITE, GREY, GREEN, text, text_block, panel, Button
from ..keyrepeat import KeyRepeat
from ..stickman import Figure
from .base import Scene

MAX_CODE = 260


def copy_text(s):
    """Put text on the clipboard. False if this system will not let us."""
    try:
        pygame.scrap.put_text(s)
        return True
    except Exception:
        return False


def paste_text():
    try:
        return pygame.scrap.get_text() or ""
    except Exception:
        return ""


def _code_lines(code, per_line=6):
    """The code in rows of a few groups, so it is easy to read out or check."""
    groups = code.split("-")
    return ["-".join(groups[k:k + per_line]) for k in range(0, len(groups), per_line)]


class ShareScene(Scene):
    """Your career fighter's code, ready to copy."""

    def __init__(self, app, profile, back):
        super().__init__(app)
        self.p = profile
        self.back_to = back
        self.code = sharecode.encode(profile)
        self.message = ""
        self.fig = Figure(220, 470, 1, profile.color, glove=profile.gloves or RED, scale=1.4).dress(profile)
        self.fig.set_pose("victory", idle="victory")
        self.copy_btn = Button((CX - 140, 520, 280, 54), "Copy code", color=(40, 110, 60), size=22)
        self.back = Button((20, H - 56, 140, 42), "Back", size=18)

    def handle(self, e):
        if self.back.handle(e) or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
            self.app.goto(self.back_to())
            return
        copy = e.type == pygame.KEYDOWN and e.key == pygame.K_c and (e.mod & pygame.KMOD_CTRL)
        if self.copy_btn.handle(e) or copy:
            ok = copy_text(self.code)
            self.message = "Copied. Paste it to a friend." if ok else "Could not copy here, write it down instead."
            self.app.sounds.play("click")

    def update(self, dt):
        self.fig.update(dt)

    def draw(self, surf):
        surf.fill((14, 15, 22))
        text(surf, "FIGHTER CODE", (CX, 24), 44, WHITE, "midtop", display=True)
        text(surf, f"{self.p.name}, {self.p.weight} {self.p.archetype}, {self.p.record()}", (CX, 80), 18,
             GREY, "midtop")
        self.fig.draw(surf)
        r = panel(surf, (380, 130, 860, 220), (22, 24, 34), border=GOLD)
        y = r.y + 24
        for ln in _code_lines(self.code):
            text(surf, ln, (r.centerx, y), 26, GOLD, "midtop", bold=True)
            y += 40
        text_block(surf, "Use this fighter in Quick fight or 2 player on any computer: pick Add fighter by "
                         "code and paste it in. It brings your stats, look, personality, deck and perks. "
                         "Make a new code after you level up to bring the changes.",
                   (r.centerx + 0, 380), 17, 760, WHITE)
        self.copy_btn.draw(surf)
        if self.message:
            text(surf, self.message, (CX, 590), 17, GREEN, "midtop", bold=True)
        text(surf, "On this computer your career fighter is already in Quick fight and 2 player.",
             (CX, H - 40), 15, GREY, "midtop")
        self.back.draw(surf)


class CodeScene(Scene):
    """Type or paste a friend's code. done(profile) runs when it reads."""

    def __init__(self, app, done, back):
        super().__init__(app)
        self.done = done
        self.back_to = back
        self.value = ""
        self.error = ""
        self.rep = KeyRepeat()
        self.text_entry = True            # typing an m must not mute the sound
        self.add = Button((CX - 150, 400, 300, 54), "Add fighter", color=(40, 110, 60), size=22)
        self.paste = Button((CX - 150, 466, 300, 40), "Paste from clipboard", size=17)
        self.back = Button((20, H - 56, 140, 42), "Back", size=18)
        self._friends()
        pygame.key.start_text_input()

    def _friends(self):
        self.saved = sharecode.load_friends()
        self.forget = []
        for k, (code, p) in enumerate(self.saved):
            b = Button((W - 120, 166 + k * 40, 90, 32), "Forget", size=14, color=(90, 40, 40))
            b.pick = p.name
            self.forget.append(b)

    def _apply(self, act):
        if act[0] == "back":
            self.value = self.value[:-1]
        else:
            self.value = (self.value + act[1])[:MAX_CODE]
        self.error = ""

    def _submit(self):
        try:
            p = sharecode.add_friend(self.value)
        except sharecode.CodeError as err:
            self.error = str(err)
            self.app.sounds.play("boo", 0.4)
            return
        self.app.sounds.play("levelup", 0.6)
        self.done(p)

    def handle(self, e):
        if self.back.handle(e) or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
            self.app.goto(self.back_to())
            return
        for b in self.forget:
            if b.handle(e):
                sharecode.remove_friend(b.pick)
                self._friends()
                return
        paste = e.type == pygame.KEYDOWN and e.key == pygame.K_v and (e.mod & pygame.KMOD_CTRL)
        if self.paste.handle(e) or paste:
            self.value = paste_text().strip()[:MAX_CODE]
            self.error = "" if self.value else "Nothing to paste. Copy the code first."
            return
        if self.add.handle(e) or (e.type == pygame.KEYDOWN and e.key in (pygame.K_RETURN, pygame.K_KP_ENTER)):
            self._submit()
            return
        if e.type == pygame.KEYDOWN and (e.mod & pygame.KMOD_CTRL):
            return                         # other shortcuts, not letters
        act = self.rep.feed(e)
        if act:
            self._apply(act)

    def update(self, dt):
        for act in self.rep.tick(dt):
            self._apply(act)

    def draw(self, surf):
        surf.fill((14, 15, 22))
        text(surf, "ADD FIGHTER BY CODE", (CX, 24), 44, WHITE, "midtop", display=True)
        text(surf, "A friend finds their code on their career screen under Code. Paste it here with Ctrl V.",
             (CX, 82), 17, GREY, "midtop")
        box = pygame.Rect(140, 150, 760, 200)
        pygame.draw.rect(surf, (30, 33, 46), box, border_radius=8)
        pygame.draw.rect(surf, GOLD, box, 2, border_radius=8)
        # Codes have no spaces to wrap at, so break them every few groups (or every 48 letters)
        v = self.value
        rows = _code_lines(v, 7) if "-" in v else [v[k:k + 48] for k in range(0, len(v), 48)] or [""]
        rows[-1] += "|" if pygame.time.get_ticks() // 500 % 2 else ""
        for n, ln in enumerate(rows[:6]):
            text(surf, ln, (box.x + 16, box.y + 14 + n * 30), 20, WHITE, max_width=box.w - 32)
        if not self.value:
            text(surf, "USC-.....", (box.x + 16, box.y + 14), 20, (90, 90, 100))
        self.add.draw(surf)
        self.paste.draw(surf)
        if self.error:
            text_block(surf, self.error, (CX, 520), 17, 700, (255, 120, 100))
        text(surf, "SAVED FIGHTERS", (W - 330, 132), 15, GOLD, bold=True)
        if not self.saved:
            text(surf, "None yet", (W - 330, 166), 15, GREY)
        for (code, p), b in zip(self.saved, self.forget):
            text(surf, p.name, (W - 330, b.rect.centery), 16, WHITE, "midleft", max_width=200)
            b.draw(surf)
        self.back.draw(surf)
