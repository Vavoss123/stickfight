"""An endless sparring session for the main menu.

Short scripted exchanges, picked at random one after another: punches, kicks, feints,
weaves, the clinch, takedowns, ground and pound, submission attempts and escapes.
Nobody ever gets finished, so it can run forever.
"""

import random

from engine.looks import default_look

from .choreo import ACTION, THROWS, lunge
from .common import RED, BLUE
from .stickman import Figure

TEMPO = 1.6           # stretches every wait, so the whole thing runs this much slower
SPEED = 0.75 * TEMPO  # how long each pose lasts, a little quicker than a real fight, then slowed down
GAP = 50              # half the standing gap, in authored units
CLINCH = 34


# Where each standing strike is aimed, so the thrower can step in until it reaches
AIM = {"jab": "head", "cross": "head", "kick": "head", "dirty": "head", "body": "body",
       "knees": "body", "legkick": "legs", "superman": "head", "spinfist": "head", "showtime": "head",
       "flyknee": "body", "liver": "body", "calfkick": "legs"}


class _Beat:
    """A list of (time, action) built up with a moving cursor."""

    def __init__(self):
        self.events = []
        self.t = 0.0

    def do(self, fn, wait=0.0):
        self.events.append((self.t, fn))
        self.t += wait * TEMPO


class Spar:
    def __init__(self, cx, floor, scale, rng=None):
        self.cx, self.floor, self.s = cx, floor, scale
        self.rng = rng or random.Random()
        self.figs = [Figure(cx - GAP * scale, floor, 1, (200, 40, 40), glove=RED, scale=scale),
                     Figure(cx + GAP * scale, floor, -1, (40, 90, 220), glove=BLUE, scale=scale)]
        self.figs[0].dress(look=default_look("Red Corner"))
        self.figs[1].dress(look=default_look("Blue Corner"))
        self.idle = ["stance", "stance"]
        self.clock = 0.0
        self.queue = []
        self.timers = []       # (time, fn) things to do a moment from now, like stepping back
        self.next_at = 0.6
        self.last = None
        self.beats = [self.boxing, self.kicks, self.feint, self.weave, self.clinch, self.guillotine,
                      self.sprawl, self.on_guard, self.on_mount, self.on_back, self.boxing, self.kicks,
                      self.flashy, self.judo, self.judo]

    # Building blocks

    def act(self, i, name):
        if name in AIM and self.idle == ["stance", "stance"]:
            f, t = self.figs[i], self.figs[1 - i]
            px = lunge(name, AIM[name], abs(f.move_dst[0] - t.move_dst[0]), f.scale, t.scale)
            self._step(i, f.facing * px)
        self.figs[i].play([(p, d * SPEED) for p, d in ACTION[name]], idle=self.idle[i])

    def _step(self, i, dx, dur=0.12):
        """Move fighter i along the mat for a moment, then back where they were."""
        f = self.figs[i]
        if abs(dx) < 1:
            return
        home = f.move_dst[0]
        f.move_to(home + dx, self.floor, dur)

        def back():
            if self.idle == ["stance", "stance"]:      # unless they have tied up or gone down since
                f.move_to(home, self.floor, 0.3)
        self.timers.append((self.clock + 0.5 * TEMPO, back))

    def hold(self, i, pose, dur=0.16):
        self.idle[i] = pose
        self.figs[i].play([(pose, dur)], idle=pose)

    def relax(self, i):
        self.idle[i] = "stance"

    def ouch(self, i, pose="hit", power=0.6):
        f = self.figs[i]
        f.play([(pose, 0.07), (pose, 0.12)], idle=self.idle[i])
        f.hit(power)
        if self.idle[i] == "stance":
            self._step(i, -f.facing * 9 * self.s)    # knocked back a step

    def tie_up(self):
        """Both lock up in the clinch."""
        self.stand(CLINCH, 0.22)
        self.hold(0, "clinch")
        self.hold(1, "clinch")

    def _home(self, i):
        return 1 if i == 0 else -1

    def place(self, xs, dur=0.3):
        for f, x in zip(self.figs, xs):
            f.move_to(x, self.floor, dur)

    def stand(self, gap=GAP, dur=0.35):
        for i, f in enumerate(self.figs):
            f.facing = self._home(i)
            f.move_to(self.cx - self._home(i) * gap * self.s, self.floor, dur)
            self.hold(i, "stance", 0.2)

    def guard(self, top, dur=0.3):
        bot = 1 - top
        fb = self._home(bot)
        bx = self.cx - fb * 30 * self.s
        xs = [0, 0]
        xs[bot], xs[top] = bx, bx + fb * 62 * self.s
        for i in (0, 1):
            self.figs[i].facing = self._home(i)
        self.place(xs, dur)
        self.hold(top, "guard_top")
        self.hold(bot, "guard_bot")

    def mount(self, top, dur=0.3):
        bot = 1 - top
        fb = self._home(bot)
        bx = self.cx + fb * 10 * self.s
        xs = [0, 0]
        xs[bot], xs[top] = bx, bx - fb * 28 * self.s
        for i in (0, 1):
            self.figs[i].facing = self._home(i)
        self.place(xs, dur)
        self.hold(top, "mount_top")
        self.hold(bot, "mount_bot")

    def back_control(self, top, tight=False, dur=0.3):
        bot = 1 - top
        ft = self._home(top)
        self.figs[bot].facing = ft
        self.figs[top].facing = ft
        gap = (16, 16) if tight else (28, 20)
        xs = [0, 0]
        xs[top], xs[bot] = self.cx - ft * gap[0] * self.s, self.cx + ft * gap[1] * self.s
        self.place(xs, dur)
        self.hold(top, "back_top")
        self.hold(bot, "back_bot")

    def get_up(self, b):
        """Both scramble back to their feet."""
        b.do(lambda: (self.act(0, "getup"), self.act(1, "getup")), 0.3)
        b.do(self.stand, 0.4)

    # The beats. a attacks first, d answers. Each ends back on the feet.

    def boxing(self, b, a, d):
        b.do(lambda: self.act(a, "jab"), 0.12)
        b.do(lambda: self.hold(d, "block", 0.08), 0.1)
        b.do(lambda: self.act(a, "jab"), 0.16)
        b.do(lambda: self.act(a, "cross"), 0.1)
        b.do(lambda: (self.relax(d), self.act(d, "weave")), 0.32)
        b.do(lambda: self.act(d, "body"), 0.1)
        b.do(lambda: self.ouch(a, "body_hit"), 0.25)
        b.do(lambda: self.act(d, "jab"), 0.08)
        b.do(lambda: self.act(a, "block"), 0.3)

    def kicks(self, b, a, d):
        b.do(lambda: self.act(a, "legkick"), 0.14)
        b.do(lambda: self.act(d, "check"), 0.35)
        b.do(lambda: self.act(d, "kick"), 0.12)
        b.do(lambda: self.act(a, "block"), 0.32)
        b.do(lambda: self.act(a, "legkick"), 0.16)
        b.do(lambda: self.ouch(d, "leg_hit", 0.4), 0.3)

    def feint(self, b, a, d):
        b.do(lambda: self.act(a, "feint"), 0.1)
        b.do(lambda: self.act(d, "block"), 0.3)
        b.do(lambda: self.act(a, "cross"), 0.2)
        b.do(lambda: self.ouch(d, "hit", 0.7), 0.25)
        b.do(lambda: self.act(d, "jab"), 0.1)
        b.do(lambda: self.act(a, "weave"), 0.35)

    def weave(self, b, a, d):
        b.do(lambda: self.act(d, "cross"), 0.1)
        b.do(lambda: self.act(a, "weave"), 0.3)
        b.do(lambda: self.act(d, "jab"), 0.06)
        b.do(lambda: self.act(a, "weave"), 0.3)
        b.do(lambda: self.act(a, "cross"), 0.18)
        b.do(lambda: self.act(d, "block"), 0.3)
        b.do(lambda: self.act(a, "body"), 0.12)
        b.do(lambda: self.ouch(d, "body_hit"), 0.3)

    def clinch(self, b, a, d):
        b.do(lambda: self.act(a, "clinch"), 0.15)
        b.do(self.tie_up, 0.35)
        b.do(lambda: self.act(a, "knees"), 0.2)
        b.do(lambda: self.ouch(d, "body_hit", 0.4), 0.2)
        b.do(lambda: self.act(d, "dirty"), 0.12)
        b.do(lambda: self.ouch(a, "hit", 0.4), 0.2)
        b.do(lambda: self.act(a, "knees"), 0.3)
        b.do(lambda: self.act(d, "break"), 0.25)
        b.do(self.stand, 0.4)

    def guillotine(self, b, a, d):
        def catch():
            self.stand(CLINCH * 0.8, 0.2)
            self.hold(a, "guillotine")
            self.hold(d, "guillotined")
        b.do(lambda: self.act(d, "takedown"), 0.22)
        b.do(catch, 1.3)
        b.do(lambda: self.hold(d, "frame", 0.2), 0.3)
        b.do(self.stand, 0.4)

    def sprawl(self, b, a, d):
        b.do(lambda: self.act(a, "takedown"), 0.14)
        b.do(lambda: self.hold(d, "sprawl", 0.12), 0.45)
        b.do(lambda: self.act(d, "dirty"), 0.12)
        b.do(lambda: self.ouch(a, "hit", 0.4), 0.2)
        b.do(self.stand, 0.4)

    def on_guard(self, b, a, d):
        b.do(lambda: self.act(a, "takedown"), 0.3)
        b.do(lambda: self.guard(a), 0.4)
        b.do(lambda: self.act(a, "gnp"), 0.2)
        b.do(lambda: self.hold(d, "guard_bot_cover", 0.1), 0.25)
        b.do(lambda: self.act(a, "elbows"), 0.3)
        b.do(lambda: self.hold(d, "guard_bot"), 0.1)
        b.do(lambda: self.act(d, "upkick"), 0.2)
        b.do(lambda: self.ouch(a, "posture", 0.4), 0.3)
        # Triangle attempt, and the escape
        b.do(lambda: (self.hold(d, "triangle", 0.25), self.hold(a, "pass", 0.25)), 1.2)
        b.do(lambda: self.hold(a, "posture", 0.2), 0.3)
        b.do(lambda: self.hold(d, "guard_bot"), 0.2)
        # Sweep, and now the other one is on top
        b.do(lambda: self.act(d, "sweep"), 0.35)
        b.do(lambda: self.guard(d, 0.3), 0.45)
        b.do(lambda: self.act(d, "gnp"), 0.3)
        self.get_up(b)

    def on_mount(self, b, a, d):
        b.do(lambda: self.act(a, "clinch"), 0.12)
        b.do(self.tie_up, 0.25)
        b.do(lambda: self.act(a, "trip"), 0.3)
        b.do(lambda: self.mount(a), 0.4)
        b.do(lambda: self.act(a, "mgnp"), 0.18)
        b.do(lambda: self.ouch(d, "mount_bot_hit", 0.5), 0.15)
        b.do(lambda: self.act(a, "mgnp"), 0.3)
        b.do(lambda: self.hold(d, "mount_bot"), 0.1)
        # Arm triangle attempt, then the bridge
        b.do(lambda: self.hold(a, "arm_tri", 0.25), 1.1)
        b.do(lambda: self.act(d, "bridge"), 0.35)
        b.do(lambda: self.guard(a, 0.3), 0.45)
        b.do(lambda: self.act(d, "upkick"), 0.3)
        self.get_up(b)

    def on_back(self, b, a, d):
        b.do(lambda: self.act(a, "takedown"), 0.3)
        b.do(lambda: self.guard(a), 0.4)
        b.do(lambda: self.act(a, "pass"), 0.3)
        b.do(lambda: self.back_control(a), 0.4)
        b.do(lambda: self.act(a, "bpunch"), 0.25)
        b.do(lambda: self.ouch(d, "back_bot_hit", 0.4), 0.25)
        # Rear naked choke, fought off
        b.do(lambda: (self.back_control(a, tight=True, dur=0.2), self.hold(a, "rnc", 0.25),
                      self.hold(d, "rnc_def", 0.25)), 1.4)
        b.do(lambda: self.back_control(a, dur=0.2), 0.3)
        b.do(lambda: self.act(d, "turnin"), 0.3)
        b.do(lambda: self.guard(a, 0.3), 0.4)
        self.get_up(b)

    def flashy(self, b, a, d):
        b.do(lambda: self.act(a, "superman"), 0.16)
        b.do(lambda: self.hold(d, "block", 0.08), 0.3)
        b.do(lambda: (self.relax(d), self.act(d, "spinfist")), 0.14)
        b.do(lambda: self.act(a, "weave"), 0.4)
        b.do(lambda: self.act(a, self.rng.choice(("showtime", "flyknee"))), 0.2)
        b.do(lambda: self.ouch(d, "hit", 0.8), 0.45)
        b.do(lambda: self.act(d, "liver"), 0.12)
        b.do(lambda: self.ouch(a, "body_hit", 0.5), 0.35)

    def _fly(self, i, anim):
        """Fighter i gets thrown: up into the air, then down onto the mat."""
        pose, height, _ = THROWS[anim]
        f = self.figs[i]
        f.play([(pose, 0.2), (pose, 0.16)], idle=pose)
        f.move_to(f.x, self.floor - height * self.s, 0.2)
        self.timers.append((self.clock + 0.36 * TEMPO, lambda: f.move_to(f.x, self.floor, 0.12)))

    def judo(self, b, a, d):
        throw = self.rng.choice(("seoi", "uchimata", "hiptoss", "osoto", "tomoe"))

        b.do(lambda: self.act(a, "clinch"), 0.12)
        b.do(self.tie_up, 0.3)
        b.do(lambda: self.act(a, throw), 0.22)
        b.do(lambda: self._fly(d, throw), 0.45)
        if throw in ("uchimata", "hiptoss"):
            b.do(lambda: self.mount(a, 0.25), 0.4)
            b.do(lambda: self.act(a, "mgnp"), 0.3)
        else:
            b.do(lambda: self.guard(a, 0.25), 0.4)
            b.do(lambda: self.act(a, "hammer"), 0.3)
        self.get_up(b)

    # Running it

    def _start_beat(self):
        options = [f for f in self.beats if f is not self.last] or self.beats
        beat = self.rng.choice(options)
        self.last = beat
        a = self.rng.randint(0, 1)
        b = _Beat()
        beat(b, a, 1 - a)
        self.queue = sorted(((self.clock + t, k, fn) for k, (t, fn) in enumerate(b.events)),
                            key=lambda e: (e[0], e[1]))
        self.next_at = self.clock + b.t + self.rng.uniform(0.4, 0.8)
        # A little footwork before the next one
        self.queue.append((self.next_at - 0.3, len(b.events), self._footwork))

    def _footwork(self):
        shift = self.rng.uniform(-24, 24) * self.s
        gap = self.rng.uniform(44, 56)
        for i, f in enumerate(self.figs):
            f.move_to(self.cx + shift - self._home(i) * gap * self.s, self.floor, 0.3)

    def update(self, dt):
        self.clock += dt
        while self.queue and self.queue[0][0] <= self.clock:
            self.queue.pop(0)[2]()
        due = [t for t in self.timers if t[0] <= self.clock]
        self.timers = [t for t in self.timers if t[0] > self.clock]
        for _, fn in due:
            fn()
        if not self.queue and self.clock >= self.next_at:
            self._start_beat()
        for f in self.figs:
            f.update(dt)

    def draw(self, surf):
        for f in self.figs:
            f.draw(surf)
