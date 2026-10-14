"""Retirement and the hall of fame.

When a career ends it is written to ~/.stickfight/hall_of_fame.json with a legacy
score. Champions and long careers get inducted; everyone else is still remembered.
"""

import json
import os
from datetime import date

from .career import SAVE_DIR

PATH = os.path.join(SAVE_DIR, "hall_of_fame.json")
INDUCT_SCORE = 60


def legacy_score(c):
    """How the career will be remembered. Belts count most, then finishes and wins."""
    p = c.player
    finishes = sum(1 for h in c.history
                   if h["result"] == "Win" and h["method"] in ("KO", "TKO", "Submission"))
    best = c.best_rank
    ranked = 0 if best is None else (11 - best) * 2
    return (p.wins * 3 + finishes * 2 + c.titles_won * 25 + c.most_defenses * 10
            + ranked - p.losses * 2)


def entry_for(c):
    p = c.player
    score = legacy_score(c)
    finishes = sum(1 for h in c.history
                   if h["result"] == "Win" and h["method"] in ("KO", "TKO", "Submission"))
    return {
        "name": p.name, "nickname": p.nickname, "archetype": p.archetype,
        "color": list(p.color), "look": dict(p.look), "record": p.record(), "wins": p.wins,
        "losses": p.losses,
        "finishes": finishes, "titles": c.titles_won, "defenses": c.most_defenses,
        "best_rank": c.best_rank, "score": score, "inducted": c.titles_won > 0 or score >= INDUCT_SCORE,
        "retired": date.today().isoformat(),
    }


def load(path=PATH):
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return [e for e in data if isinstance(e, dict) and "name" in e]
    except (OSError, ValueError, TypeError):
        return []


def retire(c, path=PATH):
    """Add the career to the hall of fame. Returns its entry. The caller deletes the save."""
    e = entry_for(c)
    hall = load(path)
    hall.append(e)
    hall.sort(key=lambda x: -x.get("score", 0))
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(hall, f, indent=1)
        os.replace(tmp, path)
    except OSError:
        pass
    return e


def best_rank_label(r):
    if r is None:
        return "Unranked"
    return "Champion" if r == 0 else f"#{r}"
