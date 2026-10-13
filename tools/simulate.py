"""Run AI vs AI fights and print a balance report.

    python -m tools.simulate --fights 200 --level normal
"""

import argparse
import os
import sys
import time
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.ai import AI
from engine.fight import Fight
from engine.cards import CARDS
from engine.moves import MOVES
from engine.roster import quick_fighters


def run_fight(p0, p1, level, seed):
    fight = Fight(p0, p1, seed=seed)
    ais = [AI(level, seed=seed * 2 + 1), AI(level, seed=seed * 2 + 2)]
    picks_used = []
    while not fight.over:
        if fight.between_rounds:
            fight.start_next_round()
            continue
        st = fight.state
        picks = (ais[0].choose(fight, 0), ais[1].choose(fight, 1))
        ais[0].observe(st, 1, picks[1])
        ais[1].observe(st, 0, picks[0])
        ex = fight.play(picks)
        if not ex.in_sub:
            for i in (0, 1):
                picks_used.append((picks[i], ex.success[i]))
    return fight, picks_used


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fights", type=int, default=100, help="fights per matchup")
    ap.add_argument("--level", default="normal")
    args = ap.parse_args()

    roster = quick_fighters()
    wins = defaultdict(lambda: [0, 0, 0])
    methods = Counter()
    finish_rounds = Counter()
    move_count = Counter()
    move_ok = Counter()
    arch_w = Counter()
    arch_n = Counter()
    t0 = time.time()
    seed = 1
    for a in roster:
        for b in roster:
            if a is b:
                continue
            for _ in range(args.fights):
                fight, used = run_fight(a, b, args.level, seed)
                seed += 1
                r = fight.result
                methods[r.method if r.method != "Decision" else r.detail] += 1
                if r.method in ("KO", "TKO", "Submission"):
                    finish_rounds[r.round] += 1
                key = (a.archetype, b.archetype)
                if r.winner is None:
                    wins[key][2] += 1
                else:
                    wins[key][r.winner] += 1
                    arch_w[(a, b)[r.winner].archetype] += 1
                arch_n[a.archetype] += 1
                arch_n[b.archetype] += 1
                for k, ok in used:
                    move_count[k] += 1
                    move_ok[k] += ok

    total = sum(methods.values())
    print(f"{total} fights in {time.time() - t0:.1f}s, level {args.level}\n")
    print("Archetype win rate")
    for k in sorted(arch_n):
        print(f"  {k:9s} {100 * arch_w[k] / arch_n[k]:5.1f}%")
    print("\nMatchups (row beats column, as red corner)")
    archs = [f.archetype for f in roster]
    print("           " + "".join(f"{x:>10s}" for x in archs))
    for x in archs:
        row = f"  {x:9s}"
        for y in archs:
            if x == y:
                row += f"{'-':>10s}"
            else:
                w0, w1, d = wins[(x, y)]
                row += f"{100 * w0 / max(1, w0 + w1 + d):9.0f}%"
        print(row)
    print("\nHow fights end")
    for k, v in methods.most_common():
        print(f"  {k:22s} {100 * v / total:5.1f}%")
    print("  finishes by round: " + ", ".join(f"R{r} {finish_rounds[r]}" for r in sorted(finish_rounds)))
    print("\nMoves (share of picks, success rate)")
    picks = sum(move_count.values())
    for k, n in move_count.most_common():
        name = (MOVES.get(k) or CARDS[k].move).name
        print(f"  {name:20s} {100 * n / picks:5.1f}%   {100 * move_ok[k] / n:5.1f}%")


if __name__ == "__main__":
    main()
