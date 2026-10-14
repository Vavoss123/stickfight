"""Rules and controls."""

import pygame

from ..common import W, H, CX, GOLD, WHITE, GREY, text, panel, Button
from .base import Scene

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
        "A feint freezes anyone who is waiting to defend.",
        "A weave dodges everything, or eats it for 1.5 times.",
    ]),
    ("The bars", [
        "Red is health. Yellow is stamina. Purple is momentum.",
        "Full momentum: your next attack goes ALL IN.",
        "Body, leg and arm damage build up under the bars.",
        "100% body or leg damage ends the fight, whatever your health.",
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
        "",
        "ESC pause   M mute   F11 fullscreen   F1 feedback note",
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
        y = 196
        for ln in lines:
            if ln:
                text(surf, ln.strip(), (CX - 420 + (40 if ln.startswith("    ") else 0), y), 25,
                     WHITE if not ln.startswith("    ") else (200, 210, 230), max_width=840)
            y += 52 if ln else 26
        text(surf, f"{self.page + 1} / {len(PAGES)}", (CX, H - 58), 18, GREY, "midtop")
        self.prev.enabled = self.page > 0
        self.next.enabled = self.page < len(PAGES) - 1
        self.prev.draw(surf)
        self.next.draw(surf)
        self.back.draw(surf)
        self.tutorial.draw(surf)
