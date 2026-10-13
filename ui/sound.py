"""Sound effects synthesised at start up, so there are no audio files to ship."""

import math
import random
from array import array

import pygame

RATE = 22050


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


def _thud(dur, freq, gain, rng, noise=0.4):
    n = int(RATE * dur)
    out = []
    y = 0.0
    for i in range(n):
        t = i / RATE
        env = math.exp(-t * 28)
        f = freq * (1 + 2 * math.exp(-t * 40))
        y += (rng.uniform(-1, 1) - y) * 0.25
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


class Sounds:
    def __init__(self):
        self.ok = False
        self.s = {}
        self.muted = False
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
            self.s["crowd"].set_volume(0.55)
            self.s["crowd_loop"].set_volume(0.08)
            self.ok = True
        except Exception:
            self.ok = False

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
            self.s["crowd_loop"].play(loops=-1)
        else:
            self.s["crowd_loop"].stop()

    def toggle_mute(self):
        self.muted = not self.muted
        if self.muted:
            pygame.mixer.stop()
        return self.muted
