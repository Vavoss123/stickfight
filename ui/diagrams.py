"""Small diagrams shared by the fight screen and How to play."""

import math

import pygame

from engine.constants import STRIKE, GRAPPLE, DEFEND

from .common import GOLD, WHITE, text

CLASS_COLOR = {STRIKE: (196, 70, 62), GRAPPLE: (58, 110, 205), DEFEND: (56, 160, 100)}
CLASS_NAME = {STRIKE: "Strike", GRAPPLE: "Grapple", DEFEND: "Defend"}


def arrow(surf, a, b, col, width=3, gap_a=0, gap_b=0, head=8):
    """A straight arrow from a to b, stopping short of each end by the gaps."""
    (x0, y0), (x1, y1) = a, b
    d = math.hypot(x1 - x0, y1 - y0) or 1
    ux, uy = (x1 - x0) / d, (y1 - y0) / d
    sx, sy = x0 + ux * gap_a, y0 + uy * gap_a
    ex, ey = x1 - ux * gap_b, y1 - uy * gap_b
    pygame.draw.line(surf, col, (sx, sy), (ex, ey), width)
    px, py = -uy, ux
    pygame.draw.polygon(surf, col, [(ex + ux * head, ey + uy * head),
                                    (ex - ux * head * 0.75 + px * head * 0.9, ey - uy * head * 0.75 + py * head * 0.9),
                                    (ex - ux * head * 0.75 - px * head * 0.9, ey - uy * head * 0.75 - py * head * 0.9)])
    return (sx + ex) / 2 + px * 14, (sy + ey) / 2 + py * 14


def rules_triangle(surf, center, rad=62, hover=None, node=22, font_size=13, label=11):
    """Strike beats Grapple beats Defend beats Strike. `hover` lights up one class."""
    cx, cy = center
    nodes = {STRIKE: (cx, cy - rad), GRAPPLE: (cx + rad * 0.95, cy + rad * 0.55),
             DEFEND: (cx - rad * 0.95, cy + rad * 0.55)}
    for a, b in ((STRIKE, GRAPPLE), (GRAPPLE, DEFEND), (DEFEND, STRIKE)):
        lit = hover in (a, b)
        col = GOLD if lit or hover is None and label > 11 else (120, 110, 70)
        mx, my = arrow(surf, nodes[a], nodes[b], col, gap_a=node + 2, gap_b=node + 4)
        text(surf, "beats", (mx, my), label, col, "center", shadow=False)
    for cls, (x, y) in nodes.items():
        lit = hover == cls
        col = CLASS_COLOR[cls]
        pygame.draw.circle(surf, tuple(min(255, int(c * 1.3)) for c in col) if lit else col, (int(x), int(y)), node)
        pygame.draw.circle(surf, WHITE if lit else (0, 0, 0), (int(x), int(y)), node, 2)
        text(surf, CLASS_NAME[cls], (x, y), font_size, WHITE, "center", bold=True)
