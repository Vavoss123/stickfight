"""The daily challenge: the same fight and the same twist for everyone on a given day.

The date picks your fighter, the opponent and a twist. Your best score for each day is
saved in ~/.stickfight/daily.json, along with how many days in a row you have won.
"""

import copy
import json
import os
import random
from datetime import date, timedelta

from .career import SAVE_DIR

PATH = os.path.join(SAVE_DIR, "daily.json")

# id, name, what it does
TWISTS = [
    ("cut", "Banged up", "You start the fight already cut, with sore legs."),
    ("heavy", "Big problem", "Your opponent comes in at heavyweight."),
    ("notice", "Short notice", "You took the fight on short notice. You start at 60% stamina."),
    ("finish", "Finish them", "Only a knockout, TKO or submission counts as a win."),
    ("five", "Championship rounds", "Five rounds instead of three."),
    ("glass", "Glass jaw", "Your chin is 3 points worse tonight."),
    ("hype", "Fight night", "The crowd is wild. Both of you start with nearly full momentum."),
]


class Challenge:
    def __init__(self, day, me, opp, twist, level="hard"):
        self.day = day
        self.me = me
        self.opp = opp
        self.twist = twist          # (id, name, text)
        self.level = level

    @property
    def rounds(self):
        return 5 if self.twist[0] == "five" else 3

    def start(self):
        """Starting conditions for the Fight: (red, blue)."""
        t = self.twist[0]
        mine, theirs = {}, {}
        if t == "cut":
            mine.update(cut=35.0, legs=30.0)
        if t == "notice":
            mine.update(stamina=60.0)
        if t == "hype":
            mine.update(hype=90.0)
            theirs.update(hype=90.0)
        return mine or None, theirs or None

    def won(self, result):
        if result.winner != 0:
            return False
        return self.twist[0] != "finish" or result.method in ("KO", "TKO", "Submission")

    def score(self, fight):
        """Points for a win: more for a finish, more for finishing early, more for health left."""
        r = fight.result
        if not self.won(r):
            return 0
        s = 1000
        if r.method in ("KO", "TKO", "Submission"):
            s += 500 + (self.rounds - r.round) * 200
        s += int(fight.state.f[0].hp * 5)
        return s


def for_day(day, roster):
    """Today's challenge, the same for anyone with the same roster."""
    rng = random.Random(day.toordinal() * 7919)
    me, opp = rng.sample(range(len(roster)), 2)
    me, opp = copy.deepcopy(roster[me]), copy.deepcopy(roster[opp])
    twist = rng.choice(TWISTS)
    if twist[0] == "heavy":
        opp.weight = "Heavyweight"
        if me.weight == "Heavyweight":
            me.weight = "Middleweight"
    else:
        opp.weight = me.weight
    if twist[0] == "glass":
        me.stats.chin = max(1, me.stats.chin - 3)
    if opp.color == me.color:
        opp.color = tuple(255 - c for c in opp.color)
    return Challenge(day, me, opp, twist)


def today(roster):
    return for_day(date.today(), roster)


def load(path=PATH):
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return {k: int(v) for k, v in data.items()} if isinstance(data, dict) else {}
    except (OSError, ValueError, TypeError):
        return {}


def record(day, score, path=PATH):
    """Keep the best score for the day. Returns the best."""
    data = load(path)
    key = day.isoformat()
    data[key] = max(data.get(key, 0), score)
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=1, sort_keys=True)
        os.replace(tmp, path)
    except OSError:
        pass
    return data[key]


def streak(day, path=PATH):
    """Days in a row with a win, counting back from `day` (or the day before if today
    is not done yet)."""
    data = load(path)
    d = day if data.get(day.isoformat(), 0) > 0 else day - timedelta(days=1)
    n = 0
    while data.get(d.isoformat(), 0) > 0:
        n += 1
        d -= timedelta(days=1)
    return n
