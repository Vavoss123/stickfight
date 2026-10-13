"""Stickfight: turn based MMA with stick figures.

    python main.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pygame

from ui.common import W, H
from ui.sound import Sounds, RATE


class App:
    def __init__(self):
        pygame.mixer.pre_init(RATE, -16, 1, 512)
        pygame.init()
        pygame.display.set_caption("Stickfight")
        self.screen = pygame.display.set_mode((W, H), pygame.SCALED | pygame.RESIZABLE)
        self.clock = pygame.time.Clock()
        self.sounds = Sounds()
        self.running = True
        from ui.scenes.menu import MenuScene
        self.scene = MenuScene(self)

    def goto(self, scene):
        self.scene = scene

    def run(self):
        while self.running:
            dt = min(self.clock.tick(60) / 1000.0, 1 / 20)
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    self.running = False
                else:
                    self.scene.handle(e)
            self.scene.update(dt)
            self.scene.draw(self.screen)
            pygame.display.flip()
        pygame.quit()


if __name__ == "__main__":
    App().run()
