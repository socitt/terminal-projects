import unittest

from board import apply_move, is_draw, is_full, new_board, winner


class NewBoardTest(unittest.TestCase):
    def test_new_board_is_nine_empty_cells(self):
        self.assertEqual(new_board(), [""] * 9)


class ApplyMoveTest(unittest.TestCase):
    def test_places_mark_at_index(self):
        board = apply_move(new_board(), 4, "X")
        self.assertEqual(board[4], "X")

    def test_does_not_mutate_original_board(self):
        original = new_board()
        apply_move(original, 0, "X")
        self.assertEqual(original, new_board())

    def test_rejects_occupied_cell(self):
        board = apply_move(new_board(), 0, "X")
        with self.assertRaises(ValueError):
            apply_move(board, 0, "O")

    def test_rejects_out_of_range_index(self):
        with self.assertRaises(ValueError):
            apply_move(new_board(), 9, "X")
        with self.assertRaises(ValueError):
            apply_move(new_board(), -1, "X")


class WinnerTest(unittest.TestCase):
    def test_no_winner_on_empty_board(self):
        self.assertEqual(winner(new_board()), "")

    def test_detects_row_win(self):
        board = list(new_board())
        board[0] = board[1] = board[2] = "X"
        self.assertEqual(winner(board), "X")

    def test_detects_column_win(self):
        board = list(new_board())
        board[1] = board[4] = board[7] = "O"
        self.assertEqual(winner(board), "O")

    def test_detects_diagonal_win(self):
        board = list(new_board())
        board[0] = board[4] = board[8] = "X"
        self.assertEqual(winner(board), "X")

    def test_detects_anti_diagonal_win(self):
        board = list(new_board())
        board[2] = board[4] = board[6] = "O"
        self.assertEqual(winner(board), "O")

    def test_no_false_positive_on_mixed_line(self):
        board = list(new_board())
        board[0], board[1], board[2] = "X", "O", "X"
        self.assertEqual(winner(board), "")


class DrawTest(unittest.TestCase):
    def test_is_full_true_when_no_empty_cells(self):
        board = ["X", "O"] * 4 + ["X"]
        self.assertTrue(is_full(board))

    def test_is_full_false_with_empty_cell(self):
        self.assertFalse(is_full(new_board()))

    def test_is_draw_true_on_full_board_with_no_winner(self):
        board = [
            "X", "O", "X",
            "X", "O", "O",
            "O", "X", "X",
        ]
        self.assertTrue(is_full(board))
        self.assertEqual(winner(board), "")
        self.assertTrue(is_draw(board))

    def test_is_draw_false_if_there_is_a_winner(self):
        board = list(new_board())
        board[0] = board[1] = board[2] = "X"
        self.assertFalse(is_draw(board))

    def test_is_draw_false_if_board_not_full(self):
        self.assertFalse(is_draw(new_board()))


if __name__ == "__main__":
    unittest.main()
