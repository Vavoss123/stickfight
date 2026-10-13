"""Player settings, saved to ~/.stickfight/settings.json so they survive updates."""

import json
import os

PATH = os.path.join(os.path.expanduser("~"), ".stickfight", "settings.json")

# Fight speed: how fast exchanges animate. Slow motion replays slow down from this.
SPEEDS = [("Normal", 1.0), ("Fast", 1.6), ("Fastest", 2.5)]

DEFAULTS = {
    "volume": 80,         # 0 to 100, every sound
    "crowd": 60,          # 0 to 100, the crowd on top of that
    "fullscreen": False,
    "speed": 0,           # index into SPEEDS
    "skip_walkouts": False,
    "card_pool": "all",   # quick fight decks: "all" cards or your "collection"
    "tutorial_done": False,
}


class Settings:
    def __init__(self, path=PATH):
        self.path = path
        self.v = dict(DEFAULTS)
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            for k, d in DEFAULTS.items():
                if isinstance(data.get(k), type(d)):
                    self.v[k] = data[k]
        except (OSError, ValueError, AttributeError):
            pass
        self.v["volume"] = max(0, min(100, self.v["volume"]))
        self.v["crowd"] = max(0, min(100, self.v["crowd"]))
        self.v["speed"] = max(0, min(len(SPEEDS) - 1, self.v["speed"]))

    def __getitem__(self, k):
        return self.v[k]

    def __setitem__(self, k, value):
        self.v[k] = value

    @property
    def fight_speed(self):
        return SPEEDS[self.v["speed"]][1]

    def save(self):
        try:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            tmp = self.path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self.v, f, indent=1)
            os.replace(tmp, self.path)
        except OSError:
            pass
