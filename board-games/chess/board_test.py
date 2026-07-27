import unittest

from board import (
    BLACK,
    EMPTY,
    SIZE,
    WHITE,
    apply_move,
    color_of,
    game_status,
    has_any_legal_move,
    in_bounds,
    is_checkmate,
    is_in_check,
    is_square_attacked,
    is_stalemate,
    king_position,
    legal_moves,
    new_board,
    new_game,
    opponent,
    pseudo_legal_moves,
    winner,
)


def _empty_state(turn=WHITE):
    return {
        "board": [[EMPTY] * SIZE for _ in range(SIZE)],
        "turn": turn,
        "castling": {"K": False, "Q": False, "k": False, "q": False},
        "en_passant": None,
    }


class NewBoardTest(unittest.TestCase):
    def test_dimensions(self):
        board = new_board()
        self.assertEqual(len(board), SIZE)
        self.assertTrue(all(len(row) == SIZE for row in board))

    def test_starting_position(self):
        board = new_board()
        self.assertEqual(board[0], list("RNBQKBNR"))
        self.assertEqual(board[1], ["P"] * SIZE)
        self.assertEqual(board[6], ["p"] * SIZE)
        self.assertEqual(board[7], list("rnbqkbnr"))
        for row in range(2, 6):
            self.assertTrue(all(cell == EMPTY for cell in board[row]))


class NewGameTest(unittest.TestCase):
    def test_initial_state(self):
        state = new_game()
        self.assertEqual(state["turn"], WHITE)
        self.assertEqual(state["en_passant"], None)
        self.assertEqual(
            state["castling"], {"K": True, "Q": True, "k": True, "q": True}
        )


class ColorOfTest(unittest.TestCase):
    def test_empty_has_no_color(self):
        self.assertIsNone(color_of(EMPTY))

    def test_uppercase_is_white(self):
        self.assertEqual(color_of("K"), WHITE)
        self.assertEqual(color_of("P"), WHITE)

    def test_lowercase_is_black(self):
        self.assertEqual(color_of("k"), BLACK)
        self.assertEqual(color_of("p"), BLACK)


class OpponentTest(unittest.TestCase):
    def test_opponent(self):
        self.assertEqual(opponent(WHITE), BLACK)
        self.assertEqual(opponent(BLACK), WHITE)


class InBoundsTest(unittest.TestCase):
    def test_in_bounds(self):
        self.assertTrue(in_bounds(0, 0))
        self.assertTrue(in_bounds(SIZE - 1, SIZE - 1))
        self.assertFalse(in_bounds(-1, 0))
        self.assertFalse(in_bounds(0, SIZE))


class KingPositionTest(unittest.TestCase):
    def test_finds_each_king(self):
        board = new_board()
        self.assertEqual(king_position(board, WHITE), (0, 4))
        self.assertEqual(king_position(board, BLACK), (7, 4))

    def test_missing_king_returns_none(self):
        board = [[EMPTY] * SIZE for _ in range(SIZE)]
        self.assertIsNone(king_position(board, WHITE))


class PieceMovementTest(unittest.TestCase):
    """Pseudo-legal move generation for each piece type in isolation."""

    def test_pawn_double_step_from_start_rank(self):
        state = new_game()
        self.assertEqual(
            set(pseudo_legal_moves(state, 1, 4)), {(2, 4), (3, 4)}
        )

    def test_pawn_single_step_after_moving(self):
        state = new_game()
        state = apply_move(state, (1, 4), (2, 4))
        # Black's turn now; check white pawn's own future move set directly.
        self.assertEqual(pseudo_legal_moves(state, 2, 4), [(3, 4)])

    def test_pawn_blocked_cannot_advance(self):
        state = _empty_state()
        state["board"][1][4] = "P"
        state["board"][2][4] = "p"
        self.assertEqual(pseudo_legal_moves(state, 1, 4), [])

    def test_pawn_double_step_blocked_by_piece_two_ahead(self):
        state = new_game()
        state["board"][3][4] = "n"
        self.assertEqual(pseudo_legal_moves(state, 1, 4), [(2, 4)])

    def test_pawn_captures_diagonally_only_opponent(self):
        state = _empty_state()
        state["board"][4][4] = "P"
        state["board"][5][3] = "p"  # capturable
        state["board"][5][5] = "P"  # own piece, not capturable
        self.assertEqual(set(pseudo_legal_moves(state, 4, 4)), {(5, 4), (5, 3)})

    def test_knight_moves_from_center(self):
        state = _empty_state()
        state["board"][4][4] = "N"
        expected = {
            (5, 6), (6, 5), (6, 3), (5, 2),
            (3, 2), (2, 3), (2, 5), (3, 6),
        }
        self.assertEqual(set(pseudo_legal_moves(state, 4, 4)), expected)

    def test_knight_cannot_land_on_own_piece(self):
        state = _empty_state()
        state["board"][4][4] = "N"
        state["board"][6][5] = "P"
        self.assertNotIn((6, 5), pseudo_legal_moves(state, 4, 4))

    def test_bishop_slides_until_blocked_and_captures(self):
        state = _empty_state()
        state["board"][4][4] = "B"
        state["board"][6][6] = "p"
        moves = set(pseudo_legal_moves(state, 4, 4))
        self.assertIn((5, 5), moves)
        self.assertIn((6, 6), moves)  # captures the opponent piece
        self.assertNotIn((7, 7), moves)  # blocked beyond the capture

    def test_rook_slides_orthogonally_and_stops_at_own_piece(self):
        state = _empty_state()
        state["board"][4][4] = "R"
        state["board"][4][6] = "P"
        moves = set(pseudo_legal_moves(state, 4, 4))
        self.assertIn((4, 5), moves)
        self.assertNotIn((4, 6), moves)  # own piece blocks, not captured
        self.assertNotIn((4, 7), moves)

    def test_queen_combines_rook_and_bishop_moves(self):
        state = _empty_state()
        state["board"][4][4] = "Q"
        moves = set(pseudo_legal_moves(state, 4, 4))
        self.assertIn((4, 7), moves)  # straight
        self.assertIn((7, 7), moves)  # diagonal

    def test_king_moves_one_square_each_direction(self):
        state = _empty_state()
        state["board"][4][4] = "K"
        expected = {
            (5, 4), (3, 4), (4, 5), (4, 3),
            (5, 5), (5, 3), (3, 5), (3, 3),
        }
        self.assertEqual(set(pseudo_legal_moves(state, 4, 4)), expected)


class CheckDetectionTest(unittest.TestCase):
    def test_not_in_check_at_game_start(self):
        state = new_game()
        self.assertFalse(is_in_check(state, WHITE))
        self.assertFalse(is_in_check(state, BLACK))

    def test_in_check_from_rook_on_open_file(self):
        state = _empty_state()
        state["board"][0][4] = "K"
        state["board"][5][4] = "r"
        self.assertTrue(is_in_check(state, WHITE))

    def test_not_in_check_when_blocked(self):
        state = _empty_state()
        state["board"][0][4] = "K"
        state["board"][3][4] = "P"
        state["board"][5][4] = "r"
        self.assertFalse(is_in_check(state, WHITE))

    def test_is_square_attacked_by_pawn(self):
        state = _empty_state()
        state["board"][3][3] = "p"  # black pawn attacks diagonally toward rank 0
        self.assertTrue(is_square_attacked(state["board"], 2, 2, BLACK))
        self.assertTrue(is_square_attacked(state["board"], 2, 4, BLACK))
        self.assertFalse(is_square_attacked(state["board"], 2, 3, BLACK))  # straight ahead isn't an attack

    def test_pinned_piece_has_no_legal_moves(self):
        state = _empty_state()
        state["board"][0][4] = "K"
        state["board"][3][4] = "N"
        state["board"][7][4] = "r"
        self.assertEqual(legal_moves(state, 3, 4), [])


class ApplyMoveTest(unittest.TestCase):
    def test_moves_piece_and_flips_turn(self):
        state = new_game()
        new_state = apply_move(state, (1, 4), (3, 4))
        self.assertEqual(new_state["board"][1][4], EMPTY)
        self.assertEqual(new_state["board"][3][4], "P")
        self.assertEqual(new_state["turn"], BLACK)

    def test_does_not_mutate_original_state(self):
        state = new_game()
        original_piece = state["board"][1][4]
        apply_move(state, (1, 4), (3, 4))
        self.assertEqual(state["board"][1][4], original_piece)

    def test_raises_on_empty_source_square(self):
        state = new_game()
        with self.assertRaises(ValueError):
            apply_move(state, (4, 4), (5, 4))

    def test_raises_on_wrong_turn(self):
        state = new_game()
        with self.assertRaises(ValueError):
            apply_move(state, (6, 4), (5, 4))  # black's pawn, white's turn

    def test_raises_on_illegal_move(self):
        state = new_game()
        with self.assertRaises(ValueError):
            apply_move(state, (1, 4), (4, 4))  # pawn can't jump 3 squares

    def test_capture_removes_opponent_piece(self):
        state = _empty_state()
        state["board"][4][4] = "P"
        state["board"][5][5] = "p"
        new_state = apply_move(state, (4, 4), (5, 5))
        self.assertEqual(new_state["board"][5][5], "P")


class CastlingTest(unittest.TestCase):
    def _clear_back_rank_between(self, state, cols):
        for col in cols:
            state["board"][0][col] = EMPTY

    def test_kingside_and_queenside_available_with_clear_path(self):
        state = new_game()
        self._clear_back_rank_between(state, [1, 2, 3, 5, 6])
        moves = set(legal_moves(state, 0, 4))
        self.assertIn((0, 6), moves)
        self.assertIn((0, 2), moves)

    def test_kingside_castle_moves_rook_too(self):
        state = new_game()
        self._clear_back_rank_between(state, [1, 2, 3, 5, 6])
        new_state = apply_move(state, (0, 4), (0, 6))
        self.assertEqual(new_state["board"][0][6], "K")
        self.assertEqual(new_state["board"][0][5], "R")
        self.assertEqual(new_state["board"][0][7], EMPTY)
        self.assertFalse(new_state["castling"]["K"])
        self.assertFalse(new_state["castling"]["Q"])

    def test_queenside_castle_moves_rook_too(self):
        state = new_game()
        self._clear_back_rank_between(state, [1, 2, 3, 5, 6])
        new_state = apply_move(state, (0, 4), (0, 2))
        self.assertEqual(new_state["board"][0][2], "K")
        self.assertEqual(new_state["board"][0][3], "R")
        self.assertEqual(new_state["board"][0][0], EMPTY)

    def test_king_having_moved_invalidates_both_sides_even_after_returning(self):
        state = new_game()
        self._clear_back_rank_between(state, [1, 2, 3, 5, 6])
        state = apply_move(state, (0, 4), (0, 5))  # Ke1-f1
        state["turn"] = WHITE  # isolate the king-return probe from black's reply
        state = apply_move(state, (0, 5), (0, 4))  # Kf1-e1
        self.assertFalse(state["castling"]["K"])
        self.assertFalse(state["castling"]["Q"])
        state["turn"] = WHITE
        moves = set(legal_moves(state, 0, 4))
        self.assertNotIn((0, 6), moves)
        self.assertNotIn((0, 2), moves)

    def test_rook_having_moved_invalidates_only_that_side(self):
        state = new_game()
        self._clear_back_rank_between(state, [1, 2, 3, 5, 6])
        state = apply_move(state, (0, 7), (0, 6))  # Rh1-g1
        self.assertFalse(state["castling"]["K"])
        self.assertTrue(state["castling"]["Q"])
        state["turn"] = WHITE
        moves = set(legal_moves(state, 0, 4))
        self.assertIn((0, 2), moves)
        self.assertNotIn((0, 6), moves)

    def test_capturing_rook_on_home_square_invalidates_that_side(self):
        state = _empty_state()
        state["castling"] = {"K": True, "Q": True, "k": True, "q": True}
        state["board"][0][4] = "K"
        state["board"][7][4] = "k"
        state["board"][7][7] = "r"
        state["board"][6][5] = "N"  # can jump to h8
        new_state = apply_move(state, (6, 5), (7, 7))
        self.assertFalse(new_state["castling"]["k"])
        self.assertTrue(new_state["castling"]["q"])

    def test_castling_forbidden_while_in_check(self):
        state = new_game()
        self._clear_back_rank_between(state, [1, 2, 3, 5, 6])
        state["board"][1][4] = EMPTY  # open e-file both sides
        state["board"][6][4] = EMPTY
        state["board"][3][4] = "r"
        moves = set(legal_moves(state, 0, 4))
        self.assertNotIn((0, 6), moves)
        self.assertNotIn((0, 2), moves)

    def test_castling_forbidden_through_attacked_square(self):
        state = new_game()
        self._clear_back_rank_between(state, [1, 2, 3, 5, 6])
        state["board"][1][5] = EMPTY  # open f-file both sides
        state["board"][6][5] = EMPTY
        state["board"][3][5] = "r"  # attacks f1, the kingside transit square
        moves = set(legal_moves(state, 0, 4))
        self.assertNotIn((0, 6), moves)  # kingside forbidden
        self.assertIn((0, 2), moves)  # queenside unaffected

    def test_castling_forbidden_onto_attacked_square(self):
        state = new_game()
        self._clear_back_rank_between(state, [1, 2, 3, 5, 6])
        state["board"][1][6] = EMPTY  # open g-file both sides
        state["board"][6][6] = EMPTY
        state["board"][3][6] = "r"  # attacks g1, the kingside landing square
        moves = set(legal_moves(state, 0, 4))
        self.assertNotIn((0, 6), moves)

    def test_castling_forbidden_if_squares_between_occupied(self):
        state = new_game()  # nothing cleared: bishop/knight still block both sides
        moves = set(legal_moves(state, 0, 4))
        self.assertNotIn((0, 6), moves)
        self.assertNotIn((0, 2), moves)


class EnPassantTest(unittest.TestCase):
    def test_capture_available_immediately_after_two_square_push(self):
        state = new_game()
        state = apply_move(state, (1, 4), (3, 4))  # e2-e4
        state = apply_move(state, (6, 0), (5, 0))  # a7-a6
        state = apply_move(state, (3, 4), (4, 4))  # e4-e5
        state = apply_move(state, (6, 3), (4, 3))  # d7-d5
        self.assertEqual(state["en_passant"], (5, 3))
        self.assertIn((5, 3), legal_moves(state, 4, 4))

    def test_capture_removes_the_passed_pawn(self):
        state = new_game()
        state = apply_move(state, (1, 4), (3, 4))
        state = apply_move(state, (6, 0), (5, 0))
        state = apply_move(state, (3, 4), (4, 4))
        state = apply_move(state, (6, 3), (4, 3))
        new_state = apply_move(state, (4, 4), (5, 3))
        self.assertEqual(new_state["board"][4][3], EMPTY)
        self.assertEqual(new_state["board"][5][3], "P")

    def test_not_available_one_move_later(self):
        state = new_game()
        state = apply_move(state, (1, 4), (3, 4))  # e2-e4
        state = apply_move(state, (6, 3), (4, 3))  # d7-d5
        state = apply_move(state, (3, 4), (4, 4))  # e4-e5 (advance, not capture)
        state = apply_move(state, (6, 0), (5, 0))  # a7-a6, unrelated
        self.assertIsNone(state["en_passant"])
        self.assertNotIn((5, 3), legal_moves(state, 4, 4))


class PromotionTest(unittest.TestCase):
    def _one_step_from_promotion(self):
        state = _empty_state()
        state["board"][0][4] = "K"
        state["board"][7][4] = "k"
        state["board"][6][0] = "P"
        return state

    def test_raises_without_promotion_choice(self):
        state = self._one_step_from_promotion()
        with self.assertRaises(ValueError):
            apply_move(state, (6, 0), (7, 0))

    def test_raises_on_invalid_promotion_choice(self):
        state = self._one_step_from_promotion()
        with self.assertRaises(ValueError):
            apply_move(state, (6, 0), (7, 0), promotion="K")

    def test_promotes_to_requested_piece(self):
        state = self._one_step_from_promotion()
        new_state = apply_move(state, (6, 0), (7, 0), promotion="q")
        self.assertEqual(new_state["board"][7][0], "Q")

    def test_promotion_is_case_insensitive_and_matches_mover_color(self):
        state = _empty_state()
        state["board"][7][4] = "k"
        state["board"][0][4] = "K"
        state["board"][1][0] = "p"
        state["turn"] = BLACK
        new_state = apply_move(state, (1, 0), (0, 0), promotion="n")
        self.assertEqual(new_state["board"][0][0], "n")  # black promotion stays lowercase

    def test_promotion_by_capture(self):
        state = self._one_step_from_promotion()
        state["board"][7][1] = "r"  # capturable on the promotion rank
        new_state = apply_move(state, (6, 0), (7, 1), promotion="r")
        self.assertEqual(new_state["board"][7][1], "R")


class CheckmateStalemateTest(unittest.TestCase):
    def test_fools_mate(self):
        state = new_game()
        state = apply_move(state, (1, 5), (2, 5))  # f2-f3
        state = apply_move(state, (6, 4), (4, 4))  # e7-e5
        state = apply_move(state, (1, 6), (3, 6))  # g2-g4
        state = apply_move(state, (7, 3), (3, 7))  # Qd8-h4#
        self.assertTrue(is_checkmate(state))
        self.assertFalse(is_stalemate(state))
        self.assertEqual(game_status(state), "checkmate")
        self.assertEqual(winner(state), BLACK)

    def test_check_but_not_checkmate(self):
        state = _empty_state()
        state["board"][0][4] = "K"
        state["board"][7][4] = "k"
        state["board"][1][4] = "r"  # checks the white king but white can capture or block
        state["board"][3][3] = "N"  # can hop to e2? actually just verify not checkmate via escape
        self.assertTrue(is_in_check(state, WHITE))
        self.assertFalse(is_checkmate(state))
        self.assertEqual(game_status(state), "check")

    def test_stalemate_king_and_queen_vs_lone_king(self):
        state = _empty_state()
        state["board"][0][0] = "K"  # white king a1, to move
        state["board"][2][1] = "q"  # black queen b3
        state["board"][1][2] = "k"  # black king c2
        self.assertTrue(is_stalemate(state))
        self.assertFalse(is_checkmate(state))
        self.assertEqual(game_status(state), "stalemate")
        self.assertEqual(winner(state), "")

    def test_ongoing_game_has_no_winner(self):
        state = new_game()
        self.assertEqual(game_status(state), "ongoing")
        self.assertEqual(winner(state), "")

    def test_has_any_legal_move_true_at_game_start(self):
        state = new_game()
        self.assertTrue(has_any_legal_move(state, WHITE))


if __name__ == "__main__":
    unittest.main()
