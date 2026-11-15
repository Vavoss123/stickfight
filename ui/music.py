"""Music, composed in code like the sound effects, so there are still no audio files to ship.

Five pieces: a menu theme, a walkout, the fight loop at three intensities (it builds as the
rounds go on) and a short sting for a win. Writing them out sample by sample takes a few
seconds in Python, so the first time the game runs they are made on a background thread and
saved under ~/.stickfight/music. After that they load straight from there.

Every loop is a whole number of bars and anything ringing past the end (a pad, a cymbal)
wraps round to the start, so the loops join up without a click.
"""

import math
import os
import random
import threading
import wave
from array import array
from functools import lru_cache

import pygame

RATE = 22050
VERSION = 3          # bump when the music changes, so old cached files are not used
CACHE = os.path.join(os.path.expanduser("~"), ".stickfight", "music")
TWO_PI = 2 * math.pi
FADE_MS = 900
VOLUME = 0.55        # music sits under the punches and the crowd


def hz(note):
    """MIDI note number to frequency."""
    return 440.0 * 2 ** ((note - 69) / 12)


# Instruments: each returns a list of samples. Cached, since a song repeats them a lot

@lru_cache(maxsize=None)
def kick(gain=1.0):
    out, ph = [], 0.0
    for i in range(int(RATE * 0.32)):
        t = i / RATE
        ph += TWO_PI * (44 + 110 * math.exp(-t * 32)) / RATE
        out.append(math.sin(ph) * math.exp(-t * 9) * gain)
    return out


@lru_cache(maxsize=None)
def snare(gain=1.0, seed=1):
    rng = random.Random(seed)
    out, y = [], 0.0
    for i in range(int(RATE * 0.22)):
        t = i / RATE
        y += (rng.uniform(-1, 1) - y) * 0.55
        tone = math.sin(TWO_PI * 185 * t) * math.exp(-t * 32)
        out.append((y * 0.75 * math.exp(-t * 17) + tone * 0.45) * gain)
    return out


@lru_cache(maxsize=None)
def hat(gain=1.0, open_=False, seed=2):
    """High passed noise: the noise minus a smoothed copy of itself."""
    rng = random.Random(seed)
    out, lp = [], 0.0
    decay = 11 if open_ else 70
    for i in range(int(RATE * (0.3 if open_ else 0.06))):
        t = i / RATE
        x = rng.uniform(-1, 1)
        lp += (x - lp) * 0.35
        out.append((x - lp) * math.exp(-t * decay) * gain)
    return out


@lru_cache(maxsize=None)
def crash(gain=1.0, seed=3):
    rng = random.Random(seed)
    out, lp = [], 0.0
    for i in range(int(RATE * 1.6)):
        t = i / RATE
        x = rng.uniform(-1, 1)
        lp += (x - lp) * 0.25
        out.append((x - lp) * math.exp(-t * 2.6) * gain)
    return out


def _env(i, n, attack, release):
    """Linear attack and release, in samples."""
    e = 1.0
    if i < attack:
        e = i / attack
    if i > n - release:
        e = min(e, max(0.0, (n - i) / release))
    return e


@lru_cache(maxsize=None)
def bass(note, dur, gain=1.0, bright=False):
    """A round, slightly buzzy bass: the first few harmonics of a saw."""
    f = hz(note)
    n = int(RATE * dur)
    parts = [(k, (1.0 / k) ** (1.0 if bright else 1.4)) for k in range(1, 7 if bright else 5)]
    norm = sum(a for _, a in parts)
    out = []
    for i in range(n):
        t = i / RATE
        s = sum(a * math.sin(TWO_PI * f * k * t) for k, a in parts) / norm
        out.append(s * _env(i, n, 60, 300) * (0.75 + 0.25 * math.exp(-t * 8)) * gain)
    return out


@lru_cache(maxsize=None)
def pad(notes, dur, gain=1.0):
    """Soft chord: two slightly detuned voices per note, slow in and out."""
    n = int(RATE * dur)
    voices = []
    for note in notes:
        for d in (0.997, 1.003):
            voices.append(hz(note) * d)
    att, rel = int(RATE * min(0.35, dur / 3)), int(RATE * min(0.45, dur / 3))
    out = []
    for i in range(n):
        t = i / RATE
        s = 0.0
        for f in voices:
            p = TWO_PI * f * t
            s += math.sin(p) + math.sin(3 * p) / 9      # a little triangle edge
        out.append(s / len(voices) * _env(i, n, att, rel) * gain)
    return out


@lru_cache(maxsize=None)
def pluck(note, dur, gain=1.0):
    """Short plucked note: bright at the start, the top falls away fast."""
    f = hz(note)
    n = int(RATE * min(dur, 0.6))
    out = []
    for i in range(n):
        t = i / RATE
        s = (math.sin(TWO_PI * f * t) * math.exp(-t * 7)
             + 0.45 * math.sin(TWO_PI * 2 * f * t) * math.exp(-t * 14)
             + 0.25 * math.sin(TWO_PI * 3 * f * t) * math.exp(-t * 22))
        out.append(s * _env(i, n, 30, 200) * gain / 1.4)
    return out


@lru_cache(maxsize=None)
def lead(note, dur, gain=1.0):
    """Hollow square-ish lead with a touch of vibrato once the note settles."""
    f = hz(note)
    n = int(RATE * dur)
    out, ph = [], 0.0
    for i in range(n):
        t = i / RATE
        vib = 1 + 0.005 * math.sin(TWO_PI * 5.5 * t) * min(1.0, max(0.0, t - 0.12) * 5)
        ph += TWO_PI * f * vib / RATE
        s = math.sin(ph) + math.sin(3 * ph) / 3 + math.sin(5 * ph) / 6
        out.append(s / 1.5 * _env(i, n, 200, 900) * gain)
    return out


@lru_cache(maxsize=None)
def chug(note, dur, gain=1.0):
    """A distorted, palm muted power chord: detuned saws into a soft clip. The fight guitar."""
    n = int(RATE * dur)
    out = []
    freqs = [hz(note) * d for d in (0.995, 1.0, 1.005)] + [hz(note + 7)]
    for i in range(n):
        t = i / RATE
        s = 0.0
        for f in freqs:
            s += sum(math.sin(TWO_PI * f * k * t) / k for k in range(1, 7))
        s = math.tanh(s * 0.9)                      # the drive
        out.append(s * math.exp(-t * 9) * _env(i, n, 15, 140) * gain)
    return out


@lru_cache(maxsize=None)
def stab(notes, dur, gain=1.0):
    """Brassy chord hit."""
    n = int(RATE * dur)
    out = []
    for i in range(n):
        t = i / RATE
        s = 0.0
        for note in notes:
            f = hz(note)
            for k in (1, 2, 3, 4):
                s += math.sin(TWO_PI * f * k * t) / k
        out.append(s / (len(notes) * 2.1) * math.exp(-t * 5) * _env(i, n, 80, 600) * gain)
    return out


# Putting a piece together

class Track:
    def __init__(self, bpm, bars, loop=True, tail=0.0):
        self.beat = 60.0 / bpm
        self.loop = loop
        self.n = int(RATE * self.beat * 4 * bars + RATE * tail)
        self.buf = array("d", bytes(8 * self.n))

    def at(self, bar, beat):
        return (bar * 4 + beat) * self.beat

    def add(self, samples, seconds, gain=1.0):
        buf, n = self.buf, self.n
        start = int(seconds * RATE)
        for i, v in enumerate(samples):
            j = start + i
            if j >= n:
                if not self.loop:
                    break
                j %= n          # ring on round the loop point
            buf[j] += v * gain

    def pcm(self, loud=0.16, ceiling=0.92):
        """16 bit samples at a set loudness (RMS), with a soft limiter so peaks never clip."""
        buf = self.buf
        rms = math.sqrt(sum(v * v for v in buf) / max(1, len(buf))) or 1e-6
        k = loud / rms
        tanh = math.tanh
        return array("h", (int(tanh(v * k / ceiling) * ceiling * 32767) for v in buf)).tobytes()


def _drums(tr, bars, kicks, snares, hats, kick_gain=0.9, snare_gain=0.6, hat_gain=0.18, crashes=()):
    for bar in range(bars):
        for b in kicks:
            tr.add(kick(), tr.at(bar, b), kick_gain)
        for b in snares:
            tr.add(snare(), tr.at(bar, b), snare_gain)
        for b in hats:
            tr.add(hat(), tr.at(bar, b), hat_gain)
        if bar in crashes:
            tr.add(crash(), tr.at(bar, 0), 0.32)


# A minor for the menu, E minor for the fight, D minor for the walkout. i, VI, III, VII.
MENU_CHORDS = [((57, 60, 64), 45), ((53, 57, 60), 41), ((52, 55, 60), 48), ((50, 55, 59), 43)]
FIGHT_CHORDS = [((55, 59, 64), 40), ((55, 60, 64), 36), ((55, 59, 62), 43), ((54, 57, 62), 38)]
WALK_CHORDS = [((50, 53, 57), 38), ((50, 53, 57), 38), ((46, 50, 53), 34), ((48, 52, 55), 36)]

MENU_TUNE = [
    [(0, 76, .5), (.5, 74, .5), (1, 72, 1), (2, 69, 1), (3, 72, 1)],
    [(0, 72, .5), (.5, 74, .5), (1, 76, 1.5), (3, 74, 1)],
    [(0, 79, 1), (1, 76, 1), (2, 74, .5), (2.5, 72, .5), (3, 74, 1)],
    [(0, 74, 1.5), (1.5, 71, .5), (2, 67, 2)],
]
# Everything in the fight sits on the eighth note grid: no dotted rhythms, the drive
# comes from straight eighths with accents on the beat.
CHUG_LINE = (0, 0, 3, 0, 5, 3, 0, -2)   # semitones off the bar's root, one chug per eighth
FIGHT_RIFF = [
    [(0, 76, .5), (.5, 76, .5), (1, 79, .5), (1.5, 76, .5), (2, 81, 1), (3, 79, 1)],
    [(0, 72, .5), (.5, 72, .5), (1, 76, .5), (1.5, 72, .5), (2, 79, 2)],
    [(0, 74, .5), (.5, 74, .5), (1, 79, .5), (1.5, 74, .5), (2, 81, 1), (3, 83, 1)],
    [(0, 79, 1), (1, 78, .5), (1.5, 76, .5), (2, 74, 2)],
]
FIGHT_RIFF_END = [(0, 79, .5), (.5, 81, .5), (1, 83, 1), (2, 86, 2)]


def menu():
    bars = 8
    tr = Track(92, bars)
    b = tr.beat
    for bar in range(bars):
        notes, root = MENU_CHORDS[bar % 4]
        tr.add(pad(notes, 4 * b), tr.at(bar, 0), 0.22)
        tr.add(bass(root, 1.5 * b), tr.at(bar, 0), 0.5)
        tr.add(bass(root, 0.75 * b), tr.at(bar, 2), 0.42)
        tr.add(bass(root + 12, 0.5 * b), tr.at(bar, 3.5), 0.32)
        if bar < 4:
            # A gentle arpeggio first time round
            arp = [notes[0] + 12, notes[1] + 12, notes[2] + 12, notes[1] + 12]
            for k in range(8):
                tr.add(pluck(arp[k % 4], 0.5 * b), tr.at(bar, k * 0.5), 0.14)
        else:
            for beat, note, dur in MENU_TUNE[bar - 4]:
                tr.add(pluck(note, dur * b), tr.at(bar, beat), 0.3)
    _drums(tr, bars, kicks=(0, 2), snares=(1, 3), hats=[k * .5 for k in range(8)],
           kick_gain=0.55, snare_gain=0.22, hat_gain=0.1)
    return tr


def fight(level):
    """The fight loop: a driving chug riff on a straight grid, heavier every round.
    1: chugs, kick on every beat, backbeat snare. 2: octave bass, open hats and stabs.
    3: the lead riff over the top, a sixteenth gallop into each bar and crashes."""
    bars = 8
    tr = Track(140, bars)
    b = tr.beat
    for bar in range(bars):
        notes, root = FIGHT_CHORDS[bar % 4]
        # The chug riff: one power chord per eighth, accents on the beat
        for k, off in enumerate(CHUG_LINE):
            if level >= 3 and k == 7:
                # A sixteenth gallop into the next bar
                for g in range(2):
                    tr.add(chug(root + off, 0.2 * b), tr.at(bar, 3.5 + g * 0.25), 0.4)
            else:
                tr.add(chug(root + off, 0.4 * b if k % 2 == 0 else 0.3 * b),
                       tr.at(bar, k * .5), 0.5 if k % 2 == 0 else 0.36)
        if level >= 2:
            for k in range(4):
                tr.add(bass(root + 12, 0.4 * b, bright=True), tr.at(bar, k), 0.3)
            tr.add(stab(tuple(n + 12 for n in notes), 0.5 * b), tr.at(bar, 0), 0.26)
            if bar % 2 == 1:
                tr.add(stab(tuple(n + 12 for n in notes), 0.5 * b), tr.at(bar, 2), 0.2)
        if level >= 3:
            riff = FIGHT_RIFF_END if bar == 7 else FIGHT_RIFF[bar % 4]
            for beat, note, dur in riff:
                tr.add(lead(note, dur * b), tr.at(bar, beat), 0.24)
    hats = [k * .5 for k in range(8)] if level == 1 else [k * .25 for k in range(16)]
    kicks = (0, 1, 2, 3)
    _drums(tr, bars, kicks=kicks, snares=(1, 3), hats=hats,
           kick_gain=0.95, snare_gain=0.55 if level == 1 else 0.68,
           hat_gain=0.13 if level == 1 else 0.1,
           crashes=(0, 4) if level >= 3 else (0,))
    if level >= 2:
        for bar in range(bars):
            tr.add(hat(open_=True), tr.at(bar, 3.5), 0.1)
    return tr


def walkout():
    """Heavy and slow: half time drums, long bass, brass hits."""
    bars = 8
    tr = Track(96, bars)
    b = tr.beat
    for bar in range(bars):
        notes, root = WALK_CHORDS[bar % 4]
        tr.add(bass(root, 3.4 * b, bright=True), tr.at(bar, 0), 0.55)
        tr.add(bass(root + 12, 0.25 * b, bright=True), tr.at(bar, 3.5), 0.35)
        tr.add(bass(root + 12, 0.25 * b, bright=True), tr.at(bar, 3.75), 0.35)
        tr.add(stab(notes, 1.2 * b), tr.at(bar, 0), 0.45)
        tr.add(stab(notes, 0.5 * b), tr.at(bar, 1.5), 0.32)
        tr.add(pad(tuple(n - 12 for n in notes), 4 * b), tr.at(bar, 0), 0.12)
    _drums(tr, bars, kicks=(0, 2.5), snares=(2,), hats=[k * .5 for k in range(8)],
           kick_gain=1.0, snare_gain=0.85, hat_gain=0.12, crashes=(0, 4))
    return tr


def win():
    """A short fanfare for the winner."""
    tr = Track(120, 2, loop=False, tail=1.6)
    b = tr.beat
    for k, note in enumerate((72, 76, 79)):
        tr.add(lead(note, 0.5 * b), k * 0.5 * b, 0.32)
        tr.add(stab((60, 64, 67), 0.4 * b), k * 0.5 * b, 0.2)
    tr.add(lead(84, 3 * b), 1.5 * b, 0.36)
    tr.add(stab((60, 64, 67, 72), 3 * b), 1.5 * b, 0.5)
    tr.add(pad((48, 55, 60, 64), 4 * b), 1.5 * b, 0.25)
    tr.add(kick(), 1.5 * b, 0.9)
    tr.add(crash(), 1.5 * b, 0.4)
    return tr


# How loud each piece sits: the fight builds round by round
LOUDNESS = {"menu": 0.12, "walkout": 0.15, "fight1": 0.15, "fight2": 0.17, "fight3": 0.19, "win": 0.15}
PIECES = {"menu": menu, "walkout": walkout, "fight1": lambda: fight(1), "fight2": lambda: fight(2),
          "fight3": lambda: fight(3), "win": win}
ORDER = ["menu", "fight1", "walkout", "fight2", "fight3", "win"]   # what is needed first


def render(name):
    """The piece as 16 bit mono PCM bytes."""
    return PIECES[name]().pcm(LOUDNESS[name])


def _path(name):
    return os.path.join(CACHE, f"{name}_v{VERSION}.wav")


def _load(name):
    try:
        with wave.open(_path(name), "rb") as w:
            if w.getframerate() != RATE or w.getsampwidth() != 2 or w.getnchannels() != 1:
                return None
            return w.readframes(w.getnframes())
    except (OSError, EOFError, wave.Error):
        return None


def _save(name, pcm):
    try:
        os.makedirs(CACHE, exist_ok=True)
        tmp = _path(name) + ".tmp"
        with wave.open(tmp, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(RATE)
            w.writeframes(pcm)
        os.replace(tmp, _path(name))
    except OSError:
        pass


def fight_level(round_no, rounds):
    """Which fight loop for this round: it builds to the last round."""
    if round_no >= rounds and rounds > 1:
        return 3
    return 1 if round_no <= 1 else 2


class Music:
    """Plays one piece at a time on its own channels, fading between them."""

    def __init__(self, sounds):
        self.sounds = sounds
        self.ok = sounds.ok
        self.ready = {}          # name -> pygame Sound
        self.pending = {}        # name -> pcm bytes made on the worker thread
        self.lock = threading.Lock()
        self.want = None         # the piece that should be playing
        self.playing = None
        self.level = 0.6         # the Music setting, 0 to 1
        self.chans = []
        self.side = 0
        if not self.ok:
            return
        try:
            pygame.mixer.set_reserved(2)
            self.chans = [pygame.mixer.Channel(0), pygame.mixer.Channel(1)]
        except pygame.error:
            self.ok = False
            return
        threading.Thread(target=self._make_all, daemon=True).start()

    def _make_all(self):
        for name in ORDER:
            pcm = _load(name)
            if pcm is None:
                pcm = render(name)
                _save(name, pcm)
            with self.lock:
                self.pending[name] = pcm

    def set_volume(self, master, music):
        self.level = master * music
        for c in self.chans:
            if c.get_busy():
                c.set_volume(VOLUME * self.level)

    def play(self, name):
        """Switch to a piece (it starts as soon as it is ready). None fades out."""
        self.want = name
        self._start()

    def stop(self, fade=FADE_MS):
        self.want = None
        self.playing = None
        for c in self.chans:
            c.fadeout(fade)

    def sting(self, name="win"):
        """Play a one off over silence: stops the loop first."""
        self.stop(300)
        self.want = None
        self._stinger = name
        self._start_sting()

    def _start_sting(self):
        name = getattr(self, "_stinger", None)
        if name and name in self.ready and not self.sounds.muted:
            c = self.chans[self.side]
            c.set_volume(VOLUME * self.level)
            c.play(self.ready[name])
            self._stinger = None

    def _start(self):
        if not self.ok or self.sounds.muted:
            return
        name = self.want
        if name == self.playing:
            return
        if name is None:
            self.stop()
            return
        if name not in self.ready:
            return              # still being made: update() starts it when it lands
        old = self.chans[self.side]
        old.fadeout(FADE_MS)
        self.side = 1 - self.side
        c = self.chans[self.side]
        c.set_volume(VOLUME * self.level)
        c.play(self.ready[name], loops=-1, fade_ms=FADE_MS)
        self.playing = name

    def muted(self, on):
        """Mute stops everything; unmuting picks the piece back up."""
        if on:
            self.playing = None
        else:
            self._start()

    def update(self):
        if not self.ok:
            return
        with self.lock:
            got, self.pending = self.pending, {}
        for name, pcm in got.items():
            try:
                self.ready[name] = pygame.mixer.Sound(buffer=pcm)
            except pygame.error:
                pass
        if got:
            self._start()
            self._start_sting()
