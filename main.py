"""Stickfight: turn based MMA with stick figures.

    python main.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pygame

import updater
from ui.common import W, H
from engine import achievements
from engine.roster import UNLOCKABLES
from ui.feedback import Feedback
from ui.toast import Toasts
from ui import gamepad
from ui.settings import Settings
from ui.sound import Sounds, RATE
from version import VERSION


class App:
    def __init__(self):
        updater.cleanup_old()
        updater.check_async()
        pygame.mixer.pre_init(RATE, -16, 1, 512)
        pygame.init()
        pygame.display.set_caption(f"Stickfight {VERSION}")
        self.screen = pygame.display.set_mode((W, H), pygame.SCALED | pygame.RESIZABLE)
        self.clock = pygame.time.Clock()
        self.sounds = Sounds()
        self.settings = Settings()
        self.fullscreen = False
        self.apply_settings()
        self.running = True
        self.focused = True
        self.minimized = False
        self.feedback = Feedback(self)
        self.toasts = Toasts(self)
        self.record = achievements.Record()
        self.pads = gamepad.Pads()
        from ui.scenes.menu import MenuScene
        self.scene = MenuScene(self)

    def goto(self, scene):
        self.scene = scene

    def award(self, aids):
        """Unlock achievements and announce the new ones, and any fighter they unlock."""
        for aid in self.record.give(list(aids)):
            self.toasts.push("ACHIEVEMENT UNLOCKED", achievements.NAMES[aid])
            for need, build in UNLOCKABLES:
                if need == aid:
                    self.toasts.push("NEW FIGHTER UNLOCKED", f"{build().name} joins the roster")

    def _pad(self, e):
        """Pads pick moves in a fight and stand in for the keyboard everywhere else."""
        got = self.pads.handle(e)
        if got is None or self.feedback.open:
            return
        if got[0] == "button":
            _, slot, button = got
            handler = getattr(self.scene, "handle_pad", None)
            if handler and handler(slot, button):
                return
            key = gamepad.AS_KEYS.get(gamepad.name(button))
        else:
            key = got[1]
        if key:
            self.scene.handle(gamepad.key_event(key))

    def apply_settings(self):
        s = self.settings
        self.sounds.set_volume(s["volume"] / 100, s["crowd"] / 100)
        if s["fullscreen"] != self.fullscreen:
            try:
                pygame.display.toggle_fullscreen()
                self.fullscreen = s["fullscreen"]
            except pygame.error:
                s["fullscreen"] = self.fullscreen

    def run(self):
        while self.running:
            # Full speed when playing, barely ticking over in the background
            fps = 5 if self.minimized else 60 if self.focused else 15
            dt = min(self.clock.tick(fps) / 1000.0, 1 / 20)
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    self.running = False
                elif e.type in (pygame.WINDOWFOCUSLOST, pygame.WINDOWFOCUSGAINED):
                    self.focused = e.type == pygame.WINDOWFOCUSGAINED
                elif e.type in (pygame.WINDOWMINIMIZED, pygame.WINDOWRESTORED, pygame.WINDOWSHOWN):
                    self.minimized = e.type == pygame.WINDOWMINIMIZED
                elif e.type == pygame.KEYDOWN and e.key == pygame.K_F11:
                    self.settings["fullscreen"] = not self.settings["fullscreen"]
                    self.apply_settings()
                    self.settings.save()
                elif e.type in gamepad.EVENTS:
                    self._pad(e)
                elif not self.feedback.handle(e):
                    self.scene.handle(e)
            if not self.feedback.open:
                self.scene.update(dt)
            self.feedback.update(dt)
            self.toasts.update(dt)
            if not self.minimized:
                self.scene.draw(self.screen)
                self.toasts.draw(self.screen)
                self.feedback.draw(self.screen)
                pygame.display.flip()
            if updater.state["status"] == "restarting":
                updater.relaunch()
                self.running = False
        pygame.quit()


if __name__ == "__main__":
    App().run()
