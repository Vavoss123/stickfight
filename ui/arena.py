"""The octagon: crowd, fence, lights and canvas. Static parts are drawn once."""

import math
import random

import pygame

from .common import W, H, FLOOR_Y, CX, font

FENCE_TOP = 250
FENCE_BOTTOM = 505


def _gradient(surf, top, bottom, rect):
    x, y, w, h = rect
    for i in range(h):
        t = i / max(1, h - 1)
        c = tuple(int(top[k] + (bottom[k] - top[k]) * t) for k in range(3))
        pygame.draw.line(surf, c, (x, y + i), (x + w, y + i))


class Arena:
    def __init__(self, title="STICKFIGHT", seed=3):
        self.title = title
        self.rng = random.Random(seed)
        self.bg = pygame.Surface((W, H))
        self.flashes = []
        self.t = 0.0
        self.excite = 0.0
        self.crowd_heads = []
        self._build()

    def _build(self):
        s = self.bg
        rng = self.rng
        _gradient(s, (6, 7, 12), (22, 24, 34), (0, 0, W, FENCE_BOTTOM))

        # Crowd in tiers, darker at the back
        for row in range(9):
            y = 120 + row * 26
            shade = 12 + row * 3
            for x in range(-10, W + 20, 22):
                xx = x + rng.randint(-6, 6) + (row % 2) * 11
                hh = rng.randint(7, 10)
                c = (shade + rng.randint(-4, 6), shade + rng.randint(-4, 4), shade + 8 + rng.randint(-4, 6))
                pygame.draw.ellipse(s, c, (xx - 13, y + 8, 26, 34))
                pygame.draw.circle(s, c, (xx, y), hh)
                self.crowd_heads.append((xx, y))

        # Light haze from the rig above
        haze = pygame.Surface((W, H), pygame.SRCALPHA)
        for lx in (260, CX, W - 260):
            for r in range(260, 0, -20):
                a = int(10 * (1 - r / 260))
                pygame.draw.ellipse(haze, (255, 245, 220, a), (lx - r, 40 - r // 3, r * 2, r * 1.3))
        s.blit(haze, (0, 0))

        # Light rig
        pygame.draw.rect(s, (12, 12, 16), (120, 22, W - 240, 12))
        for lx in range(170, W - 150, 120):
            pygame.draw.rect(s, (30, 30, 36), (lx - 14, 30, 28, 18), border_radius=3)
            pygame.draw.circle(s, (255, 250, 230), (lx, 46), 5)

        # Canvas, with perspective
        _gradient(s, (178, 176, 170), (222, 220, 212), (0, FENCE_BOTTOM, W, H - FENCE_BOTTOM))
        # Logo on the canvas
        logo = pygame.Surface((520, 140), pygame.SRCALPHA)
        pygame.draw.ellipse(logo, (150, 30, 30, 70), logo.get_rect(), 6)
        pygame.draw.ellipse(logo, (150, 30, 30, 40), logo.get_rect().inflate(-60, -24), 3)
        f = font(56, display=True)
        img = f.render(self.title, True, (150, 30, 30))
        img.set_alpha(80)
        logo.blit(img, img.get_rect(center=(260, 70)))
        logo = pygame.transform.smoothscale(logo, (520, 92))
        s.blit(logo, logo.get_rect(center=(CX, 612)))
        # Sponsor blocks near the fence
        for x in (150, 1030):
            blk = pygame.Surface((110, 26), pygame.SRCALPHA)
            pygame.draw.rect(blk, (40, 60, 120, 60), blk.get_rect(), border_radius=4)
            s.blit(blk, (x, 528))

        # Fence: mesh, posts and padding
        mesh = pygame.Surface((W, FENCE_BOTTOM - FENCE_TOP), pygame.SRCALPHA)
        hgt = FENCE_BOTTOM - FENCE_TOP
        for x in range(-hgt, W + hgt, 14):
            pygame.draw.line(mesh, (160, 165, 175, 46), (x, 0), (x + hgt, hgt), 1)
            pygame.draw.line(mesh, (160, 165, 175, 46), (x + hgt, 0), (x, hgt), 1)
        s.blit(mesh, (0, FENCE_TOP))
        for px in (40, 400, 880, 1240):
            pygame.draw.rect(s, (14, 14, 18), (px - 9, FENCE_TOP - 6, 18, FENCE_BOTTOM - FENCE_TOP + 6))
            pygame.draw.rect(s, (40, 40, 48), (px - 9, FENCE_TOP - 6, 4, FENCE_BOTTOM - FENCE_TOP + 6))
        pygame.draw.rect(s, (10, 10, 14), (0, FENCE_TOP - 16, W, 18))
        pygame.draw.rect(s, (46, 46, 56), (0, FENCE_TOP - 16, W, 4))
        pygame.draw.rect(s, (12, 12, 16), (0, FENCE_BOTTOM - 6, W, 14))
        pygame.draw.line(s, (60, 60, 70), (0, FENCE_BOTTOM - 6), (W, FENCE_BOTTOM - 6), 2)

    def blood(self, x, amount=1.0):
        """Splash some blood on the canvas. It stays for the rest of the fight."""
        for _ in range(int(2 + 4 * amount)):
            bx = x + self.rng.uniform(-40, 40)
            by = FENCE_BOTTOM + 60 + self.rng.uniform(40, 110)
            w = self.rng.uniform(4, 12) * (0.6 + amount)
            spot = pygame.Surface((int(w * 2), int(w)), pygame.SRCALPHA)
            pygame.draw.ellipse(spot, (140, 10, 10, self.rng.randint(110, 180)), spot.get_rect())
            self.bg.blit(spot, (bx - w, by - w / 2))

    def cheer(self, amount=1.0):
        self.excite = min(2.0, self.excite + amount)

    def update(self, dt):
        self.t += dt
        self.excite = max(0.0, self.excite - dt * 0.6)
        rate = 3 + self.excite * 25
        if self.rng.random() < rate * dt and self.crowd_heads:
            x, y = self.rng.choice(self.crowd_heads)
            self.flashes.append([x, y - 2, 0.12])
        for f in self.flashes:
            f[2] -= dt
        self.flashes = [f for f in self.flashes if f[2] > 0]

    def draw(self, surf, shake=(0, 0)):
        surf.blit(self.bg, shake)
        for x, y, t in self.flashes:
            r = int(3 + 10 * t)
            pygame.draw.circle(surf, (255, 255, 240), (x + shake[0], y + shake[1]), r)
        if self.excite > 0.2:
            # Crowd on their feet: little bobbing heads near the fence
            for i in range(0, len(self.crowd_heads), 7):
                x, y = self.crowd_heads[i]
                if y < 300:
                    continue
                bob = abs(math.sin(self.t * 9 + i)) * 4 * min(1.0, self.excite)
                pygame.draw.circle(surf, (48, 48, 62), (x + shake[0], int(y - bob) + shake[1]), 8)
