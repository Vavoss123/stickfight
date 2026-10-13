"""Rules and controls."""

import pygame

from ..common import W, H, CX, GOLD, WHITE, GREY, text, panel, Button
from .base import Scene

PAGES = [
    ("The basics", [
        "Each turn both fighters pick a move in secret. Then both moves happen at once.",
        "Fights are 3 rounds of 8 exchanges. Title fights are 5 rounds.",
        "Win by knockout, TKO, submission, or on the judges' scorecards.",
        "",
        "Every move is a Strike, a Grapple, a Submission or a Defend:",
        "    Strike beats Grapple, you catch them coming in.",
        "    Grapple beats Defend, they are standing still.",
        "    Defend beats Strike, you block and counter.",
        "Submissions count as grapples.",
    ]),
    ("Standing tricks", [
        "The triangle has a few twists on the feet:",
        "    A Jab is fast, so it beats a Power punch to the punch.",
        "    A Takedown walks through a Jab, a Body shot or a kick. A Power punch stops it.",
        "    Clinching up smothers a Power punch.",
        "    A Leg kick goes under a block. A Head kick does not.",
        "",
        "Power shots can rock, drop and knock out. A rocked fighter is easier to hit.",
        "Stamina drops with every move. Tired fighters hit softer and miss more.",
        "Defending moves recover stamina.",
    ]),
    ("Head, body and legs", [
        "Head shots do the damage and set up knockouts.",
        "Body shots and knees drain stamina and slow how fast it comes back.",
        "    Pile up enough body damage and one shot can fold them.",
        "Leg kicks chop down the legs. Bad legs mean weaker power shots,",
        "worse takedowns and worse takedown defence. Past 60% they start limping.",
        "",
        "Body and leg damage show under each health bar.",
        "Some of it heals between rounds, but not all.",
    ]),
    ("The ground", [
        "Takedowns, trips and knockdowns take the fight to the mat.",
        "On top you can strike, pass to mount, posture up or stand up.",
        "On the bottom you can strike, sweep, go for a submission, cover up or get up.",
        "Mount is bad. Bridge or shrimp to get out, or they may take your back.",
        "Back control is the worst. Turn in or stand up before the choke sinks in.",
        "Trying to get up while they pass gives up your back.",
        "",
        "Submissions start a contest. The attacker picks a side in secret.",
        "If the defender picks the same side, the hold loosens. Fill the meter to win.",
        "Better grapplers and fresher fighters finish faster.",
    ]),
    ("Controls", [
        "Quick fight: number keys, Q W E R A S D F, or click a move.",
        "Local 2 player: red uses Q W E R A S D F, blue uses U I O P J K L ;",
        "Picks stay hidden until both players lock in.",
        "",
        "SPACE continues between rounds and skips the KO replay.",
        "ESC pauses. M mutes sound.",
        "",
        "Judges score each round on damage, takedowns, control time,",
        "submission attempts and knockdowns.",
    ]),
]


class HowToScene(Scene):
    def __init__(self, app):
        super().__init__(app)
        self.page = 0
        self.prev = Button((CX - 280, H - 80, 160, 48), "Previous", size=18)
        self.next = Button((CX + 120, H - 80, 160, 48), "Next", size=18)
        self.back = Button((20, H - 70, 120, 40), "Back", size=18)

    def handle(self, e):
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
            text(surf, ln, (CX - 430, y), 21, WHITE if not ln.startswith("    ") else (200, 210, 230))
            y += 40
        text(surf, f"{self.page + 1} / {len(PAGES)}", (CX, H - 58), 18, GREY, "midtop")
        self.prev.enabled = self.page > 0
        self.next.enabled = self.page < len(PAGES) - 1
        self.prev.draw(surf)
        self.next.draw(surf)
        self.back.draw(surf)
