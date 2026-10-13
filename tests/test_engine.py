import os
import random
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.ai import AI
from engine.career import Career, new_player
from engine.constants import STANDING, CLINCH, GUARD, MOUNT, BACK, SUB_TAP
from engine.fight import Fight
from engine.fighter import FighterState
from engine.moves import MOVES, MOVESETS, matchup
from engine.resolve import resolve
from engine.roster import quick_fighters
from engine.state import FightState, SubState


def fresh(pos=STANDING, top=None):
    r = quick_fighters()
    return FightState([FighterState(r[0]), FighterState(r[1])], pos, top)


class Matchups(unittest.TestCase):
    def test_triangle(self):
        self.assertEqual(matchup(MOVES["cross"], MOVES["takedown"]), 1)
        self.assertEqual(matchup(MOVES["takedown"], MOVES["block"]), 1)
        self.assertEqual(matchup(MOVES["block"], MOVES["cross"]), 1)
        self.assertEqual(matchup(MOVES["jab"], MOVES["cross"]), 0)

    def test_overrides_both_ways(self):
        self.assertEqual(matchup(MOVES["kick"], MOVES["takedown"]), -1)
        self.assertEqual(matchup(MOVES["takedown"], MOVES["kick"]), 1)
        self.assertEqual(matchup(MOVES["jab"], MOVES["takedown"]), -1)
        self.assertEqual(matchup(MOVES["clinch"], MOVES["cross"]), 1)
        self.assertEqual(matchup(MOVES["legkick"], MOVES["block"]), 1)
        self.assertEqual(matchup(MOVES["kick"], MOVES["block"]), -1)
        self.assertEqual(matchup(MOVES["takedown"], MOVES["body"]), 1)

    def test_every_moveset_key_exists(self):
        for keys in MOVESETS.values():
            for k in keys:
                self.assertIn(k, MOVES)


class Resolve(unittest.TestCase):
    def test_block_stops_power_punch(self):
        for seed in range(50):
            st = fresh()
            ex = resolve(st, ("block", "cross"), random.Random(seed))
            self.assertTrue(ex.blocked[0])
            self.assertFalse(ex.landed[1])

    def test_takedown_beats_block_most_of_the_time(self):
        wins = 0
        for seed in range(200):
            st = fresh()
            resolve(st, ("block", "takedown"), random.Random(seed))
            wins += st.pos == GUARD and st.top == 1
        self.assertGreater(wins, 120)

    def test_mutual_standup_goes_to_feet(self):
        st = fresh(GUARD, 0)
        resolve(st, ("standup", "getup"), random.Random(1))
        self.assertEqual(st.pos, STANDING)

    def test_pass_reaches_mount(self):
        st = fresh(GUARD, 0)
        resolve(st, ("pass", "cover"), random.Random(3))
        self.assertIn(st.pos, (GUARD, MOUNT))

    def test_submission_can_tap(self):
        st = fresh(GUARD, 1)
        st.sub = SubState(0, "triangle", SUB_TAP - 1)
        ex = None
        for seed in range(100):
            s2 = st.clone()
            ex = resolve(s2, ("left", "right"), random.Random(seed))
            if ex.finish:
                break
        self.assertEqual(ex.finish[0], 0)
        self.assertEqual(ex.finish[1], "Submission")

    def test_matching_side_loosens_hold(self):
        st = fresh(GUARD, 1)
        st.sub = SubState(0, "triangle", 1)
        ex = resolve(st, ("left", "left"), random.Random(0))
        self.assertEqual(ex.sub_result, "escaped")
        self.assertIsNone(st.sub)

    def test_failed_guillotine_puts_attacker_on_bottom(self):
        st = fresh(CLINCH)
        st.sub = SubState(0, "guillotine", 1)
        resolve(st, ("squeeze", "squeeze"), random.Random(0))
        self.assertEqual((st.pos, st.top), (GUARD, 1))

    def test_clone_is_independent(self):
        st = fresh()
        c = st.clone()
        c.f[0].hp = 1
        c.pos = MOUNT
        self.assertEqual(st.f[0].hp, 100)
        self.assertEqual(st.pos, STANDING)


class Targets(unittest.TestCase):
    def test_body_shots_drain_stamina_more_than_head_shots(self):
        drained = {"body": [], "jab": []}
        for seed in range(100):
            for k in drained:
                st = fresh()
                ex = resolve(st, (k, "cross"), random.Random(seed))
                if ex.landed[0]:
                    drained[k].append(100 - st.f[1].stamina)
        avg = {k: sum(v) / len(v) for k, v in drained.items()}
        self.assertGreater(avg["body"], avg["jab"] + 3)

    def test_leg_kicks_build_up_and_cost_power(self):
        st = fresh()
        for seed in range(30):
            resolve(st, ("legkick", "block"), random.Random(seed))
            st.f[1].stamina = 100
        self.assertGreaterEqual(st.f[1].legs, 60)
        self.assertLess(st.f[1].mobility(), 0.8)

    def test_body_damage_slows_recovery(self):
        st = fresh()
        st.f[0].stamina = st.f[1].stamina = 50
        st.f[1].body = 80
        st.f[0].spend(-10)
        st.f[1].spend(-10)
        self.assertGreater(st.f[0].stamina, st.f[1].stamina)


class Cuts(unittest.TestCase):
    def test_elbows_open_cuts(self):
        cuts = 0
        for seed in range(200):
            st = fresh(GUARD, 0)
            ex = resolve(st, ("elbows", "getup"), random.Random(seed))
            cuts += ex.cut_opened[1]
        self.assertGreater(cuts, 10)

    def test_bad_cut_can_bring_the_doctor(self):
        stopped = 0
        for seed in range(100):
            st = fresh()
            st.f[1].cut = 90
            ex = resolve(st, ("jab", "cross"), random.Random(seed))
            if ex.finish and ex.finish[2].startswith("Doctor"):
                stopped += 1
        self.assertGreater(stopped, 10)

    def test_cutman_closes_the_cut_between_rounds(self):
        r = quick_fighters()
        f = Fight(r[0], r[1], seed=1)
        f.state.f[0].cut = 40
        f.between_rounds = True
        f.start_next_round()
        self.assertEqual(f.state.f[0].cut, 25)


class Corner(unittest.TestCase):
    def test_spots_an_opponent_who_keeps_shooting(self):
        from engine.corner import advice
        r = quick_fighters()
        f = Fight(r[0], r[1], seed=3)
        while not f.between_rounds and not f.over:
            if f.state.pos != STANDING:
                f.state.pos, f.state.top, f.state.sub = STANDING, None, None
            f.play(("cross", "takedown"))
        tips = advice(f, 0)
        self.assertTrue(1 <= len(tips) <= 3)
        self.assertTrue(any("shooting" in t for t in tips), tips)

    def test_always_gives_advice(self):
        from engine.corner import advice
        r = quick_fighters()
        f = Fight(r[2], r[3], seed=4)
        f.play(("block", "block"))
        self.assertTrue(advice(f, 0))
        self.assertTrue(advice(f, 1))


class Stamina(unittest.TestCase):
    def test_spamming_power_shots_gasses_you_out(self):
        st = fresh()
        for seed in range(6):
            resolve(st, ("cross", "block"), random.Random(seed))
        self.assertLess(st.f[0].stamina, 30)


class CardSystem(unittest.TestCase):
    def _fighter(self, deck=None, perks=None, level=1, style="Striker"):
        from engine.roster import make
        return make("Test", "", style, cards=(deck or {}, perks or [], level))

    def test_card_takes_the_slot_of_its_basic_move(self):
        p = self._fighter({"cross": "superman"})
        st = FightState([FighterState(p), FighterState(self._fighter())])
        opts = st.options(0)
        self.assertIn("superman", opts)
        self.assertNotIn("cross", opts)
        self.assertEqual(len(opts), 9)   # with the feint

    def test_levels_make_cards_better(self):
        from engine.cards import build_kit
        k1 = build_kit(self._fighter({"cross": "superman"}, level=1))
        k3 = build_kit(self._fighter({"cross": "superman"}, level=3))
        self.assertGreater(k3.moves["superman"].dmg, k1.moves["superman"].dmg)
        self.assertLess(k3.moves["superman"].cost, k1.moves["superman"].cost)

    def test_signature_inherits_basic_matchups(self):
        from engine.cards import CARDS
        sm = CARDS["superman"].move
        self.assertEqual(matchup(sm, MOVES["takedown"]), 1)   # still stops takedowns
        self.assertEqual(matchup(MOVES["clinch"], sm), 1)     # still smothered by the clinch
        sbf = CARDS["spinfist"].move
        self.assertEqual(matchup(sbf, MOVES["block"]), 1)      # its own extra rule
        self.assertEqual(matchup(sbf, MOVES["takedown"]), 1)   # still stops takedowns

    def test_iron_lungs_saves_stamina(self):
        a = FighterState(self._fighter(perks=["ironlungs"]))
        b = FighterState(self._fighter())
        a.spend(20)
        b.spend(20)
        self.assertGreater(a.stamina, b.stamina)

    def test_stat_perks_change_stats(self):
        f = FighterState(self._fighter(perks=["heavyhands"]))
        self.assertEqual(f.stats.striking, 9)
        self.assertEqual(f.profile.stats.striking, 8)  # the profile itself is untouched

    def test_combo_builds_on_landed_strikes(self):
        st = FightState([FighterState(self._fighter(perks=["combo"])), FighterState(self._fighter())])
        for seed in range(50):
            st.f[1].hp = 100
            resolve(st, ("jab", "clinch"), random.Random(seed))  # jab beats the clinch entry
            st.pos = STANDING
            if st.f[0].combo >= 2:
                break
        self.assertGreaterEqual(st.f[0].combo, 2)

    def test_tired_fighters_take_more_damage(self):
        fresh_dmg, tired_dmg = [], []
        for seed in range(80):
            for bucket, stam in ((fresh_dmg, 100), (tired_dmg, 0)):
                st = fresh()
                st.f[1].stamina = stam
                ex = resolve(st, ("cross", "takedown"), random.Random(seed))
                if ex.landed[0]:
                    bucket.append(ex.dmg[0])
        self.assertGreater(sum(tired_dmg) / len(tired_dmg), sum(fresh_dmg) / len(fresh_dmg) * 1.25)

    def test_warns_about_no_takedown_defence(self):
        from dataclasses import replace
        import engine.cards as ec
        self.assertEqual(ec.warnings(self._fighter({"cross": "spinfist"})), [])
        # A made up card that gives up the power punch's takedown defence
        weak = replace(MOVES["cross"], key="testweak", base="cross", loses_to=("takedown",))
        ec.CARDS["testweak"] = ec.Card("testweak", "Test", "common", "", move=weak)
        try:
            self.assertTrue(ec.warnings(self._fighter({"cross": "testweak"})))
        finally:
            del ec.CARDS["testweak"]


class CareerCards(unittest.TestCase):
    def _career(self):
        return Career(new_player("Test Fighter", "", "Striker", (200, 0, 0), ""), seed=7)

    def test_new_fighter_starts_with_a_card_and_a_perk(self):
        c = self._career()
        self.assertEqual(c.player.deck, {"legkick": "calfkick"})
        self.assertEqual(c.player.perks, ["counter"])

    def test_wins_pay_and_give_a_pack(self):
        c = self._career()
        opp, *_ = c.next_fight()
        reward = c.record_result(opp, True, False, "KO", "x", 1)
        self.assertEqual(c.money, reward["purse"] + reward["bonus"])
        self.assertEqual(reward["pack"], "finish")
        pack = c.make_pack(reward["pack"])
        self.assertEqual(len(pack), 3)
        self.assertEqual(len(set(pack)), 3)

    def test_duplicates_level_up_then_refund(self):
        c = self._career()
        self.assertEqual(c.gain_card("superman"), "new")
        self.assertEqual(c.gain_card("superman"), "level")
        self.assertEqual(c.gain_card("superman"), "level")
        self.assertEqual(c.player.cards["superman"], 3)
        before = c.money
        self.assertEqual(c.gain_card("superman"), "refund")
        self.assertGreater(c.money, before)

    def test_budget_limits_the_deck(self):
        c = self._career()
        for cid in ("showtime", "twister", "necktie"):
            c.gain_card(cid)
        # Starter is Calf Kick (rare, 2) and Counter Striker (common, 1)
        self.assertIsNone(c.equip("kick", "showtime"))      # 3 + 3 = 6 of 6
        self.assertIsNotNone(c.equip("rnc", "twister"))     # would be 9
        self.assertNotIn("rnc", c.player.deck)

    def test_shop(self):
        c = self._career()
        c.money = 100000
        cid = c.shop[0]
        self.assertIsNotNone(c.buy(cid))
        self.assertIn(cid, c.player.cards)
        self.assertNotIn(cid, c.shop)

    def test_old_saves_without_cards_still_load(self):
        from engine.fighter import Profile
        d = new_player("Old Save", "", "Wrestler", (0, 0, 200), "").to_dict()
        for k in ("deck", "perks", "cards"):
            d.pop(k)
        c = Career(Profile.from_dict(d))
        self.assertTrue(c.player.cards)


class BackControl(unittest.TestCase):
    def test_take_the_back_from_mount(self):
        for seed in range(20):
            st = fresh(MOUNT, 0)
            resolve(st, ("takeback", "mcover"), random.Random(seed))
            if st.pos == BACK:
                break
        self.assertEqual((st.pos, st.top), (BACK, 0))
        self.assertEqual(st.options(0), ["bpunch", "rnc", "bhold"])

    def test_turning_away_to_get_up_gives_the_back(self):
        backs = 0
        for seed in range(100):
            st = fresh(GUARD, 0)
            resolve(st, ("pass", "getup"), random.Random(seed))
            backs += st.pos == BACK
            self.assertNotEqual(st.pos, MOUNT)
        self.assertGreater(backs, 20)

    def test_escaping_the_choke_keeps_you_on_the_back(self):
        st = fresh(BACK, 0)
        st.sub = SubState(0, "rnc", 1)
        resolve(st, ("left", "left"), random.Random(0))
        self.assertIsNone(st.sub)
        self.assertEqual((st.pos, st.top), (BACK, 0))

    def test_turn_in_recovers_guard(self):
        st = fresh(BACK, 0)
        resolve(st, ("bhold", "turnin"), random.Random(5))
        self.assertEqual((st.pos, st.top), (GUARD, 0))


class FullFights(unittest.TestCase):
    def test_ai_fights_always_finish_with_a_valid_result(self):
        r = quick_fighters()
        for seed in range(30):
            f = Fight(r[seed % 4], r[(seed + 1) % 4], seed=seed)
            ais = [AI("normal", seed=seed), AI("easy", seed=seed + 100)]
            steps = 0
            while not f.over:
                if f.between_rounds:
                    f.start_next_round()
                    continue
                picks = (ais[0].choose(f, 0), ais[1].choose(f, 1))
                self.assertIn(picks[0], f.options(0))
                self.assertIn(picks[1], f.options(1))
                f.play(picks)
                steps += 1
                self.assertLess(steps, 100)
            res = f.result
            self.assertIn(res.method, ("KO", "TKO", "Submission", "Decision", "Draw"))
            if res.method == "Decision":
                self.assertEqual(len(res.cards), 3)

    def test_play_rejects_picks_after_the_end(self):
        r = quick_fighters()
        f = Fight(r[0], r[1], seed=1)
        f.state.f[1].hp = 1
        while not f.over:
            if f.between_rounds:
                f.start_next_round()
            f.play(("cross", "jab") if f.state.pos == STANDING else
                   (f.options(0)[0], f.options(1)[0]))
        with self.assertRaises(RuntimeError):
            f.play(("jab", "jab"))


class CareerMode(unittest.TestCase):
    def _win(self, c):
        opp, *_ = c.next_fight()
        c.record_result(opp, True, False, "KO", "Power punch", 1)
        return opp

    def test_climb_to_the_title(self):
        c = Career(new_player("Test Fighter", "", "Striker", (200, 0, 0), ""), seed=1)
        self.assertIsNone(c.rank())
        self._win(c)
        self._win(c)
        self.assertIsNone(c.rank())
        self._win(c)
        self.assertEqual(c.rank(), 10)
        # One spot per win, but grudge matches can jump you or cost a fight
        for _ in range(15):
            if c.rank() == 1 and not c.grudge_due():
                break
            self._win(c)
        self.assertEqual(c.rank(), 1)
        opp, rounds, title, *_ = c.next_fight()
        self.assertTrue(title)
        self.assertEqual(rounds, 5)
        self._win(c)
        self.assertTrue(c.is_champ())
        self._win(c)
        self.assertEqual(c.defenses, 1)

    def test_losing_the_belt(self):
        c = Career(new_player("Test Fighter", "", "Striker", (200, 0, 0), ""), seed=1)
        c.ladder.insert(0, c.player)
        c.ladder.pop()
        opp, *_ = c.next_fight()
        c.record_result(opp, False, False, "KO", "x", 1)
        self.assertIs(c.ladder[0], opp)
        self.assertEqual(c.rank(), 1)

    def test_training_costs_more_at_high_stats(self):
        c = Career(new_player("Test Fighter", "", "Striker", (200, 0, 0), ""))
        c.points = 3
        before = c.player.stats.striking
        self.assertEqual(before, 7)
        self.assertTrue(c.train("striking"))
        self.assertEqual(c.points, 1)
        self.assertFalse(c.train("striking"))

    def test_save_and_load(self):
        c = Career(new_player("Test Fighter", "Kid", "BJJ", (0, 200, 0), "Leeds"), seed=2)
        self._win(c)
        self._win(c)
        self._win(c)
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "career.json")
            c.save(path)
            back = Career.load(path)
        self.assertEqual(back.player.name, "Test Fighter")
        self.assertEqual(back.player.wins, 3)
        self.assertEqual(back.rank(), c.rank())
        self.assertIs(back.ladder[back.rank()], back.player)


if __name__ == "__main__":
    unittest.main()
