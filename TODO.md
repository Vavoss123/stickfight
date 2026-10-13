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
- [ ] Shared card collection: use career cards to build decks for quick fight and 2 player
      (quick fight decks exist now, with every card unlocked)

## Polish

- [x] "NEW CARD" moment when a legendary is pulled from a pack
- [x] Show the card name in the fight when a signature move lands
- [x] Gamepad support for 2 player (needs testing with a real controller)
- [ ] Weight classes with different sizes, speed and power

## Later

- [ ] Online multiplayer (needs a server)

## Balance notes

- Styles on hard: BJJ 52%, Wrestler 51%, Striker 49%, Brawler 45% (Oct 2026)
- KOs end about 8% of fights, submissions about 23%
- Showtime Kick: costs 8 now with less KO power (51% in mirror matches). At 12 the AI
  chased the knockout and gassed itself out
- Run `python -m tools.simulate --fights 100 --level hard` and
  `python -m tools.cardsim --fights 1000` after changing any numbers
