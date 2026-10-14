"""The USC logo: an octagon badge, drawn in code like everything else."""

import math

import pygame

from .common import GOLD, WHITE, text

NAME = "USC"
FULL_NAME = "Ultimate Stickfight Championship"
RED = (170, 28, 34)
DARK = (22, 10, 12)


def _octagon(cx, cy, r):
    return [(cx + r * math.cos(math.radians(22.5 + k * 45)), cy + r * math.sin(math.radians(22.5 + k * 45)))
            for k in range(8)]


def draw_badge(surf, center, r):
    """The octagon with USC in it."""
    cx, cy = center
    pygame.draw.polygon(surf, GOLD, _octagon(cx, cy, r))
    pygame.draw.polygon(surf, DARK, _octagon(cx, cy, r * 0.92))
    pygame.draw.polygon(surf, RED, _octagon(cx, cy, r * 0.84))
    pygame.draw.polygon(surf, DARK, _octagon(cx, cy, r * 0.72))
    # A stick fighter's fist breaking through the middle line
    pygame.draw.line(surf, GOLD, (cx - r * 0.6, cy + r * 0.38), (cx + r * 0.6, cy + r * 0.38), max(2, int(r * 0.04)))
    text(surf, NAME, (cx, cy - r * 0.06), int(r * 0.62), WHITE, "center", display=True)
    text(surf, "EST. 2026", (cx, cy + r * 0.52), max(9, int(r * 0.13)), GOLD, "center", bold=True)


def draw_logo(surf, topleft, r=86):
    """Badge on the left, the name on the right. Returns the bottom of the logo."""
    x, y = topleft
    draw_badge(surf, (x + r, y + r), r)
    tx = x + 2 * r + 22
    text(surf, "ULTIMATE STICKFIGHT", (tx, y + r * 0.2), int(r * 0.5), WHITE, display=True)
    text(surf, "CHAMPIONSHIP", (tx, y + r * 0.78), int(r * 0.5), GOLD, display=True)
    return y + 2 * r


def icon(size=64):
    """A small badge for the window icon."""
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    draw_badge(s, (size // 2, size // 2), size // 2 - 1)
    return s
