import unittest

from board import COLS, ROWS, apply_move, is_draw, is_full, new_board, valid_moves, winner


def _empty_board():
    return new_board()


class NewBoardTest(unittest.TestCase):
    def test_new_board_dimensions_and_emptiness(self):
        board = new_board()
        self.assertEqual(len(board), ROWS)
        self.assertTrue(all(len(row) == COLS for row in board))
        self.assertTrue(all(cell == "" for row in board for cell in row))


class ValidMovesTest(unittest.TestCase):
    def test_all_columns_valid_on_empty_board(self):
        self.assertEqual(valid_moves(_empty_board()), list(range(COLS)))

    def test_full_column_excluded(self):
        board = _empty_board()
        for _ in range(ROWS):
            board = apply_move(board, 0, "X")
        self.assertNotIn(0, valid_moves(board))
        self.assertIn(1, valid_moves(board))


class ApplyMoveTest(unittest.TestCase):
    def test_piece_falls_to_bottom_row(self):
        board = apply_move(_empty_board(), 3, "X")
        self.assertEqual(board[ROWS - 1][3], "X")

    def test_second_piece_stacks_on_first(self):
        board = apply_move(_empty_board(), 3, "X")
        board = apply_move(board, 3, "O")
        self.assertEqual(board[ROWS - 1][3], "X")
        self.assertEqual(board[ROWS - 2][3], "O")

    def test_does_not_mutate_original_board(self):
        original = _empty_board()
        apply_move(original, 0, "X")
        self.assertEqual(original, new_board())

    def test_rejects_out_of_range_column(self):
        with self.assertRaises(ValueError):
            apply_move(_empty_board(), COLS, "X")
        with self.assertRaises(ValueError):
            apply_move(_empty_board(), -1, "X")

    def test_rejects_full_column(self):
        board = _empty_board()
        for _ in range(ROWS):
            board = apply_move(board, 0, "X")
        with self.assertRaises(ValueError):
            apply_move(board, 0, "O")


class WinnerTest(unittest.TestCase):
    def test_no_winner_on_empty_board(self):
        self.assertEqual(winner(_empty_board()), "")

    def test_detects_horizontal_win(self):
        board = _empty_board()
        for col in range(4):
            board[ROWS - 1][col] = "X"
        self.assertEqual(winner(board), "X")

    def test_detects_vertical_win(self):
        board = _empty_board()
        for row in range(ROWS - 4, ROWS):
            board[row][2] = "O"
        self.assertEqual(winner(board), "O")

    def test_detects_down_right_diagonal_win(self):
        board = _empty_board()
        for i in range(4):
            board[i][i] = "X"
        self.assertEqual(winner(board), "X")

    def test_detects_down_left_diagonal_win(self):
        board = _empty_board()
        for i in range(4):
            board[i][3 - i] = "O"
        self.assertEqual(winner(board), "O")

    def test_three_in_a_row_is_not_a_win(self):
        board = _empty_board()
        for col in range(3):
            board[ROWS - 1][col] = "X"
        self.assertEqual(winner(board), "")

    def test_no_false_positive_on_mixed_line(self):
        board = _empty_board()
        board[ROWS - 1][0] = "X"
        board[ROWS - 1][1] = "X"
        board[ROWS - 1][2] = "O"
        board[ROWS - 1][3] = "X"
        self.assertEqual(winner(board), "")


class DrawTest(unittest.TestCase):
    def test_is_full_false_on_empty_board(self):
        self.assertFalse(is_full(_empty_board()))

    def test_is_full_true_when_all_columns_full(self):
        board = _empty_board()
        for col in range(COLS):
            for _ in range(ROWS):
                board = apply_move(board, col, "X")
        self.assertTrue(is_full(board))

    def test_is_draw_false_if_board_not_full(self):
        self.assertFalse(is_draw(_empty_board()))

    def test_is_draw_false_if_there_is_a_winner(self):
        # Deliberately not asserting *which* mark wins: filling with all
        # "O" also creates full-row/column O runs, and winner() returns
        # whichever four-in-a-row its scan hits first - that's already
        # covered by the WinnerTest cases above. This test only needs a
        # full board with *some* winner, to exercise is_draw's "full but
        # not a draw because someone already won" branch.
        board = [["O"] * COLS for _ in range(ROWS)]
        for col in range(4):
            board[ROWS - 1][col] = "X"
        self.assertTrue(is_full(board))
        self.assertNotEqual(winner(board), "")
        self.assertFalse(is_draw(board))


if __name__ == "__main__":
    unittest.main()
