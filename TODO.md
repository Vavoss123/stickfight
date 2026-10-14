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
