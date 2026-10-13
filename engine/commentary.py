"""Turns an Exchange into a line or two of commentary."""

import random

from .constants import STANDING, CLINCH, GUARD, MOUNT

_rng = random.Random()


def _pick(*lines):
    return _rng.choice(lines)


def describe(ex, names):
    """names: (red name, blue name). Returns a list of short lines."""
    a, b = names
    n = [a, b]
    lines = []

    if ex.in_sub:
        att, dfn = n[ex.sub_att], n[1 - ex.sub_att]
        sub = ex.sub_card.name.lower()
        r = ex.sub_result
        if r == "tap":
            lines.append(_pick(f"{dfn} taps! {att} wins by {sub}!",
                               f"It's tight and {dfn} has to tap!"))
        elif r == "escaped":
            lines.append(_pick(f"{dfn} escapes the {sub}!", f"Great defence from {dfn}, they're out!"))
        elif r == "defended":
            lines.append(_pick(f"{dfn} reads it and fights the hands.", f"{dfn} loosens the grip."))
        elif r == "tighter":
            lines.append(_pick(f"{att} cranks it tighter!", f"Oh, that {sub} is getting deep!",
                               f"{dfn} is in real trouble here!"))
        else:
            lines.append(_pick(f"{att} can't quite finish it yet.", f"{dfn} hangs on."))
        return lines

    for i in (0, 1):
        me, them = n[i], n[1 - i]
        m = ex.moves[i]
        if ex.countered[i]:
            lines.append(_pick(f"{me} blocks and counters!", f"Slick counter from {me}!"))
        elif ex.blocked[i]:
            lines.append(_pick(f"{me} blocks it.", f"{me} takes that on the gloves."))
        if ex.caught[1 - i] and ex.landed[i]:
            lines.append(_pick(f"{me} catches {them} coming in!", f"{them} walks right into it!"))
        if ex.takedown_by == i:
            if ex.moves[1 - i].base in ("kick", "legkick"):
                lines.append(f"{me} catches the kick and dumps {them}!")
            else:
                lines.append(_pick(f"{me} takes {them} down!", f"Big takedown by {me}!",
                                   f"{me} plants {them} on the mat."))
        if ex.reversal_by == i:
            lines.append(_pick(f"{me} reverses! Now on top!", f"What a sweep from {me}!"))
        if ex.sub_start == i:
            lines.append(_pick(f"{me} locks up a {m.name.lower()}!", f"{m.name}! {me} has it!"))
        if ex.stuffed[i] and m.to == "guard_top":
            lines.append(_pick(f"{them} stuffs the takedown.", f"Great sprawl by {them}."))
        if ex.knockdown == 1 - i and ex.target_hit[i] == "body":
            lines.append(_pick(f"{them} folds from the body shot!", f"Liver shot! {them} is down!"))
        elif ex.knockdown == 1 - i:
            lines.append(_pick(f"DOWN GOES {them.upper()}!", f"{me} drops {them}!"))
        elif ex.rocked[1 - i]:
            lines.append(_pick(f"{them} is hurt!", f"{them} is rocked!", f"That one wobbled {them}!"))
        if ex.cut_opened[1 - i]:
            lines.append(_pick(f"{them} is cut! There is blood everywhere.",
                               f"That opened a cut on {them}!"))
        if ex.limping[1 - i]:
            lines.append(_pick(f"{them} is limping badly!", f"That leg is done, {them} can barely stand."))

    if ex.transition and not lines:
        by, to = ex.transition
        if to == "clinch":
            lines.append(f"{n[by]} ties it up against the fence.")
        elif to == "mount_top":
            lines.append(_pick(f"{n[by]} passes to the mount!", f"{n[by]} is in full mount, this is bad."))
        elif to == "standing":
            lines.append(_pick("Back on the feet.", f"{n[by]} gets it back to the feet."))
        elif to == "guard_bottom":
            lines.append(f"{n[by]} recovers guard.")
        elif to == "back_top":
            lines.append(_pick(f"{n[by]} takes the back!", f"{n[by]} is on the back, hooks in!"))

    if not lines and any(ex.gassed):
        i = 0 if ex.gassed[0] else 1
        lines.append(_pick(f"{n[i]} is running on fumes, nothing behind it.",
                           f"{n[i]} is exhausted and it shows."))

    if not lines:
        dmg = ex.dmg
        if max(dmg) >= 1:
            i = 0 if dmg[0] >= dmg[1] else 1
            m = ex.moves[i]
            if ex.landed[0] and ex.landed[1]:
                lines.append(_pick("They trade shots!", "Both men land!", "Wild exchange!"))
            elif ex.target_hit[i] == "body":
                lines.append(_pick(f"{n[i]} digs to the body.", f"Hard shot downstairs from {n[i]}."))
            elif ex.target_hit[i] == "legs":
                lines.append(_pick(f"{n[i]} chops the lead leg.", f"Hard leg kick from {n[i]}."))
            else:
                lines.append(_pick(f"{n[i]} lands the {m.name.lower()}.",
                                   f"Good {m.name.lower()} from {n[i]}."))
        elif ex.stall:
            lines.append(_pick("Both men reset.", "A quiet moment.", "Some boos from the crowd."))
        elif ex.missed[0] or ex.missed[1]:
            lines.append(_pick("Nothing lands clean.", "Swing and a miss."))
        else:
            lines.append("They feel each other out.")
    return lines[:2]


def finish_line(result, names):
    if result.winner is None:
        return "It's a draw!"
    w = names[result.winner]
    if result.method == "KO":
        return _pick(f"{w} wins by KO! Lights out!", f"Goodnight! {w} by knockout!")
    if result.method == "TKO" and result.detail.startswith("Doctor"):
        return f"The doctor has seen enough! {w} wins by TKO!"
    if result.method == "TKO":
        return f"The referee waves it off! {w} wins by TKO!"
    if result.method == "Submission":
        return f"{w} wins by submission!"
    return f"{w} wins by {result.detail.lower()}!"
