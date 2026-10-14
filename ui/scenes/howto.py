"""Rules and controls."""

import pygame

from ..cards import draw_card
from ..common import (W, H, CX, RED, BLUE, GOLD, WHITE, GREY, GREEN, text, text_block, panel, bar,
                      Button)
from ..diagrams import rules_triangle, arrow
from ..stickman import Figure
from .base import Scene

PIC = pygame.Rect(CX + 10, 160, 450, 420)   # where each page's picture goes

PAGES = [
    ("The basics", [
        "You both pick a move in secret. Then both happen at once.",
        "",
        "Strike beats Grapple.",
        "Grapple beats Defend.",
        "Defend beats Strike.",
        "",
        "Win by knockout, TKO, submission or on the judges' cards.",
    ]),
    ("Reading them", [
        "A jab beats a power punch to the punch.",
        "A takedown ducks under jabs. A power punch or a knee stops it.",
        "A check kick stops leg kicks and hurts the kicker.",
        "A weave dodges everything, or eats it for 1.5 times.",
    ]),
    ("Feints", [
        "A feint is a fake. It costs 2 stamina.",
        "If they defend, they bite and freeze. They get no stamina back, and your next strike "
        "is more accurate, faster and harder.",
        "If they strike or grapple, they catch you standing there faking.",
        "",
        "Use it on someone who keeps blocking.",
    ]),
    ("The bars", [
        "Red is health. Yellow is stamina. Purple is momentum.",
        "Body, leg and arm damage build up under the bars.",
        "",
        "In a fight, hover any bar or tag to see what it means.",
    ]),
    ("The ground", [
        "On top: punch, pass, hold position or stand up.",
        "Underneath: cover up, sweep, get up, or go for a submission.",
        "Submissions are a guessing game. Pick a side.",
        "    If they pick the same side, the hold slips. Fill the meter and they tap.",
    ]),
    ("Cards and career", [
        "Cards swap in better versions of moves. Perks change how you fight.",
        "Between rounds the coach suggests up to 2 card swaps.",
        "Career: win fights, earn cards, train, and chase the belt.",
        "Judges score damage and strikes first, then takedowns and control.",
    ]),
    ("Controls", [
        "Click a move, or press the key shown in its corner.",
        "2 player: red uses the left of the keyboard, blue the right.",
        "Controllers work too. The button for each move is in its corner.",
    ]),
]


class HowToScene(Scene):
    def __init__(self, app):
        super().__init__(app)
        self.page = 0
        self.prev = Button((CX - 280, H - 80, 160, 48), "Previous", size=18)
        self.next = Button((CX + 120, H - 80, 160, 48), "Next", size=18)
        self.back = Button((20, H - 70, 120, 40), "Back", size=18)
        self.tutorial = Button((W - 260, H - 70, 240, 44), "Play the tutorial", color=(150, 110, 30),
                               size=18)

    def handle(self, e):
        if self.tutorial.handle(e) or (e.type == pygame.KEYDOWN and e.key == pygame.K_t):
            from .tutorial import TutorialScene
            self.app.goto(TutorialScene(self.app))
            return
        if self.prev.handle(e) or (e.type == pygame.KEYDOWN and e.key == pygame.K_LEFT):
            self.page = max(0, self.page - 1)
        if self.next.handle(e) or (e.type == pygame.KEYDOWN and e.key in (pygame.K_RIGHT, pygame.K_SPACE)):
            if self.page == len(PAGES) - 1 and e.type == pygame.KEYDOWN and e.key == pygame.K_SPACE:
                self._leave()
                return
            self.page = min(len(PAGES) - 1, self.page + 1)
        if self.back.handle(e) or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
            self._leave()

    def _leave(self):
        from .menu import MenuScene
        self.app.goto(MenuScene(self.app))

    def draw(self, surf):
        surf.fill((14, 15, 22))
        title, lines = PAGES[self.page]
        text(surf, "HOW TO PLAY", (CX, 30), 22, GOLD, "midtop", bold=True)
        text(surf, title.upper(), (CX, 64), 52, WHITE, "midtop", display=True)
        panel(surf, (CX - 470, 150, 940, 440), (22, 24, 34))
        y = 180
        for ln in lines:
            if not ln:
                y += 16
                continue
            indent = 30 if ln.startswith("    ") else 0
            col = WHITE if not indent else (200, 210, 230)
            y = text_block(surf, ln.strip(), (CX - 440 + indent, y), 21, 405 - indent, col, "topleft") + 14
        pygame.draw.line(surf, (44, 46, 60), (CX - 4, 170), (CX - 4, 570), 2)
        PICTURES[self.page](surf, PIC)
        text(surf, f"{self.page + 1} / {len(PAGES)}", (CX, H - 58), 18, GREY, "midtop")
        self.prev.enabled = self.page > 0
        self.next.enabled = self.page < len(PAGES) - 1
        self.prev.draw(surf)
        self.next.draw(surf)
        self.back.draw(surf)
        self.tutorial.draw(surf)


# ---- The pictures, one per page

def _fig(x, y, facing, pose, color, glove, scale=0.5):
    f = Figure(x, y, facing, color, glove=glove, scale=scale)
    f.set_pose(pose, idle=pose)
    return f


def _pair(surf, y, left, right, label_l, label_r, verdict, x0, w):
    """Two fighters doing their moves, and which one wins."""
    a = _fig(x0 + w * 0.3, y, 1, left, (200, 60, 60), RED)
    b = _fig(x0 + w * 0.7, y, -1, right, (60, 110, 220), BLUE)
    a.draw(surf)
    b.draw(surf)
    text(surf, label_l, (x0 + w * 0.3, y + 6), 15, (255, 140, 120), "midtop", bold=True)
    text(surf, label_r, (x0 + w * 0.7, y + 6), 15, (140, 180, 255), "midtop", bold=True)
    text(surf, verdict, (x0 + w * 0.5, y - 100), 15, GOLD, "midtop", bold=True)


def pic_basics(surf, r):
    rules_triangle(surf, (r.centerx, r.y + 230), rad=118, node=44, font_size=21, label=17)
    text(surf, "Each move beats one kind and loses to another", (r.centerx, r.bottom - 40), 15, GREY,
         "midtop")


def _rows(surf, r, rows):
    """Matchups stacked down the picture. The arrow points from the winner at the loser."""
    for k, (pa, pb, la, lb, verdict, left_wins) in enumerate(rows):
        y = r.y + 120 + k * 132
        _pair(surf, y, pa, pb, la, lb, verdict, r.x, r.w)
        a, b = (r.x + r.w * 0.42, y - 58), (r.x + r.w * 0.58, y - 58)
        arrow(surf, *((a, b) if left_wins else (b, a)), GOLD, gap_b=4)


def pic_reading(surf, r):
    _rows(surf, r, [("jab", "cross_wind", "Jab", "Power punch", "The jab gets there first", True),
                    ("knee", "shoot", "Knee", "Takedown", "The knee catches the shot", True),
                    ("legkick_wind", "legkick", "Check kick", "Leg kick", "The check hurts the kicker", True)])


def pic_feints(surf, r):
    _rows(surf, r, [("cross_wind", "block", "Feint", "Block", "They freeze. Your next strike hits harder", True),
                    ("cross_wind", "cross", "Feint", "Power punch", "Caught faking", False),
                    ("cross_wind", "shoot", "Feint", "Takedown", "Taken down", False)])


def pic_bars(surf, r):
    # A blown up HUD, with each part labelled on its own line
    hud = panel(surf, (r.x + 10, r.y + 40, 250, 230), (14, 15, 22), alpha=255)
    pygame.draw.rect(surf, RED, (hud.x, hud.y, 5, hud.h))
    text(surf, "YOUR FIGHTER", (hud.x + 16, hud.y + 12), 20, WHITE, display=True)
    x, w = hud.x + 16, hud.w - 32
    parts = [(hud.y + 62, 18, "Health", RED, "Hit zero and you're out"),
             (hud.y + 112, 12, "Stamina", (236, 200, 70), "Moves cost it, resting refills"),
             (hud.y + 160, 8, "Momentum", (190, 110, 255), "Full: next attack goes ALL IN")]
    for (y, h, name, col, what), fill in zip(parts, (0.8, 0.55, 0.7)):
        bar(surf, (x, y - h // 2, w, h), fill, col)
        pygame.draw.line(surf, col, (hud.right - 8, y), (hud.right + 14, y), 2)
        text(surf, name, (hud.right + 20, y - 12), 18, col, bold=True)
        text(surf, what, (hud.right + 20, y + 8), 12, GREY)
    y = hud.y + 200
    text(surf, "BODY 30%", (x, y), 15, (255, 200, 90), "midleft", bold=True)
    text(surf, "ARMS 20%", (x + 96, y), 15, (255, 200, 90), "midleft", bold=True)
    pygame.draw.line(surf, (255, 200, 90), (hud.right - 8, y), (hud.right + 14, y), 2)
    text(surf, "Damage", (hud.right + 20, y - 12), 18, (255, 200, 90), bold=True)
    text(surf, "100% body or legs ends it", (hud.right + 20, y + 8), 12, GREY)
    text_block(surf, "Hover any of these in a fight to see what it does.", (r.x + 10, r.bottom - 60), 15,
               r.w - 20, GREY, "topleft")


def pic_ground(surf, r):
    # Guard: red on the bottom, blue on top
    y = r.y + 150
    gx = r.x + 110
    bot = Figure(gx - 16, y, 1, (200, 60, 60), glove=RED, scale=0.55)
    bot.set_pose("guard_bot", idle="guard_bot")
    top = Figure(gx - 16 + 62 * 0.55 * 1.7, y, -1, (60, 110, 220), glove=BLUE, scale=0.55)
    top.set_pose("guard_top", idle="guard_top")
    bot.draw(surf)
    top.draw(surf)
    text(surf, "Guard", (gx + 20, y + 10), 17, WHITE, "midtop", bold=True)
    text(surf, "underneath, legs around them", (gx + 20, y + 32), 13, GREY, "midtop")
    # Mount
    mx = r.x + 330
    mbot = Figure(mx + 10, y, 1, (200, 60, 60), glove=RED, scale=0.55)
    mbot.set_pose("mount_bot", idle="mount_bot")
    mtop = Figure(mx - 20, y, 1, (60, 110, 220), glove=BLUE, scale=0.55)
    mtop.set_pose("mount_top", idle="mount_top")
    mbot.draw(surf)
    mtop.draw(surf)
    text(surf, "Mount", (mx, y + 10), 17, WHITE, "midtop", bold=True)
    text(surf, "sitting on top: bad news", (mx, y + 32), 13, GREY, "midtop")
    # The submission meter
    m = panel(surf, (r.x + 40, r.y + 250, r.w - 80, 80), (16, 10, 24), alpha=255, border=(150, 80, 205))
    text(surf, "SUBMISSION", (m.centerx, m.y + 8), 15, (210, 170, 255), "midtop", bold=True)
    text(surf, "ESCAPE", (m.x + 14, m.y + 50), 13, (120, 220, 140), "midleft", bold=True)
    text(surf, "TAP", (m.right - 14, m.y + 50), 13, GOLD, "midright", bold=True)
    for k in range(4):
        x = m.centerx - 90 + k * 60
        c = (60, 110, 70) if k == 0 else (150, 80, 205) if k <= 1 else (50, 46, 60)
        pygame.draw.circle(surf, c, (x, m.y + 50), 12)
    text_block(surf, "Guess right and it moves towards TAP. Guess the same side as them and it slips back.",
               (r.centerx, r.y + 344), 14, r.w - 40, GREY)


def pic_cards(surf, r):
    a = pygame.Rect(r.x + 20, r.y + 20, 150, 232)
    b = pygame.Rect(r.right - 170, r.y + 20, 150, 232)
    draw_card(surf, a, "cross", 1)
    draw_card(surf, b, "superman", 2)
    arrow(surf, (a.right + 10, a.centery), (b.x - 10, b.centery), GOLD, gap_b=6)
    text(surf, "swap in", (r.centerx, a.centery - 28), 15, GOLD, "midtop", bold=True)
    chip = panel(surf, (r.x + 30, r.y + 290, r.w - 60, 60), (40, 70, 50), alpha=255)
    text(surf, "Put in Sprawl", (chip.centerx, chip.y + 10), 18, WHITE, "midtop", bold=True)
    text(surf, "They shot 3 takedowns.", (chip.centerx, chip.y + 34), 14, GREY, "midtop")
    text(surf, "Between rounds the coach suggests swaps like this", (r.centerx, chip.bottom + 10), 14, GREY,
         "midtop")


def pic_controls(surf, r):
    b1 = Button((r.x + 40, r.y + 60, 170, 70), "Jab", key="1", sub="Strike, 3 stamina", color=(196, 70, 62),
                size=22)
    b2 = Button((r.x + 240, r.y + 60, 170, 70), "Takedown", key="Q", sub="Grapple, 10 stamina",
                color=(58, 110, 205), size=22)
    b1.draw(surf)
    b2.draw(surf)
    for b in (b1, b2):
        pygame.draw.circle(surf, GOLD, (b.rect.x + 13, b.rect.y + 13), 13, 2)
    arrow(surf, (r.x + 120, r.y + 190), (r.x + 56, r.y + 80), GOLD, gap_b=12)
    text(surf, "the key to press", (r.x + 120, r.y + 196), 16, GOLD, "midtop", bold=True)
    keys = [("ESC", "pause"), ("M", "mute"), ("F11", "fullscreen"), ("F1", "write a note")]
    for k, (key, what) in enumerate(keys):
        y = r.y + 250 + k * 36
        kr = pygame.Rect(r.x + 60, y, 60, 28)
        pygame.draw.rect(surf, (52, 58, 78), kr, border_radius=6)
        pygame.draw.rect(surf, (0, 0, 0), kr, 2, border_radius=6)
        text(surf, key, kr.center, 15, WHITE, "center", bold=True)
        text(surf, what, (kr.right + 16, kr.centery), 17, WHITE, "midleft")


PICTURES = [pic_basics, pic_reading, pic_feints, pic_bars, pic_ground, pic_cards, pic_controls]
