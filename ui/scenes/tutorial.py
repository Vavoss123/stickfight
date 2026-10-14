"""The tutorial: a guided first fight.

A coach says what to try, the sparring partner does what the lesson needs, and the
next lesson only starts once the last one worked. It teaches the triangle, the one
twist that matters most on the feet, the ground, and the submission contest.
"""

import math

import pygame

from engine.constants import STANDING, GUARD, MOUNT, SUB_OPTIONS, STRIKE, GRAPPLE, DEFEND
from engine.moves import base_class
from engine.roster import make

from ..common import CX, GOLD, WHITE, GREY, GREEN, text, text_block, panel
from .fight import FightScene, FightConfig

CLASS_WORD = {STRIKE: "strike", GRAPPLE: "grapple", DEFEND: "defend", "feint": "feint"}

# want: moves to highlight. opp: what the partner does. done(scene, ex): did it work.
LESSONS = [
    dict(
        title="Strike beats grapple",
        say="Every turn you both pick a move in secret, then both happen at once. Your partner "
            "is about to shoot for a takedown. A Power punch catches them coming in.",
        want=["cross"], opp="takedown", pos=(STANDING, None),
        done=lambda s, ex: ex.caught[1] and ex.landed[0],
        ok="Caught them! A strike beats a grapple. Careful though: a takedown walks straight "
           "through jabs, body shots and kicks. Only the Power punch stops it.",
    ),
    dict(
        title="Grapple beats defend",
        say="Now they are going to stand and block. Blocking beats strikes, but a grapple "
            "beats a defence. Take them down.",
        want=["takedown"], opp="block", pos=(STANDING, None),
        done=lambda s, ex: s.fight.state.pos == GUARD and s.fight.state.top == 0,
        ok="Takedown! You are on top in their guard.",
    ),
    dict(
        title="On the ground",
        say="They are covering up. Covering beats ground and pound, so pass to mount instead. "
            "Passing is a grapple, and grapples beat defence.",
        want=["pass"], opp="cover", pos=(GUARD, 0),
        done=lambda s, ex: s.fight.state.pos == MOUNT,
        ok="Full mount, the best place to be. From here you can strike, take the back or "
           "go for a submission.",
    ),
    dict(
        title="Go for the finish",
        say="They are covering their face. A submission counts as a grapple, so it beats "
            "a defence too. Lock up the Arm triangle.",
        want=["armtri"], opp="mcover", pos=(MOUNT, 0),
        done=lambda s, ex: s.fight.state.sub is not None,
        ok="It is locked in. Now the submission contest starts.",
    ),
    dict(
        title="The submission contest",
        say="Pick a side to crank. If they guess the same side the hold loosens, if not it "
            "gets tighter. Fill the meter and they tap.",
        want=list(SUB_OPTIONS), opp="dodge", pos=None,
        done=lambda s, ex: s.fight.over,
        ok="",
    ),
]

TIPS = [
    "Yellow bar: stamina. Every move costs some, defending gives some back.",
    "Purple bar: momentum. Fill it and your next attack goes ALL IN.",
    "Hover any bar or tag in a fight to see what it means.",
    "The computer learns your habits, so mix it up.",
]


class TutorialScene(FightScene):
    def __init__(self, app):
        me = make("Rookie", "The Student", "Striker", tweak={"wrestling": 3, "grappling": 3},
                  cards=({}, [], 1), color=(220, 60, 60), record=(0, 0))
        partner = make("Sparring Partner", "", "Brawler", tweak={k: -2 for k in
                       ("striking", "wrestling", "grappling", "cardio")},
                       cards=({}, [], 1), color=(60, 120, 230), record=(0, 0))

        def done(app, fight):
            app.settings["tutorial_done"] = True
            app.settings.save()
            from .menu import MenuScene
            app.goto(MenuScene(app))

        cfg = FightConfig(me, partner, mode="ai", level="easy", rounds=1, on_done=done,
                          event="Tutorial", practice=True)
        super().__init__(app, cfg)
        self.ai = None
        self.lesson = 0
        self.coach = ""
        self.result = ""
        self.t_coach = 0.0

    # The script

    def _current(self):
        return LESSONS[min(self.lesson, len(LESSONS) - 1)]

    def _start_pick(self):
        self.fight.exchange = min(self.fight.exchange, 5)   # hold the clock, no round breaks
        st = self.fight.state
        st.f[0].stamina = max(st.f[0].stamina, 70.0)        # running out of gas is a later lesson
        pos = self._current()["pos"]
        if pos and not st.sub and (st.pos, st.top) != pos:
            # Things went sideways: put them back where the lesson starts
            st.pos, st.top = pos
            self.result = (self.result + " Let's reset the position.").strip()
            from ..choreo import layout
            xs, idle, faces = layout(st)
            self._faces = faces
            self._settle(xs, idle, 0.3)
        super()._start_pick()
        self.t_coach = 0.0

    def _lock(self, i, idx):
        if self.phase != "pick" or i != 0:
            return
        opts = self.fight.options(0)
        if idx >= len(opts):
            return
        self.picks[1] = self._partner_pick(opts[idx])
        super()._lock(0, idx)

    def _partner_pick(self, mine):
        st = self.fight.state
        opp = self._current()["opp"]
        if st.sub:
            # Defending a hold: always guess wrong so the lesson can finish
            return next(o for o in SUB_OPTIONS if o != mine)
        options = self.fight.options(1)
        if opp in options:
            return opp
        return options[0]

    def _resolve(self):
        mine = self.mv(0, self.picks[0]) if not self.fight.state.sub else None
        super()._resolve()
        ex = self.last_ex
        lesson = self._current()
        if lesson["done"](self, ex):
            self.result = lesson["ok"]
            self.lesson += 1
            self.snd("levelup", 0.6)
        elif ex.in_sub:
            self.result = {"tighter": "Tighter! They guessed wrong. Again.",
                           "held": "Still holding. Keep cranking."}.get(ex.sub_result, "")
        elif not self.fight.state.sub:
            self.result = self._why(ex, mine, lesson)

    def _why(self, ex, mine, lesson):
        """Explain a lesson that did not work, then go again."""
        if mine is None:
            return ""
        want = [self.mv(0, k).name for k in lesson["want"] if k in self.fight.options(0)]
        if mine.key in lesson["want"]:
            if ex.stuffed[0]:
                return "Stuffed! Grapples can fail, more so when you are tired. Same again."
            return "Close, but it did not quite land. Same again."
        theirs = ex.moves[1]
        return (f"Your {mine.name.lower()} ({CLASS_WORD.get(base_class(mine), 'move')}) ran into their "
                f"{theirs.name.lower()}. Try the {' or '.join(want) or 'highlighted move'}.")

    # Drawing

    def update(self, dt):
        super().update(dt)
        self.t_coach += dt

    def draw(self, surf):
        super().draw(surf)
        if self.phase == "pick" and not self.paused:
            self._draw_coach(surf)
            self._highlight(surf)
        if self.phase == "finished":
            self._draw_tips(surf)

    def _draw_coach(self, surf):
        lesson = self._current()
        r = panel(surf, (CX - 430, 254, 860, 120), (14, 18, 30), alpha=235, border=GOLD)
        step = f"LESSON {min(self.lesson + 1, len(LESSONS))} OF {len(LESSONS)}: {lesson['title'].upper()}"
        text(surf, step, (r.x + 18, r.y + 10), 15, GOLD, bold=True)
        y = r.y + 34
        if self.result:
            y = text_block(surf, self.result, (r.x + 18, y), 15, r.w - 36, GREEN, "topleft", bold=True)
            y += 2
        text_block(surf, lesson["say"], (r.x + 18, y), 15, r.w - 36, WHITE, "topleft")

    def _highlight(self, surf):
        want = self._current()["want"]
        pulse = 0.5 + 0.5 * math.sin(self.t_coach * 6)
        for b in self.buttons[0]:
            if b.pick in want:
                pygame.draw.rect(surf, GOLD, b.rect.inflate(6 + 6 * pulse, 6 + 6 * pulse), 3,
                                 border_radius=10)

    def _draw_tips(self, surf):
        r = panel(surf, (CX - 360, 440, 720, 172), (14, 18, 30), alpha=235, border=GOLD)
        text(surf, "TUTORIAL DONE. A FEW MORE THINGS:", (r.x + 18, r.y + 12), 15, GOLD, bold=True)
        y = r.y + 40
        for tip in TIPS:
            text(surf, "- " + tip, (r.x + 18, y), 15, WHITE)
            y += 24
        text(surf, "How to play in the menu has the full rules.", (r.x + 18, y + 2), 13, GREY)
