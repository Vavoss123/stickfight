"""Stick figure skeleton: forward kinematics, pose blending and drawing."""

import math

import pygame

from engine.looks import look_of, colors

from .poses import POSES, BONES, LEN


def _ease(t):
    return t * t * (3 - 2 * t)


def _lerp_angle(a, b, t):
    d = (b - a + 180) % 360 - 180
    return a + d * t


def _vec(angle, length):
    r = math.radians(angle)
    return math.cos(r) * length, math.sin(r) * length


def concrete(name_or_pose):
    """Turn a pose (or pose name) into numbers with a fixed hip offset."""
    p = POSES[name_or_pose] if isinstance(name_or_pose, str) else name_or_pose
    hx, hy = p["hip"]
    if p.get("ground", True):
        feet = []
        for th, sh in (("fth", "fsh"), ("bth", "bsh")):
            feet.append(_vec(p[th], LEN["th"])[1] + _vec(p[sh], LEN["sh"])[1])
        hy = -max(feet)
    out = {"hx": hx, "hy": hy}
    for b in BONES:
        out[b] = p[b]
    return out


def blend(a, b, t):
    out = {"hx": a["hx"] + (b["hx"] - a["hx"]) * t, "hy": a["hy"] + (b["hy"] - a["hy"]) * t}
    for k in BONES:
        out[k] = _lerp_angle(a[k], b[k], t)
    return out


def joints(pose, x, y, facing, scale=1.0):
    """Screen positions of every joint."""
    def ang(a):
        return a if facing > 0 else 180 - a

    def step(origin, angle, length):
        dx, dy = _vec(ang(angle), length * scale)
        return origin[0] + dx, origin[1] + dy

    hip = (x + pose["hx"] * facing * scale, y + pose["hy"] * scale)
    neck = step(hip, pose["torso"], LEN["torso"])
    shoulder = step(hip, pose["torso"], LEN["torso"] - 5)
    head = step(neck, pose["head"], LEN["neck"] + LEN["head_r"])
    j = {"hip": hip, "neck": neck, "shoulder": shoulder, "head": head}
    j["felbow"] = step(shoulder, pose["fua"], LEN["ua"])
    j["fhand"] = step(j["felbow"], pose["ffa"], LEN["fa"])
    j["belbow"] = step(shoulder, pose["bua"], LEN["ua"])
    j["bhand"] = step(j["belbow"], pose["bfa"], LEN["fa"])
    j["fknee"] = step(hip, pose["fth"], LEN["th"])
    j["ffoot"] = step(j["fknee"], pose["fsh"], LEN["sh"])
    j["bknee"] = step(hip, pose["bth"], LEN["th"])
    j["bfoot"] = step(j["bknee"], pose["bsh"], LEN["sh"])
    return j


def _shade(c, f):
    return tuple(max(0, min(255, int(v * f))) for v in c)


def _line(surf, color, a, b, w):
    pygame.draw.line(surf, color, a, b, w)
    pygame.draw.circle(surf, color, a, w // 2)
    pygame.draw.circle(surf, color, b, w // 2)


class Figure:
    def __init__(self, x, y, facing, shorts, glove=(200, 30, 30), body=(235, 232, 225),
                 scale=1.0):
        self.x, self.y = x, y
        self.facing = facing
        self.shorts = shorts
        self.glove = glove
        self.body = body
        self.scale = scale
        self.cur = concrete("stance")
        self.src = self.cur
        self.dst = self.cur
        self.t = 1.0
        self.dur = 0.0
        self.queue = []
        self.idle = "stance"
        self.idle_clock = 0.0
        self.move_src = (x, y)
        self.move_dst = (x, y)
        self.move_t = 1.0
        self.move_dur = 0.0
        self.flash = 0.0
        self.shake = 0.0
        self.visible = True
        self.cut = 0.0
        self.hair = "bald"
        self.hair_color = (34, 28, 26)
        self.beard = False
        self.trim = None
        self.tattoo = "none"

    def dress(self, profile=None, look=None):
        """Wear a fighter's shorts colour and look. A look dict can be passed straight in."""
        if profile is not None:
            self.shorts = tuple(profile.color)
            look = look or look_of(profile)
        if look:
            self.body, self.hair_color, self.trim = colors(look)
            self.hair = look["hair"]
            self.beard = look["beard"]
            self.tattoo = look.get("tattoo", "none")
        return self

    # Control

    @property
    def busy(self):
        return bool(self.queue) or self.t < 1.0 or self.move_t < 1.0

    def play(self, seq, idle=None, clear=True):
        """seq: list of (pose_name, seconds). The figure settles into idle afterwards."""
        if clear:
            self.queue = []
        self.queue.extend(seq)
        if idle:
            self.idle = idle
        if self.t >= 1.0:
            self._next()

    def set_pose(self, name, idle=None):
        self.cur = self.src = self.dst = concrete(name)
        self.t = 1.0
        self.queue = []
        if idle:
            self.idle = idle

    def move_to(self, x, y=None, dur=0.4):
        self.move_src = (self.x, self.y)
        self.move_dst = (x, self.y if y is None else y)
        self.move_t = 0.0 if dur > 0 else 1.0
        self.move_dur = dur
        if dur <= 0:
            self.x, self.y = self.move_dst

    def place(self, x, y=None):
        self.move_to(x, y, 0)

    def hit(self, power=1.0):
        self.flash = 0.18
        self.shake = 6 * power

    def _next(self):
        if self.queue:
            name, dur = self.queue.pop(0)
            self.src = self.cur
            self.dst = concrete(name)
            self.dur = max(0.01, dur)
            self.t = 0.0

    # Frame

    def update(self, dt):
        if self.t < 1.0:
            self.t = min(1.0, self.t + dt / self.dur)
            self.cur = blend(self.src, self.dst, _ease(self.t))
            if self.t >= 1.0:
                self._next()
        elif not self.queue:
            # Idle: drift between the idle pose and its breathing variant
            self.idle_clock += dt
            base = concrete(self.idle)
            alt_name = self.idle + "_b" if self.idle + "_b" in POSES else None
            if alt_name:
                k = (math.sin(self.idle_clock * 3.0) + 1) / 2
                target = blend(base, concrete(alt_name), k)
            else:
                target = dict(base)
                target["hy"] += math.sin(self.idle_clock * 3.0) * 1.2
            self.cur = blend(self.cur, target, min(1.0, dt * 8))
        if self.move_t < 1.0:
            self.move_t = min(1.0, self.move_t + dt / self.move_dur)
            e = _ease(self.move_t)
            self.x = self.move_src[0] + (self.move_dst[0] - self.move_src[0]) * e
            self.y = self.move_src[1] + (self.move_dst[1] - self.move_src[1]) * e
        self.flash = max(0.0, self.flash - dt)
        self.shake = max(0.0, self.shake - dt * 30)

    def _blood(self, surf, j):
        """A gash over the eye and a trickle down the face, worse as the cut opens up."""
        hx, hy = j["head"]
        r = LEN["head_r"] * self.scale
        sev = min(1.0, self.cut / 100)
        ex = hx + self.facing * r * 0.45
        ey = hy - r * 0.35
        red = (170, 20, 20)
        pygame.draw.circle(surf, red, (ex, ey), max(2, int(2 + 4 * sev)))
        drip = r * (0.6 + 1.6 * sev)
        pygame.draw.line(surf, red, (ex, ey), (ex + self.facing * 2, ey + drip), max(2, int(2 + 3 * sev)))
        if sev > 0.5:
            pygame.draw.circle(surf, red, (ex - self.facing * 4, ey + drip * 0.6), 3)

    def _ink(self, surf, body, a, b, w, bands=(0.3, 0.55, 0.8)):
        """Tattoo bands across a limb from a to b."""
        ink = tuple(int(c * 0.35 + d * 0.65) for c, d in zip(body, (24, 30, 52)))
        (ax, ay), (bx, by) = a, b
        d = math.hypot(bx - ax, by - ay) or 1
        nx, ny = -(by - ay) / d * w * 0.6, (bx - ax) / d * w * 0.6
        for t in bands:
            px, py = ax + (bx - ax) * t, ay + (by - ay) * t
            pygame.draw.line(surf, ink, (px - nx, py - ny), (px + nx, py + ny), max(1, w // 3))

    def _inked(self, part):
        t = self.tattoo
        return (t == "full" or (part == "farm" and t in ("sleeve", "sleeves")) or
                (part == "barm" and t == "sleeves") or (part == t))

    def _head_frame(self, j):
        """Centre, radius, 'up' out of the top of the head and 'forward' out of the face."""
        (nx, ny), (hx, hy) = j["neck"], j["head"]
        d = math.hypot(hx - nx, hy - ny) or 1
        up = ((hx - nx) / d, (hy - ny) / d)
        fwd = (-up[1] * self.facing, up[0] * self.facing)
        return (hx, hy), LEN["head_r"] * self.scale, up, fwd

    @staticmethod
    def _at(c, r, up, fwd, deg, k):
        """A point k head radii out from the centre, deg degrees from straight up towards the face."""
        a = math.radians(deg)
        return (c[0] + r * k * (up[0] * math.cos(a) + fwd[0] * math.sin(a)),
                c[1] + r * k * (up[1] * math.cos(a) + fwd[1] * math.sin(a)))

    def _arc(self, surf, col, frame, a0, a1, outer, inner):
        """A thick crescent round the head, used for hair caps and beards."""
        c, r, up, fwd = frame
        steps = 8
        out = [self._at(c, r, up, fwd, a0 + (a1 - a0) * t / steps, outer) for t in range(steps + 1)]
        ins = [self._at(c, r, up, fwd, a1 - (a1 - a0) * t / steps, inner) for t in range(steps + 1)]
        pygame.draw.polygon(surf, col, out + ins)

    def _hair_back(self, surf, frame):
        """Hair that sits behind the head."""
        c, r, up, fwd = frame
        col = _shade(self.hair_color, 0.85)
        if self.hair == "afro":
            pygame.draw.circle(surf, self.hair_color, self._at(c, r, up, fwd, -30, 0.35), int(r * 1.5))
        elif self.hair == "long":
            _line(surf, col, self._at(c, r, up, fwd, -90, 0.5), self._at(c, r, up, fwd, -150, 1.8),
                  max(3, int(r * 1.1)))
        elif self.hair == "ponytail":
            _line(surf, col, self._at(c, r, up, fwd, -100, 0.9), self._at(c, r, up, fwd, -125, 2.1),
                  max(2, int(r * 0.5)))

    def _hair_front(self, surf, frame):
        """Hair over the top of the head, and the beard."""
        c, r, up, fwd = frame
        h = self.hair
        if h == "buzz":
            self._arc(surf, self.hair_color, frame, -105, 45, 1.06, 0.78)
        elif h in ("short", "topknot", "ponytail", "long"):
            self._arc(surf, self.hair_color, frame, -115, 45, 1.14, 0.66)
        elif h == "afro":
            self._arc(surf, self.hair_color, frame, -100, 45, 1.1, 0.55)
        elif h == "mohawk":
            for deg in range(-60, 31, 15):
                _line(surf, self.hair_color, self._at(c, r, up, fwd, deg, 0.8),
                      self._at(c, r, up, fwd, deg, 1.7), max(2, int(r * 0.4)))
        if h == "topknot":
            pygame.draw.circle(surf, self.hair_color, self._at(c, r, up, fwd, -35, 1.35), max(2, int(r * 0.48)))
        if self.beard:
            self._arc(surf, self.hair_color, frame, 100, 200, 1.08, 0.66)

    def draw(self, surf):
        if not self.visible:
            return
        sx = math.sin(pygame.time.get_ticks() * 0.09) * self.shake
        j = joints(self.cur, self.x + sx, self.y, self.facing, self.scale)
        body = (255, 120, 120) if self.flash > 0 else self.body
        back = _shade(body, 0.7)
        w = max(3, int(7 * self.scale))
        # Shadow on the mat
        shadow = pygame.Surface((90, 14), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 90), shadow.get_rect())
        surf.blit(shadow, (j["hip"][0] - 45, self.y - 6))
        # Back limbs first
        _line(surf, back, j["hip"], j["bknee"], w)
        _line(surf, back, j["bknee"], j["bfoot"], w)
        _line(surf, back, j["shoulder"], j["belbow"], w)
        _line(surf, back, j["belbow"], j["bhand"], w)
        if self._inked("barm"):
            self._ink(surf, back, j["shoulder"], j["belbow"], w)
            self._ink(surf, back, j["belbow"], j["bhand"], w, (0.4,))
        if self._inked("legs"):
            self._ink(surf, back, j["bknee"], j["bfoot"], w)
        pygame.draw.circle(surf, _shade(self.glove, 0.75), j["bhand"], int(7 * self.scale))
        # Shorts over the top of the back thigh
        mid_b = ((j["hip"][0] * 0.45 + j["bknee"][0] * 0.55), (j["hip"][1] * 0.45 + j["bknee"][1] * 0.55))
        _line(surf, _shade(self.shorts, 0.75), j["hip"], mid_b, w + 5)
        if self.trim:
            _line(surf, _shade(self.trim, 0.75), j["hip"], mid_b, max(1, w // 3))
        # Torso and head
        _line(surf, body, j["hip"], j["neck"], w + 1)
        if self._inked("chest"):
            self._ink(surf, body, j["hip"], j["neck"], w + 1, (0.6, 0.72, 0.84))
        _line(surf, body, j["neck"], j["head"], w - 1)
        frame = self._head_frame(j)
        self._hair_back(surf, frame)
        pygame.draw.circle(surf, body, j["head"], int(LEN["head_r"] * self.scale))
        self._hair_front(surf, frame)
        if self.cut > 0:
            self._blood(surf, j)
        # Front limbs
        _line(surf, body, j["hip"], j["fknee"], w)
        _line(surf, body, j["fknee"], j["ffoot"], w)
        if self._inked("legs"):
            self._ink(surf, body, j["fknee"], j["ffoot"], w)
        mid_f = ((j["hip"][0] * 0.45 + j["fknee"][0] * 0.55), (j["hip"][1] * 0.45 + j["fknee"][1] * 0.55))
        _line(surf, self.shorts, j["hip"], mid_f, w + 5)
        pygame.draw.circle(surf, self.shorts, j["hip"], (w + 5) // 2 + 1)
        if self.trim:
            _line(surf, self.trim, j["hip"], mid_f, max(1, w // 3))
        _line(surf, body, j["shoulder"], j["felbow"], w)
        _line(surf, body, j["felbow"], j["fhand"], w)
        if self._inked("farm"):
            self._ink(surf, body, j["shoulder"], j["felbow"], w)
            self._ink(surf, body, j["felbow"], j["fhand"], w, (0.4,))
        pygame.draw.circle(surf, self.glove, j["fhand"], int(7 * self.scale))
        return j
