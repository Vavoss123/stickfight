"""Every card you have earned in any career, kept after you retire.

Quick fight, 2 player and tournament decks can be built from it instead of from every
card. A card's level here is the best level you ever had it at.
"""

import json
import os

from .cards import CARDS
from .career import SAVE_DIR

PATH = os.path.join(SAVE_DIR, "collection.json")


def load(path=PATH):
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return {}
    if not isinstance(data, dict):
        return {}
    return {cid: int(lv) for cid, lv in data.items() if cid in CARDS and isinstance(lv, int) and lv > 0}


def add(cards, path=PATH):
    """Merge cards (id -> level) into the collection. Returns the new collection."""
    have = load(path)
    changed = False
    for cid, lv in cards.items():
        if cid in CARDS and lv > have.get(cid, 0):
            have[cid] = lv
            changed = True
    if changed:
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            tmp = path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(have, f, indent=1, sort_keys=True)
            os.replace(tmp, path)
        except OSError:
            pass
    return have
