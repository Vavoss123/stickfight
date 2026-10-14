"""Resolves one exchange: both picks are revealed and play out together.

Everything here works on a FightState and a random.Random, with no UI, so it can be
tested, simulated and used by the AI for lookahead. Moves come from each fighter's own
kit, so signature cards and perks apply.
"""

from .cards import ESCAPES
from .constants import (STANDING, CLINCH, GUARD, MOUNT, BACK, STRIKE, GRAPPLE, SUB, DEFEND, FEINT,
                        SUB_TAP, SUB_START, HEAD, BODY, LEGS, TIRED_DAMAGE)
from .moves import matchup, base_class
from .weights import SIZE_DAMAGE, SIZE_GRAPPLE, SIZE_TOUGH
from .state import SubState

def _size(a, d):
    """How much heavier fighter a is than d, in hundreds of pounds."""
    return (a.wc["lbs"] - d.wc["lbs"]) / 100


def _power(a, d):
    """Weight class punching power, plus extra for the bigger fighter, and less for
    hitting someone bigger than you."""
    gap = _size(a, d)
    return (a.wc["power"] * (1 + max(0.0, gap) * SIZE_DAMAGE)
            / (1 + max(0.0, -gap) * SIZE_TOUGH))


# Momentum. Exciting work fills a fighter's hype, stalling drains it. Full hype makes
# the next attack go all in.
HYPE_DECAY = 1.0
HYPE_PER_DAMAGE = 1.9
HYPE_EVENTS = {"knockdown": 30, "rocked": 10, "takedown": 16, "reversal": 18, "sub_start": 16,
               "counter": 8, "tighter": 6, "escape": 20}
BOO_AFTER = 3          # defensive picks in a row that block nothing
BOO_DRAIN = 15
SURGE_ACC = 0.15
SURGE_DMG = 1.3
SURGE_GRAPPLE = 0.15


# Openings for the next strike: (accuracy, speed, damage). A read comes from a feint
# that froze them, a follow up from landing clean the exchange before.
OPENINGS = {"read": (0.15, 2, 1.1), "follow": (0.05, 1, 1.0)}
FEINT_PUNISH = 0.1      # a feinter is this much easier to hit, and a bit harder to take down


# Fouls: a small chance on every strike thrown, more when gassed. The first is a
# warning, every one after that costs a point. The victim gets a breather.
FOUL_CHANCE = 0.015
FOUL_GASSED = 0.02
FOUL_REST = 12
FOULS = {"head": "Eye poke", "legs": "Low blow", "body": "Low blow", "ground": "Shot to the back of the head"}
# The referee stands them up after this many quiet exchanges
IDLE_LIMIT = {CLINCH: 2, GUARD: 4, MOUNT: 4, BACK: 4}


# How much harder an escape from the bottom is when the top fighter's strike lands on
# you at the same time. Without it, covering up was the only answer to ground and pound.
SCRAMBLE = -0.5


class Exchange:
    """What happened in one exchange. The UI animates from this, scoring reads it."""

    def __init__(self, picks, st):
        self.picks = tuple(picks)
        self.pos_before = st.pos
        self.top_before = st.top
        self.in_sub = st.sub is not None
        self.sub_move = st.sub.move if st.sub else None
        self.sub_att = st.sub.att if st.sub else None
        self.sub_card = st.f[st.sub.att].move(st.sub.move) if st.sub else None
        self.moves = (None, None) if st.sub else (st.f[0].move(picks[0]), st.f[1].move(picks[1]))
        self.success = [False, False]   # the move did what it was meant to
        self.landed = [False, False]    # strike connected
        self.missed = [False, False]
        self.dmg = [0.0, 0.0]           # damage dealt BY fighter i
        self.blocked = [False, False]   # fighter i blocked a strike
        self.countered = [False, False] # fighter i landed a counter
        self.caught = [False, False]    # fighter i got caught coming in
        self.stuffed = [False, False]   # fighter i's grapple was stopped
        self.rocked = [False, False]    # fighter i became rocked
        self.knockdown = None           # index of fighter knocked down
        self.target_hit = [None, None]  # head / body / legs that fighter i landed on
        self.limping = [False, False]   # fighter i's legs just went
        self.cut_opened = [False, False]  # fighter i got cut this exchange
        self.combo = [0, 0]             # strikes in a row fighter i has landed
        self.effort = [1.0, 1.0]        # below 1 when fighter i could not pay for the move
        self.gassed = [False, False]
        self.stamina_before = [f.stamina for f in st.f]
        self.opening = [f.opening for f in st.f]   # read / follow / None, see OPENINGS
        self.foul = None                # (fighter, what, "warning" or "point")
        self.ref_break = None           # "clinch" or "ground" when the referee resets them
        self.feinted = [False, False]   # fighter i's feint froze the other
        self.frozen = [False, False]    # fighter i bit on a feint
        self.surging = [False, False]   # fighter i went all in with full momentum
        self.surge_ready = [False, False]  # fighter i's momentum just filled up
        self.booed = [False, False]     # the crowd is on fighter i for stalling
        self.transition = None          # (by, to)
        self.takedown_by = None
        self.reversal_by = None
        self.sub_start = None           # attacker index
        self.sub_result = None          # tighter / held / defended / escaped / tap
        self.lock = None
        self.stall = False
        self.finish = None              # (winner, method, detail)
        self.round_over = False
        self.pos = st.pos
        self.top = st.top


def _clamp(x, lo, hi):
    return lo if x < lo else hi if x > hi else x


def _chin_factor(f):
    """Above 1 for weak chins, below 1 for iron chins."""
    return (1.3 - f.stats.chin * 0.06) * (1 - f.perk("granite"))


def _apply_transition(st, ex, i, to):
    before = (st.pos, st.top)
    if to == "standing":
        st.pos, st.top = STANDING, None
    elif to == "clinch":
        st.pos, st.top = CLINCH, None
    elif to == "guard_top":
        st.pos, st.top = GUARD, i
    elif to == "guard_bottom":
        st.pos, st.top = GUARD, 1 - i
    elif to == "mount_top":
        st.pos, st.top = MOUNT, i
    elif to == "back_top":
        st.pos, st.top = BACK, i
    ex.transition = (i, to)
    if to in ("guard_top", "mount_top"):
        if before[0] in (STANDING, CLINCH):
            ex.takedown_by = i
        elif before[1] == 1 - i:
            ex.reversal_by = i


def _target(st, i, move):
    """The (pos, top) a grappling move would produce, for comparing two moves."""
    to = move.to
    if to == "standing":
        return (STANDING, None)
    if to == "clinch":
        return (CLINCH, None)
    if to == "guard_top":
        return (GUARD, i)
    if to == "guard_bottom":
        return (GUARD, 1 - i)
    if to == "mount_top":
        return (MOUNT, i)
    if to == "back_top":
        return (BACK, i)
    return None


def _damage_mult(st, i):
    """Perks that make fighter i hit harder right now."""
    a, d = st.f[i], st.f[1 - i]
    m = 1.0
    if a.hp < 40:
        m += a.perk("nevergiveup")
    if d.rocked:
        m += a.perk("killer")
    if a.combo:
        m += a.perk("combo") * min(3, a.combo)
    if st.top == i and st.pos not in (STANDING, CLINCH):
        m += a.perk("heavytop")
    # Tired fighters cannot defend themselves
    m *= 1 + TIRED_DAMAGE * (1 - d.stamina / 100)
    return m


def _foul(st, ex, i, move, rng):
    """Did that strike go somewhere it should not? Returns True if it was a foul."""
    a, d = st.f[i], st.f[1 - i]
    p = FOUL_CHANCE + (FOUL_GASSED if ex.gassed[i] else 0.0)
    if ex.foul or rng.random() >= p:
        return False
    a.fouls += 1
    where = "ground" if st.pos not in (STANDING, CLINCH) else move.target
    ex.foul = (i, FOULS[where], "warning" if a.fouls == 1 else "point")
    d.stamina = min(100.0, d.stamina + FOUL_REST)
    d.rocked = 0
    st.pos, st.top = STANDING, None   # the referee restarts them on the feet
    return True


def _strike(st, ex, i, move, rng, bonus_acc=0.0, mult=1.0):
    if st.f[i].hp <= 0:
        return  # knocked out by the other shot
    if _foul(st, ex, i, move, rng):
        ex.missed[i] = True
        return
    a, d = st.f[i], st.f[1 - i]
    p = move.acc + bonus_acc + (a.stat(move.stat) - d.stat(move.stat)) * 0.025
    p += a.wc["speed"]   # lighter classes are quicker
    p -= d.perk("slick")
    op = OPENINGS.get(ex.opening[i])
    if op:
        p += op[0]
    if ex.surging[i]:
        p += SURGE_ACC
    p *= 0.55 + 0.45 * a.stamina_factor()
    p *= 0.35 + 0.65 * ex.effort[i]   # thrown on an empty tank
    if a.rocked:
        p -= 0.15
    if d.rocked:
        p += 0.12
    if a.cut >= 40:
        p -= 0.06  # blood in the eyes
    if rng.random() >= _clamp(p, 0.05, 0.97):
        ex.missed[i] = True
        return
    dmg = move.dmg * (0.65 + 0.07 * a.stat(move.stat)) * a.stamina_factor() * mult
    dmg *= 0.5 + 0.5 * ex.effort[i]
    dmg *= _power(a, d)
    if op:
        dmg *= op[2]
    if ex.surging[i]:
        dmg *= SURGE_DMG
    dmg *= _damage_mult(st, i)
    if move.power:
        dmg *= a.mobility()  # no legs, no power
    if d.rocked:
        dmg *= 1.2
    if move.target == HEAD:
        dmg /= 0.75 + 0.05 * d.stats.chin
    dmg *= rng.uniform(0.85, 1.15)
    was_rocked = d.rocked > 0
    standing = st.pos in (STANDING, CLINCH)
    chin = _chin_factor(d)
    ex.landed[i] = True
    ex.success[i] = True
    ex.target_hit[i] = move.target
    ex.dmg[i] += dmg

    if move.target == BODY:
        # Less damage now, but it takes the gas out of them
        limb = move.limb * (1 + a.perk("bodysnatcher"))
        d.take(dmg * 0.7)
        d.body = min(100.0, d.body + dmg * 2.4 * limb)
        d.stamina = max(0.0, d.stamina - dmg * 0.9 * limb)
        fold = max(0.0, (d.body - 45) / 300) * chin * move.limb
        if standing and rng.random() < fold:
            ex.knockdown = 1 - i
            d.rocked = 1
            ex.rocked[1 - i] = True
            st.pos, st.top = GUARD, i
            ex.transition = (i, "knockdown")
        return
    if move.target == LEGS:
        limb = move.limb * (1 + a.perk("dutch"))
        was_ok = d.legs < 60
        d.take(dmg * 0.6)
        d.legs = min(100.0, d.legs + dmg * 3.2 * limb)
        d.stamina = max(0.0, d.stamina - dmg * 0.3)
        if was_ok and d.legs >= 60:
            ex.limping[1 - i] = True
        return

    d.take(dmg)
    if a.perk("relentless"):
        d.stamina = max(0.0, d.stamina - dmg * a.perk("relentless"))
    _cut(st, ex, i, move, dmg, rng)
    if ex.finish:
        return
    rock = max(0.0, (dmg - 5) * 0.045) * chin + (0.2 if d.hp < 30 else 0.0)
    if rng.random() < rock:
        d.rocked = 1
        ex.rocked[1 - i] = True

    if d.hp <= 0:
        return

    if move.power and standing:
        # A clean power shot can end it at any time, more likely when hurt
        ko = _clamp(dmg / max(d.hp, 1.0) * 0.22 * chin * move.ko * a.wc["ko"]
                    * (SURGE_DMG if ex.surging[i] else 1.0), 0, 0.5)
        if was_rocked:
            ko *= 1.5
        if rng.random() < ko:
            d.hp = 0.0
            return
        kd = (0.35 if was_rocked else 0.1 if ex.rocked[1 - i] else 0.0) * chin
        if rng.random() < kd:
            ex.knockdown = 1 - i
            d.rocked = 1
            ex.rocked[1 - i] = True
            st.pos, st.top = GUARD, i
            ex.transition = (i, "knockdown")

    if not standing and st.top == i and (was_rocked or ex.rocked[1 - i]) and d.hp < 40:
        # Referee steps in when a hurt fighter is not defending on the bottom
        if rng.random() < 0.25 + (40 - d.hp) / 100:
            ex.finish = (i, "TKO", "Referee stoppage, " + move.name.lower())


def _cut(st, ex, i, move, dmg, rng):
    """Head shots can open a cut. Once open, every head shot makes it worse."""
    d = st.f[1 - i]
    if d.cut > 0:
        d.cut = min(100.0, d.cut + dmg * 0.9)
    elif rng.random() < move.cuts:
        d.cut = 15 + dmg * 1.5
        ex.cut_opened[1 - i] = True
    if d.cut >= 65 and rng.random() < (d.cut - 55) / 90 * (1 - 0.01 * d.perk("cutman")):
        ex.finish = (i, "TKO", "Doctor stoppage, cut")


def _counter(st, ex, i, rng, move, open_shot=False):
    """Fighter i blocked a strike and fires back. Blocked power shots leave a bigger opening."""
    a, d = st.f[i], st.f[1 - i]
    p = 0.45 + (0.2 if open_shot else 0.0) + (a.stats.striking - d.stats.striking) * 0.04
    p += move.counter + a.perk("counter")
    if a.rocked:
        p -= 0.2
    if rng.random() >= _clamp(p, 0.05, 0.92):
        return
    dmg = (3.5 + a.stats.striking * 0.45) * a.stamina_factor() * rng.uniform(0.8, 1.2)
    if open_shot:
        dmg *= 1.35
    if move.counter:
        dmg *= 1.25
    dmg *= _damage_mult(st, i) * _power(a, d)
    dmg /= 0.75 + 0.05 * d.stats.chin
    d.take(dmg)
    ex.dmg[i] += dmg
    ex.countered[i] = True
    ex.landed[i] = True
    if rng.random() < max(0.0, (dmg - 5) * 0.06) * _chin_factor(d):
        d.rocked = 1
        ex.rocked[1 - i] = True


def _grapple_success(st, ex, i, move):
    if move.cls == SUB:
        st.sub = SubState(i, move.key, SUB_START)
        ex.sub_start = i
        ex.lock = SUB_START
    else:
        from_feet = st.pos in (STANDING, CLINCH)
        _apply_transition(st, ex, i, move.to)
        if move.slam and from_feet:
            st.f[1 - i].take(move.slam)
            ex.dmg[i] += move.slam
    ex.success[i] = True


def _grapple_edge(st, i, move):
    """Card and perk bonuses for fighter i's grapple."""
    a, d = st.f[i], st.f[1 - i]
    edge = move.bonus
    if move.base in ESCAPES:
        edge += a.perk("getup")
        if st.top == 1 - i:
            edge -= d.perk("heavytop") * 0.35
    return edge


def _grapple_uncontested(st, ex, i, move, rng, bonus=0.0):
    a, d = st.f[i], st.f[1 - i]
    p = 0.78 + bonus + _grapple_edge(st, i, move) + (a.stat(move.stat) - d.stat(move.stat)) * 0.03
    p *= 0.7 + 0.3 * a.stamina_factor()
    p -= 0.4 * (1 - ex.effort[i])
    p += (d.legs - a.legs) * 0.0015  # bad legs cannot shoot or sprawl
    if move.base in ("takedown", "trip"):
        p -= d.perk("sprawl")
    p += _size(a, d) * SIZE_GRAPPLE   # the bigger fighter wins scrambles
    if ex.surging[i]:
        p += SURGE_GRAPPLE
    if d.rocked:
        p += 0.1
    if rng.random() < _clamp(p, 0.1, 0.97):
        _grapple_success(st, ex, i, move)
    else:
        ex.stuffed[i] = True
        a.spend(3)


def _grapple_contest(st, ex, moves, rng):
    a, b = st.f
    p = 0.5 + (a.stat(moves[0].stat) - b.stat(moves[1].stat)) * 0.05
    p += _grapple_edge(st, 0, moves[0]) - _grapple_edge(st, 1, moves[1])
    p += (a.stamina - b.stamina) * 0.002
    p += 0.35 * (ex.effort[0] - ex.effort[1])
    p += _size(a, b) * SIZE_GRAPPLE
    for k, sign in ((0, -1), (1, 1)):
        if moves[k].base in ("takedown", "trip"):
            p += sign * st.f[1 - k].perk("sprawl")
    p += SURGE_GRAPPLE * (ex.surging[0] - ex.surging[1])
    p += (b.legs - a.legs) * 0.002
    if a.rocked:
        p -= 0.15
    if b.rocked:
        p += 0.15
    w = 0 if rng.random() < _clamp(p, 0.1, 0.9) else 1
    if moves[w].base == "pass" and moves[1 - w].base == "getup":
        # They turned away to get up and gave up the back
        _apply_transition(st, ex, w, "back_top")
        ex.success[w] = True
    else:
        _grapple_success(st, ex, w, moves[w])
    ex.stuffed[1 - w] = True


def _end_of_exchange(st, ex, rocked_before):
    for i in (0, 1):
        f = st.f[i]
        if not ex.rocked[i] and rocked_before[i]:
            f.rocked = max(0, f.rocked - 1)
        # Strikes landed in a row
        m = ex.moves[i]
        clean = m is not None and base_class(m) == STRIKE and ex.landed[i] and not ex.countered[1 - i]
        f.opening = "read" if ex.feinted[i] else "follow" if clean and not ex.finish else None
        if m is not None and base_class(m) == STRIKE and ex.landed[i]:
            f.combo = min(3, f.combo + 1)
        elif not ex.countered[i]:
            f.combo = 0
        ex.combo[i] = f.combo
    if ex.finish is None:
        dead = [st.f[0].hp <= 0, st.f[1].hp <= 0]
        if any(dead):
            if all(dead):
                loser = 0 if ex.dmg[1] >= ex.dmg[0] else 1
            else:
                loser = 0 if dead[0] else 1
            w = 1 - loser
            move = ex.moves[w]
            name = move.name.lower() if move else "strikes"
            if ex.countered[w]:
                name = "counter punch"
            if ex.pos_before in (STANDING, CLINCH):
                ex.finish = (w, "KO", name.capitalize())
            else:
                ex.finish = (w, "TKO", "Punches" if "elbow" not in name else "Elbows")
    _momentum(st, ex)
    _referee(st, ex)
    ex.pos = st.pos
    ex.top = st.top


def _referee(st, ex):
    """Stand them up when nothing is happening in the clinch or on the ground."""
    if ex.finish or st.sub or st.pos == STANDING or ex.foul:
        st.idle = 0
        return
    busy = ex.transition is not None or sum(ex.dmg) >= 3 or ex.sub_start is not None or ex.in_sub
    st.idle = 0 if busy else st.idle + 1
    if st.idle >= IDLE_LIMIT.get(st.pos, 99):
        ex.ref_break = "clinch" if st.pos == CLINCH else "ground"
        st.pos, st.top, st.idle = STANDING, None, 0


def _momentum(st, ex):
    """Fill hype for exciting work, drain it for stalling, and spend it when used."""
    for i in (0, 1):
        f, o = st.f[i], 1 - i
        gain = ex.dmg[i] * HYPE_PER_DAMAGE
        gain += HYPE_EVENTS["knockdown"] * (ex.knockdown == o)
        gain += HYPE_EVENTS["rocked"] * ex.rocked[o]
        gain += HYPE_EVENTS["takedown"] * (ex.takedown_by == i)
        gain += HYPE_EVENTS["reversal"] * (ex.reversal_by == i)
        gain += HYPE_EVENTS["sub_start"] * (ex.sub_start == i)
        gain += HYPE_EVENTS["counter"] * ex.countered[i]
        if ex.in_sub:
            gain += HYPE_EVENTS["tighter"] * (ex.sub_att == i and ex.sub_result == "tighter")
            gain += HYPE_EVENTS["escape"] * (ex.sub_att == o and ex.sub_result == "escaped")
        m = ex.moves[i]
        if m is not None and base_class(m) == DEFEND and not ex.blocked[i]:
            f.passive += 1
        elif m is not None:
            f.passive = 0
        if f.passive >= BOO_AFTER:
            gain -= BOO_DRAIN
            ex.booed[i] = True
        if ex.surging[i]:
            f.surge = False
            f.hype = 0.0
            continue
        if gain > 0:
            gain *= 1 + f.perk("showman")
        f.hype = _clamp(f.hype + gain - HYPE_DECAY, 0.0, 100.0)
        if f.hype >= 100.0 and not f.surge:
            f.surge = True
            ex.surge_ready[i] = True


def resolve(st, picks, rng):
    """Play one exchange. Mutates st and returns an Exchange describing it."""
    if st.sub:
        return _resolve_sub(st, picks, rng)

    ex = Exchange(picks, st)
    rocked_before = [st.f[0].rocked > 0, st.f[1].rocked > 0]
    moves = list(ex.moves)
    for i in (0, 1):
        ex.effort[i] = st.f[i].effort(moves[i])
        ex.gassed[i] = ex.effort[i] < 1.0
        ex.surging[i] = st.f[i].surge and base_class(moves[i]) not in (DEFEND, FEINT)
        st.f[i].spend(moves[i].cost)

    if FEINT in (moves[0].cls, moves[1].cls):
        _feint(st, ex, moves, rng)
        _end_of_exchange(st, ex, rocked_before)
        return ex

    rel = matchup(moves[0], moves[1])
    if rel != 0:
        w = 0 if rel > 0 else 1
        l = 1 - w
        mw, ml = moves[w], moves[l]
        cw = base_class(mw)
        if cw == STRIKE:
            # Caught coming in (or a kick that goes under the guard): extra accurate and hard
            caught = base_class(ml) == GRAPPLE
            if caught:
                ex.caught[l] = True
                st.f[l].spend(3)
            _strike(st, ex, w, mw, rng, bonus_acc=0.12, mult=mw.catch if caught else 1.2)
            if ex.missed[w] and not ex.foul and st.f[l].hp > 0 and base_class(ml) != DEFEND:
                # Punch missed, so the shot can still get through
                ex.caught[l] = False
                _grapple_uncontested(st, ex, l, ml, rng, bonus=-0.2)
            elif (ex.landed[w] and not ex.foul and st.top == w and ml.cls == GRAPPLE and not ex.finish
                  and st.f[l].hp > 0 and ex.knockdown is None):
                # Eating shots on the bottom but still scrambling out
                _grapple_uncontested(st, ex, l, ml, rng, bonus=SCRAMBLE)
        elif cw == DEFEND:
            ex.blocked[w] = True
            ex.success[w] = True
            st.f[l].spend(5 if ml.power else 2)
            if ml.power:
                chip = ml.dmg * 0.12
                st.f[w].take(chip)
                ex.dmg[l] += chip
            _counter(st, ex, w, rng, mw, open_shot=ml.power)
        else:
            caught_kick = ml.base in ("kick", "legkick")
            _grapple_uncontested(st, ex, w, mw, rng, bonus=0.15 if caught_kick else 0.0)
    else:
        c = base_class(moves[0])
        if c == STRIKE:
            # The faster strike lands first and disrupts the slower one.
            # Equal speed means a true trade, in random order so neither corner has an edge.
            # A gassed strike is slower than anything
            s0, s1 = [-1 if ex.gassed[i] else
                      moves[i].speed + (OPENINGS[ex.opening[i]][1] if ex.opening[i] else 0)
                      for i in (0, 1)]
            if s0 == s1:
                order = (0, 1) if rng.random() < 0.5 else (1, 0)
                bonus = {0: 0.0, 1: 0.0}
                mult = {0: 1.0, 1: 1.0}
            else:
                fast = 0 if s0 > s1 else 1
                order = (fast, 1 - fast)
                bonus = {fast: 0.08, 1 - fast: -0.15}
                mult = {fast: 1.0, 1 - fast: 1.0}
            for i in order:
                if ex.knockdown == i:
                    continue  # already on the floor
                if s0 != s1 and i != order[0] and ex.landed[order[0]]:
                    mult[i] = 0.6  # beaten to the punch
                _strike(st, ex, i, moves[i], rng, bonus_acc=bonus[i], mult=mult[i])
        elif c == GRAPPLE:
            same = (moves[0].cls != SUB and moves[1].cls != SUB
                    and _target(st, 0, moves[0]) == _target(st, 1, moves[1]))
            if same:
                _apply_transition(st, ex, 0, moves[0].to)
                ex.success = [True, True]
            else:
                _grapple_contest(st, ex, moves, rng)
        else:
            ex.stall = True
            ex.success = [True, True]
            st.f[0].spend(-3)
            st.f[1].spend(-3)

    _end_of_exchange(st, ex, rocked_before)
    return ex


def _feint(st, ex, moves, rng):
    """A fake. Someone blocking freezes; anything else catches the feinter open."""
    if moves[0].cls == moves[1].cls:
        ex.stall = True
        ex.success = [True, True]
        return
    i = 0 if moves[0].cls == FEINT else 1
    o = 1 - i
    mo = moves[o]
    c = base_class(mo)
    if c == DEFEND:
        # They bit: stuck behind the guard, no rest, and you have read them
        st.f[o].stamina = min(st.f[o].stamina, ex.stamina_before[o])
        ex.feinted[i] = True
        ex.frozen[o] = True
        st.f[o].stamina = max(0.0, st.f[o].stamina - st.f[i].perk("feintmaster"))
        ex.success[i] = True
    elif c == STRIKE:
        _strike(st, ex, o, mo, rng, bonus_acc=FEINT_PUNISH)
    else:
        # You see the shot coming a little early
        _grapple_uncontested(st, ex, o, mo, rng, bonus=-FEINT_PUNISH)


def _resolve_sub(st, picks, rng):
    ex = Exchange(picks, st)
    rocked_before = [st.f[0].rocked > 0, st.f[1].rocked > 0]
    s = st.sub
    a, d = s.att, 1 - s.att
    A, D = st.f[a], st.f[d]
    hold = ex.sub_card
    A.spend(4)
    D.spend(3)
    if picks[a] == picks[d]:
        s.lock -= 1
        ex.sub_result = "defended"
        ex.success[d] = True
    else:
        p = 0.52 + (A.stats.grappling - D.stats.grappling) * 0.05
        p += hold.bonus + A.perk("subhunter") - D.perk("ironwill")
        p += 0.3 * (1 - D.stamina / 100) - 0.3 * (1 - A.stamina / 100)
        if D.rocked:
            p += 0.15
        if rng.random() < _clamp(p, 0.15, 0.92):
            s.lock += 1
            ex.sub_result = "tighter"
            ex.success[a] = True
        else:
            ex.sub_result = "held"
    ex.lock = s.lock
    if s.lock >= SUB_TAP:
        ex.sub_result = "tap"
        ex.finish = (a, "Submission", hold.name)
    elif s.lock <= 0:
        ex.sub_result = "escaped"
        if hold.sub_fail == "bottom":
            st.pos, st.top = GUARD, d
        elif hold.sub_fail == "guard":
            st.pos = GUARD if st.pos not in (STANDING, CLINCH) else st.pos
        # "stay": escaping a choke from the back keeps you on the back
        st.sub = None
    _end_of_exchange(st, ex, rocked_before)
    return ex
