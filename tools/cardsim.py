"""How strong is each card on its own?

Mirror matches: the same fighter twice, one side with a single card equipped at
level 1, the other with no cards. A fair card wins somewhere around 52 to 60 percent.

    python -m tools.cardsim --fights 100
"""

import argparse
import copy
import os
import sys
from multiprocessing import Pool

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.ai import AI
from engine.cards import CARDS, group_of
from engine.fight import Fight
from engine.roster import make

STYLE_FOR_GROUP = {"Standing": "Striker", "Clinch": "Brawler", "Ground top": "Wrestler",
                   "Ground bottom": "BJJ"}


def _one(args):
    """One fight. Returns 1 if the side with the card won, 0.5 for a draw, else 0."""
    a, b, seed, card_red, level = args
    p0, p1 = (a, b) if card_red else (b, a)
    f = Fight(copy.deepcopy(p0), copy.deepcopy(p1), seed=seed)
    ais = [AI(level, seed=seed * 3 + 1), AI(level, seed=seed * 3 + 2)]
    while not f.over:
        if f.between_rounds:
            f.start_next_round()
            continue
        st = f.state
        picks = (ais[0].choose(f, 0), ais[1].choose(f, 1))
        ais[0].observe(st, 1, picks[1])
        ais[1].observe(st, 0, picks[0])
        f.play(picks)
    w = f.result.winner
    if w is None:
        return 0.5
    return 1.0 if (w == 0) == card_red else 0.0


def duel(card, fights, level, pool=None):
    if card.is_perk:
        style = "Striker"
        deck, perks = {}, [card.id]
    else:
        style = STYLE_FOR_GROUP[group_of(card.move.base)]
        deck, perks = {card.move.base: card.id}, []
    a = make("A", "", style, cards=(deck, perks, 1))
    b = make("B", "", style, cards=({}, [], 1))
    # Every seed is played from both corners, which cancels out corner luck
    jobs = [(a, b, seed, red, level) for seed in range(fights // 2) for red in (True, False)]
    results = pool.map(_one, jobs, chunksize=8) if pool else list(map(_one, jobs))
    return 100 * sum(results) / len(results)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fights", type=int, default=100)
    ap.add_argument("--level", default="normal")
    ap.add_argument("--jobs", type=int, default=os.cpu_count())
    ap.add_argument("--only", nargs="*", help="card ids to test, default all")
    args = ap.parse_args()
    rows = []
    err = 100 * 0.5 / (args.fights ** 0.5)
    print(f"{args.fights} fights per card, margin of error about +/-{2 * err:.0f} points")
    with Pool(args.jobs) as pool:
        for card in CARDS.values():
            if args.only and card.id not in args.only:
                continue
            rows.append((duel(card, args.fights, args.level, pool), card))
            print(f"  {card.name:22s} {rows[-1][0]:5.1f}%", flush=True)
    print("\nStrongest to weakest")
    for pct, card in sorted(rows, key=lambda r: -r[0]):
        flag = "  too strong?" if pct > 64 else "  too weak?" if pct < 47 else ""
        print(f"  {card.name:22s} {card.rarity:9s} {pct:5.1f}%{flag}")


if __name__ == "__main__":
    main()
