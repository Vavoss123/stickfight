"""USC, the Ultimate Stickfight Championship: turn based MMA with stick figures.

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
from ui.music import Music
from version import VERSION


def window_size(desktop):
    """The biggest window with the game's shape that fits the screen, leaving room for the taskbar."""
    dw, dh = desktop
    scale = min(dw * 0.92 / W, dh * 0.86 / H)
    scale = max(0.4, scale)
    return int(W * scale), int(H * scale)


def fit_window():
    """Size the window to the monitor, so it fits a small laptop and isn't tiny on a big screen."""
    try:
        desktop = pygame.display.get_desktop_sizes()[0]
        import warnings
        with warnings.catch_warnings():
            # Only the window's size and position are touched here, not its drawing
            warnings.simplefilter("ignore", DeprecationWarning)
            win = pygame.Window.from_display_module()
        win.size = window_size(desktop)
        win.position = pygame.WINDOWPOS_CENTERED
    except (AttributeError, IndexError, pygame.error):
        pass


class App:
    def __init__(self):
        updater.cleanup_old()
        updater.check_async()
        pygame.mixer.pre_init(RATE, -16, 1, 512)
        pygame.init()
        pygame.display.set_caption(f"USC: Ultimate Stickfight Championship {VERSION}")
        from ui.logo import icon
        pygame.display.set_icon(icon())
        # The game draws at W x H and SDL scales it to the window, keeping the shape
        # (black bars on a screen of another shape) and mapping the mouse for us
        os.environ.setdefault("SDL_RENDER_SCALE_QUALITY", "1")
        self.screen = pygame.display.set_mode((W, H), pygame.SCALED | pygame.RESIZABLE)
        fit_window()
        self.clock = pygame.time.Clock()
        self.sounds = Sounds()
        self.music = Music(self.sounds)
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
        # Which the player last touched: the keyboard and mouse, or a pad. Move buttons show
        # the keys for one or the buttons for the other, not pad buttons just for being plugged in
        self.using_pad = False
        from ui.scenes.menu import MenuScene
        self.scene = MenuScene(self)
        self._scene_music(self.scene)

    def goto(self, scene):
        self.scene = scene
        self._scene_music(scene)

    def _scene_music(self, scene):
        """Each screen says what should play: a piece, or "keep" to leave it be."""
        want = getattr(scene, "music", "menu")
        if want != "keep":
            self.music.play(want)

    def award(self, aids):
        """Unlock achievements and announce the new ones, and any fighter they unlock."""
        for aid in self.record.give(list(aids)):
            self.toasts.push("ACHIEVEMENT UNLOCKED", achievements.NAMES[aid])
            for need, build in UNLOCKABLES:
                if need == aid:
                    self.toasts.push("NEW FIGHTER UNLOCKED", f"{build().name} joins the roster")

    def _mute_key(self, e):
        """F10 always mutes. M does too, unless it is a letter being typed or a 2 player move key."""
        if e.key == pygame.K_F10:
            return True
        return (e.key == pygame.K_m and not self.feedback.open
                and not getattr(self.scene, "text_entry", False)
                and not getattr(self.scene, "m_is_move", False))

    def toggle_mute(self):
        off = self.sounds.toggle_mute()
        self.music.muted(off)
        self.toasts.push("SOUND OFF" if off else "SOUND ON", "M or F10 to switch it back" if off else "")

    def _pad(self, e):
        """Pads pick moves in a fight and stand in for the keyboard everywhere else."""
        got = self.pads.handle(e)
        if got is None or self.feedback.open:
            return
        self.using_pad = True
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
        self.music.set_volume(s["volume"] / 100, s["music"] / 100)
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
                if e.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN) or (
                        e.type == pygame.MOUSEMOTION and abs(e.rel[0]) + abs(e.rel[1]) > 4):
                    self.using_pad = False
                if e.type == pygame.QUIT:
                    self.running = False
                elif e.type in (pygame.WINDOWFOCUSLOST, pygame.WINDOWFOCUSGAINED):
                    self.focused = e.type == pygame.WINDOWFOCUSGAINED
                elif e.type in (pygame.WINDOWMINIMIZED, pygame.WINDOWRESTORED, pygame.WINDOWSHOWN):
                    self.minimized = e.type == pygame.WINDOWMINIMIZED
                elif e.type == pygame.KEYDOWN and self._mute_key(e):
                    self.toggle_mute()
                elif e.type == pygame.KEYDOWN and e.key == pygame.K_F11:
                    self.settings["fullscreen"] = not self.settings["fullscreen"]
                    self.apply_settings()
                    self.settings.save()
                elif e.type in gamepad.EVENTS:
                    self._pad(e)
                elif not self.feedback.handle(e):
                    self.scene.handle(e)
            self.music.update()
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
