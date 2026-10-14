"""Custom decks for quick fight, 2 player and tournaments.

Two card pools:
    all         every card unlocked at level 2, the level the ready-made fighters use
    collection  the cards you have earned in your careers (see collection.py)
Either way a fighter keeps their own signature cards, and a deck gets a fixed budget.
Decks are remembered per fighter in ~/.stickfight/decks.json.
"""

import json
import os

from . import collection
from .cards import CARDS, equip, toggle_perk, validate
from .career import SAVE_DIR

PATH = os.path.join(SAVE_DIR, "decks.json")
BUDGET = 10
LEVEL = 2
POOLS = ("all", "collection")


def own_cards(profile):
    """The cards a fighter brings themselves: whatever is in their deck."""
    ids = list((profile.deck or {}).values()) + list(profile.perks or [])
    return {cid: profile.cards.get(cid, LEVEL) for cid in ids if cid in CARDS}


def pool_cards(own, pool, collection_path=collection.PATH):
    """Every card a fighter can use with this pool, with its level."""
    out = dict(own)
    extra = {cid: LEVEL for cid in CARDS} if pool == "all" else collection.load(collection_path)
    for cid, lv in extra.items():
        out[cid] = max(out.get(cid, 0), lv)
    return out


def unlock_all(profile, level=LEVEL):
    for cid in CARDS:
        profile.cards[cid] = max(profile.cards.get(cid, 0), level)


def _read(path=PATH):
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def _write(data, path=PATH):
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=1)
        os.replace(tmp, path)
    except OSError:
        pass  # a deck that does not save is not worth crashing over


def apply_saved(profiles, path=PATH, pool="all", collection_path=collection.PATH):
    """Put each fighter's saved custom deck on them. Decks that are broken, or use cards
    the pool does not have, are skipped."""
    saved = _read(path)
    for p in profiles:
        d = saved.get(p.name)
        if not isinstance(d, dict):
            continue
        old = (dict(p.deck), list(p.perks), dict(p.cards))
        p.cards = pool_cards(own_cards(p), pool, collection_path)
        p.deck = dict(d.get("deck", {}))
        p.perks = list(d.get("perks", []))
        if validate(p, BUDGET):
            p.deck, p.perks, p.cards = old


class Loadout:
    """Gives the deck builder the same calls as a Career, for a quick fight fighter."""

    money = None

    def __init__(self, profile, default, path=PATH, pool="all", collection_path=collection.PATH):
        """default: the fighter's own (deck, perks), as they come in the roster."""
        self.player = profile
        self.default = (dict(default[0]), list(default[1]))
        self.own = {cid: profile.cards.get(cid, LEVEL)
                    for cid in list(self.default[0].values()) + self.default[1] if cid in CARDS}
        self.path = path
        self.collection_path = collection_path
        self.title = f"{profile.name.upper()}'S DECK"
        self.set_pool(pool)

    def set_pool(self, pool):
        """Switch card pools. Cards the new pool does not have come out of the deck."""
        self.pool = pool if pool in POOLS else "all"
        p = self.player
        p.cards = pool_cards(self.own, self.pool, self.collection_path)
        p.deck = {slot: cid for slot, cid in p.deck.items() if cid in p.cards}
        p.perks = [pid for pid in p.perks if pid in p.cards]
        if self.pool == "all":
            self.hint = f"Every card unlocked. Cards cost 1 to 3 points by how strong they are, {BUDGET} to spend."
        else:
            n = len(collection.load(self.collection_path))
            self.hint = (f"Your collection: {n} card{'s' if n != 1 else ''} from your careers, plus "
                         f"this fighter's own. {BUDGET} points to spend.")

    def budget(self):
        return BUDGET

    def equip(self, slot, cid):
        return equip(self.player, slot, cid, BUDGET)

    def toggle_perk(self, pid):
        return toggle_perk(self.player, pid, BUDGET)

    def save(self):
        data = _read(self.path)
        p = self.player
        data[p.name] = {"deck": dict(p.deck), "perks": list(p.perks)}
        _write(data, self.path)

    def reset(self):
        """Back to the fighter's own deck."""
        self.player.deck, self.player.perks = dict(self.default[0]), list(self.default[1])
        data = _read(self.path)
        data.pop(self.player.name, None)
        _write(data, self.path)
