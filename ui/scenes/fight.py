"""The fight itself: picking moves, the reveal, animating each exchange."""

import pygame

from engine.ai import AI
from engine.commentary import describe, finish_line
from engine.corner import advice
from engine.constants import (STRIKE, GRAPPLE, SUB, DEFEND, SUB_ATTACK_LABELS,
                              SUB_DEFEND_LABELS, SUB_TAP, STANDING, CLINCH, GUARD, MOUNT, BACK,
                              EXCHANGES_PER_ROUND, ROUND_SECONDS)
from engine.fight import Fight

from ..arena import Arena
from ..choreo import ACTION, IMPACT, SCALE, layout, hit_pose
from ..common import (W, H, CX, FLOOR_Y, RED, BLUE, GOLD, WHITE, GREY, CORNER, text, panel,
                      bar, Button, font, text_block)
from ..stickman import Figure
from .base import Scene

CLASS_COLOR = {STRIKE: (196, 70, 62), GRAPPLE: (58, 110, 205), SUB: (150, 80, 205),
               DEFEND: (56, 160, 100)}
CLASS_NAME = {STRIKE: "Strike", GRAPPLE: "Grapple", SUB: "Submission", DEFEND: "Defend"}
SUB_COLOR = (150, 80, 205)

KEYS_P1 = [pygame.K_q, pygame.K_w, pygame.K_e, pygame.K_r,
           pygame.K_a, pygame.K_s, pygame.K_d, pygame.K_f]
KEYS_P2 = [pygame.K_u, pygame.K_i, pygame.K_o, pygame.K_p,
           pygame.K_j, pygame.K_k, pygame.K_l, pygame.K_SEMICOLON]
KEYS_SOLO = [[getattr(pygame, f"K_{n + 1}"), KEYS_P1[n]] for n in range(8)]
LABEL_P1 = "QWERASDF"
LABEL_P2 = "UIOPJKL;"

POS_NAME = {STANDING: "Standing", CLINCH: "Clinch", GUARD: "Guard", MOUNT: "Mount",
            BACK: "Back control"}
REPLAY_SPEED = 0.3
REPLAY_ZOOM = 1.7


class FightConfig:
    def __init__(self, p0, p1, mode="ai", level="normal", rounds=3, title=False,
                 on_done=None, event=""):
        self.p0, self.p1 = p0, p1
        self.mode = mode
        self.level = level
        self.rounds = rounds
        self.title = title
        self.on_done = on_done   # called with (app, fight) when the player leaves the result
        self.event = event


class FightScene(Scene):
    def __init__(self, app, cfg):
        super().__init__(app)
        self.cfg = cfg
        self.fight = Fight(cfg.p0, cfg.p1, rounds=cfg.rounds, title=cfg.title)
        self.ai = AI(cfg.level) if cfg.mode == "ai" else None
        self.names = (cfg.p0.name.split()[-1], cfg.p1.name.split()[-1])
        self.arena = Arena()
        self.figs = [
            Figure(CX - 330, FLOOR_Y, 1, cfg.p0.color, glove=RED, scale=SCALE),
            Figure(CX + 330, FLOOR_Y, -1, cfg.p1.color, glove=BLUE, scale=SCALE),
        ]
        self.ref = Figure(CX, FLOOR_Y - 14, 1, (25, 25, 30), glove=(120, 125, 140),
                          body=(120, 125, 140), scale=0.9 * SCALE)
        self.ref.set_pose("ref_fight", idle="ref")
        self.lines = []
        self.popups = []
        self.events = []
        self.t = 0.0
        self.shake = 0.0
        self.ghost = [100.0, 100.0]
        self.banner = None
        self.picks = [None, None]
        self.buttons = [[], []]
        self.hover_desc = None
        self.paused = False
        self.pause_buttons = []
        self.phase = None
        self.phase_t = 0.0
        self.last_ex = None
        self.can_continue = False
        self.time_scale = 1.0
        self.corner_tips = None
        self.snap = None
        self.saved_banner = None
        self.world = pygame.Surface((W, H))
        self._intro()

    # Timeline helpers

    def at(self, delay, fn):
        self.events.append([self.t + delay, fn])

    def say(self, *lines):
        for ln in lines:
            self.lines.append([ln, 0.0])
        self.lines = self.lines[-3:]

    def popup(self, i, s, color=WHITE, size=26, dy=0):
        f = self.figs[i]
        self.popups.append([s, f.x, f.y - 240 + dy, color, 1.1, size])

    def set_banner(self, big, small="", color=WHITE, dur=1.6):
        self.banner = [big, small, color, dur, dur]

    def mv(self, i, key):
        """Fighter i's version of a move, so signature cards show up."""
        return self.fight.state.f[i].move(key)

    def snd(self, name, vol=1.0):
        self.app.sounds.play(name, vol)

    # Phases

    def _intro(self):
        self.phase = "intro"
        xs, idle, _ = layout(self.fight.state)
        walk = [("walk1", 0.16), ("walk2", 0.16)] * 4
        for i, f in enumerate(self.figs):
            f.play(walk + [("stance", 0.2)], idle="stance")
            f.move_to(xs[i], dur=1.3)
        self.ref.place(CX)
        self.ref.set_pose("ref_fight", idle="ref_fight")
        title = "TITLE FIGHT" if self.cfg.title else self.cfg.event
        self.set_banner(f"ROUND {self.fight.round}", title, GOLD, 1.5)
        self.at(1.5, self._fight_call)

    def _fight_call(self):
        self.set_banner("FIGHT!", "", WHITE, 0.9)
        self.snd("bell")
        self.app.sounds.ambience(True)
        self.ref.play([("ref_stop", 0.15), ("ref", 0.3)], idle="ref")
        self.ref.move_to(CX + 300, dur=0.6)
        self.arena.cheer(1.0)
        self.snd("crowd", 0.6)
        self.at(0.7, self._start_pick)

    def _start_pick(self):
        self.phase = "pick"
        self.phase_t = 0.0
        self.picks = [None, None]
        self._build_buttons()
        if self.ai:
            self.picks[1] = self.ai.choose(self.fight, 1)

    def _option_label(self, i, k):
        st = self.fight.state
        if st.sub:
            labels = SUB_ATTACK_LABELS if st.sub.att == i else SUB_DEFEND_LABELS
            return labels[k], "Read your opponent", SUB_COLOR
        m = self.mv(i, k)
        cost = f"{abs(int(m.cost))} stamina" if m.cost > 0 else f"+{abs(int(m.cost))} stamina"
        return m.name, f"{CLASS_NAME[m.cls]}, {cost}", CLASS_COLOR[m.cls]

    def _build_buttons(self):
        self.buttons = [[], []]
        if self.cfg.mode == "ai":
            opts = self.fight.options(0)
            n = len(opts)
            gap = 10
            bw = (W - 40 - gap * (n - 1)) // n
            for j, k in enumerate(opts):
                label, sub, color = self._option_label(0, k)
                b = Button((20 + j * (bw + gap), 634, bw, 74), label, key=f"{j + 1}",
                           sub=sub, color=color, size=21)
                b.pick = k
                b.badge = self._badge(0, k)
                self.buttons[0].append(b)
        else:
            for i in (0, 1):
                opts = self.fight.options(i)
                x0 = 20 if i == 0 else W // 2 + 10
                bw, bh = 146, 36
                keys = LABEL_P1 if i == 0 else LABEL_P2
                for j, k in enumerate(opts):
                    label, sub, color = self._option_label(i, k)
                    b = Button((x0 + (j % 4) * (bw + 6), 632 + (j // 4) * (bh + 6), bw, bh),
                               label, key=keys[j], color=color, size=17)
                    b.pick = k
                    b.badge = self._badge(i, k)
                    self.buttons[i].append(b)

    def _badge(self, i, k):
        from engine.cards import CARDS
        if self.fight.state.sub or k not in CARDS:
            return None
        return {"common": (190, 190, 200), "rare": (90, 160, 255), "legendary": GOLD}[CARDS[k].rarity]

    def _lock(self, i, idx):
        if self.phase != "pick":
            return
        opts = self.fight.options(i)
        if idx >= len(opts):
            return
        self.picks[i] = opts[idx]
        self.snd("click")
        if self.cfg.mode == "ai":
            for j, b in enumerate(self.buttons[0]):
                b.selected = j == idx
        if self.picks[0] is not None and self.picks[1] is not None:
            self._reveal()

    def _reveal(self):
        self.phase = "reveal"
        self.reveal = tuple(self.picks)
        self.at(0.65, self._resolve)

    def _resolve(self):
        before = self.fight.state.clone()
        if self.ai:
            self.ai.observe(self.fight.state, 0, self.picks[0])
        hp_before = [f.hp for f in self.fight.state.f]
        self.snap = self._snapshot()
        self.last_before = before
        ex = self.fight.play(tuple(self.picks))
        self.last_ex = ex
        self.ghost = hp_before
        self.phase = "anim"
        dur = self._animate(ex, before)
        self.say(*describe(ex, self.names))
        if ex.finish:
            self.at(dur, self._finish)
        elif ex.round_over:
            self.at(dur, self._round_end)
        else:
            self.at(dur, self._start_pick)

    # Exchange animation

    def _animate(self, ex, before):
        st = self.fight.state
        xs, idle, faces = layout(st)
        self._faces = faces
        figs = self.figs

        if ex.in_sub:
            a = ex.sub_att
            d = 1 - a
            r = ex.sub_result
            if r == "tighter":
                self.at(0.15, lambda: (figs[d].hit(0.6), self.snd("block", 0.6),
                                       self.popup(d, "TIGHTER!", SUB_COLOR)))
                self.arena.cheer(0.5)
            elif r == "defended":
                self.at(0.15, lambda: self.popup(d, "DEFENDED", (120, 220, 140)))
            elif r == "held":
                self.at(0.15, lambda: self.popup(a, "HOLDING", GREY, 20))
            if r == "escaped":
                self.at(0.3, lambda: self.popup(d, "ESCAPED!", (120, 220, 140), 30))
                self.arena.cheer(0.8)
            if r == "tap":
                self.at(0.2, lambda: self.popup(d, "TAP!", GOLD, 40))
                self.at(0.3, lambda: self._finish_anim(ex, xs, idle))
                return 1.3
            self.at(0.45, lambda: self._settle(xs, idle))
            return 1.0

        # Each fighter throws their move
        for i in (0, 1):
            figs[i].play(list(ACTION[ex.moves[i].anim]))
            if ex.moves[i].cls == STRIKE:
                self.at(max(0.0, IMPACT.get(ex.moves[i].anim, 0.15) - 0.1),
                        lambda: self.snd("whoosh", 0.5))

        for i in (0, 1):
            o = 1 - i
            k = ex.picks[i]
            m = ex.moves[i]
            impact = IMPACT.get(m.anim, 0.15)
            if ex.countered[i]:
                self.at(0.42, lambda i=i: self._counter_anim(i, before))
                continue
            if ex.landed[i]:
                self.at(impact, lambda i=i, k=k: self._hit_anim(i, k, ex, before))
            elif ex.missed[i] and m.power:
                self.at(impact, lambda i=i: self.popup(i, "MISS", GREY, 20))
            if ex.blocked[o] and m.cls == STRIKE:
                self.at(impact, lambda o=o: (self.snd("block"), self.popup(o, "BLOCKED", (150, 220, 255), 22),
                                             self.figs[o].play([("block", 0.08), ("block", 0.2)])))
            if ex.caught[o] and ex.landed[i]:
                self.at(impact + 0.05, lambda i=i: self.popup(i, "CAUGHT!", GOLD, 26, dy=-30))
            if ex.stuffed[i] and m.base in ("takedown", "trip", "sweep", "bridge", "pass"):
                if before.pos == STANDING:
                    self.at(0.16, lambda o=o: self.figs[o].play([("sprawl", 0.14), ("sprawl", 0.2)]))
                self.at(0.25, lambda o=o: self.popup(o, "STUFFED", (150, 220, 255), 22))
            if ex.sub_start == i:
                self.at(0.3, lambda i=i, m=m: (self.popup(i, m.name.upper() + "!", SUB_COLOR, 28),
                                               self.snd("crowd", 0.7), self.arena.cheer(1.0)))
            if ex.rocked[o]:
                self.at(impact + 0.08, lambda o=o: self.popup(o, "ROCKED!", GOLD, 30, dy=-34))
            if ex.cut_opened[o]:
                self.at(impact + 0.1, lambda o=o: (self.popup(o, "CUT!", (220, 40, 40), 30, dy=-64),
                                                   self.arena.blood(self.figs[o].x, 1.5)))
            if ex.limping[o]:
                self.at(impact + 0.1, lambda o=o: self.popup(o, "LIMPING!", (255, 170, 60), 28, dy=-34))
            if ex.knockdown == o:
                self.at(impact + 0.05, lambda o=o: (self.figs[o].play([("ko", 0.25)]),
                                                    self.popup(o, "KNOCKDOWN!", GOLD, 34, dy=-60),
                                                    self.snd("slam"), self.snd("crowd", 1.0),
                                                    self.arena.cheer(2.0)))

        changed = (before.pos, before.top) != (st.pos, st.top)
        ground_now = st.pos in (GUARD, MOUNT, BACK)
        settle_at = 0.55
        if ex.knockdown is not None:
            settle_at = 0.85
        if changed:
            if ground_now and before.pos in (STANDING, CLINCH) and ex.knockdown is None:
                self.at(settle_at, lambda: (self.snd("slam"), self.arena.cheer(0.8)))
                self.at(settle_at, lambda: setattr(self, "shake", 6))
            if ex.reversal_by is not None:
                self.at(settle_at, lambda: self.arena.cheer(0.8))

        if ex.finish:
            self.at(settle_at, lambda: self._finish_anim(ex, xs, idle))
            return 1.4
        self.at(settle_at, lambda: self._settle(xs, idle, 0.35 if changed else 0.25))
        return settle_at + 0.45

    def _settle(self, xs, idle, dur=0.3):
        faces = getattr(self, "_faces", (1, -1))
        for i, f in enumerate(self.figs):
            f.facing = faces[i]
            f.move_to(xs[i], dur=dur)
            f.play([(idle[i], dur)], idle=idle[i])

    def _hit_anim(self, i, k, ex, before):
        o = 1 - i
        dmg = ex.dmg[i]
        move = ex.moves[i]
        power = move.power
        bottom = before.top == i and before.pos in (GUARD, MOUNT, BACK)
        target = move.target
        self.figs[o].hit(1.5 if power else 0.8)
        pose = hit_pose(before.pos, bottom, target)
        self.figs[o].play([(pose, 0.07), (pose, 0.14)])
        self.popup(o, f"-{dmg:.0f}", (255, 90, 80) if dmg >= 9 else (255, 180, 160),
                   34 if dmg >= 9 else 26)
        if target != "head":
            self.popup(o, "BODY" if target == "body" else "LEG", (255, 170, 60), 18, dy=30)
        self.snd("punch" if dmg >= 8 else "jab")
        if self.fight.state.f[o].cut > 0 and target == "head":
            self.arena.blood(self.figs[o].x, min(1.5, dmg / 10))
        if dmg >= 9:
            self.shake = 8
            self.arena.cheer(0.9)
        elif dmg >= 5:
            self.arena.cheer(0.3)

    def _counter_anim(self, i, before):
        o = 1 - i
        ex = self.last_ex
        self.figs[i].play([("counter", 0.08), ("counter", 0.12)])
        self.figs[o].hit(1.0)
        self.figs[o].play([("hit", 0.07), ("hit", 0.12)])
        self.popup(i, "COUNTER!", GOLD, 28, dy=-30)
        self.popup(o, f"-{ex.dmg[i]:.0f}", (255, 120, 100), 28)
        self.snd("punch")
        self.shake = 5
        self.arena.cheer(0.8)

    def _finish_anim(self, ex, xs, idle):
        w, method, _ = ex.finish
        l = 1 - w
        fw, fl = self.figs[w], self.figs[l]
        if method == "Submission":
            if self.fight.state.pos in (GUARD, MOUNT):
                fl.play([("tapping", 0.25)], idle="tapping")
            elif self.fight.state.pos == BACK:
                fl.play([("rnc_def", 0.15), ("back_bot_hit", 0.3)], idle="back_bot_hit")
        else:
            fl.play([("hit", 0.08), ("ko", 0.45)], idle="ko")
            self.shake = 14
            self.snd("slam")
        self.ref.move_to(fl.x + (90 if l == 0 else -90), dur=0.35)
        self.ref.play([("walk1", 0.12), ("ref_stop", 0.15)], idle="ref_stop")
        self.arena.cheer(2.0)
        self.snd("crowd", 1.0)
        self.app.sounds.ambience(False)

    # Round end and finish

    def _round_end(self):
        self.phase = "round_end"
        self.corner_tips = [advice(self.fight, 0), advice(self.fight, 1)]
        self.snd("bell")
        self.at(0.25, lambda: self.snd("bell"))
        self.can_continue = False
        self.at(0.8, lambda: setattr(self, "can_continue", True))
        if self.fight.over:
            self.set_banner("TIME!", "We go to the judges", GOLD, 2.0)
            self.at(2.2, self._to_result)
            self.phase = "decision"

    def _next_round(self):
        self.can_continue = False
        self.fight.start_next_round()
        for i, f in enumerate(self.figs):
            f.facing = 1 if i == 0 else -1
            f.place(CX - 330 if i == 0 else CX + 330)
            f.set_pose("stance", idle="stance")
        self.ghost = [f.hp for f in self.fight.state.f]
        self.lines = []
        self._intro()

    def _finish(self):
        self.phase = "finished"
        self.can_continue = False
        r = self.fight.result
        self.snd("bell")
        self.at(0.3, lambda: self.snd("bell"))
        self.at(0.6, lambda: self.snd("bell"))
        big = {"KO": "KNOCKOUT!", "TKO": "TKO!", "Submission": "SUBMISSION!"}.get(r.method, r.method)
        self.set_banner(big, f"{r.detail}, round {r.round}, {r.time}", GOLD, 99)
        self.say(finish_line(r, self.names))
        self._victory()
        if r.method in ("KO", "TKO") and self.snap:
            self.at(2.4, self._start_replay)
        else:
            self.at(1.2, lambda: setattr(self, "can_continue", True))

    def _victory(self):
        r = self.fight.result
        w = self.figs[r.winner]
        w.facing = 1 if r.winner == 0 else -1
        w.play([("victory", 0.3)], idle="victory")

    # Slow motion replay of the finish

    def _snapshot(self):
        out = []
        for f in self.figs + [self.ref]:
            out.append((dict(f.cur), f.x, f.y, f.facing, f.idle))
        return out

    def _restore(self, snap):
        for f, (cur, x, y, facing, idle) in zip(self.figs + [self.ref], snap):
            f.cur = f.src = f.dst = dict(cur)
            f.t = 1.0
            f.queue = []
            f.x, f.y = x, y
            f.move_t = 1.0
            f.facing = facing
            f.idle = idle

    def _start_replay(self):
        self.phase = "replay"
        self.saved_banner = self.banner
        self.banner = None
        self.popups = []
        self.events = []
        self.after_replay = self._snapshot()
        self._restore(self.snap)
        self.time_scale = REPLAY_SPEED
        dur = self._animate(self.last_ex, self.last_before)
        self.at(dur + 0.5, self._end_replay)

    def _end_replay(self):
        if self.phase != "replay":
            return
        self.events = []
        self.time_scale = 1.0
        self._restore(self.after_replay)
        self.popups = []
        self.banner = self.saved_banner
        self.phase = "finished"
        self.can_continue = True

    def _to_result(self):
        from .result import ResultScene
        self.app.sounds.ambience(False)
        self.app.goto(ResultScene(self.app, self.fight, self.cfg))

    # Input

    def handle(self, e):
        if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
            self._toggle_pause()
            return
        if self.paused:
            for b in self.pause_buttons:
                if b.handle(e):
                    if b.pick == "resume":
                        self._toggle_pause()
                    elif b.pick == "quit":
                        self.app.sounds.ambience(False)
                        from .menu import MenuScene
                        self.app.goto(MenuScene(self.app))
            return
        if e.type == pygame.KEYDOWN and e.key == pygame.K_m:
            self.app.sounds.toggle_mute()
            return
        cont = (e.type == pygame.KEYDOWN and e.key in (pygame.K_SPACE, pygame.K_RETURN)) or \
               (e.type == pygame.MOUSEBUTTONDOWN and e.button == 1)
        if self.phase == "round_end" and self.can_continue and cont:
            self._next_round()
            return
        if self.phase == "replay" and cont:
            self._end_replay()
            return
        if self.phase == "finished" and self.can_continue and cont:
            self._to_result()
            return
        if self.phase != "pick":
            return
        if self.cfg.mode == "ai":
            for b in self.buttons[0]:
                if b.handle(e):
                    self._lock(0, self.buttons[0].index(b))
                if e.type == pygame.MOUSEMOTION and b.hover:
                    self.hover_desc = b
            if e.type == pygame.KEYDOWN:
                for idx, keys in enumerate(KEYS_SOLO):
                    if e.key in keys:
                        self._lock(0, idx)
        else:
            if e.type == pygame.KEYDOWN:
                if e.key in KEYS_P1:
                    self._lock(0, KEYS_P1.index(e.key))
                elif e.key in KEYS_P2:
                    self._lock(1, KEYS_P2.index(e.key))

    def _toggle_pause(self):
        self.paused = not self.paused
        if self.paused:
            self.pause_buttons = [Button((CX - 130, 320, 260, 54), "Resume"),
                                  Button((CX - 130, 386, 260, 54), "Quit to menu", color=(120, 40, 40))]
            self.pause_buttons[0].pick = "resume"
            self.pause_buttons[1].pick = "quit"

    # Frame

    def update(self, dt):
        if self.paused:
            return
        real_dt = dt
        dt *= self.time_scale
        self.t += dt
        self.phase_t += dt
        due = [ev for ev in self.events if ev[0] <= self.t]
        self.events = [ev for ev in self.events if ev[0] > self.t]
        for ev in due:
            ev[1]()
        for i, f in enumerate(self.figs):
            f.cut = self.fight.state.f[i].cut
            f.update(dt)
        self.ref.update(dt)
        self.arena.update(real_dt)
        self.shake = max(0.0, self.shake - dt * 40)
        for p in self.popups:
            p[2] -= dt * 40
            p[4] -= dt
        self.popups = [p for p in self.popups if p[4] > 0]
        for ln in self.lines:
            ln[1] += dt
        hp = [f.hp for f in self.fight.state.f]
        for i in (0, 1):
            if self.ghost[i] > hp[i]:
                self.ghost[i] = max(hp[i], self.ghost[i] - dt * 25)
        if self.banner:
            self.banner[3] -= dt
            if self.banner[3] <= 0:
                self.banner = None

    def draw(self, surf):
        import math
        import random
        sh = (0, 0)
        if self.shake > 0:
            sh = (int(random.uniform(-1, 1) * self.shake), int(random.uniform(-1, 1) * self.shake * 0.5))
        replay = self.phase == "replay"
        target = self.world if replay else surf
        self.arena.draw(target, sh)
        layer = target
        self.ref.draw(layer)
        # Draw the top fighter last so they sit over the bottom one
        order = (0, 1)
        st = self.fight.state
        if st.top is not None:
            order = (1 - st.top, st.top)
        for i in order:
            self.figs[i].draw(layer)
        for s, x, y, c, t, size in self.popups:
            text(layer, s, (x, y), size, c, "center", bold=True, display=size >= 26,
                 alpha=int(255 * min(1.0, t * 2)))
        if replay:
            self._draw_replay(surf)
            return
        self._draw_hud(surf)
        if self.phase in ("pick",):
            self._draw_picks(surf)
        if self.phase == "reveal":
            self._draw_reveal(surf)
        if st.sub and self.phase in ("pick", "reveal", "anim"):
            self._draw_sub_meter(surf)
        if self.banner:
            self._draw_banner(surf)
        if self.phase == "round_end":
            self._draw_round_summary(surf)
        if self.phase == "finished" and self.can_continue:
            text(surf, "Press SPACE to continue", (CX, 410), 20, WHITE, "center", bold=True)
        if self.paused:
            panel(surf, (0, 0, W, H), (0, 0, 0), alpha=160, radius=0)
            text(surf, "PAUSED", (CX, 250), 54, WHITE, "center", display=True)
            for b in self.pause_buttons:
                b.draw(surf)

    def _draw_replay(self, surf):
        xs = [f.x for f in self.figs]
        cx = sum(xs) / 2
        cy = FLOOR_Y - 150
        w, h = int(W / REPLAY_ZOOM), int(H / REPLAY_ZOOM)
        rect = pygame.Rect(0, 0, w, h)
        rect.center = (int(cx), int(cy))
        rect.clamp_ip(pygame.Rect(0, 0, W, H))
        zoomed = pygame.transform.smoothscale(self.world.subsurface(rect), (W, H))
        surf.blit(zoomed, (0, 0))
        pygame.draw.rect(surf, (0, 0, 0), (0, 0, W, 56))
        pygame.draw.rect(surf, (0, 0, 0), (0, H - 56, W, 56))
        if (pygame.time.get_ticks() // 500) % 2:
            pygame.draw.circle(surf, (220, 30, 30), (40, 28), 9)
        text(surf, "REPLAY", (58, 28), 26, WHITE, "midleft", display=True)
        text(surf, "SPACE to skip", (W - 24, H - 28), 15, GREY, "midright")

    def _draw_hud(self, surf):
        f = self.fight
        st = f.state
        for i in (0, 1):
            p = self.cfg.p0 if i == 0 else self.cfg.p1
            fs = st.f[i]
            left = i == 0
            x = 20 if left else W - 20 - 500
            panel(surf, (x, 12, 500, 78), (14, 15, 22), alpha=200)
            pygame.draw.rect(surf, CORNER[i], (x if left else x + 494, 12, 6, 78))
            name = p.name.upper()
            anchor = "topleft" if left else "topright"
            nx = x + 16 if left else x + 484
            name_r = text(surf, name, (nx, 16), 24, WHITE, anchor, display=True, max_width=300)
            info = f"{p.record()}  {p.archetype}"
            r = name_r.w
            text(surf, info, (nx + (r + 12 if left else -(r + 12)), 22), 15, GREY, anchor)
            bar(surf, (x + 16, 50, 468, 18), fs.hp / 100, CORNER[i], flip=not left,
                ghost=self.ghost[i] / 100)
            bar(surf, (x + 16, 72, 468, 8), fs.stamina / 100, (236, 200, 70), flip=not left)
            if fs.rocked:
                text(surf, "ROCKED", (x + 250, 52), 14, GOLD, "midtop", bold=True)
            tags = []
            if fs.body >= 10:
                tags.append(("BODY", fs.body))
            if fs.legs >= 10:
                tags.append(("LEGS", fs.legs))
            if fs.cut > 0:
                tags.append(("CUT", fs.cut))
            tx = x + 16 if left else x + 484
            for label, v in tags:
                c = (255, 200, 90) if v < 40 else (255, 140, 60) if v < 70 else (255, 80, 60)
                r2 = text(surf, f"{label} {v:.0f}%", (tx, 94), 14, c, "topleft" if left else "topright",
                          bold=True)
                tx = r2.right + 14 if left else r2.left - 14
        # Clock
        panel(surf, (CX - 84, 12, 168, 78), (10, 10, 14), alpha=230)
        rounds = f"ROUND {f.round} OF {f.rounds}"
        text(surf, rounds, (CX, 18), 14, GREY, "midtop", bold=True)
        text(surf, f.clock(), (CX, 34), 38, WHITE, "midtop", display=True)
        if self.cfg.title:
            text(surf, "TITLE FIGHT", (CX + 92, 76), 13, GOLD, "topleft", bold=True)
        # Commentary
        y = 128
        lines = [] if self.phase == "round_end" else self.lines[-2:]
        for ln, age in lines:
            a = 255 if age < 6 else max(0, int(255 - (age - 6) * 120))
            if a > 0:
                text(surf, ln, (CX, y), 20, WHITE, "midtop", alpha=a)
            y += 26
        # Position
        if self.phase in ("pick", "reveal", "anim"):
            if st.sub:
                pos = f"Submission attempt: {self.mv(st.sub.att, st.sub.move).name}"
            elif st.pos in (GUARD, MOUNT, BACK):
                pos = f"{POS_NAME[st.pos]}, {self.names[st.top]} on top"
            else:
                pos = POS_NAME[st.pos]
            text(surf, pos.upper(), (CX, 96), 15, GOLD, "midtop", bold=True)

    def _draw_picks(self, surf):
        st = self.fight.state
        if self.cfg.mode == "ai":
            panel(surf, (10, 604, W - 20, 112), (10, 11, 16), alpha=225)
            for b in self.buttons[0]:
                b.draw(surf)
            hint = "Pick a move with the number keys, QWER ASDF or the mouse"
            if st.sub:
                hint = ("Attacking: pick a side they will not guess" if st.sub.att == 0
                        else "Defending: match their side to escape")
            hb = next((b for b in self.buttons[0] if b.hover), None)
            if hb and not st.sub:
                hint = self.mv(0, hb.pick).desc
            text(surf, hint, (24, 609), 16, WHITE, bold=True)
            if not st.sub:
                text(surf, "Strike beats grapple, grapple beats defend, defend beats strike",
                     (W - 24, 610), 14, GREY, "topright")
        else:
            for i in (0, 1):
                x0 = 10 if i == 0 else W // 2
                panel(surf, (x0, 604, W // 2 - 10, 112), (10, 11, 16), alpha=225)
                for b in self.buttons[i]:
                    b.draw(surf)
                who = self.names[i].upper()
                keys = " ".join(LABEL_P1 if i == 0 else LABEL_P2)
                if st.sub:
                    role = "attacking, hide a side" if st.sub.att == i else "defending, match their side"
                    tip = f"{who}  {role}"
                else:
                    tip = f"{who}  keys {keys}"
                text(surf, tip, (x0 + 14, 608), 15, CORNER[i], bold=True)
                if self.picks[i] is not None:
                    panel(surf, (x0, 604, W // 2 - 10, 112), CORNER[i], alpha=255)
                    text(surf, "LOCKED IN", (x0 + (W // 2 - 10) // 2, 660), 34, WHITE, "center",
                         display=True)

    def _draw_reveal(self, surf):
        st = self.fight.state
        for i in (0, 1):
            k = self.reveal[i]
            if st.sub:
                labels = SUB_ATTACK_LABELS if st.sub.att == i else SUB_DEFEND_LABELS
                name, color = labels[k], SUB_COLOR
            else:
                m = self.mv(i, k)
                name, color = m.name, CLASS_COLOR[m.cls]
            x = CX - 300 if i == 0 else CX + 300
            r = font(36, display=True).size(name.upper())
            rect = pygame.Rect(0, 0, r[0] + 40, 58)
            rect.center = (x, 300)
            panel(surf, rect, color, alpha=235)
            text(surf, name.upper(), rect.center, 36, WHITE, "center", display=True)
        text(surf, "VS", (CX, 300), 30, GOLD, "center", display=True)

    def _draw_sub_meter(self, surf):
        s = self.fight.state.sub
        name = self.mv(s.att, s.move).name.upper()
        rect = panel(surf, (CX - 190, 176, 380, 70), (16, 10, 24), alpha=225, border=SUB_COLOR)
        text(surf, name, (CX, 182), 18, (210, 170, 255), "midtop", bold=True)
        text(surf, "ESCAPE", (rect.x + 14, 216), 14, (120, 220, 140), "midleft", bold=True)
        text(surf, "TAP", (rect.right - 14, 216), 14, GOLD, "midright", bold=True)
        for k in range(SUB_TAP + 1):
            x = CX - 90 + k * 60
            filled = k <= s.lock and k > 0
            c = SUB_COLOR if filled else (50, 46, 60)
            if k == 0:
                c = (60, 110, 70)
            pygame.draw.circle(surf, c, (x, 218), 13)
            pygame.draw.circle(surf, (0, 0, 0), (x, 218), 13, 2)
        x = CX - 90 + s.lock * 60
        pygame.draw.circle(surf, WHITE, (x, 218), 17, 3)

    def _draw_banner(self, surf):
        big, small, color, t, total = self.banner
        a = int(255 * min(1.0, t * 3, (total - t) * 6 + 0.2))  # fade in, then out
        text(surf, big, (CX, 300), 92, color, "center", display=True, alpha=a)
        if small:
            text(surf, small, (CX, 365), 26, WHITE, "center", alpha=a)

    def _draw_round_summary(self, surf):
        f = self.fight
        rect = panel(surf, (CX - 300 - 160, 160, 920, 380), (12, 13, 20), alpha=240, border=GOLD)
        rect = pygame.Rect(rect.x, rect.y, 600, rect.h)
        text(surf, f"END OF ROUND {f.round}", (CX - 160, rect.y + 16), 34, GOLD, "midtop", display=True)
        self._draw_corner(surf, pygame.Rect(rect.right + 10, rect.y + 16, 300, rect.h - 32))
        CXs = CX - 160
        s0, s1 = f.stats[-1]
        rows = [
            ("Strikes landed", f"{s0.landed}/{s0.thrown}", f"{s1.landed}/{s1.thrown}"),
            ("Damage", f"{s0.dmg:.0f}", f"{s1.dmg:.0f}"),
            ("Takedowns", f"{s0.takedowns}", f"{s1.takedowns}"),
            ("Control time", _ctrl(s0.control), _ctrl(s1.control)),
            ("Sub attempts", f"{int(s0.sub_attempts)}", f"{int(s1.sub_attempts)}"),
            ("Knockdowns", f"{s0.knockdowns}", f"{s1.knockdowns}"),
        ]
        text(surf, self.names[0].upper(), (rect.x + 110, rect.y + 66), 20, RED, "midtop", bold=True)
        text(surf, self.names[1].upper(), (rect.right - 110, rect.y + 66), 20, BLUE, "midtop", bold=True)
        y = rect.y + 100
        for label, a, b in rows:
            text(surf, a, (rect.x + 110, y), 20, WHITE, "midtop")
            text(surf, label, (CXs, y), 17, GREY, "midtop")
            text(surf, b, (rect.right - 110, y), 20, WHITE, "midtop")
            y += 30
        if self.can_continue:
            text(surf, f"Press SPACE for round {f.round + 1}", (CXs, rect.bottom - 40), 18, WHITE,
                 "midtop", bold=True)

    def _draw_corner(self, surf, rect):
        pygame.draw.line(surf, (60, 60, 70), (rect.x - 6, rect.y), (rect.x - 6, rect.bottom), 2)
        corners = [0] if self.cfg.mode == "ai" else [0, 1]
        y = rect.y
        for i in corners:
            who = "YOUR CORNER" if self.cfg.mode == "ai" else f"{self.names[i].upper()}'S CORNER"
            text(surf, who, (rect.x + 10, y), 18, CORNER[i], bold=True)
            y += 32
            tips = self.corner_tips[i] if self.corner_tips else []
            for tip in tips[:3 if len(corners) == 1 else 2]:
                pygame.draw.circle(surf, GOLD, (rect.x + 16, y + 10), 4)
                y = text_block(surf, tip, (rect.x + 28, y), 16, rect.w - 34, WHITE, "topleft") + 8
            y += 10


def _ctrl(n):
    secs = int(n * ROUND_SECONDS / EXCHANGES_PER_ROUND)
    return f"{secs // 60}:{secs % 60:02d}"
