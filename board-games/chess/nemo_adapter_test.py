import random
import unittest

import nemo
from nemo.search import minimax

import nemo_adapter as adapter
from board import BLACK, EMPTY, SIZE, WHITE, new_game


def _position(pieces, turn=WHITE):
    """pieces: {"e1": "K", "e8": "k", ...}."""
    board = [[EMPTY] * SIZE for _ in range(SIZE)]
    for square, piece in pieces.items():
        board[int(square[1]) - 1]["abcdefgh".index(square[0])] = piece
    return {"board": board, "turn": turn,
            "castling": {"K": False, "Q": False, "k": False, "q": False},
            "en_passant": None}


def _sq(name):
    return int(name[1]) - 1, "abcdefgh".index(name[0])


class AdapterTest(unittest.TestCase):
    def test_twenty_moves_from_the_start(self):
        self.assertEqual(len(adapter.moves(new_game())), 20)

    def test_captures_are_offered_first(self):
        state = _position({"e1": "K", "e8": "k", "d4": "N", "e6": "p", "h2": "P"})
        first = adapter.moves(state)[0]
        self.assertEqual(first[:2], (_sq("d4"), _sq("e6")))

    def test_promotion_moves_carry_a_queen(self):
        state = _position({"e1": "K", "h8": "k", "a7": "P"})
        promos = [m for m in adapter.moves(state) if m[0] == _sq("a7")]
        self.assertEqual(promos, [(_sq("a7"), _sq("a8"), "Q")])

    def test_outcomes(self):
        mated = _position({"h8": "k", "g7": "Q", "f6": "K"}, turn=BLACK)
        self.assertEqual(adapter.outcome(mated), WHITE)
        stale = _position({"h8": "k", "f7": "Q", "f6": "K"}, turn=BLACK)
        self.assertEqual(adapter.outcome(stale), "draw")
        self.assertIsNone(adapter.outcome(new_game()))


class NemoPlaysChessTest(unittest.TestCase):
    def test_finds_a_back_rank_mate(self):
        state = _position({"g1": "K", "a1": "R", "g8": "k",
                           "f7": "p", "g7": "p", "h7": "p"})
        for level in (nemo.MEDIUM, nemo.HARD):
            move = minimax.choose_move(adapter, state, level, random.Random(0))
            self.assertEqual(move[:2], (_sq("a1"), _sq("a8")))

    def test_hard_takes_a_free_queen(self):
        state = _position({"e1": "K", "e8": "k", "c3": "N", "d5": "q",
                           "h2": "P", "h7": "p"})
        move = minimax.choose_move(adapter, state, nemo.HARD, random.Random(0))
        self.assertEqual(move[:2], (_sq("c3"), _sq("d5")))

    def test_hard_wont_trade_its_queen_for_a_defended_pawn(self):
        state = _position({"e1": "K", "d1": "Q", "e8": "k",
                           "d5": "p", "e6": "p", "h2": "P", "h7": "p"})
        for seed in range(5):
            move = minimax.choose_move(adapter, state, nemo.HARD,
                                       random.Random(seed))
            self.assertNotEqual(move[:2], (_sq("d1"), _sq("d5")))


if __name__ == "__main__":
    unittest.main()
