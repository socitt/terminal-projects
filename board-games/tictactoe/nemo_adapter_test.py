import random
import unittest

import nemo
from nemo.search import minimax

import nemo_adapter as adapter
from board import new_board


def _board(cells):
    return [c if c != "." else "" for c in cells]


def _play_out(levels, rng):
    """levels: {"X": level, "O": level}. Returns the outcome."""
    state = (new_board(), "X")
    while adapter.outcome(state) is None:
        level = levels[adapter.to_move(state)]
        state = adapter.play(state, minimax.choose_move(adapter, state, level, rng))
    return adapter.outcome(state)


class AdapterTest(unittest.TestCase):
    def test_moves_are_the_empty_cells(self):
        self.assertEqual(adapter.moves((_board("XO.......".ljust(9, ".")), "X")),
                         list(range(2, 9)))

    def test_play_does_not_mutate_and_passes_the_turn(self):
        board = new_board()
        nxt = adapter.play((board, "X"), 4)
        self.assertEqual(board, new_board())
        self.assertEqual(nxt[0][4], "X")
        self.assertEqual(adapter.to_move(nxt), "O")

    def test_outcomes(self):
        self.assertEqual(adapter.outcome((_board("XXXOO...."), "O")), "X")
        self.assertEqual(adapter.outcome((_board("XOXXOOOXX"), "X")), "draw")
        self.assertIsNone(adapter.outcome((new_board(), "X")))


class NemoPlaysTicTacToeTest(unittest.TestCase):
    def test_medium_completes_a_line(self):
        state = (_board("XX.OO...."), "X")
        self.assertEqual(minimax.choose_move(adapter, state, nemo.MEDIUM,
                                             random.Random(0)), 2)

    def test_medium_blocks_a_line(self):
        state = (_board("OO.X....X"), "X")
        self.assertEqual(minimax.choose_move(adapter, state, nemo.MEDIUM,
                                             random.Random(0)), 2)

    def test_hard_never_loses_to_easy(self):
        rng = random.Random(3)
        for nemo_mark in ("X", "O"):
            for _ in range(15):
                levels = {nemo_mark: nemo.HARD,
                          adapter.other(nemo_mark): nemo.EASY}
                self.assertIn(_play_out(levels, rng), (nemo_mark, "draw"))

    def test_hard_against_itself_is_a_draw(self):
        self.assertEqual(_play_out({"X": nemo.HARD, "O": nemo.HARD},
                                   random.Random(0)), "draw")


if __name__ == "__main__":
    unittest.main()
