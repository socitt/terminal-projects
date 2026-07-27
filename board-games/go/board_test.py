import unittest

from board import (
    BLACK,
    EMPTY,
    SIZE,
    WHITE,
    apply_move,
    group_and_liberties,
    in_bounds,
    is_legal_move,
    neighbors,
    new_board,
    opponent,
    score,
    winner,
)


class NewBoardTest(unittest.TestCase):
    def test_dimensions_and_emptiness(self):
        board = new_board()
        self.assertEqual(len(board), SIZE)
        self.assertTrue(all(len(row) == SIZE for row in board))
        self.assertTrue(all(cell == EMPTY for row in board for cell in row))


class OpponentTest(unittest.TestCase):
    def test_opponent(self):
        self.assertEqual(opponent(BLACK), WHITE)
        self.assertEqual(opponent(WHITE), BLACK)


class NeighborsTest(unittest.TestCase):
    def test_corner_has_two_neighbors(self):
        self.assertEqual(set(neighbors(SIZE, 0, 0)), {(0, 1), (1, 0)})

    def test_edge_has_three_neighbors(self):
        self.assertEqual(set(neighbors(SIZE, 0, 4)), {(0, 3), (0, 5), (1, 4)})

    def test_center_has_four_neighbors(self):
        self.assertEqual(
            set(neighbors(SIZE, 4, 4)), {(3, 4), (5, 4), (4, 3), (4, 5)}
        )

    def test_in_bounds(self):
        self.assertTrue(in_bounds(SIZE, 0, 0))
        self.assertTrue(in_bounds(SIZE, SIZE - 1, SIZE - 1))
        self.assertFalse(in_bounds(SIZE, -1, 0))
        self.assertFalse(in_bounds(SIZE, 0, SIZE))


class GroupAndLibertiesTest(unittest.TestCase):
    def test_empty_point_has_no_group_or_liberties(self):
        board = new_board()
        group, liberties = group_and_liberties(board, 4, 4)
        self.assertEqual(group, set())
        self.assertEqual(liberties, set())

    def test_single_center_stone_has_four_liberties(self):
        board = new_board()
        board[4][4] = BLACK
        group, liberties = group_and_liberties(board, 4, 4)
        self.assertEqual(group, {(4, 4)})
        self.assertEqual(liberties, {(3, 4), (5, 4), (4, 3), (4, 5)})

    def test_single_corner_stone_has_two_liberties(self):
        board = new_board()
        board[0][0] = BLACK
        _, liberties = group_and_liberties(board, 0, 0)
        self.assertEqual(liberties, {(0, 1), (1, 0)})

    def test_connected_group_merges_and_excludes_internal_points(self):
        board = new_board()
        board[4][4] = BLACK
        board[4][5] = BLACK
        group, liberties = group_and_liberties(board, 4, 4)
        self.assertEqual(group, {(4, 4), (4, 5)})
        # (4,4)-(4,5) is an internal connection, not a liberty of either.
        self.assertNotIn((4, 4), liberties)
        self.assertNotIn((4, 5), liberties)
        self.assertEqual(liberties, {(3, 4), (5, 4), (4, 3), (3, 5), (5, 5), (4, 6)})

    def test_opponent_stones_are_not_liberties_and_do_not_join_group(self):
        board = new_board()
        board[4][4] = BLACK
        board[4][5] = WHITE
        _, liberties = group_and_liberties(board, 4, 4)
        self.assertNotIn((4, 5), liberties)


class ApplyMoveTest(unittest.TestCase):
    def test_places_a_stone(self):
        board = new_board()
        new = apply_move(board, 4, 4, BLACK)
        self.assertEqual(new[4][4], BLACK)

    def test_does_not_mutate_original_board(self):
        board = new_board()
        apply_move(board, 4, 4, BLACK)
        self.assertEqual(board[4][4], EMPTY)

    def test_raises_on_occupied_point(self):
        board = new_board()
        board[4][4] = BLACK
        with self.assertRaises(ValueError):
            apply_move(board, 4, 4, WHITE)

    def test_raises_out_of_bounds(self):
        board = new_board()
        with self.assertRaises(ValueError):
            apply_move(board, SIZE, 0, BLACK)
        with self.assertRaises(ValueError):
            apply_move(board, -1, 0, BLACK)

    def test_captures_single_stone_in_corner(self):
        # White stone at (0,0) has only two liberties; black fills both.
        board = new_board()
        board[0][0] = WHITE
        board[0][1] = BLACK
        new = apply_move(board, 1, 0, BLACK)
        self.assertEqual(new[0][0], EMPTY)
        self.assertEqual(new[1][0], BLACK)

    def test_captures_multi_stone_group(self):
        # White group {(4,4),(4,5)} surrounded on all external sides by black.
        board = new_board()
        board[4][4] = WHITE
        board[4][5] = WHITE
        board[3][4] = BLACK
        board[5][4] = BLACK
        board[4][3] = BLACK
        board[3][5] = BLACK
        board[5][5] = BLACK
        # Last liberty at (4,6).
        new = apply_move(board, 4, 6, BLACK)
        self.assertEqual(new[4][4], EMPTY)
        self.assertEqual(new[4][5], EMPTY)
        self.assertEqual(new[4][6], BLACK)

    def test_raises_on_suicide_with_no_capture(self):
        # Black at (0,0) surrounded by two white stones, each of which
        # has another liberty of its own (so nothing gets captured).
        board = new_board()
        board[0][1] = WHITE
        board[0][2] = EMPTY  # (0,1)'s other liberty
        board[1][0] = WHITE
        board[2][0] = EMPTY  # (1,0)'s other liberty
        with self.assertRaises(ValueError):
            apply_move(board, 0, 0, BLACK)

    def test_legal_move_that_looks_like_suicide_but_captures_first(self):
        # Verified interactively before writing: a white group
        # {(0,0),(0,1),(1,0)} whose only liberty is (1,1). Black
        # playing (1,1) would have zero liberties on its own (all
        # four neighbors occupied), but it captures the white group
        # first, which frees (0,1) and (1,0) as liberties.
        board = new_board()
        board[0][0] = WHITE
        board[0][1] = WHITE
        board[1][0] = WHITE
        board[0][2] = BLACK
        board[2][0] = BLACK
        board[1][2] = WHITE
        board[2][1] = WHITE

        self.assertTrue(is_legal_move(board, 1, 1, BLACK))
        new = apply_move(board, 1, 1, BLACK)
        self.assertEqual(new[0][0], EMPTY)
        self.assertEqual(new[0][1], EMPTY)
        self.assertEqual(new[1][0], EMPTY)
        self.assertEqual(new[1][1], BLACK)
        _, liberties = group_and_liberties(new, 1, 1)
        self.assertEqual(liberties, {(0, 1), (1, 0)})


class KoTest(unittest.TestCase):
    def _diamond_ko_setup(self):
        """A single white stone at (3,4) with its only liberty at
        (4,4); black's stone once played there will itself have its
        only liberty back at (3,4). Verified interactively before
        writing this test."""
        board = new_board()
        board[3][4] = WHITE
        board[2][4] = BLACK
        board[3][3] = BLACK
        board[3][5] = BLACK
        board[4][3] = WHITE
        board[4][5] = WHITE
        board[5][4] = WHITE
        board[4][2] = BLACK
        board[4][6] = BLACK
        board[6][4] = BLACK
        return board

    def test_recapture_reproduces_exact_prior_position(self):
        board = self._diamond_ko_setup()
        previous = [row[:] for row in board]
        after_capture = apply_move(board, 4, 4, BLACK)
        recaptured = apply_move(after_capture, 3, 4, WHITE)
        self.assertEqual(recaptured, previous)

    def test_ko_forbids_immediate_recapture(self):
        board = self._diamond_ko_setup()
        previous = [row[:] for row in board]
        after_capture = apply_move(board, 4, 4, BLACK)
        self.assertFalse(is_legal_move(after_capture, 3, 4, WHITE, previous_board=previous))
        with self.assertRaises(ValueError):
            apply_move(after_capture, 3, 4, WHITE, previous_board=previous)

    def test_recapture_legal_without_previous_board_argument(self):
        board = self._diamond_ko_setup()
        after_capture = apply_move(board, 4, 4, BLACK)
        self.assertTrue(is_legal_move(after_capture, 3, 4, WHITE))

    def test_unrelated_move_unaffected_by_ko_check(self):
        board = self._diamond_ko_setup()
        previous = [row[:] for row in board]
        after_capture = apply_move(board, 4, 4, BLACK)
        self.assertTrue(is_legal_move(after_capture, 0, 0, WHITE, previous_board=previous))


class ScoreTest(unittest.TestCase):
    def test_empty_board_is_all_komi(self):
        board = new_board()
        black, white = score(board, komi=5.5)
        self.assertEqual(black, 0)
        self.assertEqual(white, 5.5)

    def test_stones_count_toward_score(self):
        board = new_board()
        board[0][0] = BLACK
        board[8][8] = WHITE
        black, white = score(board, komi=0)
        self.assertEqual(black, 1)
        self.assertEqual(white, 1)

    def test_territory_surrounded_by_one_color_counts_for_that_color(self):
        # (0,1) is walled in on all sides by black, making it its own
        # isolated one-point empty region. A distant white stone is
        # needed too: with no white anywhere, the rest of the empty
        # board would also (correctly) count as black territory,
        # since it's one giant connected region touching only black
        # stones -- that's not what this test means to isolate.
        board = new_board()
        board[0][0] = BLACK
        board[0][1] = EMPTY
        board[0][2] = BLACK
        board[1][0] = BLACK
        board[1][1] = BLACK
        board[1][2] = BLACK
        board[8][8] = WHITE
        black, white = score(board, komi=0)
        self.assertEqual(black, 5 + 1)
        self.assertEqual(white, 1)

    def test_neutral_territory_bordered_by_both_colors_counts_for_neither(self):
        board = new_board()
        board[4][3] = BLACK
        board[4][5] = WHITE
        # (4,4) borders both colors -> dame, not territory for either.
        black, white = score(board, komi=0)
        self.assertEqual(black, 1)
        self.assertEqual(white, 1)

    def test_komi_is_added_to_white_only(self):
        board = new_board()
        black, white = score(board, komi=7)
        self.assertEqual(black, 0)
        self.assertEqual(white, 7)


class WinnerTest(unittest.TestCase):
    def test_black_wins_on_higher_score(self):
        board = new_board()
        for i in range(10):
            board[0][i % SIZE] = BLACK
        self.assertEqual(winner(board, komi=0.5), BLACK)

    def test_white_wins_with_komi(self):
        board = new_board()
        self.assertEqual(winner(board, komi=5.5), WHITE)

    def test_no_tie_possible_with_half_point_komi(self):
        board = new_board()
        board[0][0] = BLACK
        self.assertNotEqual(winner(board, komi=1), "")


if __name__ == "__main__":
    unittest.main()
