"""Fight cards.

Every fighter has a deck. Move cards are signature versions of the basic moves and take
that move's slot (Superman Punch takes the Power punch slot). Some take the slot of a
different kind of move, like Guard Pull in the Body shot slot, so a grappler can trade
strikes they do not need for more ways to get it to the mat. Perk cards change how a
fighter fights. Cards come in three rarities and level up from 1 to 3 when you get a
duplicate. A deck has a point budget, so you cannot equip everything you own.
"""

from dataclasses import dataclass, replace

from .constants import (STANDING, CLINCH, GUARD, MOUNT, BACK, NEUTRAL, TOP, BOTTOM,
                        STRIKE, GRAPPLE, SUB, DEFEND, HEAD, BODY, LEGS, STAT_NAMES, STAT_LIMIT, STAT_MIN)
from .moves import Move, MOVES, MOVESETS

COMMON, RARE, LEGENDARY = "common", "rare", "legendary"
DECK_COST = {COMMON: 1, RARE: 2, LEGENDARY: 3}
# Deck points for cards that are stronger or weaker than their rarity says. From
# tools/cardsim.py: a card that wins well over half its mirror matches costs more.
POINTS = {
    "ironlungs": 3,                                          # 60%
    "base": 2, "secondwind": 2, "heavyhands": 2, "gastank": 2,   # 54 to 56% for a common
    "imanari": 2, "twister": 2, "showtime": 2, "gogo": 2,    # legendaries that only win about half
    "flyknee": 1, "granite": 1, "killer": 1, "spinelbow": 1, "plum": 1, "butterfly": 1,
}
PRICE = {COMMON: 5000, RARE: 12000, LEGENDARY: 30000}
MAX_LEVEL = 5
MAX_PERKS = 3


@dataclass(frozen=True)
class Card:
    id: str
    name: str
    rarity: str
    desc: str
    move: Move = None           # move cards
    perk: tuple = None          # perk cards: effect strength at level 1, 2, 3

    @property
    def is_perk(self):
        return self.perk is not None

    @property
    def points(self):
        """What it costs to put in a deck."""
        return POINTS.get(self.id, DECK_COST[self.rarity])


def _m(key, name, base, cls, stat, cost, **kw):
    return Move(key, name, cls, stat, cost, base=base, **kw)


_MOVE_CARDS = [
    # Standing
    (RARE, _m("superman", "Superman Punch", "cross", STRIKE, "striking", 12, dmg=10, acc=0.55,
              power=True, speed=2, cuts=0.06, anim="cross",
              desc="A power punch as fast as a jab. Harder to land."),
     "Leaps in behind a power shot. Wins the race against jabs."),
    (RARE, _m("spinfist", "Spinning Back Fist", "cross", STRIKE, "striking", 13, dmg=12, acc=0.55,
              power=True, cuts=0.06, anim="cross", beats=("block",),
              desc="Spins around a high guard. Costly and harder to land."),
     "Spins around a high guard. Costly and harder to land."),
    (LEGENDARY, _m("showtime", "Showtime Kick", "kick", STRIKE, "striking", 8, dmg=15, acc=0.62,
                   power=True, speed=0, cuts=0.08, ko=1.3, anim="kick", beats=("takedown", "clinch"),
                   desc="Off the fence, over their shot or their clinch. Huge knockout power."),
     "Off the fence, over their shot or their clinch. Huge knockout power."),
    (RARE, _m("flyknee", "Flying Knee", "kick", STRIKE, "striking", 12, dmg=14, acc=0.64,
              power=True, speed=1, cuts=0.08, catch=1.8, anim="kick", loses_to=(),
              beats=("takedown",),
              desc="Catches them shooting in. Costs a lot of gas."),
     "Catches them shooting in. Costs a lot of gas."),
    (RARE, _m("calfkick", "Calf Kick", "legkick", STRIKE, "striking", 6, dmg=5.5, acc=0.8, speed=2,
              target=LEGS, limb=1.8, anim="legkick",
              desc="Chops the calf. Nearly double the leg damage."),
     "Chops the calf. Nearly double the leg damage."),
    (COMMON, _m("liver", "Liver Hook", "body", STRIKE, "striking", 7, dmg=7.5, acc=0.74,
                target=BODY, limb=1.4, anim="body",
                desc="Right on the liver. More drain, more chance to fold them."),
     "Right on the liver. More drain, more chance to fold them."),
    (COMMON, _m("checkhook", "Check Hook", "block", DEFEND, "striking", -4, counter=0.25,
                anim="block",
                desc="Pivot and counter. Better counters, less rest."),
     "Pivot and counter. Better counters, less rest."),
    (RARE, _m("doubleleg", "Double Leg Blast", "takedown", GRAPPLE, "wrestling", 14,
              to="guard_top", bonus=0.06, slam=5, anim="takedown",
              desc="Explosive shot that slams them down."),
     "Explosive shot that slams them down."),
    (LEGENDARY, _m("imanari", "Imanari Roll", "clinch", SUB, "grappling", 15, anim="imanari",
                   sub_fail="bottom",
                   desc="Roll straight into a heel hook. If it fails you are on your back."),
     "Roll straight into a heel hook. If it fails you are on your back."),
    # Grappling cards that take a strike's slot. They play like the move named as base.
    (COMMON, _m("guardpull", "Guard Pull", "clinch", GRAPPLE, "grappling", 4, slot="body",
                to="guard_bottom", bonus=0.1, anim="clinch",
                desc="Pull them into your guard. Takes the Body shot slot."),
     "Pull them into your guard. Takes the Body shot slot."),
    (COMMON, _m("singleleg", "Single Leg", "takedown", GRAPPLE, "wrestling", 8, slot="legkick",
                to="guard_top", bonus=-0.04, anim="takedown",
                desc="A cheaper shot that is a bit easier to stop. Takes the Leg kick slot."),
     "A cheaper shot that is a bit easier to stop. Takes the Leg kick slot."),
    (RARE, _m("flytri", "Flying Triangle", "clinch", SUB, "grappling", 14, slot="kick",
              bonus=0.04, sub_fail="bottom", anim="triangle",
              desc="Jump straight into a triangle. If it fails you are on your back. "
                   "Takes the Head kick slot."),
     "Jump straight into a triangle. Takes the Head kick slot."),

    # Clinch
    (RARE, _m("plum", "Thai Plum Knees", "knees", STRIKE, "striking", 9, dmg=10, acc=0.7,
              power=True, cuts=0.1, anim="knees",
              desc="Pull the head down into knees. Head shots, not body."),
     "Pull the head down into knees. Head shots, not body."),
    (RARE, _m("spinelbow", "Spinning Elbow", "dirty", STRIKE, "striking", 9, dmg=10, acc=0.62,
              power=True, cuts=0.3, anim="dirty",
              desc="Slower than dirty boxing, but it slices."),
     "Slower than dirty boxing, but it slices."),
    (RARE, _m("hiptoss", "Judo Hip Toss", "trip", GRAPPLE, "wrestling", 12, to="mount_top",
              bonus=0.05, slam=5, anim="trip",
              desc="Throw them and land straight in mount."),
     "Throw them and land straight in mount."),
    (RARE, _m("anaconda", "Anaconda Choke", "guillotine", SUB, "grappling", 12, bonus=0.08,
              anim="guillotine",
              desc="A tighter front headlock. Still risky if it fails."),
     "A tighter front headlock. Still risky if it fails."),

    # Ground, top
    (COMMON, _m("hammer", "Hammer Fists", "gnp", STRIKE, "wrestling", 6, dmg=7.5, acc=0.88,
                speed=2, cuts=0.06, anim="gnp",
                desc="Short, accurate shots from the top."),
     "Short, accurate shots from the top."),
    (COMMON, _m("smash", "Smash Pass", "pass", GRAPPLE, "grappling", 10, to="mount_top",
                bonus=0.08, anim="pass",
                desc="Heavy pressure pass."),
     "Heavy pressure pass."),
    (RARE, _m("darce", "D'Arce Choke", "standup", SUB, "grappling", 12, anim="armtri",
              desc="Choke from the top instead of standing up."),
     "Choke from the top instead of standing up."),
    (LEGENDARY, _m("necktie", "Peruvian Necktie", "standup", SUB, "grappling", 13, bonus=0.1,
                   anim="armtri",
                   desc="A rare, brutal choke from the top."),
     "A rare, brutal choke from the top."),
    (RARE, _m("suloev", "Suloev Stretch", "armtri", SUB, "grappling", 12, bonus=0.07,
              anim="armtri",
              desc="A leg lock from on top. Finishes quicker."),
     "A leg lock from on top. Finishes quicker."),
    (LEGENDARY, _m("twister", "Twister", "rnc", SUB, "grappling", 13, bonus=0.1, anim="rnc",
                   desc="A spine lock from the back. Very hard to escape."),
     "A spine lock from the back. Very hard to escape."),

    # Ground, bottom
    (RARE, _m("kimura", "Kimura", "triangle", SUB, "grappling", 11, bonus=0.05, anim="triangle",
              desc="Shoulder lock from guard. Cheaper and tighter than the triangle."),
     "Shoulder lock from guard. Cheaper and tighter than the triangle."),
    (LEGENDARY, _m("gogo", "Gogoplata", "triangle", SUB, "grappling", 14, bonus=0.12,
                   anim="triangle",
                   desc="A shin across the throat. Nobody sees it coming."),
     "A shin across the throat. Nobody sees it coming."),
    (RARE, _m("butterfly", "Butterfly Sweep", "sweep", GRAPPLE, "grappling", 10, to="guard_top",
              bonus=0.1, anim="sweep",
              desc="Hook and elevate. Sweeps more often."),
     "Hook and elevate. Sweeps more often."),
    (COMMON, _m("wallwalk", "Wall Walk", "getup", GRAPPLE, "wrestling", 8, to="standing",
                bonus=0.1, anim="getup",
                desc="Use the fence to get back up."),
     "Use the fence to get back up."),
    (RARE, _m("upkicko", "Upkick", "upkick", STRIKE, "striking", 8, dmg=9, acc=0.55, power=True,
              anim="upkick",
              desc="A heel to the jaw from the bottom."),
     "A heel to the jaw from the bottom."),
    (COMMON, _m("granby", "Granby Roll", "shrimp", GRAPPLE, "grappling", 7, to="guard_bottom",
                bonus=0.1, anim="shrimp",
                desc="Roll out from under the mount."),
     "Roll out from under the mount."),
]

# Perks. Values are the effect at level 1, 2 and 3.
_PERKS = [
    ("nevergiveup", "Never Say Die", RARE, (0.3, 0.4, 0.5, 0.58, 0.65),
     "Hit {pct} harder when your health is under 40%."),
    ("combo", "Combination Puncher", RARE, (0.1, 0.13, 0.16, 0.18, 0.2),
     "Every strike that lands in a row hits {pct} harder, up to 3 in a row."),
    ("dutch", "Dutch Kickboxing", COMMON, (0.4, 0.6, 0.8, 0.95, 1.1),
     "Leg kicks do {pct} more leg damage."),
    ("bodysnatcher", "Body Snatcher", COMMON, (0.4, 0.6, 0.8, 0.95, 1.1),
     "Body shots drain {pct} more stamina."),
    ("ironlungs", "Iron Lungs", RARE, (0.18, 0.24, 0.3, 0.34, 0.38),
     "Every move costs {pct} less stamina."),
    ("granite", "Granite Chin", RARE, (0.4, 0.5, 0.6, 0.65, 0.7),
     "{pct} less chance of being rocked or knocked out."),
    ("killer", "Killer Instinct", RARE, (0.35, 0.45, 0.55, 0.62, 0.7),
     "Hit {pct} harder when they are rocked."),
    ("subhunter", "Submission Hunter", RARE, (0.05, 0.08, 0.11, 0.13, 0.15),
     "Submissions sink in {pts} more often."),
    ("getup", "Get Up Artist", COMMON, (0.14, 0.2, 0.26, 0.3, 0.34),
     "Escapes and getting up work {pts} more often."),
    ("heavytop", "Heavy Top", RARE, (0.25, 0.35, 0.45, 0.52, 0.6),
     "Ground strikes from the top do {pct} more and escapes are harder."),
    ("counter", "Counter Striker", COMMON, (0.18, 0.24, 0.3, 0.34, 0.38),
     "Counters land {pts} more often."),
    ("secondwind", "Second Wind", COMMON, (12, 18, 24, 28, 32),
     "Get {num} extra stamina back between rounds."),
    ("heavyhands", "Heavy Hands", COMMON, (1, 1, 2, 2, 3), "+{num} striking."),
    ("base", "Wrestling Base", COMMON, (1, 1, 2, 2, 3), "+{num} wrestling."),
    ("blackbelt", "Black Belt", COMMON, (1, 1, 2, 2, 3), "+{num} grappling."),
    ("gastank", "Gas Tank", COMMON, (1, 1, 2, 2, 3), "+{num} cardio."),
    ("glass", "Glass Cannon", LEGENDARY, (2, 3, 3, 4, 4), "+{num} striking, but -2 chin."),
    # Newer perks
    ("ironwill", "Iron Will", RARE, (0.06, 0.09, 0.12, 0.14, 0.16),
     "Submissions get tighter {pts} less often on you."),
    ("relentless", "Relentless", RARE, (0.25, 0.35, 0.45, 0.52, 0.6),
     "Head shots that land also drain {pct} of their damage as stamina."),
    ("sprawl", "Sprawl", COMMON, (0.06, 0.09, 0.12, 0.14, 0.16),
     "Takedowns and trips on you work {pts} less often."),
    ("cutman", "Cut Man", COMMON, (10, 15, 20, 24, 28),
     "Your corner closes {num} more of a cut between rounds, and the doctor is more patient."),
    ("feintmaster", "Feint Master", COMMON, (6, 9, 12, 14, 16),
     "A feint that freezes them also drains {num} of their stamina."),
    ("slick", "Slick", RARE, (0.04, 0.06, 0.08, 0.09, 0.1),
     "Strikes against you land {pts} less often."),
    ("showman", "Showman", COMMON, (0.25, 0.35, 0.45, 0.52, 0.6),
     "Your momentum builds {pct} faster."),
]

STAT_PERKS = {"heavyhands": "striking", "base": "wrestling", "blackbelt": "grappling",
              "gastank": "cardio"}
ESCAPES = {"getup", "bstand", "turnin", "shrimp", "bridge", "break"}

CARDS = {}
for rarity, mv, desc in _MOVE_CARDS:
    CARDS[mv.key] = Card(mv.key, mv.name, rarity, desc, move=mv)
for pid, name, rarity, vals, desc in _PERKS:
    CARDS[pid] = Card(pid, name, rarity, desc, perk=vals)


def perk_text(card, level):
    v = card.perk[level - 1]
    return card.desc.format(pct=f"{int(round(v * 100))}%", pts=f"{int(round(v * 100))}%", num=v)


# Where each basic move lives, for grouping cards in the deck builder
GROUPS = [
    ("Standing", [(STANDING, NEUTRAL)]),
    ("Clinch", [(CLINCH, NEUTRAL)]),
    ("Ground top", [(GUARD, TOP), (MOUNT, TOP), (BACK, TOP)]),
    ("Ground bottom", [(GUARD, BOTTOM), (MOUNT, BOTTOM), (BACK, BOTTOM)]),
]


def group_of(slot):
    for name, keys in GROUPS:
        for k in keys:
            if slot in MOVESETS[k]:
                return name
    return "Standing"


def group_slots(group):
    """The basic move keys in a group, in order, without repeats."""
    for name, keys in GROUPS:
        if name == group:
            out = []
            for k in keys:
                for b in MOVESETS[k]:
                    if b not in out:
                        out.append(b)
            return out
    return []


def variants(slot):
    """Move cards that can go in the slot of this basic move."""
    return [c for c in CARDS.values() if c.move and c.move.slot == slot]


def leveled(move, level):
    """A move card gets a bit better with each level, a little less from level 4 on."""
    n = max(0, level - 1)
    if n == 0:
        return move
    n = min(n, 2) + 0.5 * max(0, n - 2)   # levels 2 and 3 count fully, 4 and 5 half
    cost = move.cost * (1 - 0.08 * n) if move.cost > 0 else move.cost
    return replace(move, dmg=move.dmg * (1 + 0.1 * n), acc=move.acc + 0.03 * n, cost=cost,
                   bonus=move.bonus + 0.04 * n, counter=move.counter + 0.04 * n if move.counter else 0.0)


# The fighter's kit: what the engine uses in a fight

class Kit:
    __slots__ = ("moves", "movesets", "perks", "stats", "weight")

    def __init__(self, moves, movesets, perks, stats, weight=None):
        from .weights import get
        self.moves = moves          # key -> Move, for every move this fighter can pick
        self.movesets = movesets    # (pos, role) -> list of keys
        self.perks = perks          # perk id -> level
        self.stats = stats          # stats after stat perks
        self.weight = weight or get(None)   # weight class numbers

    def perk(self, pid):
        lvl = self.perks.get(pid)
        return CARDS[pid].perk[lvl - 1] if lvl else 0


def build_kit(profile):
    from .fighter import Stats
    deck = getattr(profile, "deck", {}) or {}
    levels = getattr(profile, "cards", {}) or {}
    moves = dict(MOVES)
    movesets = {}
    for pr, keys in MOVESETS.items():
        out = []
        for k in keys:
            cid = deck.get(k)
            card = CARDS.get(cid) if cid else None
            if card and card.move and card.move.slot == k:
                m = leveled(card.move, levels.get(cid, 1))
                moves[m.key] = m
                out.append(m.key)
            else:
                out.append(k)
        movesets[pr] = out
    perks = {}
    for pid in (getattr(profile, "perks", []) or [])[:MAX_PERKS]:
        if pid in CARDS and CARDS[pid].is_perk:
            perks[pid] = levels.get(pid, 1)
    s = profile.stats
    stats = Stats(**{n: s.get(n) for n in STAT_NAMES})
    for pid, lvl in perks.items():
        v = CARDS[pid].perk[lvl - 1]
        if pid in STAT_PERKS:
            st = STAT_PERKS[pid]
            setattr(stats, st, stats.get(st) + v)
        elif pid == "glass":
            stats.striking += v
            stats.chin -= 2
    stats.clamp(STAT_LIMIT)   # perks can take a maxed stat past 10
    boost = getattr(profile, "camp_boost", None)   # training camp, see Career.fighter_for_fight
    if boost:
        setattr(stats, boost, min(STAT_LIMIT, stats.get(boost) + 1))
    for st, v in (getattr(profile, "injury", None) or {}).items():   # hurt from a loss
        setattr(stats, st, max(STAT_MIN, stats.get(st) - v))
    from .weights import get
    return Kit(moves, movesets, perks, stats, get(getattr(profile, "weight", None)))


def deck_points(profile):
    pts = 0
    for cid in (profile.deck or {}).values():
        if cid in CARDS:
            pts += CARDS[cid].points
    for pid in profile.perks or []:
        if pid in CARDS:
            pts += CARDS[pid].points
    return pts


def signature_names(profile):
    """Names of the cards a fighter has equipped, for showing before a fight."""
    out = [CARDS[c].name for c in (profile.deck or {}).values() if c in CARDS]
    out += [CARDS[p].name for p in (profile.perks or []) if p in CARDS]
    return out


# Preset decks for each style and starter cards for a new career

PRESETS = {
    "Striker": ({"cross": "superman", "legkick": "calfkick"}, ["combo"]),
    "Wrestler": ({"takedown": "doubleleg", "gnp": "hammer"}, ["heavytop"]),
    "BJJ": ({"body": "guardpull", "legkick": "singleleg", "triangle": "kimura",
             "sweep": "butterfly"}, []),
    "Brawler": ({"body": "liver", "dirty": "spinelbow"}, ["nevergiveup"]),
}

STARTERS = {
    "Striker": ({"legkick": "calfkick"}, ["counter"]),
    "Wrestler": ({"getup": "wallwalk"}, ["base"]),
    "BJJ": ({"pass": "smash"}, ["blackbelt"]),
    "Brawler": ({"body": "liver"}, ["secondwind"]),
}


def apply_deck(profile, deck, perks, level=1):
    """Give a profile these cards at a level and equip them."""
    profile.deck = dict(deck)
    profile.perks = list(perks)
    profile.cards = dict(getattr(profile, "cards", {}) or {})
    for cid in list(deck.values()) + list(perks):
        profile.cards[cid] = max(profile.cards.get(cid, 0), level)
    return profile


def equip(profile, slot, cid, budget):
    """Put a card in a move slot, or None for the basic move. Returns an error or None."""
    old = dict(profile.deck)
    if cid is None:
        profile.deck.pop(slot, None)
    else:
        c = CARDS.get(cid)
        if not c or not c.move or c.move.slot != slot or cid not in profile.cards:
            return "That card does not go there"
        profile.deck[slot] = cid
    if deck_points(profile) > budget:
        profile.deck = old
        return "Not enough deck points"
    return None


def toggle_perk(profile, pid, budget):
    """Equip or remove a perk. Returns an error or None."""
    if pid in profile.perks:
        profile.perks.remove(pid)
        return None
    if pid not in profile.cards:
        return "You do not own that perk"
    if len(profile.perks) >= MAX_PERKS:
        return f"Only {MAX_PERKS} perks at a time"
    profile.perks.append(pid)
    if deck_points(profile) > budget:
        profile.perks.remove(pid)
        return "Not enough deck points"
    return None


def validate(profile, budget):
    """Problems with a deck, as plain strings. Empty means it is fine."""
    problems = []
    if deck_points(profile) > budget:
        problems.append(f"Over budget: {deck_points(profile)} of {budget} points")
    if len(profile.perks or []) > MAX_PERKS:
        problems.append(f"Only {MAX_PERKS} perks allowed")
    for slot, cid in (profile.deck or {}).items():
        c = CARDS.get(cid)
        if not c or not c.move or c.move.slot != slot:
            problems.append(f"{cid} cannot go in the {slot} slot")
        elif cid not in (profile.cards or {}):
            problems.append(f"You do not own {c.name}")
    return problems


def warnings(profile):
    """Holes in a deck worth pointing out in the deck builder."""
    from .moves import matchup
    kit = build_kit(profile)
    out = []
    stand = [kit.moves[k] for k in kit.movesets[(STANDING, NEUTRAL)]]
    if not any(matchup(m, MOVES["takedown"]) == 1 for m in stand):
        out.append("Nothing in your standing deck stops a takedown.")
    return out
