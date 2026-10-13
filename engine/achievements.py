"""Achievements, and the record of what you have done to earn them.

Saved in ~/.stickfight/achievements.json. A few of them unlock secret fighters (see
roster.UNLOCKABLES).
"""

import json
import os
from datetime import date

from .career import SAVE_DIR
from .weights import get as weight_class

PATH = os.path.join(SAVE_DIR, "achievements.json")

# id, name, how to get it
LIST = [
    ("first_win", "First blood", "Win a fight against the computer."),
    ("ko", "Lights out", "Win by knockout."),
    ("sub", "Tap, tap, tap", "Win by submission."),
    ("headkick", "Shin to chin", "Knock someone out with a kick."),
    ("comeback", "Comeback kid", "Win after being knocked down."),
    ("all_in", "All in", "Finish a fight with an all in attack."),
    ("feints", "Mind games", "Freeze your opponent with a feint three times in one fight."),
    ("round1", "Early night", "Finish a fight in the first round."),
    ("flawless", "Flawless", "Win while taking less than 10 damage."),
    ("underdog", "David and Goliath", "Beat a heavier fighter."),
    ("hard", "No easy fights", "Beat the computer on hard."),
    ("ko10", "Knockout artist", "Win 10 fights by knockout."),
    ("tournament", "One night only", "Win a tournament."),
    ("champion", "Champion of the world", "Win the title in career mode."),
    ("dynasty", "Dynasty", "Defend the title three times."),
    ("hall", "Hall of famer", "Get inducted into the hall of fame."),
    ("daily", "Daily grind", "Win a daily challenge."),
    ("streak", "Regular", "Win daily challenges three days in a row."),
]
NAMES = {aid: name for aid, name, _ in LIST}
FINISHES = ("KO", "TKO", "Submission")


class Record:
    def __init__(self, path=PATH):
        self.path = path
        self.unlocked = {}     # id -> date it was earned
        self.counts = {}       # running totals, like knockout wins
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            self.unlocked = {k: v for k, v in data.get("unlocked", {}).items() if k in NAMES}
            self.counts = {k: int(v) for k, v in data.get("counts", {}).items()}
        except (OSError, ValueError, AttributeError, TypeError):
            pass

    def has(self, aid):
        return aid in self.unlocked

    def give(self, aids):
        """Unlock these. Returns the ones that are new, and saves."""
        new = [a for a in dict.fromkeys(aids) if a in NAMES and a not in self.unlocked]
        for a in new:
            self.unlocked[a] = date.today().isoformat()
        if new or aids:
            self.save()
        return new

    def add(self, key, n=1):
        self.counts[key] = self.counts.get(key, 0) + n
        return self.counts[key]

    def save(self):
        try:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            tmp = self.path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump({"unlocked": self.unlocked, "counts": self.counts}, f, indent=1)
            os.replace(tmp, self.path)
        except OSError:
            pass


def for_fight(fight, me=0, level="normal", rec=None):
    """What fighter `me` earned in a finished fight against the computer.
    Updates running totals in rec. Returns achievement ids (new or not)."""
    r = fight.result
    if r is None or r.winner != me:
        return []
    out = ["first_win"]
    if level == "hard":
        out.append("hard")
    if r.method in ("KO", "TKO"):
        out.append("ko")
        if rec is not None and rec.add("ko_wins") >= 10:
            out.append("ko10")
    if r.method == "Submission":
        out.append("sub")
    if r.method in FINISHES and r.round == 1:
        out.append("round1")
    hist = fight.history
    last = hist[-1] if hist else None
    if last is not None and r.method in ("KO", "TKO") and last.moves[me] is not None \
            and last.moves[me].base in ("kick", "legkick", "upkick"):
        out.append("headkick")
    if last is not None and r.method in FINISHES and last.surging[me]:
        out.append("all_in")
    if any(ex.knockdown == me for ex in hist):
        out.append("comeback")
    if sum(1 for ex in hist if ex.feinted[me]) >= 3:
        out.append("feints")
    taken = sum(ex.dmg[1 - me] for ex in hist)
    if taken < 10:
        out.append("flawless")
    mine, theirs = (getattr(p, "weight", None) for p in (fight.profiles[me], fight.profiles[1 - me]))
    if weight_class(theirs)["lbs"] > weight_class(mine)["lbs"]:
        out.append("underdog")
    return out


def for_career(c):
    out = []
    if c.titles_won >= 1:
        out.append("champion")
    if c.most_defenses >= 3:
        out.append("dynasty")
    return out
