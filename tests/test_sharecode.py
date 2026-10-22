import os
import tempfile
import unittest

from engine import sharecode
from engine.career import Career, new_player
from engine.cards import CARDS
from engine.constants import STAT_MAX
from engine.sharecode import CodeError, decode, encode


def fighter():
    c = Career(new_player("Sam Okoro", "The Hammer", "Wrestler", (60, 190, 110), "Lagos"), seed=1)
    p = c.player
    p.look = {"skin": 3, "hair": "afro", "hair_color": 1, "beard": True, "trim": 2, "tattoo": "full"}
    p.personality = "headhunter"
    p.wins, p.losses, p.draws = 7, 2, 1
    return p


class Codes(unittest.TestCase):
    def test_round_trip(self):
        p = fighter()
        q = decode(encode(p))
        for k in ("name", "nickname", "hometown", "archetype", "weight", "personality", "height",
                  "color", "look", "deck", "perks", "wins", "losses", "draws"):
            self.assertEqual(getattr(q, k), getattr(p, k), k)
        self.assertEqual(q.stats, p.stats)
        for cid in list(p.deck.values()) + p.perks:
            self.assertEqual(q.cards[cid], p.cards[cid])

    def test_codes_are_forgiving_to_type(self):
        code = encode(fighter())
        messy = "  " + code.lower().replace("-", " ").replace("1", "l").replace("0", "o") + " "
        self.assertEqual(decode(messy).name, "Sam Okoro")

    def test_a_typo_is_caught(self):
        code = encode(fighter())
        k = len(code) // 2
        swapped = code[:k] + ("A" if code[k] != "A" else "B") + code[k + 1:]
        with self.assertRaises(CodeError):
            decode(swapped)

    def test_cut_short_and_junk(self):
        code = encode(fighter())
        for bad in (code[:20], "", "hello!!", "USC"):
            with self.assertRaises(CodeError):
                decode(bad)

    def test_stats_cannot_be_pushed_past_the_max(self):
        p = fighter()
        p.stats.striking = 99
        self.assertLessEqual(decode(encode(p)).stats.striking, STAT_MAX)

    def test_card_hashes_do_not_collide(self):
        hashes = [sharecode._h(k) for k in CARDS]
        self.assertEqual(len(hashes), len(set(hashes)))

    def test_an_unknown_card_is_dropped_not_fatal(self):
        """A code from a version with a card this one does not have still reads."""
        from unittest import mock
        p = fighter()
        code = encode(p)
        gone = next(iter(p.deck.values()))
        fewer = {k: v for k, v in CARDS.items() if k != gone}
        with mock.patch.object(sharecode, "CARDS", fewer):
            q = decode(code)
        self.assertEqual(q.name, p.name)
        self.assertNotIn(gone, q.deck.values())


class Friends(unittest.TestCase):
    def test_add_list_and_forget(self):
        path = os.path.join(tempfile.mkdtemp(), "friends.json")
        p = fighter()
        sharecode.add_friend(encode(p), path)
        sharecode.add_friend(encode(p), path)          # the same fighter twice stays once
        self.assertEqual([f.name for _, f in sharecode.load_friends(path)], ["Sam Okoro"])
        sharecode.remove_friend("Sam Okoro", path)
        self.assertEqual(sharecode.load_friends(path), [])

    def test_a_bad_code_is_not_saved(self):
        path = os.path.join(tempfile.mkdtemp(), "friends.json")
        with self.assertRaises(CodeError):
            sharecode.add_friend("USC-NOPE", path)
        self.assertEqual(sharecode.load_friends(path), [])


class Effects(unittest.TestCase):
    def test_every_popup_word_is_explained(self):
        import re
        from ui import effects
        with open(os.path.join(os.path.dirname(__file__), "..", "ui", "scenes", "fight.py"),
                  encoding="utf-8") as f:
            src = f.read()
        words = set(re.findall(r'self\.popup\([^,]+, "([A-Z !\']+)"', src))
        skip = {"BODY", "LEG", "TAP!", "HOLDING", "LEG!"}
        for w in words - skip:
            self.assertIsNotNone(effects.key(w), w)
        for k in effects.MAIN:
            self.assertIn(k, effects.EFFECTS)


if __name__ == "__main__":
    unittest.main()
