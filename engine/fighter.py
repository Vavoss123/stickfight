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

    def clamp(self, limit=STAT_MAX):
        for n in STAT_NAMES:
            setattr(self, n, max(STAT_MIN, min(limit, self.get(n))))
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
    weight: str = "Welterweight"
    personality: str = ""      # how the computer fights them, see personality.py
    gloves: tuple = None       # glove colour bought in the career shop, None for the corner colour
    deck: dict = field(default_factory=dict)    # basic move key -> card id in that slot
    perks: list = field(default_factory=list)   # equipped perk card ids
    cards: dict = field(default_factory=dict)   # owned card id -> level
    look: dict = field(default_factory=dict)    # skin, hair, beard, shorts stripe, see looks.py

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
        if d.get("gloves"):
            d["gloves"] = tuple(d["gloves"])
        known = cls.__dataclass_fields__
        return cls(**{k: v for k, v in d.items() if k in known})


class FighterState:
    """Mutable per-fight numbers. Kept small so the AI can clone it cheaply."""

    __slots__ = ("profile", "stats", "hp", "stamina", "rocked", "body", "legs", "cut", "kit",
                 "combo", "wc", "hype", "surge", "passive", "opening", "fouls", "arms")

    def __init__(self, profile, hp=MAX_HP, stamina=MAX_STAMINA, rocked=0, body=0.0, legs=0.0,
                 cut=0.0, kit=None, combo=0, hype=0.0, surge=False, passive=0, opening=None,
                 fouls=0, arms=0.0):
        if kit is None:
            from .cards import build_kit
            kit = build_kit(profile)
        self.profile = profile
        self.kit = kit
        self.stats = kit.stats
        self.wc = kit.weight   # weight class numbers, see weights.py
        self.combo = combo  # strikes landed in a row
        self.hp = hp
        self.stamina = stamina
        self.rocked = rocked
        self.body = body    # 0 to 100, body damage slows stamina recovery
        self.legs = legs    # 0 to 100, leg damage saps power and movement
        self.cut = cut      # 0 to 100, blood in the eyes, the doctor may stop it
        self.hype = hype        # 0 to 100, the crowd behind them (see momentum in resolve.py)
        self.surge = surge      # full hype: the next attack goes all in
        self.passive = passive  # defensive picks in a row that did nothing
        self.opening = opening  # "read" or "follow": the next strike is quicker
        self.fouls = fouls      # fouls this fight: the first is a warning, then points go
        self.arms = arms        # 0 to 100, from blocking heavy shots: the guard leaks, punches soften

    def clone(self):
        return FighterState(self.profile, self.hp, self.stamina, self.rocked, self.body, self.legs,
                            self.cut, self.kit, self.combo, self.hype, self.surge, self.passive,
                            self.opening, self.fouls, self.arms)

    def perk(self, pid):
        return self.kit.perk(pid)

    def move(self, key):
        return self.kit.moves[key]

    def mobility(self):
        """1.0 on fresh legs, down to 0.6 when the legs are gone."""
        return 1.0 - self.legs * 0.004

    def stat(self, name):
        return self.stats.get(name)

    def stamina_factor(self):
        """1.0 when fresh, STAMINA_FLOOR when empty."""
        return STAMINA_FLOOR + (1 - STAMINA_FLOOR) * (self.stamina / MAX_STAMINA)

    def cost_of(self, amount):
        """What a cost really takes out of this fighter. Cardio scales both ways."""
        cardio = self.stats.cardio
        if amount > 0:
            return (amount * (1.3 - cardio * 0.06) * STAMINA_COST * (1 - self.kit.perk("ironlungs"))
                    * self.wc["gas"])
        return amount * (0.7 + cardio * 0.06) * (1.0 - self.body / 160)

    def effort(self, move):
        """1.0 when there is gas for the move, down to 0 when the tank is empty.
        A move you cannot pay for still comes out, but slow and weak."""
        cost = self.cost_of(move.cost)
        if cost <= 0 or self.stamina >= cost:
            return 1.0
        return self.stamina / cost

    def spend(self, amount):
        """Positive amount costs stamina, negative recovers it."""
        self.stamina = max(0.0, min(MAX_STAMINA, self.stamina - self.cost_of(amount)))

    def take(self, dmg):
        self.hp = max(0.0, self.hp - dmg)
