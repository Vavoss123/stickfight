# To do

## Now

- [ ] Play a few fights with the cards and note what feels off (pacing, AI, deck builder)
- [ ] Check the Showtime Kick against wrestlers, it tests as neutral in mirror matches

## Next

- [ ] Settings: volume, fullscreen, faster animations
- [ ] Windows .exe build so friends can play without Python
- [ ] Career story: a rival who calls you out, a training camp before title fights,
      retirement and a hall of fame
- [ ] Tournament mode: 8 fighter bracket in one night, injuries carry over
- [ ] Shared card collection: use career cards to build decks for quick fight and 2 player

## Polish

- [ ] "NEW CARD" moment when a legendary is pulled from a pack
- [ ] Show the card name in the fight when a signature move lands
- [ ] Gamepad support for 2 player
- [ ] Weight classes with different sizes, speed and power

## Later

- [ ] Online multiplayer (needs a server)

## Balance notes

- Striker is still the strongest style, around 54% against the field on hard
- KOs end about 9 to 12% of fights, submissions about 20%
- Run `python -m tools.simulate --fights 100 --level hard` and
  `python -m tools.cardsim --fights 1000` after changing any numbers
