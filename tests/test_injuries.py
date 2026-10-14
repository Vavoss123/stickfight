import unittest

from engine.cards import build_kit
from engine.career import Career, new_player, PURSES


def career(personality="", seed=1):
    c = Career(new_player("Test Fighter", "", "Wrestler", (60, 190, 110), ""), seed=seed)
    c.player.personality = personality
    c.money = 50000
    return c


class Injuries(unittest.TestCase):
    def test_a_ko_loss_sends_a_bill_and_hurts_the_chin(self):
        c = career("grinder")
        opp = c.next_fight()[0]
        before = c.money
        r = c.record_result(opp, False, False, "KO", "Punch", 1)
        self.assertGreater(r["bill"], 0)
        self.assertEqual(c.money, before + r["purse"] - r["bill"])
        self.assertEqual(c.injury["stats"]["chin"], 2)
        chin = c.player.stats.chin
        self.assertEqual(build_kit(c.fighter_for_fight()).stats.chin, max(1, chin - 2))

    def test_injuries_heal_after_their_fights(self):
        c = career("grinder")
        c.record_result(c.next_fight()[0], False, False, "Decision", "", 3)
        self.assertEqual(c.injury["fights"], 1)
        c.record_result(c.next_fight()[0], True, False, "Decision", "", 3)
        self.assertIsNone(c.injury)

    def test_wins_cost_nothing(self):
        c = career()
        r = c.record_result(c.next_fight()[0], True, False, "KO", "Punch", 1)
        self.assertEqual(r["bill"], 0)
        self.assertIsNone(c.injury)

    def test_the_bill_never_takes_you_below_zero(self):
        c = career()
        c.money = 0
        c.record_result(c.next_fight()[0], False, False, "KO", "Punch", 1)
        self.assertGreaterEqual(c.money, 0)

    def test_a_bad_ko_can_cost_chin_for_good(self):
        lost = 0
        for seed in range(40):
            c = career("grinder", seed)
            chin = c.player.stats.chin
            r = c.record_result(c.next_fight()[0], False, False, "KO", "Punch", 1)
            lost += c.player.stats.chin < chin
            self.assertEqual(bool(r["permanent"]), c.player.stats.chin < chin)
        self.assertTrue(0 < lost < 40)

    def test_physio_heals_now(self):
        c = career("grinder")
        c.record_result(c.next_fight()[0], False, False, "KO", "Punch", 1)
        price = c.rehab_price()
        money = c.money
        self.assertTrue(c.rehab())
        self.assertIsNone(c.injury)
        self.assertEqual(c.money, money - price)

    def test_injury_survives_a_save(self):
        c = career("grinder")
        c.record_result(c.next_fight()[0], False, False, "TKO", "Punch", 1)
        self.assertEqual(Career.from_dict(c.to_dict()).injury, c.injury)


class CareerPerks(unittest.TestCase):
    def test_counter_punchers_shrug_off_a_decision(self):
        c = career("counter")
        c.record_result(c.next_fight()[0], False, False, "Decision", "", 3)
        self.assertIsNone(c.injury)

    def test_balanced_pays_smaller_bills(self):
        a, b = career("balanced"), career("grinder")
        ra = a.record_result(a.next_fight()[0], False, False, "TKO", "Punch", 1)
        rb = b.record_result(b.next_fight()[0], False, False, "TKO", "Punch", 1)
        self.assertLess(ra["bill"], rb["bill"])

    def test_showboat_purse_is_bigger(self):
        c = career("showboat")
        r = c.record_result(c.next_fight()[0], True, False, "Decision", "", 3)
        self.assertEqual(r["purse"], int(PURSES["prospect"][0] * 1.15))


if __name__ == "__main__":
    unittest.main()
