"""The career's story: the people around the gym, and the moments worth stopping for.

Beats are data. Each has a condition on the career, one or more scripts (rotated, so a
repeat never reads the same twice in a row), and whether it can come back. Career.record_result
queues the beats a result has earned; the hub shows each one once.
Lines can use {name} (the player's first name), {opp}, {rival} and {champ}.
"""

RAY = "Coach Ray"
LOU = "Lou"
DEZ = "Dez Harlan"
COACH = RAY   # the old name, kept for anything still importing it

# How each character looks on the story stage: body colour and hand colour
CHARACTERS = {
    RAY: ((60, 60, 70), (120, 120, 130)),
    LOU: ((110, 80, 55), (235, 225, 210)),
    DEZ: ((34, 36, 46), (240, 196, 60)),
}


def _beat(when, *scripts, repeat=False):
    return {"when": when, "scripts": scripts, "repeat": repeat}


# In queue order. "intro" is queued once when a career starts, so its condition is never.
BEATS = {
    "intro": _beat(
        lambda c, x: False,
        ((RAY, "So you're {name}. A hundred kids walk in here wanting to be champion."),
         (RAY, "Most of them quit the first time they get hit properly."),
         (RAY, "See that letter by the door? Three months of rent. Three."),
         (RAY, "Win me three fights and the lights stay on. Then we talk rankings.")),
    ),
    "first_win": _beat(
        lambda c, x: x["won"] and c.player.wins == 1,
        ((RAY, "That's one. Remember how it felt."),
         (LOU, "Name's Lou. Cuts, tape and the truth. You dropped your right twice out there."),
         (RAY, "Listen to him. He's patched up every fighter I've ever had."),
         (RAY, "Spend your points and get in the gym. Two more for the rent.")),
    ),
    "first_loss": _beat(
        lambda c, x: not x["won"] and not x["draw"] and c.player.losses == 1,
        ((RAY, "Hey. Look at me. Everybody loses."),
         (RAY, "The ones who make it are the ones who come back and figure out why."),
         (RAY, "Watch the scouting report next time. They told us exactly what they were going to do.")),
    ),
    "dez": _beat(
        lambda c, x: x["won"] and c.player.wins == 2,
        ((DEZ, "Dez Harlan. I put on the fights people pay to see."),
         (DEZ, "Two wins out of a dead gym. That's a story, and stories sell tickets."),
         (DEZ, "Keep winning, kid. There's real money where you're heading. Call me."),
         (RAY, "He said all that to my last champion too. Count your fingers after you shake.")),
    ),
    "rent_paid": _beat(
        lambda c, x: x["won"] and c.player.wins == 3,
        ((RAY, "Three. The rent's paid through the winter."),
         (LOU, "He framed the eviction letter. Won't say why, but he's proud of you."),
         (RAY, "Don't get comfortable. A paid-up gym never won anybody a belt.")),
    ),
    "ranked": _beat(
        lambda c, x: not x["was_ranked"] and c.rank() is not None,
        ((RAY, "Number ten in the world, {name}. They had to print your name."),
         (LOU, "There's a new sign going up out front. First one in twenty years."),
         (RAY, "From here, everyone you fight is good. Every single one.")),
    ),
    "rival": _beat(
        lambda c, x: c.rival is not None,
        ((RAY, "{rival} is running their mouth about you. Don't take the bait."),
         (RAY, "We'll get them in the cage soon enough. Then you can answer.")),
    ),
    "title_shot": _beat(
        lambda c, x: c.next_fight()[2] and not c.is_champ(),
        ((RAY, "This is it. {champ}, for the title."),
         (RAY, "Twenty years I've waited to walk someone out for one of these."),
         (RAY, "Pick a camp, stick to the plan, and don't stop moving forward.")),
    ),
    "champion": _beat(
        lambda c, x: c.is_champ() and not x["was_champ"],
        ((RAY, "Champion of the world."),
         (RAY, "..."),
         (LOU, "That's the first time I've seen him cry since the nineties."),
         (RAY, "Now everybody wants what you've got. Let's go and keep it.")),
    ),
    "lost_belt": _beat(
        lambda c, x: x["was_champ"] and not c.is_champ(),
        ((RAY, "It hurts. It's supposed to hurt."),
         (RAY, "You were the best in the world once. We'll get back there.")),
    ),
    "losing_streak": _beat(
        lambda c, x: x["streak"] == 3,
        ((RAY, "Three in a row. Sit down, we need to talk."),
         (RAY, "Change something. Your deck, your camp, the way you start fights. Anything."),
         (RAY, "Keep doing the same thing and we keep getting the same result.")),
        ((RAY, "Three in a row again. I'm not going to shout."),
         (LOU, "Your body's telling you something, kid. It costs nothing to listen."),
         (RAY, "Change one real thing before the next one. Deck, camp, anything.")),
        repeat=True,
    ),
    "defences": _beat(
        lambda c, x: c.defenses == 3,
        ((RAY, "Three title defences. People are starting to say your name with the greats."),
         (RAY, "Don't listen to them yet.")),
    ),
}


def repeats(beat):
    """Whether a beat can be shown again after it has been seen."""
    return BEATS[beat]["repeat"]


def lines(beat, player, rival=None, opp=None, champ=None):
    """The beat's script as (speaker, line) pairs, names filled in."""
    scripts = BEATS[beat]["scripts"]
    script = scripts[(player.wins + player.losses) % len(scripts)]
    first = player.name.split()[0] if player.name else "kid"
    return [(who, t.format(name=first, rival=rival or "Your rival",
                           opp=opp or "them", champ=champ or "the champ"))
            for who, t in script]


def after_fight(c, won, draw, was_champ, was_ranked, losses_in_a_row):
    """Story beats a result has earned, that have not been seen yet."""
    x = {"won": won, "draw": draw, "was_champ": was_champ, "was_ranked": was_ranked,
         "streak": losses_in_a_row}
    return [b for b, d in BEATS.items()
            if (b not in c.story_seen or d["repeat"]) and d["when"](c, x)]
