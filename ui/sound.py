"""Sound effects synthesised at start up, so there are no audio files to ship."""

import math
import random
from array import array

import pygame

RATE = 22050

CROWD = {"crowd", "crowd_loop", "roar", "boo"}
# Every sound starts at full volume except these. Settings scale on top.
BASE_VOLUME = {"crowd": 0.55, "crowd_loop": 0.08, "roar": 0.6, "boo": 0.5, "breath": 0.8}


def _sound(samples):
    data = array("h", (max(-32767, min(32767, int(s * 32767))) for s in samples))
    return pygame.mixer.Sound(buffer=data.tobytes())


def _noise_burst(dur, decay, lowpass, gain, rng):
    n = int(RATE * dur)
    out = []
    y = 0.0
    for i in range(n):
        t = i / RATE
        y += (rng.uniform(-1, 1) - y) * lowpass
        out.append(y * gain * math.exp(-t * decay))
    return out


def _thud(dur, freq, gain, rng, noise=0.4, decay=28, lowpass=0.25):
    n = int(RATE * dur)
    out = []
    y = 0.0
    for i in range(n):
        t = i / RATE
        env = math.exp(-t * decay)
        f = freq * (1 + 2 * math.exp(-t * 40))
        y += (rng.uniform(-1, 1) - y) * lowpass
        out.append((math.sin(2 * math.pi * f * t) * (1 - noise) + y * noise) * env * gain)
    return out


def _bell(dur, rng):
    n = int(RATE * dur)
    parts = [(880, 1.0), (1320, 0.5), (2205, 0.35), (2960, 0.2)]
    out = []
    for i in range(n):
        t = i / RATE
        s = sum(a * math.sin(2 * math.pi * f * t) for f, a in parts)
        out.append(s * 0.22 * math.exp(-t * 2.2))
    return out


def _crowd(dur, rng, swell=True):
    n = int(RATE * dur)
    out = []
    y1 = y2 = 0.0
    for i in range(n):
        t = i / RATE
        y1 += (rng.uniform(-1, 1) - y1) * 0.08
        y2 += (y1 - y2) * 0.3
        env = math.sin(math.pi * t / dur) if swell else 1.0
        out.append(y2 * 1.6 * env)
    return out


def _mix(*parts, at=None):
    """Add sample lists together. at gives each part's start time in seconds."""
    at = at or [0.0] * len(parts)
    n = max(int(RATE * t) + len(p) for p, t in zip(parts, at))
    out = [0.0] * n
    for p, t in zip(parts, at):
        o = int(RATE * t)
        for i, v in enumerate(p):
            out[o + i] += v
    return out


def _tone(dur, freq, gain, decay):
    return [math.sin(2 * math.pi * freq * i / RATE) * gain * math.exp(-i / RATE * decay)
            for i in range(int(RATE * dur))]


def _roar(dur, rng):
    """The crowd jumping out of their seats: fast rise, slow fade."""
    n = int(RATE * dur)
    out = []
    y1 = y2 = y3 = 0.0
    for i in range(n):
        t = i / RATE
        y1 += (rng.uniform(-1, 1) - y1) * 0.12
        y2 += (y1 - y2) * 0.35
        y3 += (rng.uniform(-1, 1) - y3) * 0.4   # a brighter layer for the screams
        env = min(1.0, t / 0.12) * math.exp(-max(0.0, t - 0.4) * 1.6)
        out.append((y2 * 1.7 + y3 * 0.12) * env)
    return out


def _boo(dur, rng):
    """A low, wobbling 'booo' from the crowd."""
    n = int(RATE * dur)
    voices = [(rng.uniform(120, 190), rng.uniform(3, 6), rng.uniform(0, 6)) for _ in range(10)]
    out = []
    y = 0.0
    for i in range(n):
        t = i / RATE
        env = math.sin(math.pi * t / dur) ** 0.7
        v = sum(math.sin(2 * math.pi * f * t + 0.6 * math.sin(2 * math.pi * w * t + ph))
                for f, w, ph in voices) / len(voices)
        y += (rng.uniform(-1, 1) - y) * 0.06
        out.append((v * 0.35 + y * 0.9) * env * 0.6)
    return out


def _breath(rng):
    """Two heavy breaths, in and out."""
    out = []
    y = 0.0
    for k, (dur, gain) in enumerate(((0.45, 0.35), (0.55, 0.45), (0.45, 0.32), (0.6, 0.42))):
        for i in range(int(RATE * dur)):
            t = i / RATE
            y += (rng.uniform(-1, 1) - y) * (0.18 if k % 2 else 0.1)
            out.append(y * gain * math.sin(math.pi * t / dur) ** 2)
    return out


def _squeeze(rng):
    """A creaking, grinding squeeze for a submission getting tighter."""
    n = int(RATE * 0.45)
    out = []
    y = 0.0
    for i in range(n):
        t = i / RATE
        pulse = 1.0 if (t * 38) % 1 < 0.18 else 0.0
        y += (rng.uniform(-1, 1) - y) * 0.2
        env = math.sin(math.pi * t / 0.45)
        out.append((pulse * 0.5 + y * 0.6) * env * 0.5)
    return out


def _rise(dur, rng):
    """A whoosh that gets brighter, for an escape."""
    n = int(RATE * dur)
    out = []
    y = 0.0
    for i in range(n):
        t = i / RATE
        y += (rng.uniform(-1, 1) - y) * (0.05 + 0.5 * t / dur)
        out.append(y * 0.35 * math.sin(math.pi * t / dur))
    return out


class Sounds:
    def __init__(self):
        self.ok = False
        self.s = {}
        self.muted = False
        self.ambient_on = False
        self.master = self.crowd_level = 1.0
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(RATE, -16, 1, 512)
            rng = random.Random(7)
            self.s["jab"] = _sound(_thud(0.12, 140, 0.55, rng))
            self.s["punch"] = _sound(_thud(0.22, 90, 0.9, rng, noise=0.5))
            self.s["block"] = _sound(_noise_burst(0.08, 50, 0.6, 0.5, rng))
            self.s["whoosh"] = _sound(_noise_burst(0.18, 14, 0.35, 0.18, rng))
            self.s["slam"] = _sound(_thud(0.35, 55, 1.0, rng, noise=0.6))
            self.s["bell"] = _sound(_bell(1.6, rng))
            self.s["crowd"] = _sound(_crowd(2.2, rng))
            self.s["crowd_loop"] = _sound(_crowd(3.0, rng, swell=False))
            self.s["click"] = _sound(_noise_burst(0.03, 120, 0.9, 0.25, rng))
            # Kicks: a slap on top of a deeper thud
            self.s["kick"] = _sound(_mix(_noise_burst(0.05, 70, 0.8, 0.6, rng),
                                         _thud(0.24, 70, 0.8, rng, noise=0.35, decay=20)))
            self.s["body"] = _sound(_thud(0.2, 60, 0.95, rng, noise=0.65, decay=24, lowpass=0.08))
            self.s["boom"] = _sound(_thud(0.7, 38, 1.0, rng, noise=0.5, decay=7, lowpass=0.12))
            self.s["roar"] = _sound(_roar(3.0, rng))
            self.s["boo"] = _sound(_boo(1.6, rng))
            self.s["breath"] = _sound(_breath(rng))
            self.s["squeeze"] = _sound(_squeeze(rng))
            slap = _noise_burst(0.05, 80, 0.7, 0.55, rng)
            self.s["tap"] = _sound(_mix(slap, slap, slap, at=[0.0, 0.14, 0.28]))
            self.s["escape"] = _sound(_rise(0.4, rng))
            flick = _noise_burst(0.04, 90, 0.5, 0.35, rng)
            self.s["flip"] = _sound(_mix(flick, flick, at=[0.0, 0.07]))
            self.s["cash"] = _sound(_mix(_tone(0.5, 2093, 0.25, 9), _tone(0.5, 2637, 0.22, 9),
                                         at=[0.0, 0.07]))
            notes = [_tone(0.3, f, 0.3, 10) for f in (523, 659, 784, 1047)]
            self.s["levelup"] = _sound(_mix(*notes, at=[0.0, 0.08, 0.16, 0.24]))
            self.ok = True
            for name in self.s:
                BASE_VOLUME.setdefault(name, 1.0)
            self.set_volume(1.0, 1.0)
        except Exception:
            self.ok = False

    def set_volume(self, master, crowd):
        """master and crowd are 0 to 1."""
        self.master = master
        self.crowd_level = crowd
        if not self.ok:
            return
        for name, base in BASE_VOLUME.items():
            level = master * (crowd if name in CROWD else 1.0)
            self.s[name].set_volume(base * level)

    def play(self, name, volume=1.0):
        if not self.ok or self.muted or name not in self.s:
            return
        ch = self.s[name].play()
        if ch:
            ch.set_volume(volume)

    def ambience(self, on=True):
        if not self.ok:
            return
        if on and not self.muted:
            if not self.ambient_on:
                self.s["crowd_loop"].play(loops=-1)
            self.ambient_on = True
        else:
            self.s["crowd_loop"].stop()
            self.ambient_on = False

    def toggle_mute(self):
        self.muted = not self.muted
        if self.muted:
            pygame.mixer.stop()
            self.ambient_on = False
        return self.muted
