"""Main menu with a little sparring session going on behind it."""

import pygame

import updater
from engine.career import Career
from version import VERSION

from ..arena import Arena
from ..common import (W, H, CX, FLOOR_Y, RED, GOLD, WHITE, GREY, GREEN, text, panel,
                      bar, Button)
from ..choreo import SCALE
from ..spar import Spar
from .base import Scene

_shade = None


def _menu_shade():
    """The dark fade behind the buttons. Built once."""
    global _shade
    if _shade is None:
        _shade = pygame.Surface((480, H), pygame.SRCALPHA)
        for x in range(480):
            a = int(200 * (1 - x / 480) ** 1.4)
            pygame.draw.line(_shade, (0, 0, 0, a), (x, 0), (x, H))
    return _shade


class MenuScene(Scene):
    def __init__(self, app):
        super().__init__(app)
        self.arena = Arena()
        self.spar = Spar(CX + 110, FLOOR_Y, SCALE)
        self.t = 0.0
        has_save = Career.load() is not None
        items = [
            ("Quick fight", "Fight the computer", "quick"),
            ("Local 2 player", "Same keyboard, hidden picks", "versus"),
            ("Career", "Continue your career" if has_save else "Start from the bottom", "career"),
            ("Tournament", "Eight fighters, one night", "tournament"),
            ("Challenges", "Daily challenge and achievements", "challenges"),
            ("How to play", "Tutorial, rules and controls", "help"),
            ("Settings", "Sound, screen and speed", "settings"),
            ("Quit", "", "quit"),
        ]
        self.buttons = []
        for k, (label, sub, pick) in enumerate(items):
            b = Button((60, 222 + k * 58, 340, 52), label, sub=sub, size=21,
                       color=(150, 40, 40) if k == 0 else (40, 44, 62))
            b.pick = pick
            self.buttons.append(b)
        self.focus = 0
        app.sounds.ambience(False)

    def _go(self, pick):
        self.app.sounds.play("click")
        if pick == "quick":
            from .select import SelectScene
            self.app.goto(SelectScene(self.app, "ai"))
        elif pick == "versus":
            from .select import SelectScene
            self.app.goto(SelectScene(self.app, "2p"))
        elif pick == "career":
            from .career import open_career
            open_career(self.app)
        elif pick == "tournament":
            from .tournament import TournamentSetupScene
            self.app.goto(TournamentSetupScene(self.app))
        elif pick == "challenges":
            from .challenges import ChallengesScene
            self.app.goto(ChallengesScene(self.app))
        elif pick == "help":
            from .howto import HowToScene
            self.app.goto(HowToScene(self.app))
        elif pick == "settings":
            from .settings import SettingsScene
            self.app.goto(SettingsScene(self.app, lambda: MenuScene(self.app)))
        elif pick == "quit":
            self.app.running = False

    def handle(self, e):
        for b in self.buttons:
            if b.handle(e):
                self._go(b.pick)
                return
        if e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_DOWN, pygame.K_s):
                self.focus = (self.focus + 1) % len(self.buttons)
            elif e.key in (pygame.K_UP, pygame.K_w):
                self.focus = (self.focus - 1) % len(self.buttons)
            elif e.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._go(self.buttons[self.focus].pick)
            elif e.key == pygame.K_ESCAPE:
                self.app.running = False
            elif e.key == pygame.K_t:
                self.app.sounds.play("click")
                from .tutorial import TutorialScene
                self.app.goto(TutorialScene(self.app))
                return
            elif e.key == pygame.K_u and updater.state["status"] in ("available", "failed"):
                if updater.state["status"] == "failed":
                    updater.state["status"] = "available"
                self.app.sounds.play("click")
                updater.start_update()
        for k, b in enumerate(self.buttons):
            b.selected = k == self.focus
            if b.hover:
                self.focus = k

    def update(self, dt):
        self.t += dt
        self.spar.update(dt)
        self.arena.update(dt)

    def draw(self, surf):
        self.arena.draw(surf)
        surf.blit(_menu_shade(), (0, 0))
        self.spar.draw(surf)
        from ..logo import draw_logo
        draw_logo(surf, (40, 26), 84)
        text(surf, "TURN BASED MMA", (238, 156), 20, GREY, bold=True)
        for b in self.buttons:
            b.draw(surf)
        text(surf, "M mutes sound, ESC pauses in a fight, F1 writes a feedback note", (W - 20, H - 16), 14, GREY, "bottomright")
        text(surf, f"v{VERSION}", (20, H - 16), 14, GREY, "bottomleft")
        if not self.app.settings["tutorial_done"]:
            r = panel(surf, (430, 236, 330, 62), (40, 34, 14), alpha=230, border=GOLD)
            text(surf, "New here?", (r.x + 16, r.y + 10), 18, GOLD, bold=True)
            text(surf, "Press T for a two minute tutorial", (r.x + 16, r.y + 34), 15, WHITE)
        self._draw_update(surf)

    def _draw_update(self, surf):
        st = updater.state
        status = st["status"]
        if status not in ("available", "downloading", "restarting", "failed"):
            return
        r = panel(surf, (W - 380, 20, 360, 74), border=GOLD if status == "available" else None)
        if status == "available":
            text(surf, f"Update available: {st['latest']}", (r.x + 16, r.y + 12), 20, GOLD,
                 bold=True)
            how = "Press U to update and restart" if updater.FROZEN and st["asset"] \
                else "Press U to open the download page"
            text(surf, how, (r.x + 16, r.y + 42), 16, WHITE)
        elif status == "downloading":
            text(surf, f"Downloading {st['latest']}...", (r.x + 16, r.y + 12), 20, WHITE,
                 bold=True)
            bar(surf, (r.x + 16, r.y + 44, r.w - 32, 14), st["progress"], GREEN)
        elif status == "restarting":
            text(surf, "Restarting...", (r.x + 16, r.y + 24), 20, GREEN, bold=True)
        else:
            text(surf, "Update failed", (r.x + 16, r.y + 12), 20, RED, bold=True)
            text(surf, "Press U to try again", (r.x + 16, r.y + 42), 16, WHITE)
