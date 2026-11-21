import random
import unittest

import nemo
from nemo.search import minimax

import nemo_adapter as adapter
from board import COLS, ROWS, new_board


def _board(rows_bottom_up):
    """Rows given bottom row first, '.' for empty."""
    board = new_board()
    for i, row in enumerate(rows_bottom_up):
        for c, cell in enumerate(row):
            board[ROWS - 1 - i][c] = "" if cell == "." else cell
    return board


def _play_out(levels, rng):
    state = (new_board(), "X")
    while adapter.outcome(state) is None:
        level = levels[adapter.to_move(state)]
        state = adapter.play(state, minimax.choose_move(adapter, state, level, rng))
    return adapter.outcome(state)


class AdapterTest(unittest.TestCase):
    def test_moves_are_open_columns_centre_first(self):
        moves = adapter.moves((new_board(), "X"))
        self.assertEqual(sorted(moves), list(range(COLS)))
        self.assertEqual(moves[0], COLS // 2)

    def test_full_columns_are_not_offered(self):
        board = _board(["X..", "O..", "X..", "O..", "X..", "O.."])
        self.assertNotIn(0, adapter.moves((board, "X")))

    def test_evaluate_is_symmetric_and_bounded(self):
        board = _board(["..XX..."])
        x, o = adapter.evaluate((board, "O"), "X"), adapter.evaluate((board, "O"), "O")
        self.assertGreater(x, 0)
        self.assertAlmostEqual(x, -o)
        self.assertLessEqual(abs(x), 1.0)


class NemoPlaysConnect4Test(unittest.TestCase):
    def test_takes_a_win_at_every_level_but_easy(self):
        state = (_board(["XXX.OO.", "OO....."]), "X")
        for level in (nemo.MEDIUM, nemo.HARD):
            self.assertEqual(minimax.choose_move(adapter, state, level,
                                                 random.Random(0)), 3)

    def test_blocks_a_threat(self):
        state = (_board(["OOO.XX."]), "X")
        for level in (nemo.MEDIUM, nemo.HARD):
            self.assertEqual(minimax.choose_move(adapter, state, level,
                                                 random.Random(0)), 3)

    def test_hard_sees_a_double_threat_coming(self):
        # X to move: dropping in column 2 or 5 makes ".XXX." open on both
        # ends -- a win next move whatever O does. Medium can't see it.
        state = (_board(["...XX..", "...OO.."]), "X")
        move = minimax.choose_move(adapter, state, nemo.HARD, random.Random(0))
        self.assertIn(move, (2, 5))

    def test_hard_beats_easy(self):
        rng = random.Random(5)
        results = [_play_out({"X": nemo.HARD, "O": nemo.EASY}, rng)
                   for _ in range(4)]
        results += [_play_out({"X": nemo.EASY, "O": nemo.HARD}, rng)
                    for _ in range(4)]
        self.assertEqual(results, ["X"] * 4 + ["O"] * 4)


if __name__ == "__main__":
    unittest.main()
