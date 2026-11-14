"""Looking back over a fight: who got the better of each exchange, the turning point, and
a couple of things the player could do differently next time."""

from collections import Counter

from .commentary import describe
from .constants import STRIKE, GRAPPLE, SUB, DEFEND, FEINT, EXCHANGES_PER_ROUND, ROUND_SECONDS
from .fight import fmt_time

# How much each thing counts when deciding who won an exchange
WEIGHTS = {"success": 6, "countered": 6, "blocked": 4, "checked": 4, "slipped": 4, "feinted": 5,
           "stuffed": 3, "takedown": 10, "knockdown": 12, "sub_start": 8, "reversal": 8}
EVEN = 3          # closer than this and the exchange was even

PLURAL = {STRIKE: "strikes", GRAPPLE: "grapples", DEFEND: "defending", FEINT: "feints"}
BEATS = {STRIKE: GRAPPLE, GRAPPLE: DEFEND, DEFEND: STRIKE, FEINT: DEFEND}
# When the move that should have won by the triangle lost anyway, the usual reason
EXCEPTION = {(STRIKE, GRAPPLE): "Strikes should beat grapples, but kicks get caught and a jab won't stop a "
                                "shot. A knee or a power punch will.",
             (GRAPPLE, DEFEND): "Grapples should beat defending, but some defences are built for it: "
                                "a sprawl or a good base stuffs a tired shot.",
             (DEFEND, STRIKE): "Defending should beat strikes, but blocking power shots still hurts, and "
                               "kicks go round a high guard. Try a check or a weave.",
             (DEFEND, FEINT): "A feint freezes anyone waiting to defend. Attack instead."}
ANSWER = {STRIKE: "Defending beats strikes", GRAPPLE: "A strike catches a grapple",
          DEFEND: "A grapple beats someone waiting to defend", FEINT: "Any real attack beats a feint"}


def kind(move):
    """A move's class, with submissions counted as grapples like the rules triangle does."""
    return GRAPPLE if move.cls == SUB else move.cls


def score(ex):
    """[red, blue]: how well each fighter did in one exchange."""
    w = WEIGHTS
    out = [0.0, 0.0]
    for i in (0, 1):
        o = 1 - i
        out[i] = (ex.dmg[i] + w["success"] * ex.success[i] + w["countered"] * ex.countered[i]
                  + w["blocked"] * ex.blocked[i] + w["checked"] * ex.checked[i]
                  + w["slipped"] * ex.slipped[i] + w["feinted"] * ex.feinted[i] + w["stuffed"] * ex.stuffed[o]
                  + w["takedown"] * (ex.takedown_by == i) + w["knockdown"] * (ex.knockdown == o)
                  + w["sub_start"] * (ex.sub_start == i) + w["reversal"] * (ex.reversal_by == i))
    return out


def winner(ex):
    """Who got the better of a stand up, clinch or ground exchange: 0, 1 or None."""
    if ex.in_sub:
        return None
    s = score(ex)
    if abs(s[0] - s[1]) < EVEN:
        return None
    return 0 if s[0] > s[1] else 1


def when(k):
    """Round and clock for the k-th exchange of the fight (every round has the same number)."""
    rnd = k // EXCHANGES_PER_ROUND + 1
    left = ROUND_SECONDS - (k % EXCHANGES_PER_ROUND + 1) * ROUND_SECONDS / EXCHANGES_PER_ROUND
    return rnd, fmt_time(left)


def turning_point(fight, names):
    """The exchange that swung the fight most, as a line, or None for a fight with no big moment."""
    best = None
    won = fight.result.winner if fight.result else None
    for k, ex in enumerate(fight.history):
        if ex.finish:
            continue      # the result already says how it ended: find what led there
        s = score(ex)
        if won is not None and s[won] <= s[1 - won]:
            continue      # a turning point goes the way the fight went
        swing = abs(s[0] - s[1])
        if best is None or swing > best[0]:
            best = (swing, k, ex)
    if best is None or best[0] < 10:
        return None
    _, k, ex = best
    lines = describe(ex, names)
    if not lines:
        return None
    rnd, clock = when(k)
    return f"Round {rnd}, {clock}: {lines[0]}"


def tips(fight, i, names, limit=2):
    """A couple of plain things fighter i could change, from what actually happened."""
    o = 1 - i
    out = []
    theirs, lost = Counter(), Counter()
    gassed = 0
    for ex in fight.history:
        gassed += bool(ex.gassed[i])
        if ex.in_sub:
            continue
        mine, them = kind(ex.moves[i]), kind(ex.moves[o])
        theirs[them] += 1
        if winner(ex) == o:
            lost[(mine, them)] += 1
    if lost:
        (mine, them), n = lost.most_common(1)[0]
        if n >= 3:
            if mine == them:
                out.append(f"Your {PLURAL[mine]} lost the trade to theirs {n} times. "
                           f"{names[o]} had the edge there: try something else.")
            elif BEATS.get(them) == mine:
                # The triangle says they should win that: switch to what beats them
                out.append(f"Your {PLURAL[mine]} ran into their {PLURAL[them]} {n} times. {ANSWER[them]}.")
            else:
                why = EXCEPTION.get((mine, them), "Try a different answer to it.")
                out.append(f"Your {PLURAL[mine]} lost to their {PLURAL[them]} {n} times. {why}")
    total = sum(theirs.values())
    if total >= 5:
        them, n = theirs.most_common(1)[0]
        if n / total >= 0.4 and not any(PLURAL[them] in t for t in out):
            out.append(f"{names[o]} went to {PLURAL[them]} {n} times out of {total}. {ANSWER[them]}.")
    if gassed >= 2:
        out.append(f"You gassed {gassed} times. Defending gets stamina back before the big moves.")
    return out[:limit]
