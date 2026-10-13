# Stickfight

A turn based MMA game with stick figures. Both fighters pick a move in secret, then
both moves play out at the same time. Read your opponent, manage your stamina, and win
by knockout, submission or on the scorecards.

## Running it

```
pip install -r requirements.txt
python main.py
```

Needs Python 3.10 or newer.

## Modes

- **Quick fight** against the computer on easy, normal or hard.
- **Local 2 player** on one keyboard. Red uses Q W E R A S D F, blue uses U I O P J K L ;
  Picks stay hidden until both players have locked in.
- **Career**. Create a fighter, beat two prospects to get ranked, climb the top 10,
  win the belt and defend it. Wins earn training points to spend on your stats.
  Your career is saved in `~/.stickfight/career.json`.

## How fights work

Every move is a Strike, a Grapple, a Submission or a Defend.

- Strike beats Grapple, you catch them coming in.
- Grapple beats Defend, they are standing still.
- Defend beats Strike, you block and counter.

On the feet there are a few twists. A jab is fast and beats a power punch to the punch.
A takedown walks through jabs, body shots and kicks but gets stopped by a power punch.
Clinching smothers a power punch. A leg kick goes under a block, a head kick does not.

Strikes hit the head, body or legs. Head shots do the damage. Body shots drain stamina
and slow its recovery, and enough of them can fold a fighter. Leg kicks take away power
and wrestling, and a fighter past 60% leg damage starts limping.

The fight moves between standing, the clinch, guard, mount and back control. Each
position has its own moves. A submission starts a contest: the attacker hides a side
and the defender escapes by matching it. The rear naked choke from the back is the most
dangerous of them, and escaping it still leaves you with them on your back.

Stamina is scarce. Every move costs it, the break between rounds only gives some back,
and a tired fighter hits softer, misses more and gets taken down and submitted.

Elbows and big shots can open cuts. Blood in the eyes hurts accuracy, and a bad enough
cut gets the fight stopped by the doctor. Between rounds your corner reads the fight
and tells you what the other guy keeps doing, what he is reading from you, and how the
round went.

Knockouts get a slow motion replay.

## Fight cards

Every fighter has a deck. Signature cards are named after the techniques fighters made
famous (Superman Punch, Showtime Kick, Calf Kick, Imanari Roll, D'Arce, Peruvian Necktie,
Twister, Gogoplata and more). Each one takes the slot of a basic move and changes how it
works, usually with a trade-off. Perk cards change how you fight: Never Say Die,
Combination Puncher, Dutch Kickboxing, Iron Lungs, Granite Chin and others.

In career mode fights pay purse money, wins give a pack to pick one card from, and the
shop restocks after every fight. A duplicate levels a card up to a maximum of 3. Cards
cost deck points by rarity and the budget grows as you climb the rankings. Quick fight
and 2 player use each fighter's preset deck, which shows on the select screen.

Fights are 3 rounds of 8 exchanges (title fights are 5 rounds). Three judges score each
round on damage, takedowns, control time, submission attempts and knockdowns.

## Project layout

```
engine/      game rules, no pygame (fighters, moves, resolving exchanges, AI, career)
ui/          pygame drawing: stick figures, poses, the arena, screens
tools/       balance simulator
tests/       engine tests
```

All move numbers live in `engine/moves.py` and the fighter styles in `engine/roster.py`.

## Balancing

The simulator plays thousands of AI vs AI fights and reports win rates by style, how
fights end, and how often each move is picked and works:

```
python -m tools.simulate --fights 100 --level hard
```

The card tester puts one card on a fighter and plays mirror matches against the same
fighter without it, to find cards that are too strong or too weak:

```
python -m tools.cardsim --fights 1000
```

## Tests

```
python -m unittest discover tests
```
