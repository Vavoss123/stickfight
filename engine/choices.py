"""Crossroads between fights.

Every few fights the hub deals a choice card: two or three ways to spend the week.
Each option quietly moves one of three meters that decide how a career ends:

  loyalty  - Ray and the gym            fame  - Dez, the crowd, the money
  health   - Lou, and how much of you is left when it's over

Options can also pay now, heal an injury, or change how the NEXT fight starts
(stamina, hype, purse), through Career.pending_start and pending_purse.
"""

from .story import RAY, LOU, DEZ

METER_MIN, METER_MAX = 0, 100


def _choice(when, speaker, title, intro, *options, cooldown=6):
    return {"when": when, "speaker": speaker, "title": title, "intro": intro,
            "options": options, "cooldown": cooldown}


def _opt(label, blurb, effects, response):
    return {"label": label, "blurb": blurb, "effects": effects, "response": response}


CHOICES = {
    "short_notice": _choice(
        lambda c: "dez" in c.story_seen and c.injury is None,
        DEZ, "Dez has an offer",
        "The co-main fell through. Same opponent, four days early, double the purse. In or out?",
        _opt("Take it", "Double purse. You start the fight tired",
             {"purse_mult": 2.0, "stamina": 65.0, "fame": 8, "health": -6, "loyalty": -4},
             "Dez grins. Ray doesn't. You'll start the next fight on half a camp."),
        _opt("Turn it down", "A full camp, and Ray's respect",
             {"loyalty": 6, "health": 4, "fame": -3},
             "Ray nods. Full camps win fights. Dez stops calling for a while."),
    ),
    "appearance": _choice(
        lambda c: c.player.wins >= 2,
        DEZ, "A sponsor wants you",
        "An energy drink wants your face for a day. Lou wants you at the kids' clinic. Ray wants you training.",
        _opt("Take the cheque", "Paid appearance: money and fame",
             {"money": 8000, "fame": 6, "loyalty": -3},
             "Easy money. The gym felt quiet without you."),
        _opt("Kids' clinic", "A day at the gym with Lou",
             {"loyalty": 8, "fame": 2},
             "Forty kids learned a jab. Lou talked about you all week."),
        _opt("Just train", "Head down, door shut",
             {"health": 6},
             "No cameras, no kids, no cheque. Just rounds."),
    ),
    "doctor": _choice(
        lambda c: c.injury is not None,
        LOU, "Lou's table",
        "Lou looks at the damage and doesn't hide it. You could sit until it heals, or fight through.",
        _opt("Sit and heal", "The injury clears now. The hype fades",
             {"heal": True, "health": 8, "loyalty": 3, "fame": -5},
             "You healed up right. The phone was quieter when you came back."),
        _opt("Fight through it", "Keep the slot, carry the damage",
             {"fame": 5, "health": -8},
             "Lou taped it in silence. He's seen how this goes."),
        cooldown=4,
    ),
    "media_day": _choice(
        lambda c: c.rank() is not None,
        RAY, "Media day",
        "A microphone, a camera, and a question about your next opponent. What do they get?",
        _opt("Talk it up", "Sell the fight: hype and fame",
             {"fame": 8, "hype": 55.0, "loyalty": -2},
             "The clip did numbers. Ray watched it with his arms folded."),
        _opt("Respect", "Straight answers, no circus",
             {"loyalty": 5, "fame": 2},
             "No headlines. The people who matter noticed."),
        _opt("No comment", "Let the fighting talk",
             {"health": 3, "fame": -4},
             "They wrote about somebody louder. You got an early night."),
    ),
    "presser": _choice(
        lambda c: c.next_fight()[2] and not c.is_champ(),
        DEZ, "The press conference",
        "Face to face at the title press conference. The whole sport is watching. Your move.",
        _opt("Trash talk", "Light the fuse: big hype, big fame",
             {"fame": 10, "hype": 60.0, "loyalty": -3},
             "The staredown made every front page. No way back now."),
        _opt("Respect", "Calm, sharp, ready",
             {"loyalty": 6, "fame": 3, "hype": 50.0},
             "Short answers. Cold eyes. Some people found that scarier."),
        _opt("Let Ray talk", "His twenty years say it better",
             {"loyalty": 10, "hype": 45.0},
             'Ray leaned in: "My fighter does the talking Saturday." The room went quiet.'),
        cooldown=5,
    ),
}

EVERY = 3     # fights between ordinary choice cards


def _ok(c, cid):
    d = CHOICES[cid]
    return d["when"](c) and len(c.history) - c.choice_last.get(cid, -99) >= d["cooldown"]


def next_for(c):
    """The choice card the hub should deal now, or None."""
    if _ok(c, "presser"):
        return "presser"   # a title fight presser always happens
    if len(c.history) - c.last_choice < EVERY:
        return None
    due = [cid for cid in CHOICES if cid != "presser" and _ok(c, cid)]
    return c.rng.choice(due) if due else None


def apply(c, cid, k):
    """Apply option k of choice cid to the career. Returns the response line."""
    opt = CHOICES[cid]["options"][k]
    eff = opt["effects"]
    for meter in ("loyalty", "fame", "health"):
        if meter in eff:
            v = getattr(c, meter) + eff[meter]
            setattr(c, meter, max(METER_MIN, min(METER_MAX, v)))
    c.money += eff.get("money", 0)
    if eff.get("heal"):
        c.injury = None
    if "purse_mult" in eff:
        c.pending_purse = eff["purse_mult"]
    if "stamina" in eff:
        c.pending_start["stamina"] = eff["stamina"]
    if "hype" in eff:
        c.pending_start["hype"] = eff["hype"]
    c.choice_last[cid] = len(c.history)
    c.last_choice = len(c.history)
    return opt["response"]
