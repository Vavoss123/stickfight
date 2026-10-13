# Stickfight

A turn based MMA game with stick figures. Both fighters pick a move in secret, then
both moves play out at the same time. Read your opponent, manage your stamina, and win
by knockout, submission or on the scorecards.

## Download

**Windows:** grab `Stickfight.exe` from the [latest release](https://github.com/Vavoss123/stickfight/releases/latest)
and double-click it. No install needed.

Windows may say "Windows protected your PC" because the exe isn't signed. Click
**More info**, then **Run anyway**.

The game checks for updates when it starts. When a new version is out, the menu says so
and pressing **U** downloads it and restarts the game.

## Running from source

```
pip install -r requirements.txt
python main.py
```

Needs Python 3.10 or newer. Works on Windows, Mac and Linux.

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
position has its own moves. Covering up stops strikes from the top, but it is not the
only way out: in guard a sweep or get up can scramble out through the punches, under
the mount a shrimp beats punches and a bridge beats elbows, and from the bottom of back
control you can turn in while they punch. A submission starts a contest: the attacker hides a side
and the defender escapes by matching it. The rear naked choke from the back is the most
dangerous of them, and escaping it still leaves you with them on your back.

Stamina is scarce. Every move costs it, the break between rounds only gives some back,
and a tired fighter hits softer, misses more and gets taken down and submitted. A move
you do not have the stamina for still comes out, but slow and weak (it shows as GASSED).

Elbows and big shots can open cuts. Blood in the eyes hurts accuracy, and a bad enough
cut gets the fight stopped by the doctor. Between rounds your corner reads the fight
and tells you what the other guy keeps doing, what he is reading from you, and how the
round went.

Knockouts get a slow motion replay.

## Fight cards

Every fighter has a deck. Signature cards are named after the techniques fighters made
famous (Superman Punch, Showtime Kick, Calf Kick, Imanari Roll, D'Arce, Peruvian Necktie,
Twister, Gogoplata and more). Each one takes the slot of a basic move and changes how it
works, usually with a trade-off. Some swap in a different kind of move, so a grappler can
trade strikes for Guard Pull, Single Leg or a Flying Triangle. Perk cards change how you fight: Never Say Die,
Combination Puncher, Dutch Kickboxing, Iron Lungs, Granite Chin and others.

In career mode fights pay purse money, wins give a pack to pick one card from, and the
shop restocks after every fight. A duplicate levels a card up to a maximum of 3. Cards
cost deck points by rarity and the budget grows as you climb the rankings.

In quick fight and 2 player, press **Edit deck** on the select screen. Every card is
unlocked there with a 10 point budget, and the deck is remembered for that fighter.

## Feedback

Press **F1** on any screen to write a quick note. Notes go to `~/.stickfight/feedback.txt`
along with the fight situation (round, position, health, stamina and the last few moves).

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

## Releasing a new version

Push a version tag and GitHub builds the exe and publishes the release:

```
git tag v0.2.0
git push origin v0.2.0
```

The version number comes from the tag, and players on older versions get the update
prompt the next time they start the game.

## License

MIT, see [LICENSE](LICENSE).
