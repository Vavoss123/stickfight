"""Fighter profiles (who they are) and fighter state (how they are doing in a fight)."""

from dataclasses import dataclass, field, asdict

from .constants import (MAX_HP, MAX_STAMINA, STAT_NAMES, STAT_MAX, STAT_MIN, STAMINA_COST,
                        STAMINA_FLOOR)


@dataclass
class Stats:
    striking: int = 5
    wrestling: int = 5
    grappling: int = 5
    cardio: int = 5
    chin: int = 5

    def get(self, name):
        return getattr(self, name)

    def total(self):
        return sum(self.get(n) for n in STAT_NAMES)

    def clamp(self):
        for n in STAT_NAMES:
            setattr(self, n, max(STAT_MIN, min(STAT_MAX, self.get(n))))
        return self


@dataclass
class Profile:
    name: str
    nickname: str = ""
    archetype: str = "Striker"
    stats: Stats = field(default_factory=Stats)
    color: tuple = (220, 60, 60)
    hometown: str = ""
    wins: int = 0
    losses: int = 0
    draws: int = 0
    height: str = "6'0\""

    def record(self):
        if self.draws:
            return f"{self.wins}-{self.losses}-{self.draws}"
        return f"{self.wins}-{self.losses}"

    def to_dict(self):
        d = asdict(self)
        d["color"] = list(self.color)
        return d

    @classmethod
    def from_dict(cls, d):
        d = dict(d)
        d["stats"] = Stats(**d.get("stats", {}))
        d["color"] = tuple(d.get("color", (220, 60, 60)))
        return cls(**d)


class FighterState:
    """Mutable per-fight numbers. Kept small so the AI can clone it cheaply."""

    __slots__ = ("profile", "stats", "hp", "stamina", "rocked", "body", "legs", "cut")

    def __init__(self, profile, hp=MAX_HP, stamina=MAX_STAMINA, rocked=0, body=0.0, legs=0.0,
                 cut=0.0):
        self.profile = profile
        self.stats = profile.stats
        self.hp = hp
        self.stamina = stamina
        self.rocked = rocked
        self.body = body    # 0 to 100, body damage slows stamina recovery
        self.legs = legs    # 0 to 100, leg damage saps power and movement
        self.cut = cut      # 0 to 100, blood in the eyes, the doctor may stop it

    def clone(self):
        return FighterState(self.profile, self.hp, self.stamina, self.rocked, self.body, self.legs,
                            self.cut)

    def mobility(self):
        """1.0 on fresh legs, down to 0.6 when the legs are gone."""
        return 1.0 - self.legs * 0.004

    def stat(self, name):
        return self.stats.get(name)

    def stamina_factor(self):
        """1.0 when fresh, STAMINA_FLOOR when empty."""
        return STAMINA_FLOOR + (1 - STAMINA_FLOOR) * (self.stamina / MAX_STAMINA)

    def spend(self, amount):
        """Positive amount costs stamina, negative recovers it. Cardio scales both."""
        cardio = self.stats.cardio
        if amount > 0:
            amount *= (1.3 - cardio * 0.06) * STAMINA_COST
        else:
            amount *= (0.7 + cardio * 0.06) * (1.0 - self.body / 160)
        self.stamina = max(0.0, min(MAX_STAMINA, self.stamina - amount))

    def take(self, dmg):
        self.hp = max(0.0, self.hp - dmg)
