"""The coach between rounds: what to change in the deck for the next round.

The corner (corner.py) talks about tactics. The coach looks at the same round and picks
cards: if they keep shooting, put Sprawl in; if you are gassed, Iron Lungs. Only cards
the fighter owns, only ones that fit the budget, at most a couple a break.
"""

import copy

from .cards import CARDS, MAX_PERKS, deck_points
from .constants import STANDING
from .corner import _picks, _habit

SWAPS_PER_BREAK = 2

# What each problem calls for, best first: ("perk", id) or ("move", slot, card id)
FIXES = {
    "takedowns": [("perk", "sprawl"), ("move", "cross", "superman"), ("move", "kick", "flyknee"),
                  ("move", "kick", "showtime")],
    "blocking": [("perk", "feintmaster"), ("move", "cross", "spinfist"), ("move", "legkick", "calfkick")],
    "striking": [("move", "block", "checkhook"), ("perk", "counter"), ("perk", "slick"), ("perk", "granite")],
    "gassed": [("perk", "ironlungs"), ("perk", "secondwind"), ("perk", "gastank")],
    "cut": [("perk", "cutman")],
    "subs": [("perk", "ironwill")],
    "bottom": [("move", "getup", "wallwalk"), ("move", "sweep", "butterfly"), ("move", "shrimp", "granby"),
               ("perk", "getup")],
    "top": [("perk", "heavytop"), ("move", "gnp", "hammer"), ("move", "pass", "smash")],
    "finish": [("perk", "killer"), ("perk", "subhunter")],
    "behind": [("perk", "nevergiveup")],
}


# Cards a computer fighter's corner can bring in between rounds, by style
BENCH = {
    "Striker": ["slick", "counter", "sprawl"],
    "Wrestler": ["ironlungs", "heavytop", "sprawl"],
    "BJJ": ["ironwill", "subhunter", "getup"],
    "Brawler": ["granite", "killer", "secondwind"],
}


def give_bench(profile, level=2):
    """Let a computer fighter's corner use its style's bench cards (on a copy for the fight)."""
    for cid in BENCH.get(profile.archetype, []):
        profile.cards[cid] = max(profile.cards.get(cid, 0), level)


class Suggestion:
    def __init__(self, kind, card, slot=None, out=None, why=""):
        self.kind = kind      # "move" or "perk"
        self.card = card      # card id to put in
        self.slot = slot      # basic move slot, for move cards
        self.out = out        # what comes out: a card id, or None for the basic move
        self.why = why

    def text(self):
        name = CARDS[self.card].name
        out = CARDS[self.out].name if self.out in CARDS else None
        swap = f"Put in {name}" + (f", out goes {out}" if out else "")
        return f"{self.why} {swap}."

    def apply(self, profile):
        if self.kind == "move":
            profile.deck[self.slot] = self.card
        else:
            if self.out in profile.perks:
                profile.perks.remove(self.out)
            profile.perks.append(self.card)


def problems(fight, me):
    """What went wrong (or right) for fighter `me` last round, most pressing first."""
    opp = 1 - me
    s_me, s_opp = fight.stats[-1][me], fight.stats[-1][opp]
    m, o = fight.state.f[me], fight.state.f[opp]
    out = []
    stand = _habit(_picks(fight, opp, STANDING))
    if s_opp.takedowns >= 2 or stand == "takedown":
        out.append(("takedowns", f"They shot {max(2, s_opp.takedowns)} takedowns." if s_opp.takedowns
                    else "They keep shooting."))
    elif s_opp.takedowns >= 1 and s_opp.control >= 4:
        out.append(("takedowns", "They took you down and kept you there."))
    if s_opp.sub_attempts >= 1:
        out.append(("subs", "They are hunting submissions."))
    if m.cut >= 25:
        out.append(("cut", "That cut needs looking after."))
    if m.stamina < 45:
        out.append(("gassed", "You are running out of gas."))
    if s_opp.control >= 3:
        out.append(("bottom", "You spent too long on your back."))
    if stand == "block":
        out.append(("blocking", "They keep shelling up."))
    if s_opp.landed >= 5 and s_opp.dmg >= 18:
        out.append(("striking", f"They landed {s_opp.landed} strikes on you."))
    if s_me.control >= 3:
        out.append(("top", "You are winning the ground game."))
    if o.hp < 55 or o.rocked:
        out.append(("finish", "They are hurt. Go and finish it."))
    if m.hp < 45:
        out.append(("behind", "You are hurt."))
    return out


def suggest(fight, me, budget, profile=None, limit=SWAPS_PER_BREAK):
    """Card swaps for fighter `me`, from cards they own, that fit `budget`."""
    return _ideas(problems(fight, me), profile or fight.profiles[me], budget, limit)


# Before a fight: what an opponent is likely to do, from their style, personality and cards
STYLE_NEEDS = {
    "Wrestler": [("takedowns", "They will shoot for takedowns."), ("bottom", "They hold you down once there.")],
    "BJJ": [("subs", "They hunt submissions from anywhere."), ("bottom", "They want it on the ground.")],
    "Striker": [("striking", "They want to keep it standing and pick you apart.")],
    "Brawler": [("striking", "They throw heavy, and they can take a punch."),
                ("finish", "They fade late, so be ready to finish them.")],
}
PERSONALITY_NEEDS = {
    "pressure": ("striking", "A pressure fighter: always coming forward."),
    "counter": ("blocking", "A counter puncher: they wait behind the guard."),
    "grinder": ("takedowns", "A grinder: takedowns and top control."),
    "showboat": ("striking", "A showboat: big shots and spinning stuff."),
}
SUB_CARDS = {"imanari", "flytri", "anaconda", "darce", "necktie", "suloev", "twister", "kimura", "gogo",
             "subhunter"}


def scout(opp, me, budget, limit=3):
    """A scouting report: (what to expect, card ideas for fighter `me`)."""
    from .personality import of as personality_of
    needs = list(STYLE_NEEDS.get(opp.archetype, []))
    pers = personality_of(opp)
    if pers in PERSONALITY_NEEDS:
        needs.insert(0, PERSONALITY_NEEDS[pers])
    cards = set((opp.deck or {}).values()) | set(opp.perks or [])
    if cards & SUB_CARDS and not any(n == "subs" for n, _ in needs):
        needs.append(("subs", "Their cards are built for submissions."))
    expect, seen = [], set()
    for need, line in needs:
        if line not in seen:
            expect.append(line)
            seen.add(line)
    return expect, _ideas(needs, me, budget, limit)


def _ideas(probs, p, budget, limit):
    """The card search behind suggest(), for a list of (problem, reason)."""
    wanted = {fix[-1] for need, _ in probs for fix in FIXES.get(need, [])}
    out, used = [], set()
    for need, why in probs:
        for fix in FIXES.get(need, []):
            cid = fix[-1]
            if cid in used or cid not in p.cards or cid not in CARDS:
                continue
            if fix[0] == "perk":
                if cid in p.perks:
                    break
                drop = None
                if len(p.perks) >= MAX_PERKS:
                    spare = [x for x in p.perks if x not in wanted] or p.perks
                    drop = spare[-1]
                s = Suggestion("perk", cid, out=drop, why=why)
            else:
                slot = fix[1]
                if p.deck.get(slot) == cid:
                    break
                s = Suggestion("move", cid, slot=slot, out=p.deck.get(slot), why=why)
            trial = copy.deepcopy(p)
            s.apply(trial)
            if deck_points(trial) > budget:
                continue
            out.append(s)
            used.add(cid)
            break
        if len(out) >= limit:
            break
    return out


def changes(start, now):
    """How many cards differ between two decks: slots changed plus perks swapped."""
    slots = set(start.deck) | set(now.deck)
    n = sum(1 for k in slots if start.deck.get(k) != now.deck.get(k))
    n += len(set(now.perks) - set(start.perks))
    n += max(0, len(set(start.perks) - set(now.perks)) - len(set(now.perks) - set(start.perks)))
    return n
