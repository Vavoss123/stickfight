"""Custom decks for quick fight and 2 player.

Outside career mode every card is unlocked at level 2 (the level the ready-made
fighters use) and a deck gets a fixed budget. Decks are remembered per fighter in
~/.stickfight/decks.json.
"""

import json
import os

from .cards import CARDS, equip, toggle_perk, validate
from .career import SAVE_DIR

PATH = os.path.join(SAVE_DIR, "decks.json")
BUDGET = 10
LEVEL = 2


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


def apply_saved(profiles, path=PATH):
    """Put each fighter's saved custom deck on them. Broken or outdated decks are skipped."""
    saved = _read(path)
    for p in profiles:
        d = saved.get(p.name)
        if not isinstance(d, dict):
            continue
        old = (dict(p.deck), list(p.perks), dict(p.cards))
        unlock_all(p)
        p.deck = dict(d.get("deck", {}))
        p.perks = list(d.get("perks", []))
        if validate(p, BUDGET):
            p.deck, p.perks, p.cards = old


class Loadout:
    """Gives the deck builder the same calls as a Career, for a quick fight fighter."""

    money = None

    def __init__(self, profile, default, path=PATH):
        self.player = profile
        self.default = (dict(default[0]), list(default[1]))
        self.path = path
        self.title = f"{profile.name.upper()}'S DECK"
        self.hint = f"Every card is unlocked here. Common 1 point, rare 2, legendary 3, {BUDGET} to spend."
        unlock_all(profile)

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
