# To do

## Now

- [ ] Play a few fights with the cards and note what feels off (pacing, AI, deck builder).
      Press F1 in game to write a note, they land in ~/.stickfight/feedback.txt
- [x] Check the Showtime Kick, it was losing mirror matches
- [x] Edit decks before quick fight and 2 player
- [x] Penalty for moves thrown with no stamina (GASSED)
- [x] Ways out from under ground and pound besides covering up

## Next

- [x] Settings: volume, fullscreen, faster animations
- [x] Windows .exe build so friends can play without Python (GitHub release + in-game updater)
- [x] Career story: a rival who calls you out, a training camp before title fights,
      retirement and a hall of fame
- [x] Tournament mode: 8 fighter bracket in one night, injuries carry over
- [x] Shared card collection: use career cards to build decks for quick fight and 2 player

## Playtest feedback (Oct 2026)

- [x] What beats what diagram during fights (Settings can hide it)
- [x] Deck screen: active deck strip, click a card to see its replacements, smaller cards
- [x] Spare training points: 5 for a deck point, 3 for a card pack
- [x] Shop and packs say whether a card is in your deck and what level it goes to
- [x] Bug: maxed cards could still be bought. They leave the shop now
- [x] Training camp still helps a maxed fighter (stat to 11, or film study)
- [x] Deck costs by tested strength, not rarity (POINTS in engine/cards.py)
- [x] Max card level 5, seven new perks
- [x] Money sinks: training points, deck points, restock, glove colours

## Third round (Oct 2026)

- [x] Renamed to USC, the Ultimate Stickfight Championship, with a logo
- [x] Fighters stand higher so the ground game is not hidden by the move bar
- [x] Ground counters, blocks and hits use ground poses; flying triangles look like a guard
- [x] Hover the bars and tags in a fight to see what they mean
- [x] Judging: damage and strikes first, control counts less (a takedown 4, control 1.1 an exchange, was 5 and 1.5)
- [x] Round summary says who the judges saw it for and why, result shows each judge's rounds
- [x] Speech bubbles for what fighters say
- [x] The tutorial gives no achievements
- [x] Shorter How to play

## Second round of ideas (Oct 2026)

- [x] Gym mini game: pad work, price grows with your deck, a deck point for a good session
- [x] Story: Coach Ray at the big career moments
- [x] Trophies button on the career hub
- [x] Cracked ribs and broken legs at 100% body or leg damage
- [x] Check kick separate from block and counter, and it hurts the kicker
- [x] Moves laid out by target (head, body, legs, arms, neck), armbar added
- [x] Knee counters a takedown hard, jab never stops one
- [x] Blocking hurts the arms, weave move
- [x] Perks on a maxed stat go past 10 (up to 12)
- [x] Hover a stat to see what a point does

## Roadmap (from the Oct 2026 plan)

- [x] Between round card swaps, two a break, with coach suggestions
- [x] Scouting report before career fights, what to expect in quick fight and tournaments
- [x] Contextual dialogue by personality: hurt, tired, takedowns, subs, momentum, last round
- [ ] Deeper character customisation (more stats, abilities, signature styles)
- [ ] Career: more progression, training choices and unlocks
- [ ] Grappling polish and balance
- [ ] Online PvP with your own fighter and deck (needs a server)

## Making it more fun for other people

- [x] Interactive tutorial (press T on the menu)
- [x] Momentum: hype meter, all in attacks, booing for stalling
- [x] AI personalities with walkout quotes and taunts
- [x] Mind games: feints and follow up combos
- [x] Fight variety: fouls and point deductions, ref breaking up the clinch, slow motion on big shots
- [x] Reasons to come back: daily challenge, achievements, unlockable fighters
- [x] Get it seen: KO replay GIF in the README, Mac and Linux builds
- [ ] Make the itch.io page and add the BUTLER_API_KEY secret (text is in docs/itch.md)
- [ ] Try the Mac and Linux builds on a real machine

## Polish

- [x] "NEW CARD" moment when a legendary is pulled from a pack
- [x] Show the card name in the fight when a signature move lands
- [x] Gamepad support for 2 player (needs testing with a real controller)
- [x] Weight classes with different sizes, speed and power

## Later

- [ ] Online multiplayer (needs a server)

## Balance notes

- Judging at takedown 4, control 1.1: BJJ 50%, Striker 51%, Brawler 50%, Wrestler 46%.
  Control at 0.6 dropped wrestlers to 42%. Harder ground strikes did not help them

- After knee, check, weave, arms and limb TKOs (1800 fights on hard): BJJ 51%, Striker 50%,
  Wrestler 48%, Brawler 48%. Subs 25%, KOs 11%, broken legs and cracked ribs under 1%.
  The knee only beats takedowns (punches and tying up beat it) or the AI spammed it and
  grapplers fell to 37%. BJJ grappling is back to 10

- After feints, fouls and referee breaks (3600 fights on hard): Striker 54%, BJJ 48%,
  Brawler 47%, Wrestler 46%. Strikers are a touch ahead again, worth a look after playtesting

- Momentum fills about 1.3 times a fight between two hard AIs. Turning it off moves the
  styles by about 2 points, inside the noise
- Personalities against a balanced AI in mirror matches: pressure 46%, showboat 50%,
  counter 53%, grinder 52%. Nudges live in engine/personality.py

- Styles on hard: BJJ 52%, Wrestler 51%, Striker 49%, Brawler 45% (Oct 2026)
- Weight classes: KOs go from about 7% at lightweight to 12% at heavyweight. Across
  classes in mirror matches welter beats light 54%, heavy beats middle 68%, heavy beats
  light 76% (SIZE_* in engine/weights.py)
- KOs end about 8% of fights, submissions about 23%
- Showtime Kick: costs 8 now with less KO power (51% in mirror matches). At 12 the AI
  chased the knockout and gassed itself out
- Run `python -m tools.simulate --fights 100 --level hard` and
  `python -m tools.cardsim --fights 1000` after changing any numbers
