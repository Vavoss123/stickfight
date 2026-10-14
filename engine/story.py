"""The career's story: Coach Ray, and the moments worth stopping for.

Career.record_result queues story beats as they happen. The hub shows each one once.
Lines can use {name} (the player's first name), {opp} and {rival}.
"""

COACH = "Coach Ray"

BEATS = {
    "intro": [
        (COACH, "So you're {name}. I've seen a hundred kids walk in here wanting to be champion."),
        (COACH, "Most of them quit when they get punched in the mouth for the first time."),
        (COACH, "Win two fights for me and the rankings will start paying attention. Let's get to work."),
    ],
    "first_win": [
        (COACH, "That's your first one. Remember how that felt."),
        (COACH, "Spend your training points, and get in the gym this week. We're not done."),
    ],
    "first_loss": [
        (COACH, "Hey. Look at me. Everybody loses."),
        (COACH, "The ones who make it are the ones who come back and figure out why."),
        (COACH, "Watch the scouting report next time. They told us exactly what they were going to do."),
    ],
    "ranked": [
        (COACH, "Number ten in the world, {name}. They've had to put your name on the list."),
        (COACH, "From here everyone you fight is good. Every single one."),
    ],
    "rival": [
        (COACH, "{rival} is running their mouth about you. Don't take the bait."),
        (COACH, "We'll get them in the cage soon enough. Then you can answer."),
    ],
    "title_shot": [
        (COACH, "This is it. A title shot."),
        (COACH, "I've waited twenty years to walk a fighter out for one of these."),
        (COACH, "Pick a camp, stick to the plan, and whatever happens, don't stop moving forward."),
    ],
    "champion": [
        (COACH, "Champion of the world."),
        (COACH, "..."),
        (COACH, "Now everybody wants what you've got. Let's go and keep it."),
    ],
    "lost_belt": [
        (COACH, "It hurts. It's supposed to hurt."),
        (COACH, "You were the best in the world once. We'll get back there."),
    ],
    "losing_streak": [
        (COACH, "Three in a row. Sit down, we need to talk."),
        (COACH, "Change something. Your deck, your camp, the way you start fights. Anything."),
        (COACH, "If we keep doing the same thing we're going to keep getting the same result."),
    ],
    "defences": [
        (COACH, "Three title defences. People are starting to say your name with the greats."),
        (COACH, "Don't listen to them yet."),
    ],
}


def lines(beat, player, rival=None, opp=None):
    first = player.name.split()[0]
    out = []
    for who, text in BEATS[beat]:
        out.append((who, text.format(name=first, rival=rival or "Your rival", opp=opp or "them")))
    return out


def after_fight(c, won, draw, was_champ, was_ranked, losses_in_a_row):
    """Story beats a result has earned, that have not been seen yet."""
    beats = []
    if won and c.player.wins == 1:
        beats.append("first_win")
    if not won and not draw and c.player.losses == 1:
        beats.append("first_loss")
    if not was_ranked and c.rank() is not None:
        beats.append("ranked")
    if c.is_champ() and not was_champ:
        beats.append("champion")
    if was_champ and not c.is_champ():
        beats.append("lost_belt")
    if losses_in_a_row == 3:
        beats.append("losing_streak")
    if c.defenses == 3:
        beats.append("defences")
    if c.rival and "rival" not in c.story_seen:
        beats.append("rival")
    nxt = c.next_fight()
    if nxt[2] and not c.is_champ():
        beats.append("title_shot")
    return [b for b in beats if b not in c.story_seen or b in ("losing_streak",)]
