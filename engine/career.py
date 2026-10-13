"""Career mode: climb the rankings, win the belt, defend it.

The ladder is a list of profiles: index 0 is the champion, 1 to 10 are ranked.
The player is in the ladder once they break into the top 10.
"""

import json
import os
import random

from .constants import STAT_NAMES, STAT_MAX
from .fighter import Profile, Stats
from .roster import ARCHETYPES, division, prospect

LADDER_SIZE = 11
SAVE_DIR = os.path.join(os.path.expanduser("~"), ".stickfight")
SAVE_PATH = os.path.join(SAVE_DIR, "career.json")


def new_player(name, nickname, archetype, color, hometown):
    base = {k: v - 1 for k, v in ARCHETYPES[archetype].items()}
    return Profile(name=name, nickname=nickname, archetype=archetype,
                   stats=Stats(**base).clamp(), color=tuple(color), hometown=hometown)


def train_cost(value):
    return 1 if value < 7 else 2


class Career:
    def __init__(self, player, seed=None):
        self.player = player
        self.ladder = division()
        self.points = 0
        self.unranked_wins = 0
        self.defenses = 0
        self.history = []
        self.next_prospect = None
        self.rng = random.Random(seed)

    # Standing

    def rank(self):
        """0 for champion, 1 to 10 for ranked, None for unranked."""
        for i, p in enumerate(self.ladder):
            if p is self.player:
                return i
        return None

    def rank_label(self, i=None):
        r = self.rank() if i is None else i
        if r is None:
            return "Unranked"
        return "Champion" if r == 0 else f"#{r}"

    def is_champ(self):
        return self.rank() == 0

    # Next fight

    def next_fight(self):
        """(opponent, rounds, title, ai_level, label)."""
        r = self.rank()
        if r is None:
            if self.unranked_wins >= 2:
                opp = self.ladder[-1]
                return opp, 3, False, "normal", f"Ranked #{LADDER_SIZE - 1}"
            if self.next_prospect is None:
                self.next_prospect = prospect(self.rng, strength=self.unranked_wins)
            level = "easy" if self.unranked_wins == 0 and not self.history else "normal"
            return self.next_prospect, 3, False, level, "Prospect"
        if r == 0:
            opp = self.ladder[1]
            return opp, 5, True, "hard", "Title defence"
        opp = self.ladder[r - 1]
        title = r - 1 == 0
        level = "hard" if r - 1 <= 5 else "normal"
        label = "Title fight" if title else f"Ranked #{r - 1}"
        return opp, 5 if title else 3, title, level, label

    # Results

    def record_result(self, opp, won, draw, method, detail, round_no):
        p = self.player
        before = self.rank_label()
        if draw:
            p.draws += 1
            opp.draws += 1
            self.points += 1
        elif won:
            p.wins += 1
            opp.losses += 1
            self.points += 2 + (1 if method in ("KO", "TKO", "Submission") else 0)
            self._win_vs(opp)
        else:
            p.losses += 1
            opp.wins += 1
            self.points += 1
            self._loss_vs(opp)
        self.history.append({
            "opponent": opp.name, "result": "Draw" if draw else ("Win" if won else "Loss"),
            "method": method, "detail": detail, "round": round_no,
            "rank_before": before, "rank_after": self.rank_label(),
        })

    def _win_vs(self, opp):
        r = self.rank()
        if opp is self.next_prospect:
            self.next_prospect = None
            self.unranked_wins += 1
            return
        k = self.ladder.index(opp) if opp in self.ladder else None
        if k is None:
            return
        if r == 0:
            self.defenses += 1
            return
        if r is not None and r < k:
            return
        if r is not None:
            self.ladder.remove(self.player)
        self.ladder.insert(k, self.player)
        while len(self.ladder) > LADDER_SIZE:
            self.ladder.pop()

    def _loss_vs(self, opp):
        if opp is self.next_prospect:
            self.next_prospect = None
            return
        r = self.rank()
        if r is None:
            return
        if r == 0:
            # Lose the belt: the challenger becomes champion
            self.defenses = 0
            self.ladder.remove(opp)
            self.ladder.insert(0, opp)
            return
        self.ladder.remove(self.player)
        new = r + 2
        if new < LADDER_SIZE:
            self.ladder.insert(new, self.player)
        else:
            self.unranked_wins = 1
        self.ladder = self.ladder[:LADDER_SIZE]
        while len(self.ladder) < LADDER_SIZE:
            self.ladder.append(prospect(self.rng, strength=1))

    # Training

    def train(self, stat):
        v = self.player.stats.get(stat)
        cost = train_cost(v)
        if v >= STAT_MAX or self.points < cost:
            return False
        setattr(self.player.stats, stat, v + 1)
        self.points -= cost
        return True

    # Saving

    def to_dict(self):
        ladder = []
        for p in self.ladder:
            ladder.append("PLAYER" if p is self.player else p.to_dict())
        return {
            "player": self.player.to_dict(),
            "ladder": ladder,
            "points": self.points,
            "unranked_wins": self.unranked_wins,
            "defenses": self.defenses,
            "history": self.history,
            "next_prospect": self.next_prospect.to_dict() if self.next_prospect else None,
        }

    @classmethod
    def from_dict(cls, d):
        c = cls(Profile.from_dict(d["player"]))
        c.ladder = [c.player if x == "PLAYER" else Profile.from_dict(x) for x in d["ladder"]]
        c.points = d.get("points", 0)
        c.unranked_wins = d.get("unranked_wins", 0)
        c.defenses = d.get("defenses", 0)
        c.history = d.get("history", [])
        np_ = d.get("next_prospect")
        c.next_prospect = Profile.from_dict(np_) if np_ else None
        return c

    def save(self, path=SAVE_PATH):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=1)
        os.replace(tmp, path)

    @classmethod
    def load(cls, path=SAVE_PATH):
        if not os.path.exists(path):
            return None
        try:
            with open(path, encoding="utf-8") as f:
                return cls.from_dict(json.load(f))
        except (OSError, ValueError, KeyError, TypeError):
            return None


def delete_save(path=SAVE_PATH):
    if os.path.exists(path):
        os.remove(path)


__all__ = ["Career", "new_player", "train_cost", "delete_save", "STAT_NAMES"]
