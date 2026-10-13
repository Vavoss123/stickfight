"""Resolves one exchange: both picks are revealed and play out together.

Everything here works on a FightState and a random.Random, with no UI, so it can be
tested, simulated and used by the AI for lookahead.
"""

from .constants import (STANDING, CLINCH, GUARD, MOUNT, BACK, STRIKE, GRAPPLE, SUB, DEFEND,
                        SUB_TAP, SUB_START, HEAD, BODY, LEGS)
from .moves import MOVES, matchup, base_class
from .state import SubState


class Exchange:
    """What happened in one exchange. The UI animates from this, scoring reads it."""

    def __init__(self, picks, st):
        self.picks = tuple(picks)
        self.pos_before = st.pos
        self.top_before = st.top
        self.in_sub = st.sub is not None
        self.sub_move = st.sub.move if st.sub else None
        self.sub_att = st.sub.att if st.sub else None
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
    return 1.3 - f.stats.chin * 0.06


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
    if to == "guard_top":
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


def _strike(st, ex, i, move, rng, bonus_acc=0.0, mult=1.0):
    if st.f[i].hp <= 0:
        return  # knocked out by the other shot
    a, d = st.f[i], st.f[1 - i]
    p = move.acc + bonus_acc + (a.stat(move.stat) - d.stat(move.stat)) * 0.025
    p *= 0.55 + 0.45 * a.stamina_factor()
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
        d.take(dmg * 0.7)
        d.body = min(100.0, d.body + dmg * 2.4)
        d.stamina = max(0.0, d.stamina - dmg * 0.9)
        fold = max(0.0, (d.body - 45) / 300) * chin
        if standing and rng.random() < fold:
            ex.knockdown = 1 - i
            d.rocked = 1
            ex.rocked[1 - i] = True
            st.pos, st.top = GUARD, i
            ex.transition = (i, "knockdown")
        return
    if move.target == LEGS:
        was_ok = d.legs < 60
        d.take(dmg * 0.6)
        d.legs = min(100.0, d.legs + dmg * 3.2)
        d.stamina = max(0.0, d.stamina - dmg * 0.3)
        if was_ok and d.legs >= 60:
            ex.limping[1 - i] = True
        return

    d.take(dmg)
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
        ko = _clamp(dmg / max(d.hp, 1.0) * 0.22 * chin, 0, 0.4)
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
    if d.cut >= 65 and rng.random() < (d.cut - 55) / 90:
        ex.finish = (i, "TKO", "Doctor stoppage, cut")


def _counter(st, ex, i, rng, open_shot=False):
    """Fighter i blocked a strike and fires back. Blocked power shots leave a bigger opening."""
    a, d = st.f[i], st.f[1 - i]
    p = 0.45 + (0.2 if open_shot else 0.0) + (a.stats.striking - d.stats.striking) * 0.04
    if a.rocked:
        p -= 0.2
    if rng.random() >= _clamp(p, 0.05, 0.9):
        return
    dmg = (3.5 + a.stats.striking * 0.45) * a.stamina_factor() * rng.uniform(0.8, 1.2)
    if open_shot:
        dmg *= 1.35
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
        _apply_transition(st, ex, i, move.to)
    ex.success[i] = True


def _grapple_uncontested(st, ex, i, move, rng, bonus=0.0):
    a, d = st.f[i], st.f[1 - i]
    p = 0.78 + bonus + (a.stat(move.stat) - d.stat(move.stat)) * 0.03
    p *= 0.7 + 0.3 * a.stamina_factor()
    p += (d.legs - a.legs) * 0.0015  # bad legs cannot shoot or sprawl
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
    p += (a.stamina - b.stamina) * 0.002
    p += (b.legs - a.legs) * 0.002
    if a.rocked:
        p -= 0.15
    if b.rocked:
        p += 0.15
    w = 0 if rng.random() < _clamp(p, 0.1, 0.9) else 1
    if moves[w].key == "pass" and moves[1 - w].key == "getup":
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
    if ex.finish is None:
        dead = [st.f[0].hp <= 0, st.f[1].hp <= 0]
        if any(dead):
            if all(dead):
                loser = 0 if ex.dmg[1] >= ex.dmg[0] else 1
            else:
                loser = 0 if dead[0] else 1
            w = 1 - loser
            move = MOVES[ex.picks[w]] if not ex.in_sub else None
            name = move.name.lower() if move else "strikes"
            if ex.countered[w]:
                name = "counter punch"
            if ex.pos_before in (STANDING, CLINCH):
                ex.finish = (w, "KO", name.capitalize())
            else:
                ex.finish = (w, "TKO", "Punches" if "elbow" not in name else "Elbows")
    ex.pos = st.pos
    ex.top = st.top


def resolve(st, picks, rng):
    """Play one exchange. Mutates st and returns an Exchange describing it."""
    if st.sub:
        return _resolve_sub(st, picks, rng)

    ex = Exchange(picks, st)
    rocked_before = [st.f[0].rocked > 0, st.f[1].rocked > 0]
    moves = [MOVES[picks[0]], MOVES[picks[1]]]
    for i in (0, 1):
        st.f[i].spend(moves[i].cost)

    rel = matchup(moves[0], moves[1])
    if rel != 0:
        w = 0 if rel > 0 else 1
        l = 1 - w
        mw, ml = moves[w], moves[l]
        cw = base_class(mw)
        if cw == STRIKE:
            # Caught coming in (or a kick that goes under the guard): extra accurate and hard
            if base_class(ml) == GRAPPLE:
                ex.caught[l] = True
                st.f[l].spend(3)
            _strike(st, ex, w, mw, rng, bonus_acc=0.12, mult=1.2)
            if ex.missed[w] and st.f[l].hp > 0:
                # Punch missed, so the shot can still get through
                ex.caught[l] = False
                _grapple_uncontested(st, ex, l, ml, rng, bonus=-0.2)
        elif cw == DEFEND:
            ex.blocked[w] = True
            ex.success[w] = True
            st.f[l].spend(5 if ml.power else 2)
            if ml.power:
                chip = ml.dmg * 0.12
                st.f[w].take(chip)
                ex.dmg[l] += chip
            _counter(st, ex, w, rng, open_shot=ml.power)
        else:
            caught_kick = ml.key == "kick"
            _grapple_uncontested(st, ex, w, mw, rng, bonus=0.15 if caught_kick else 0.0)
    else:
        c = base_class(moves[0])
        if c == STRIKE:
            # The faster strike lands first and disrupts the slower one.
            # Equal speed means a true trade, in random order so neither corner has an edge.
            s0, s1 = moves[0].speed, moves[1].speed
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


def _resolve_sub(st, picks, rng):
    ex = Exchange(picks, st)
    rocked_before = [st.f[0].rocked > 0, st.f[1].rocked > 0]
    s = st.sub
    a, d = s.att, 1 - s.att
    A, D = st.f[a], st.f[d]
    A.spend(4)
    D.spend(3)
    if picks[a] == picks[d]:
        s.lock -= 1
        ex.sub_result = "defended"
        ex.success[d] = True
    else:
        p = 0.52 + (A.stats.grappling - D.stats.grappling) * 0.05
        p += 0.3 * (1 - D.stamina / 100) - 0.3 * (1 - A.stamina / 100)
        if D.rocked:
            p += 0.15
        if rng.random() < _clamp(p, 0.15, 0.9):
            s.lock += 1
            ex.sub_result = "tighter"
            ex.success[a] = True
        else:
            ex.sub_result = "held"
    ex.lock = s.lock
    if s.lock >= SUB_TAP:
        ex.sub_result = "tap"
        ex.finish = (a, "Submission", MOVES[s.move].name)
    elif s.lock <= 0:
        ex.sub_result = "escaped"
        if s.move == "guillotine":
            st.pos, st.top = GUARD, d
        elif s.move != "rnc":
            st.pos = GUARD  # escaping a choke from the back keeps you on the back
        st.sub = None
    _end_of_exchange(st, ex, rocked_before)
    return ex
