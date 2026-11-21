import random
import unittest
from types import SimpleNamespace

import nemo
from nemo.search import minimax

import nemo_adapter as adapter
from board import dice_to_moves, new_game, roll_dice


def _game(points=None, bar=None, off=None):
    board_points = [0] * 25
    for point, value in (points or {}).items():
        board_points[point] = value
    return {"points": board_points,
            "bar": dict(bar) if bar else {"X": 0, "O": 0},
            "off": dict(off) if off else {"X": 0, "O": 0}}


class AdapterTest(unittest.TestCase):
    def test_turn_is_kept_while_dice_remain(self):
        state = (new_game(), "X", (3, 1))
        after_one = adapter.play(state, adapter.moves(state)[0])
        self.assertEqual(adapter.to_move(after_one), "X")
        after_two = adapter.play(after_one, adapter.moves(after_one)[0])
        self.assertEqual(adapter.to_move(after_two), "O")
        self.assertEqual(adapter.moves(after_two), [])

    def test_a_blocked_die_offers_only_skip(self):
        # X on the bar; O owns every entry point.
        game = _game({p: -2 for p in range(19, 25)}, bar={"X": 1, "O": 0})
        self.assertEqual(adapter.moves((game, "X", (4,))), [adapter.SKIP])
        nxt = adapter.play((game, "X", (4, 2)), adapter.SKIP)
        self.assertEqual(nxt, (game, "X", (2,)))

    def test_play_does_not_mutate(self):
        game = new_game()
        adapter.play((game, "X", (6,)), ("move", 24))
        self.assertEqual(game, new_game())

    def test_evaluate_prefers_fewer_pips_and_is_antisymmetric(self):
        ahead = _game({6: 2, 19: -2})  # X needs 12 pips, O needs 12
        better = _game({5: 2, 19: -2})
        self.assertGreater(adapter.evaluate((better, "O", ()), "X"),
                           adapter.evaluate((ahead, "O", ()), "X"))
        self.assertAlmostEqual(adapter.evaluate((better, "O", ()), "X"),
                               -adapter.evaluate((better, "O", ()), "O"))


    def test_an_opponent_on_the_bar_is_worth_more_than_its_pips(self):
        # O's checker on the bar vs on O's 1-point: 1 pip apart, so the
        # gap is almost all the bar term.
        on_bar = _game({6: 2, 19: -2}, bar={"X": 0, "O": 1})
        on_one = _game({6: 2, 19: -2, 1: -1})
        gap = (adapter.evaluate((on_bar, "O", ()), "X")
               - adapter.evaluate((on_one, "O", ()), "X"))
        self.assertGreater(gap, 0.05)


class NemoPlaysBackgammonTest(unittest.TestCase):
    def test_hard_hits_a_blot(self):
        # X on 13 with a 5: hitting O's lone checker on 8 beats any other move.
        game = _game({13: 2, 6: 2, 8: -1, 24: -2})
        move = minimax.choose_move(adapter, (game, "X", (5,)), nemo.HARD,
                                   random.Random(0))
        self.assertEqual(move, ("move", 13))

    def test_hard_bears_off_to_win(self):
        game = _game({2: 1}, off={"X": 14, "O": 0})
        game["points"][20] = -15
        state = (game, "X", (2, 1))
        self.assertEqual(minimax.choose_move(adapter, state, nemo.HARD,
                                             random.Random(0)), ("bear_off", 2))

    def test_hard_uses_the_whole_roll(self):
        # A mid-game position (found by search, not hand-made) where the
        # best 1 is only best given the 6 that follows. Judging each die
        # alone (depth 1) ends the turn measurably worse.
        game = _game({1: -2, 3: 2, 6: 4, 8: 3, 9: 2, 11: 2, 12: -3, 17: -3,
                      19: -6, 20: 2, 23: -1})
        start = (game, "X", (1, 6))
        greedy = SimpleNamespace(
            **{k: getattr(adapter, k) for k in
               ("moves", "play", "to_move", "outcome", "evaluate", "STOCHASTIC")},
            HARD_DEPTH=1)

        def end_of_turn(ad):
            state = start
            while adapter.to_move(state) == "X":
                state = adapter.play(state, minimax.choose_move(
                    ad, state, nemo.HARD, random.Random(0)))
            return adapter.evaluate(state, "X")

        self.assertGreater(end_of_turn(adapter), end_of_turn(greedy) + 0.05)

    def test_a_whole_nemo_game_finishes(self):
        rng = random.Random(4)
        game, player = new_game(), "X"
        for _ in range(2000):
            dice = tuple(dice_to_moves(*roll_dice(rng)))
            state = (game, player, dice)
            while adapter.to_move(state) == player and adapter.outcome(state) is None:
                level = nemo.HARD if player == "X" else nemo.EASY
                state = adapter.play(state, minimax.choose_move(adapter, state,
                                                                level, rng))
            game, player = state[0], state[1]
            if adapter.outcome(state):
                self.assertIn(adapter.outcome(state), ("X", "O"))
                return
        self.fail("game did not finish")


if __name__ == "__main__":
    unittest.main()
