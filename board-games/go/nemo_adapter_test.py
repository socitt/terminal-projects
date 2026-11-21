import random
import unittest

import nemo
from nemo.search import minimax

import nemo_adapter as adapter
from board import BLACK, EMPTY, WHITE, new_board


def _board(rows):
    return [["" if ch == "." else ch for ch in row] for row in rows]


class AdapterTest(unittest.TestCase):
    def test_pass_is_always_offered(self):
        self.assertEqual(adapter.moves(adapter.new_state(new_board(), BLACK))[-1],
                         adapter.PASS)

    def test_own_single_point_eye_is_not_offered(self):
        board = _board([".B...", "B....", ".....", ".....", "....."])
        black = adapter.moves(adapter.new_state(board, BLACK))
        self.assertNotIn((0, 0), black)
        self.assertIn((0, 2), black)

    def test_two_passes_end_the_game_on_area_score(self):
        state = adapter.new_state(new_board(5), BLACK)
        state = adapter.play(adapter.play(state, adapter.PASS), adapter.PASS)
        self.assertEqual(adapter.outcome(state), WHITE)  # komi decides

    def test_a_stone_resets_the_pass_count_and_records_ko_history(self):
        state = adapter.play(adapter.new_state(new_board(5), BLACK), adapter.PASS)
        board_before = state[0]
        state = adapter.play(state, (2, 2))
        self.assertEqual(state[3], 0)
        self.assertIs(state[2], board_before)
        self.assertEqual(adapter.to_move(state), BLACK)

    def test_evaluate_is_from_the_given_side(self):
        board = _board(["BB...", "BB...", ".....", ".....", "....W"])
        black = adapter.evaluate((board, BLACK, None, 0), BLACK)
        white = adapter.evaluate((board, BLACK, None, 0), WHITE)
        self.assertNotEqual(black, 0)
        self.assertAlmostEqual(black, -white)

    def test_play_does_not_mutate(self):
        board = new_board(5)
        adapter.play(adapter.new_state(board, BLACK), (0, 0))
        self.assertEqual(board, new_board(5))


class NemoPlaysGoTest(unittest.TestCase):
    def test_hard_captures_an_atari_stone(self):
        board = _board([".....", "..B..", ".BW..", "..B..", "....."])
        move = minimax.choose_move(adapter, adapter.new_state(board, BLACK),
                                   nemo.HARD, random.Random(0))
        self.assertEqual(move, (2, 3))

    def test_hard_passes_to_end_a_won_game(self):
        board = _board(["BBBB.", "BBBBB", "BBBBB", "BBBBB", "BBBBW"])
        state = (board, BLACK, None, 1)  # white just passed
        self.assertEqual(minimax.choose_move(adapter, state, nemo.HARD,
                                             random.Random(0)), adapter.PASS)

    def test_hard_plays_on_rather_than_pass_into_a_loss(self):
        state = (new_board(5), BLACK, None, 1)  # passing loses on komi
        self.assertNotEqual(minimax.choose_move(adapter, state, nemo.HARD,
                                                random.Random(0)), adapter.PASS)

    def test_a_whole_nemo_game_ends_by_itself(self):
        # The own-eye rule is what makes this terminate.
        rng = random.Random(2)
        for levels in ((nemo.EASY, nemo.EASY), (nemo.HARD, nemo.MEDIUM)):
            state, plies = adapter.new_state(new_board(5), BLACK), 0
            while adapter.outcome(state) is None:
                level = levels[0] if adapter.to_move(state) == BLACK else levels[1]
                state = adapter.play(state, minimax.choose_move(adapter, state,
                                                                level, rng))
                plies += 1
                self.assertLess(plies, 300)
            self.assertIn(adapter.outcome(state), (BLACK, WHITE, "draw"))


if __name__ == "__main__":
    unittest.main()
