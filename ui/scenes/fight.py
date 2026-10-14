"""The fight itself: picking moves, the reveal, animating each exchange."""

import copy
import math

import pygame

from engine import coach, personality
from engine.ai import AI
from engine.commentary import describe, finish_line
from engine.corner import advice
from engine.constants import (STRIKE, GRAPPLE, SUB, DEFEND, FEINT, SUB_ATTACK_LABELS,
                              SUB_DEFEND_LABELS, SUB_TAP, STANDING, CLINCH, GUARD, MOUNT, BACK,
                              EXCHANGES_PER_ROUND, ROUND_SECONDS)
from engine.fight import Fight
from engine.moves import zone
from engine.weights import get as weight_class

from .. import gamepad
from ..arena import Arena
from ..choreo import ACTION, IMPACT, SCALE, layout, hit_pose
from ..common import (W, H, CX, FLOOR_Y, RED, BLUE, GOLD, WHITE, GREY, GREEN, CORNER, text, panel,
                      bar, Button, font, text_block, wrap)
from ..stickman import Figure
from .base import Scene

CLASS_COLOR = {STRIKE: (196, 70, 62), GRAPPLE: (58, 110, 205), SUB: (150, 80, 205),
               DEFEND: (56, 160, 100), FEINT: (176, 128, 52)}
CLASS_NAME = {STRIKE: "Strike", GRAPPLE: "Grapple", SUB: "Submission", DEFEND: "Defend",
              FEINT: "Feint"}
SUB_COLOR = (150, 80, 205)
HYPE_COLOR = (190, 110, 255)

KEYS_P1 = [pygame.K_q, pygame.K_w, pygame.K_e, pygame.K_r, pygame.K_a, pygame.K_s,
           pygame.K_d, pygame.K_f, pygame.K_z, pygame.K_x, pygame.K_c, pygame.K_v]
KEYS_P2 = [pygame.K_u, pygame.K_i, pygame.K_o, pygame.K_p, pygame.K_j, pygame.K_k,
           pygame.K_l, pygame.K_SEMICOLON, pygame.K_m, pygame.K_COMMA, pygame.K_PERIOD, pygame.K_SLASH]
NUMBER_KEYS = [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_6, pygame.K_7,
               pygame.K_8, pygame.K_9, pygame.K_0, pygame.K_MINUS, pygame.K_EQUALS]
KEYS_SOLO = [[NUMBER_KEYS[n], KEYS_P1[n]] for n in range(12)]
LABEL_P1 = "QWERASDFZXCV"
LABEL_P2 = "UIOPJKL;M,./"
LABEL_SOLO = "1234567890-="
ZONES = ["head", "body", "legs", "arms", "neck", "position", "defence", "trick"]
# What the bars and tags under each name mean, for hovering
HUD_HELP = {
    "health": ("HEALTH", "At zero it is a knockout. A little comes back between rounds."),
    "stamina": ("STAMINA (yellow)", "Every move costs some, defending gives some back. Tired fighters "
                "miss more, hit softer and get taken down."),
    "momentum": ("MOMENTUM (purple)", "Landing shots, takedowns and big moments fill it. When it is full "
                 "your next attack goes ALL IN: more accurate and harder hitting. Stalling gets you booed "
                 "and drains it."),
    "rocked": ("ROCKED", "Hurt and wobbly: easier to hit, hits softer and can be finished. "
               "Clears after an exchange."),
    "body": ("BODY DAMAGE", "Drains stamina and slows recovery. At 100% the ribs crack: TKO."),
    "legs": ("LEG DAMAGE", "Weaker power shots and takedowns, limping past 60%. At 100% the leg breaks: TKO."),
    "arms": ("ARM DAMAGE", "From blocking heavy shots. The guard leaks, punches soften and armbars sink "
             "in easier."),
    "cut": ("CUT", "Blood in the eyes hurts accuracy. A bad enough cut and the doctor stops the fight."),
    "momentum ": ("ALL IN READY", "Momentum is full. The next attack goes all in."),
}
ZONE_LABEL = {"head": "HEAD", "body": "BODY", "legs": "LEGS", "arms": "ARMS", "neck": "NECK",
              "position": "POSITION", "defence": "DEFENCE", "trick": "TRICK"}
ATTACK_ZONES = {"head", "body", "legs", "arms", "neck"}

POS_NAME = {STANDING: "Standing", CLINCH: "Clinch", GUARD: "Guard", MOUNT: "Mount",
            BACK: "Back control"}
REPLAY_SPEED = 0.3
FIGHT_Y = FLOOR_Y - 62    # where the fighters stand: high enough that the ground game clears the move bar
KICKS = {"kick", "legkick", "upkick", "knees", "imanari"}
REPLAY_ZOOM = 1.7


def size_of(profile):
    """How big to draw a fighter, from their weight class."""
    return weight_class(getattr(profile, "weight", None))["size"]


def gloves_of(profile, corner):
    """Gloves bought in the career shop, otherwise the corner colour."""
    return getattr(profile, "gloves", None) or corner


class FightConfig:
    def __init__(self, p0, p1, mode="ai", level="normal", rounds=3, title=False,
                 on_done=None, event="", start=None, deck_budget=None, practice=False):
        self.p0, self.p1 = p0, p1
        self.mode = mode
        self.level = level
        self.rounds = rounds
        self.title = title
        self.on_done = on_done   # called with (app, fight) when the player leaves the result
        self.event = event
        self.start = start       # carried damage, see Fight
        self.deck_budget = deck_budget   # deck points for swaps between rounds
        self.practice = practice         # the tutorial: no achievements


class FightScene(Scene):
    def __init__(self, app, cfg):
        super().__init__(app)
        self.cfg = cfg
        # Copies, so swapping cards between rounds never changes a career or a saved deck
        self.fight = Fight(copy.deepcopy(cfg.p0), copy.deepcopy(cfg.p1), rounds=cfg.rounds,
                           title=cfg.title, start=cfg.start)
        if cfg.mode == "ai":
            coach.give_bench(self.fight.profiles[1])   # the computer's corner has a few cards to bring in
        self.coach_cards = [[], []]     # card swaps the coach suggests at the break
        self.break_start = [None, None]
        self.coach_buttons = []
        self.their_swap = ""
        self.ai = AI(cfg.level, personality=personality.of(cfg.p1)) if cfg.mode == "ai" else None
        self.names = (cfg.p0.name.split()[-1], cfg.p1.name.split()[-1])
        self.arena = Arena()
        self.figs = [
            Figure(CX - 330, FIGHT_Y, 1, cfg.p0.color, glove=gloves_of(cfg.p0, RED),
                   scale=SCALE * size_of(cfg.p0)),
            Figure(CX + 330, FIGHT_Y, -1, cfg.p1.color, glove=gloves_of(cfg.p1, BLUE),
                   scale=SCALE * size_of(cfg.p1)),
        ]
        self.ref = Figure(CX, FIGHT_Y - 14, 1, (25, 25, 30), glove=(120, 125, 140),
                          body=(120, 125, 140), scale=0.9 * SCALE)
        self.ref.set_pose("ref_fight", idle="ref")
        self.lines = []
        self.popups = []
        self.events = []
        self.t = 0.0
        self.shake = 0.0
        self.ghost = [f.hp for f in self.fight.state.f]
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
        self.slowmo = 0.0      # seconds of slow motion left after a big shot
        self.corner_tips = None
        self.snap = None
        self.saved_banner = None
        self.history = []   # move names of recent exchanges, for feedback notes
        self.bubble = None  # [fighter, words, seconds left]
        self.hud_tips = []  # (rect, title, words) for hovering the health bars and tags
        self.world = pygame.Surface((W, H))
        self._intro()

    def feedback_context(self):
        """What a feedback note should remember about the fight."""
        f, st, cfg = self.fight, self.fight.state, self.cfg
        mode = f"vs AI ({cfg.level})" if cfg.mode == "ai" else "2 player"
        out = [f"{cfg.p0.name} ({cfg.p0.archetype}) vs {cfg.p1.name} ({cfg.p1.archetype}), {mode}",
               f"Round {f.round} {f.clock()}, {POS_NAME[st.pos]}"
               + (f", {self.names[st.top]} on top" if st.top is not None else "")]
        for i in (0, 1):
            fs = st.f[i]
            out.append(f"{self.names[i]}: health {fs.hp:.0f}, stamina {fs.stamina:.0f}, "
                       f"body {fs.body:.0f}, legs {fs.legs:.0f}")
        for picks in self.history[-3:]:
            out.append(f"{self.names[0]} {picks[0]} / {self.names[1]} {picks[1]}")
        return out

    # Timeline helpers

    def at(self, delay, fn):
        self.events.append([self.t + delay, fn])

    def say(self, *lines):
        for ln in lines:
            self.lines.append([ln, 0.0])
        self.lines = self.lines[-3:]

    def speak(self, i, line, secs=3.0):
        """A speech bubble over fighter i's head."""
        self.bubble = [i, line, secs]

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
        if self.ai and self.fight.round == self.fight.rounds and self.fight.rounds > 1:
            import random
            self.speak(1, personality.line(self.ai.personality, "last_round", random))
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
        if st.f[i].effort(m) < 1:
            # Not enough gas for it: it will come out slow and weak
            dim = tuple(int(c * 0.5) for c in CLASS_COLOR[m.cls])
            return m.name, "Too tired, weak and slow", dim
        cost = f"{abs(int(m.cost))} stamina" if m.cost > 0 else f"+{abs(int(m.cost))} stamina"
        opening = st.f[i].opening
        if opening and m.cls == STRIKE:
            return m.name, ("You read them: faster" if opening == "read" else "Follow up: faster"), \
                tuple(min(255, int(c * 1.25)) for c in CLASS_COLOR[m.cls])
        return m.name, f"{CLASS_NAME[m.cls]}, {cost}", CLASS_COLOR[m.cls]

    def _display_order(self, i):
        """The options grouped by what they go after, attacks first."""
        opts = self.fight.options(i)
        if self.fight.state.sub:
            return list(opts)
        return sorted(opts, key=lambda k: ZONES.index(zone(self.mv(i, k))))

    def _rows(self, i, order):
        """Attacks on the top row, position, defence and tricks underneath."""
        if self.fight.state.sub:
            return [order]
        top = [k for k in order if zone(self.mv(i, k)) in ATTACK_ZONES]
        bottom = [k for k in order if k not in top]
        return [r for r in (top, bottom) if r]

    def _build_buttons(self):
        self.buttons = [[], []]
        self.order = [self._display_order(0), self._display_order(1)]
        self.zone_heads = [[], []]
        sides = (0,) if self.cfg.mode == "ai" else (0, 1)
        for i in sides:
            order = self.order[i]
            if self.cfg.mode == "ai":
                x0, width = 20, W - 40
                keys = gamepad.PICK_LABELS if self._pad_for(0) is not None else LABEL_SOLO
            else:
                x0, width = (20, W // 2 - 30) if i == 0 else (W // 2 + 10, W // 2 - 30)
                keys = LABEL_P1 if i == 0 else LABEL_P2
                if self._pad_for(i) is not None:
                    keys = gamepad.PICK_LABELS
            rows = self._rows(i, order)
            ys = [618, 672] if len(rows) == 2 else [628]
            hs = [42, 40] if len(rows) == 2 else [72]
            for row, y, h in zip(rows, ys, hs):
                gap = 8
                bw = (width - gap * (len(row) - 1)) // len(row)
                last_zone = None
                for n, k in enumerate(row):
                    j = order.index(k)
                    label, sub, color = self._option_label(i, k)
                    x = x0 + n * (bw + gap)
                    two_p = self.cfg.mode != "ai"
                    b = Button((x, y, bw, h), label, key=keys[j] if j < len(keys) else None,
                               sub="" if two_p else sub, color=color,
                               size=15 if two_p else (16 if len(rows) == 2 else 21),
                               sub_size=11 if len(rows) == 2 else 15)
                    b.pick = k
                    b.badge = self._badge(i, k)
                    self.buttons[i].append(b)
                    if not self.fight.state.sub:
                        z = zone(self.mv(i, k))
                        if z != last_zone:
                            self.zone_heads[i].append((ZONE_LABEL[z], x, y - 12))
                            last_zone = z
        # Buttons in key order, so key n presses button n
        for i in sides:
            self.buttons[i].sort(key=lambda b, i=i: self.order[i].index(b.pick))

    def _lock_display(self, i, j):
        """Key or pad press j, in the order shown on screen."""
        order = getattr(self, "order", None)
        if not order or j >= len(order[i]):
            return
        self._lock(i, self.fight.options(i).index(order[i][j]))

    # Controllers

    def _side_for_pad(self, slot):
        """Which corner a pad plays. One pad in 2 player is blue, red keeps the keyboard."""
        if self.cfg.mode == "ai":
            return 0
        if self.app.pads.count >= 2:
            return slot if slot in (0, 1) else None
        return 1

    def _pad_for(self, side):
        """The pad slot playing this corner, or None if it is on the keyboard."""
        pads = self.app.pads.count
        if pads == 0:
            return None
        for slot in range(min(pads, 2)):
            if self._side_for_pad(slot) == side:
                return slot
        return None

    def handle_pad(self, slot, button):
        """Pad buttons pick moves directly. Returns True when the press was used here."""
        name = gamepad.name(button)
        if name == "start":
            self._toggle_pause()
            return True
        if self.paused:
            if name == "a":
                self._toggle_pause()
            elif name == "back":
                self.app.sounds.ambience(False)
                from .menu import MenuScene
                self.app.goto(MenuScene(self.app))
            return True
        if self.phase == "pick" and button in gamepad.PICK_BUTTONS:
            side = self._side_for_pad(slot)
            if side is not None and self.picks[side] is None:
                self._lock_display(side, gamepad.PICK_BUTTONS.index(button))
            return True
        if name == "a":
            self.handle(gamepad.key_event(pygame.K_SPACE))
            return True
        return False

    def _is_card(self, m):
        from engine.cards import CARDS
        return m.key in CARDS and not CARDS[m.key].is_perk

    def _signature(self, i, m):
        """The card's name flashes up when a signature move works."""
        from engine.cards import CARDS
        color = {"common": (220, 220, 230), "rare": (120, 180, 255), "legendary": GOLD}[CARDS[m.key].rarity]
        self.popup(i, m.name.upper() + "!", color, 30, dy=-130)
        if CARDS[m.key].rarity == "legendary":
            self.arena.cheer(1.2)

    def _badge(self, i, k):
        from engine.cards import CARDS
        if self.fight.state.sub or k not in CARDS or CARDS[k].is_perk:
            return None  # a perk can share a basic move's name (Get Up Artist is "getup")
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
            for b in self.buttons[0]:
                b.selected = b.pick == opts[idx]
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
        if before.sub:
            self.history.append(tuple(self.picks))
        else:
            self.history.append(tuple(self.mv(i, self.picks[i]).name for i in (0, 1)))
        ex = self.fight.play(tuple(self.picks))
        self.last_ex = ex
        self.ghost = hp_before
        self.phase = "anim"
        dur = self._animate(ex, before)
        self.say(*describe(ex, self.names))
        self._taunt(ex)
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
        self._momentum_popups(ex)
        self._referee_moments(ex)

        if ex.in_sub:
            a = ex.sub_att
            d = 1 - a
            r = ex.sub_result
            if r == "tighter":
                self.at(0.15, lambda: (figs[d].hit(0.6), self.snd("squeeze"),
                                       self.popup(d, "TIGHTER!", SUB_COLOR)))
                self.arena.cheer(0.5)
            elif r == "defended":
                self.at(0.15, lambda: self.popup(d, "DEFENDED", (120, 220, 140)))
            elif r == "held":
                self.at(0.15, lambda: self.popup(a, "HOLDING", GREY, 20))
            if r == "escaped":
                self.at(0.3, lambda: (self.popup(d, "ESCAPED!", (120, 220, 140), 30),
                                      self.snd("escape"), self.snd("crowd", 0.8)))
                self.arena.cheer(0.8)
            if r == "tap":
                self.at(0.2, lambda: (self.popup(d, "TAP!", GOLD, 40), self.snd("tap")))
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
            if self._is_card(m) and (ex.success[i] or ex.landed[i]) and ex.sub_start != i:
                self.at(0.05, lambda i=i, m=m: self._signature(i, m))
            if ex.gassed[i]:
                self.at(0.05, lambda i=i: (self.popup(i, "GASSED", (236, 200, 70), 20, dy=-90),
                                           self.snd("breath")))
            if ex.landed[i]:
                self.at(impact, lambda i=i, k=k: self._hit_anim(i, k, ex, before))
            elif ex.missed[i] and m.power:
                self.at(impact, lambda i=i: self.popup(i, "MISS", GREY, 20))
            if ex.blocked[o] and m.cls == STRIKE:
                cover = self._ground_pose(o, before, "cover") or "block"
                self.at(impact, lambda o=o, cover=cover: (
                    self.snd("block"), self.popup(o, "BLOCKED", (150, 220, 255), 22),
                    self.figs[o].play([(cover, 0.08), (cover, 0.2)])))
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
                                                    self.snd("boom"), self.snd("roar"),
                                                    self.arena.cheer(2.0)))

        if ex.stall and self.phase != "replay":
            self.at(0.3, lambda: self.snd("boo", 0.7))

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

    def _taunt(self, ex):
        """The computer talks: when it lands something big, gets hurt, tires, takes you
        down, and so on. In its own voice, and not every exchange."""
        import random
        if not self.ai or ex.finish:
            return
        self.taunt_wait = max(0, getattr(self, "taunt_wait", 0) - 1)
        if self.taunt_wait:
            return
        me, you = self.fight.state.f[1], self.fight.state.f[0]
        event = None
        if ex.sub_start == 1:
            event = "sub"
        elif ex.in_sub and ex.sub_result == "escaped" and ex.sub_att == 0:
            event = "escaped"
        elif ex.surge_ready[1]:
            event = "momentum"
        elif ex.knockdown == 0 or ex.rocked[0] or ex.dmg[1] >= 10:
            event = "big"
        elif ex.rocked[1] or ex.dmg[0] >= 10:
            event = "hurt"
        elif ex.takedown_by == 1:
            event = "takedown"
        elif ex.takedown_by == 0:
            event = "taken_down"
        elif ex.booed[1]:
            event = "booed"
        elif you.stamina < 25 and random.random() < 0.5:
            event = "you_tired"
        elif me.stamina < 20 and random.random() < 0.5:
            event = "tired"
        if event is None or random.random() > 0.55:
            return
        name = self.ai.personality
        if event == "big":
            said = random.choice(personality.PERSONALITIES[name]["taunts"])
        else:
            said = personality.line(name, event, random)
        if said:
            self.speak(1, said)
            self.taunt_wait = 2

    def _referee_moments(self, ex):
        """Fouls, breaks, and a moment of slow motion when something big lands."""
        if ex.foul:
            i, what, result = ex.foul
            o = 1 - i
            self.at(0.3, lambda: (self.popup(o, "FOUL!", (255, 90, 80), 30, dy=-130),
                                  self.snd("boo", 0.7), self._ref_in()))
            label = "WARNING" if result == "warning" else "POINT DEDUCTED"
            self.at(0.6, lambda: self.popup(i, label, (255, 170, 60), 24, dy=-100))
        if ex.ref_break:
            self.at(0.45, lambda: (self.popup(0, "BREAK!", WHITE, 26, dy=-140), self._ref_in()))
        big = ex.knockdown is not None or (any(ex.rocked) and max(ex.dmg) >= 9)
        if big and self.phase != "replay":
            m = ex.moves[ex.dmg.index(max(ex.dmg))]
            at = IMPACT.get(m.anim, 0.15) if m else 0.15
            self.at(max(0.0, at - 0.05), lambda: setattr(self, "slowmo", 0.45))

    def _ref_in(self):
        """The referee steps in, then gets back out of the way."""
        self.ref.move_to(CX, dur=0.25)
        self.ref.play([("ref_stop", 0.2), ("ref_stop", 0.5)], idle="ref")
        self.at(0.9, lambda: self.ref.move_to(CX + 300, dur=0.4))

    def _momentum_popups(self, ex):
        """Feints, ALL IN when someone spends full momentum, MOMENTUM when it fills, boos."""
        for i in (0, 1):
            o = 1 - i
            if ex.checked[i]:
                self.at(0.22, lambda i=i, o=o: (self.popup(i, "CHECKED!", (150, 220, 255), 26, dy=-110),
                                                self.popup(o, "LEG!", (255, 140, 60), 22, dy=30),
                                                self.snd("kick"), self.figs[o].hit(1.0)))
            if ex.slipped[i]:
                self.at(0.18, lambda i=i: (self.popup(i, "SLIPPED!", (150, 220, 255), 26, dy=-110),
                                           self.snd("whoosh", 0.8)))
            if ex.walked_in[i]:
                self.at(0.2, lambda i=i: self.popup(i, "WALKED INTO IT!", (255, 120, 90), 24, dy=-140))
        if ex.broken:
            who, what = ex.broken
            label = "CRACKED RIBS!" if what == "ribs" else "BROKEN LEG!"
            self.at(0.35, lambda who=who, label=label: (self.popup(who, label, (255, 70, 60), 32, dy=-170),
                                                        self.snd("boom"), self.snd("roar")))
        for i in (0, 1):
            if ex.feinted[i]:
                self.at(0.12, lambda i=i: (self.popup(i, "FEINT!", (230, 180, 90), 26, dy=-120),
                                           self.popup(1 - i, "FROZEN!", (150, 220, 255), 24, dy=-90),
                                           self.snd("whoosh", 0.7)))
            if ex.surging[i]:
                self.at(0.0, lambda i=i: (self.popup(i, "ALL IN!", GOLD, 32, dy=-160),
                                          self.snd("roar", 0.6), self.arena.cheer(1.5)))
            if ex.surge_ready[i]:
                self.at(0.5, lambda i=i: (self.popup(i, "MOMENTUM!", HYPE_COLOR, 28, dy=-190),
                                          self.snd("crowd", 0.8), self.arena.cheer(1.2)))
            if ex.booed[i]:
                self.at(0.25, lambda i=i: (self.popup(i, "BOOO!", (170, 170, 180), 24, dy=-100),
                                           self.snd("boo", 0.8)))

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
        if target == "body":
            self.snd("body")
        elif move.anim in KICKS:
            self.snd("kick")
        else:
            self.snd("punch" if dmg >= 8 else "jab")
        if self.fight.state.f[o].cut > 0 and target == "head":
            self.arena.blood(self.figs[o].x, min(1.5, dmg / 10))
        if dmg >= 9:
            self.shake = 8
            self.arena.cheer(0.9)
        elif dmg >= 5:
            self.arena.cheer(0.3)

    def _ground_pose(self, i, before, kind):
        """A strike or cover pose for fighter i in a ground position, or None on the feet."""
        if before.pos in (STANDING, CLINCH):
            return None
        top = before.top == i
        poses = {
            GUARD: {"strike": ("gnp", "guard_bot_strike"), "cover": ("posture", "guard_bot_cover")},
            MOUNT: {"strike": ("mount_strike", "mount_bot"), "cover": ("mount_top", "mount_bot")},
            BACK: {"strike": ("back_punch", "rnc_def"), "cover": ("back_top", "rnc_def")},
        }
        pair = poses.get(before.pos, {}).get(kind)
        return pair and (pair[0] if top else pair[1])

    def _counter_anim(self, i, before):
        o = 1 - i
        ex = self.last_ex
        ground = self._ground_pose(i, before, "strike")
        self.figs[i].play([(ground or "counter", 0.08), (ground or "counter", 0.12)])
        self.figs[o].hit(1.0)
        hit = hit_pose(before.pos, before.top == i, "head") if ground else "hit"
        self.figs[o].play([(hit, 0.07), (hit, 0.12)])
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
            self.snd("boom")
        self.ref.move_to(fl.x + (90 if l == 0 else -90), dur=0.35)
        self.ref.play([("walk1", 0.12), ("ref_stop", 0.15)], idle="ref_stop")
        self.arena.cheer(2.0)
        self.snd("roar")
        self.app.sounds.ambience(False)

    # Round end and finish

    def _round_end(self):
        self.phase = "round_end"
        self.corner_tips = [advice(self.fight, 0), advice(self.fight, 1)]
        if not self.fight.over:
            self._coach_break()
        self.snd("bell")
        self.at(0.25, lambda: self.snd("bell"))
        self.can_continue = False
        self.at(0.8, lambda: setattr(self, "can_continue", True))
        if self.fight.over:
            self.set_banner("TIME!", "We go to the judges", GOLD, 2.0)
            self.at(2.2, self._to_result)
            self.phase = "decision"

    # Card swaps between rounds

    def _budget(self, i):
        from engine.cards import deck_points
        from engine.loadouts import BUDGET
        p = self.fight.profiles[i]
        if i == 0 and self.cfg.deck_budget:
            return max(self.cfg.deck_budget, deck_points(p))
        return max(BUDGET, deck_points(p))

    def _human(self, i):
        return i == 0 or self.cfg.mode != "ai"

    def _coach_break(self):
        self.break_start = [copy.deepcopy(p) for p in self.fight.profiles]
        self.their_swap = ""
        for i in (0, 1):
            self.coach_cards[i] = coach.suggest(self.fight, i, self._budget(i)) if self._human(i) else []
        if self.ai:
            ideas = coach.suggest(self.fight, 1, self._budget(1), limit=1)
            if ideas:
                p = self.fight.profiles[1]
                ideas[0].apply(p)
                self.fight.refit(1, p)
                self.their_swap = f"Their corner put in {coach.CARDS[ideas[0].card].name}."
        self._build_coach_buttons()

    def _build_coach_buttons(self):
        self.coach_buttons = []
        sides = (0,) if self.cfg.mode == "ai" else (0, 1)
        for i in sides:
            x0 = 180 if self.cfg.mode == "ai" else (40 if i == 0 else CX + 20)
            width = 920 if self.cfg.mode == "ai" else 580
            ideas = self.coach_cards[i]
            per = (width - 200 - 8 * len(ideas)) // max(1, len(ideas)) if ideas else 0
            for k, s in enumerate(ideas):
                b = Button((x0 + k * (per + 8), 592, per, 46), f"Put in {coach.CARDS[s.card].name}",
                           sub=s.why, size=16, color=(40, 70, 50))
                b.pick = ("idea", i, s)
                self.coach_buttons.append(b)
            key = "C" if i == 0 else "N"
            b = Button((x0 + width - 190, 592, 190, 46), "Adjust deck", key=key, size=17, color=(60, 50, 110))
            b.pick = ("deck", i, None)
            self.coach_buttons.append(b)

    def _swaps_left(self, i):
        if self.break_start[i] is None:
            return coach.SWAPS_PER_BREAK
        return coach.SWAPS_PER_BREAK - coach.changes(self.break_start[i], self.fight.profiles[i])

    def _use_idea(self, i, s):
        if self._swaps_left(i) <= 0:
            self.say("No more changes this break.")
            return
        p = self.fight.profiles[i]
        s.apply(p)
        self.fight.refit(i, p)
        self.coach_cards[i] = [x for x in self.coach_cards[i] if x is not s]
        self._build_coach_buttons()
        self.snd("levelup", 0.6)

    def _open_deck(self, i):
        from .deck import DeckScene
        self.app.goto(DeckScene(self.app, CornerDeck(self, i), lambda: self))

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

    def _handle_break(self, e):
        """Coach ideas and the deck button at the end of a round. True if the event was used."""
        for b in self.coach_buttons:
            if b.handle(e):
                kind, i, s = b.pick
                if kind == "idea":
                    self._use_idea(i, s)
                else:
                    self._open_deck(i)
                return True
        if e.type == pygame.KEYDOWN and e.key in (pygame.K_c, pygame.K_n) and not self.fight.over:
            i = 0 if e.key == pygame.K_c else 1
            if self._human(i):
                self._open_deck(i)
                return True
        if e.type == pygame.MOUSEBUTTONDOWN and any(b.rect.collidepoint(e.pos) for b in self.coach_buttons):
            return True
        return False

    def handle(self, e):
        if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
            self._toggle_pause()
            return
        if self.paused:
            for b in self.pause_buttons:
                if b.handle(e):
                    if b.pick == "resume":
                        self._toggle_pause()
                    elif b.pick == "settings":
                        from .settings import SettingsScene
                        self.app.goto(SettingsScene(self.app, lambda: self))
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
        if self.phase == "round_end" and not self.fight.over and self._handle_break(e):
            return
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
                    self._lock(0, self.fight.options(0).index(b.pick))
                if e.type == pygame.MOUSEMOTION and b.hover:
                    self.hover_desc = b
            if e.type == pygame.KEYDOWN:
                for idx, keys in enumerate(KEYS_SOLO):
                    if e.key in keys:
                        self._lock_display(0, idx)
        else:
            if e.type == pygame.KEYDOWN:
                if e.key in KEYS_P1:
                    self._lock_display(0, KEYS_P1.index(e.key))
                elif e.key in KEYS_P2:
                    self._lock_display(1, KEYS_P2.index(e.key))

    def _toggle_pause(self):
        self.paused = not self.paused
        if self.paused:
            self.pause_buttons = [Button((CX - 130, 310, 260, 54), "Resume"),
                                  Button((CX - 130, 372, 260, 54), "Settings"),
                                  Button((CX - 130, 434, 260, 54), "Quit to menu", color=(120, 40, 40))]
            for b, pick in zip(self.pause_buttons, ("resume", "settings", "quit")):
                b.pick = pick

    # Frame

    def update(self, dt):
        if self.paused:
            return
        real_dt = dt
        dt *= self.time_scale * self.app.settings.fight_speed
        if self.slowmo > 0:
            self.slowmo -= real_dt
            dt *= 0.35
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
        if self.bubble:
            self.bubble[2] -= real_dt
            if self.bubble[2] <= 0:
                self.bubble = None
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
            if self.app.settings["show_rules"] and not st.sub:
                self._draw_rules(surf)
        if self.phase == "reveal":
            self._draw_reveal(surf)
        if st.sub and self.phase in ("pick", "reveal", "anim"):
            self._draw_sub_meter(surf)
        if self.banner:
            self._draw_banner(surf)
        if self.phase == "round_end":
            self._draw_round_summary(surf)
            if not self.fight.over:
                self._draw_coach(surf)
        if self.phase == "finished" and self.can_continue:
            text(surf, "Press SPACE to continue", (CX, 410), 20, WHITE, "center", bold=True)
        if self.bubble and not replay:
            self._draw_bubble(surf)
        if not self.paused:
            self._draw_hud_tip(surf)
        if self.paused:
            panel(surf, (0, 0, W, H), (0, 0, 0), alpha=160, radius=0)
            text(surf, "PAUSED", (CX, 250), 54, WHITE, "center", display=True)
            for b in self.pause_buttons:
                b.draw(surf)
            text(surf, "Something feel off? Press F1 to write a note", (CX, 516), 16, GREY, "center")

    def _draw_replay(self, surf):
        xs = [f.x for f in self.figs]
        cx = sum(xs) / 2
        cy = FIGHT_Y - 150
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
        self.hud_tips = []
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
            self.hud_tips.append((pygame.Rect(x + 16, 48, 468, 22), *HUD_HELP["health"]))
            self.hud_tips.append((pygame.Rect(x + 16, 70, 468, 11), *HUD_HELP["stamina"]))
            self.hud_tips.append((pygame.Rect(x + 16, 81, 468, 9), *HUD_HELP["momentum"]))
            # Momentum: purple while it builds, flashing gold when it is full
            hype_col = HYPE_COLOR
            if fs.surge:
                hype_col = GOLD if (pygame.time.get_ticks() // 250) % 2 else (255, 240, 170)
            bar(surf, (x + 16, 82, 468, 5), fs.hype / 100, hype_col, back=(30, 26, 40), flip=not left)
            if fs.rocked:
                rr = text(surf, "ROCKED", (x + 250, 52), 14, GOLD, "midtop", bold=True)
                self.hud_tips.append((rr.inflate(8, 6), *HUD_HELP["rocked"]))
            tags = []
            if fs.surge:
                tags.append(("MOMENTUM ", None))
            if fs.body >= 10:
                tags.append(("BODY", fs.body))
            if fs.legs >= 10:
                tags.append(("LEGS", fs.legs))
            if fs.arms >= 10:
                tags.append(("ARMS", fs.arms))
            if fs.cut > 0:
                tags.append(("CUT", fs.cut))
            tx = x + 16 if left else x + 484
            for label, v in tags:
                if v is None:
                    c, s = GOLD, label
                else:
                    c = (255, 200, 90) if v < 40 else (255, 140, 60) if v < 70 else (255, 80, 60)
                    s = f"{label} {v:.0f}%"
                r2 = text(surf, s, (tx, 94), 14, c, "topleft" if left else "topright", bold=True)
                tx = r2.right + 14 if left else r2.left - 14
                if label.lower() in HUD_HELP:
                    self.hud_tips.append((r2.inflate(8, 6), *HUD_HELP[label.lower()]))
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

    def _draw_bubble(self, surf):
        """What the fighter says, in a bubble over their head."""
        from ..stickman import joints
        i, line, left = self.bubble
        f = self.figs[i]
        head = joints(f.cur, f.x, f.y, f.facing, f.scale)["head"]
        lines = wrap(line, 17, 260, bold=True)
        w = max(font(17, True).size(l)[0] for l in lines) + 28
        h = 22 * len(lines) + 16
        x = min(max(20, head[0] - w // 2), W - 20 - w)
        y = max(122, head[1] - 40 - h)
        a = int(255 * min(1.0, left * 3))
        bub = pygame.Surface((w, h + 14), pygame.SRCALPHA)
        pygame.draw.rect(bub, (250, 250, 245, a), (0, 0, w, h), border_radius=14)
        tip = max(16, min(w - 16, int(head[0] - x)))
        pygame.draw.polygon(bub, (250, 250, 245, a), [(tip - 10, h - 2), (tip + 10, h - 2), (tip, h + 12)])
        surf.blit(bub, (x, y))
        yy = y + 8
        for ln in lines:
            text(surf, ln, (x + w // 2, yy), 17, (20, 20, 26), "midtop", bold=True, shadow=False, alpha=a)
            yy += 22

    def _draw_hud_tip(self, surf):
        mouse = pygame.mouse.get_pos()
        for rect, title, words in self.hud_tips:
            if rect.collidepoint(mouse):
                lines = wrap(words, 14, 300)
                h = 30 + 18 * len(lines)
                x = min(mouse[0] + 14, W - 340)
                r = panel(surf, (x, mouse[1] + 18, 330, h), (16, 18, 28), alpha=245, border=GOLD)
                text(surf, title, (r.x + 12, r.y + 7), 15, GOLD, bold=True)
                yy = r.y + 28
                for ln in lines:
                    text(surf, ln, (r.x + 12, yy), 14, WHITE)
                    yy += 18
                return

    def _draw_rules(self, surf):
        """What beats what, in the corner. The class of the move under the mouse lights up."""
        import math
        r = panel(surf, (W - 250, 118, 230, 206), (10, 11, 16), alpha=215)
        text(surf, "WHAT BEATS WHAT", (r.centerx, r.y + 8), 13, GOLD, "midtop", bold=True)
        cx, cy, rad = r.centerx, r.y + 112, 62
        nodes = {STRIKE: (cx, cy - rad), GRAPPLE: (cx + rad * 0.95, cy + rad * 0.55),
                 DEFEND: (cx - rad * 0.95, cy + rad * 0.55)}
        hover = None
        hb = next((b for b in self.buttons[0] if b.hover), None) if self.cfg.mode == "ai" else None
        if hb and not self.fight.state.sub:
            hover = self.mv(0, hb.pick).cls
            hover = GRAPPLE if hover == SUB else hover
        for a, b in ((STRIKE, GRAPPLE), (GRAPPLE, DEFEND), (DEFEND, STRIKE)):
            (x0, y0), (x1, y1) = nodes[a], nodes[b]
            dx, dy = x1 - x0, y1 - y0
            d = math.hypot(dx, dy)
            ux, uy = dx / d, dy / d
            sx, sy = x0 + ux * 24, y0 + uy * 24
            ex_, ey = x1 - ux * 26, y1 - uy * 26
            lit = hover in (a, b)
            col = GOLD if lit else (120, 110, 70)
            pygame.draw.line(surf, col, (sx, sy), (ex_, ey), 3)
            px, py = -uy, ux
            pygame.draw.polygon(surf, col, [(ex_ + ux * 8, ey + uy * 8),
                                            (ex_ - ux * 6 + px * 7, ey - uy * 6 + py * 7),
                                            (ex_ - ux * 6 - px * 7, ey - uy * 6 - py * 7)])
            mx, my = (sx + ex_) / 2 + px * 14, (sy + ey) / 2 + py * 14
            text(surf, "beats", (mx, my), 11, col, "center", shadow=False)
        for cls, (x, y) in nodes.items():
            lit = hover == cls
            col = CLASS_COLOR[cls]
            pygame.draw.circle(surf, tuple(min(255, int(c * 1.3)) for c in col) if lit else col,
                               (int(x), int(y)), 22)
            pygame.draw.circle(surf, WHITE if lit else (0, 0, 0), (int(x), int(y)), 22, 2)
            text(surf, CLASS_NAME[cls], (x, y), 13, WHITE, "center", bold=True)
        if hover == FEINT:
            note = "Feint: beats Defend, loses to the rest"
        elif hover:
            beats = {STRIKE: "Grapple", GRAPPLE: "Defend", DEFEND: "Strike"}[hover]
            loses = {STRIKE: "Defend", GRAPPLE: "Strike", DEFEND: "Grapple"}[hover]
            note = f"{CLASS_NAME[hover]} beats {beats}, loses to {loses}"
        else:
            note = "Feint beats Defend only. Subs count as grapples."
        text(surf, note, (r.centerx, r.bottom - 18), 11, GREY if not hover else WHITE, "midtop",
             max_width=r.w - 16)

    def _draw_picks(self, surf):
        st = self.fight.state
        if self.cfg.mode == "ai":
            panel(surf, (10, 584, W - 20, 132), (10, 11, 16), alpha=225)
            self._draw_zone_heads(surf, 0)
            for b in self.buttons[0]:
                b.draw(surf)
            hint = "Pick a move: number keys, the letters in the corners, or the mouse"
            if self._pad_for(0) is not None:
                hint = "Pick a move with the button in its corner"
            if st.sub:
                hint = ("Attacking: pick a side they will not guess" if st.sub.att == 0
                        else "Defending: match their side to escape")
            hb = next((b for b in self.buttons[0] if b.hover), None)
            if hb and not st.sub:
                m = self.mv(0, hb.pick)
                hint = f"{ZONE_LABEL[zone(m)]}: {m.desc}"
                self._draw_target(surf, zone(m))
            text(surf, hint, (24, 588), 15, WHITE, bold=True, max_width=W - 60)
        else:
            for i in (0, 1):
                x0 = 10 if i == 0 else W // 2
                panel(surf, (x0, 584, W // 2 - 10, 132), (10, 11, 16), alpha=225)
                self._draw_zone_heads(surf, i)
                for b in self.buttons[i]:
                    b.draw(surf)
                who = self.names[i].upper()
                if st.sub:
                    role = "attacking, hide a side" if st.sub.att == i else "defending, match their side"
                    tip = f"{who}  {role}"
                else:
                    tip = f"{who}  keys {' '.join(LABEL_P1 if i == 0 else LABEL_P2)}"
                    if self._pad_for(i) is not None:
                        tip = f"{who}  controller: the button in each corner"
                text(surf, tip, (x0 + 14, 588), 14, CORNER[i], bold=True)
                if self.picks[i] is not None:
                    panel(surf, (x0, 584, W // 2 - 10, 132), CORNER[i], alpha=255)
                    text(surf, "LOCKED IN", (x0 + (W // 2 - 10) // 2, 650), 34, WHITE, "center",
                         display=True)

    def _draw_zone_heads(self, surf, i):
        for label, x, y in getattr(self, "zone_heads", [[], []])[i]:
            text(surf, label, (x + 2, y), 11, GOLD, bold=True, shadow=False)

    def _draw_target(self, surf, where):
        """Light up where on the opponent the move under the mouse goes."""
        from ..stickman import joints
        f = self.figs[1]
        j = joints(f.cur, f.x, f.y, f.facing, f.scale)
        mid = lambda a, b: ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        spot = {"head": j["head"], "neck": j["neck"], "body": mid(j["neck"], j["hip"]),
                "legs": mid(j["fknee"], j["bknee"]), "arms": j["felbow"]}.get(where)
        if not spot:
            return
        pulse = 0.5 + 0.5 * math.sin(pygame.time.get_ticks() / 120)
        r = int((24 + 6 * pulse) * f.scale)
        glow = pygame.Surface((r * 2 + 8, r * 2 + 8), pygame.SRCALPHA)
        pygame.draw.circle(glow, (255, 210, 80, int(40 + 30 * pulse)), (r + 4, r + 4), r)
        pygame.draw.circle(glow, (255, 220, 100, int(150 + 80 * pulse)), (r + 4, r + 4), r, 4)
        surf.blit(glow, (spot[0] - r - 4, spot[1] - r - 4))

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
        lead = 0 if s0.points((1, 1, 1)) >= s1.points((1, 1, 1)) else 1
        a, b = (s0, s1) if lead == 0 else (s1, s0)
        reason = next((r for r in a.why(b) if r[1] > r[2]), None)
        if reason and abs(s0.points((1, 1, 1)) - s1.points((1, 1, 1))) > 2:
            label, mine, theirs = reason
            fmt = (lambda v: _ctrl(v)) if label == "control" else (lambda v: f"{v:.0f}")
            view = f"Judges' view: {self.names[lead].upper()}'s round, on {label} ({fmt(mine)} to {fmt(theirs)})"
        else:
            view = "Judges' view: too close to call"
        text(surf, view, (CXs, y + 4), 15, GOLD, "midtop", bold=True, max_width=rect.w - 40)
        if self.can_continue:
            text(surf, f"Press SPACE for round {f.round + 1}", (CXs, rect.bottom - 40), 18, WHITE,
                 "midtop", bold=True)

    def _draw_coach(self, surf):
        ai = self.cfg.mode == "ai"
        r = panel(surf, (160, 548, 960, 100) if ai else (20, 548, W - 40, 100), (12, 20, 16), alpha=235,
                  border=GREEN)
        sides = (0,) if ai else (0, 1)
        for i in sides:
            x = r.x + 20 if (ai or i == 0) else CX + 20
            left = self._swaps_left(i)
            who = "COACH" if ai else f"{self.names[i].upper()}'S COACH"
            ideas = "card ideas" if self.coach_cards[i] else "no card changes needed"
            text(surf, f"{who}: {ideas}, {left} change{'s' if left != 1 else ''} left this break",
                 (x, r.y + 12), 15, GREEN, bold=True)
        if self.their_swap:
            text(surf, self.their_swap, (r.right - 20, r.y + 12), 14, (150, 200, 255), "topright")
        for b in self.coach_buttons:
            b.draw(surf)

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


class CornerDeck:
    """Lets the deck builder change a fighter's cards between rounds, a couple at most."""

    money = None

    def __init__(self, scene, i):
        self.scene = scene
        self.i = i
        self.player = scene.fight.profiles[i]
        self.title = "BETWEEN ROUNDS"

    @property
    def hint(self):
        left = self.scene._swaps_left(self.i)
        return f"{left} change{'s' if left != 1 else ''} left this break. Changes last for this fight only."

    def budget(self):
        return self.scene._budget(self.i)

    def _try(self, change):
        from engine.cards import equip, toggle_perk
        before = (dict(self.player.deck), list(self.player.perks))
        err = change(equip, toggle_perk)
        if err:
            return err
        if self.scene._swaps_left(self.i) < 0:
            self.player.deck, self.player.perks = before
            return f"Only {coach.SWAPS_PER_BREAK} changes a break"
        self.scene.fight.refit(self.i, self.player)
        return None

    def equip(self, slot, cid):
        return self._try(lambda equip, _: equip(self.player, slot, cid, self.budget()))

    def toggle_perk(self, pid):
        return self._try(lambda _, toggle: toggle(self.player, pid, self.budget()))

    def save(self):
        self.scene.fight.refit(self.i, self.player)
        self.scene._build_coach_buttons()

    def reset(self):
        start = self.scene.break_start[self.i]
        self.player.deck, self.player.perks = dict(start.deck), list(start.perks)
        self.scene.fight.refit(self.i, self.player)


def _ctrl(n):
    secs = int(n * ROUND_SECONDS / EXCHANGES_PER_ROUND)
    return f"{secs // 60}:{secs % 60:02d}"
