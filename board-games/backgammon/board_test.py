import random
import unittest

from board import (
    all_checkers_in_home,
    bar_entry_point,
    bear_off,
    can_bear_off,
    can_enter_from_bar,
    can_move,
    destination,
    dice_to_moves,
    direction,
    enter_from_bar,
    home_range,
    is_blocked,
    is_game_over,
    legal_actions,
    move_checker,
    new_game,
    opponent,
    pip_distance,
    point_count,
    point_owner,
    roll_dice,
    winner,
)


def _state(points=None, bar=None, off=None):
    """Build a custom state. `points` is a {point: signed_count} dict
    overlaid on an otherwise-empty board."""
    board_points = [0] * 25
    for point, value in (points or {}).items():
        board_points[point] = value
    return {
        "points": board_points,
        "bar": dict(bar) if bar else {"X": 0, "O": 0},
        "off": dict(off) if off else {"X": 0, "O": 0},
    }


class _FakeRng:
    def __init__(self, values):
        self._values = list(values)

    def randint(self, low, high):
        return self._values.pop(0)


class NewGameTest(unittest.TestCase):
    def test_checker_counts_are_fifteen_each(self):
        state = new_game()
        x_count = sum(v for v in state["points"] if v > 0)
        o_count = sum(-v for v in state["points"] if v < 0)
        self.assertEqual(x_count, 15)
        self.assertEqual(o_count, 15)

    def test_standard_starting_positions(self):
        state = new_game()
        self.assertEqual(state["points"][24], 2)
        self.assertEqual(state["points"][13], 5)
        self.assertEqual(state["points"][8], 3)
        self.assertEqual(state["points"][6], 5)
        self.assertEqual(state["points"][1], -2)
        self.assertEqual(state["points"][12], -5)
        self.assertEqual(state["points"][17], -3)
        self.assertEqual(state["points"][19], -5)

    def test_bar_and_off_start_empty(self):
        state = new_game()
        self.assertEqual(state["bar"], {"X": 0, "O": 0})
        self.assertEqual(state["off"], {"X": 0, "O": 0})


class OpponentDirectionHomeTest(unittest.TestCase):
    def test_opponent(self):
        self.assertEqual(opponent("X"), "O")
        self.assertEqual(opponent("O"), "X")

    def test_direction(self):
        self.assertEqual(direction("X"), -1)
        self.assertEqual(direction("O"), 1)

    def test_home_range(self):
        self.assertEqual(list(home_range("X")), [1, 2, 3, 4, 5, 6])
        self.assertEqual(list(home_range("O")), [19, 20, 21, 22, 23, 24])


class PointHelpersTest(unittest.TestCase):
    def test_point_owner_and_count(self):
        state = _state({5: 3, 10: -2})
        self.assertEqual(point_owner(state, 5), "X")
        self.assertEqual(point_count(state, 5), 3)
        self.assertEqual(point_owner(state, 10), "O")
        self.assertEqual(point_count(state, 10), 2)

    def test_point_owner_none_when_empty(self):
        state = _state()
        self.assertIsNone(point_owner(state, 7))
        self.assertEqual(point_count(state, 7), 0)


class IsBlockedTest(unittest.TestCase):
    def test_blocked_with_two_or_more_opponent_checkers(self):
        state = _state({10: -2})
        self.assertTrue(is_blocked(state, "X", 10))

    def test_not_blocked_with_a_single_opponent_checker_a_blot(self):
        state = _state({10: -1})
        self.assertFalse(is_blocked(state, "X", 10))

    def test_not_blocked_on_own_checkers(self):
        state = _state({10: 4})
        self.assertFalse(is_blocked(state, "X", 10))

    def test_not_blocked_on_empty_point(self):
        state = _state()
        self.assertFalse(is_blocked(state, "X", 10))


class DestinationAndEntryPointTest(unittest.TestCase):
    def test_destination_moves_toward_home_per_player(self):
        self.assertEqual(destination("X", 10, 4), 6)
        self.assertEqual(destination("O", 10, 4), 14)

    def test_bar_entry_point_per_player(self):
        self.assertEqual(bar_entry_point("X", 1), 24)
        self.assertEqual(bar_entry_point("X", 6), 19)
        self.assertEqual(bar_entry_point("O", 1), 1)
        self.assertEqual(bar_entry_point("O", 6), 6)


class CanMoveTest(unittest.TestCase):
    def test_true_for_open_destination(self):
        state = _state({10: 1})
        self.assertTrue(can_move(state, "X", 10, 4))

    def test_false_no_checker_at_source(self):
        state = _state()
        self.assertFalse(can_move(state, "X", 10, 4))

    def test_false_source_belongs_to_opponent(self):
        state = _state({10: -1})
        self.assertFalse(can_move(state, "X", 10, 4))

    def test_false_destination_blocked(self):
        state = _state({10: 1, 6: -2})
        self.assertFalse(can_move(state, "X", 10, 4))

    def test_true_destination_is_a_blot_hit_allowed(self):
        state = _state({10: 1, 6: -1})
        self.assertTrue(can_move(state, "X", 10, 4))

    def test_false_destination_out_of_range(self):
        state = _state({3: 1})
        self.assertFalse(can_move(state, "X", 3, 5))
        state = _state({22: -1})
        self.assertFalse(can_move(state, "O", 22, 5))

    def test_false_when_checkers_on_bar_must_enter_first(self):
        state = _state({10: 1}, bar={"X": 1, "O": 0})
        self.assertFalse(can_move(state, "X", 10, 4))


class MoveCheckerTest(unittest.TestCase):
    def test_relocates_checker(self):
        state = _state({10: 1})
        new_state = move_checker(state, "X", 10, 4)
        self.assertEqual(new_state["points"][10], 0)
        self.assertEqual(new_state["points"][6], 1)

    def test_stacks_on_own_point(self):
        state = _state({10: 1, 6: 2})
        new_state = move_checker(state, "X", 10, 4)
        self.assertEqual(new_state["points"][6], 3)

    def test_hits_lone_opponent_checker(self):
        state = _state({10: 1, 6: -1})
        new_state = move_checker(state, "X", 10, 4)
        self.assertEqual(new_state["points"][6], 1)
        self.assertEqual(new_state["bar"]["O"], 1)

    def test_does_not_mutate_original_state(self):
        state = _state({10: 1, 6: -1})
        move_checker(state, "X", 10, 4)
        self.assertEqual(state["points"][10], 1)
        self.assertEqual(state["points"][6], -1)
        self.assertEqual(state["bar"]["O"], 0)

    def test_raises_on_illegal_move(self):
        state = _state({10: 1, 6: -2})
        with self.assertRaises(ValueError):
            move_checker(state, "X", 10, 4)


class BarEntryTest(unittest.TestCase):
    def test_can_enter_when_target_open(self):
        state = _state(bar={"X": 1, "O": 0})
        self.assertTrue(can_enter_from_bar(state, "X", 3))

    def test_cannot_enter_when_target_blocked(self):
        state = _state({22: -2}, bar={"X": 1, "O": 0})
        self.assertFalse(can_enter_from_bar(state, "X", 3))

    def test_cannot_enter_when_no_checkers_on_bar(self):
        state = _state(bar={"X": 0, "O": 0})
        self.assertFalse(can_enter_from_bar(state, "X", 3))

    def test_enter_places_checker_and_decrements_bar(self):
        state = _state(bar={"X": 1, "O": 0})
        new_state = enter_from_bar(state, "X", 3)
        self.assertEqual(new_state["bar"]["X"], 0)
        self.assertEqual(new_state["points"][22], 1)

    def test_enter_hits_lone_opponent_checker(self):
        state = _state({22: -1}, bar={"X": 1, "O": 0})
        new_state = enter_from_bar(state, "X", 3)
        self.assertEqual(new_state["points"][22], 1)
        self.assertEqual(new_state["bar"]["O"], 1)

    def test_raises_when_illegal(self):
        state = _state({22: -2}, bar={"X": 1, "O": 0})
        with self.assertRaises(ValueError):
            enter_from_bar(state, "X", 3)

    def test_closed_board_blocks_every_die(self):
        # O holds all six points of X's entry zone (19-24) with 2+ each.
        state = _state(
            {19: -2, 20: -2, 21: -2, 22: -2, 23: -2, 24: -2},
            bar={"X": 1, "O": 0},
        )
        for die in range(1, 7):
            self.assertFalse(can_enter_from_bar(state, "X", die), f"die={die}")


class AllCheckersInHomeTest(unittest.TestCase):
    def test_false_with_checker_on_bar(self):
        state = _state({3: 1}, bar={"X": 1, "O": 0})
        self.assertFalse(all_checkers_in_home(state, "X"))

    def test_false_with_checker_outside_home(self):
        state = _state({3: 1, 10: 1})
        self.assertFalse(all_checkers_in_home(state, "X"))

    def test_true_when_all_within_home_and_no_bar(self):
        state = _state({1: 2, 4: 3})
        self.assertTrue(all_checkers_in_home(state, "X"))

    def test_true_for_opponent_home_range(self):
        state = _state({19: -3, 24: -2})
        self.assertTrue(all_checkers_in_home(state, "O"))


class BearOffTest(unittest.TestCase):
    def test_pip_distance(self):
        self.assertEqual(pip_distance("X", 4), 4)
        self.assertEqual(pip_distance("O", 21), 4)

    def test_false_when_not_all_checkers_in_home(self):
        state = _state({4: 1, 10: 1})
        self.assertFalse(can_bear_off(state, "X", 4, 4))

    def test_false_when_checker_on_bar(self):
        state = _state({4: 1}, bar={"X": 1, "O": 0})
        self.assertFalse(can_bear_off(state, "X", 4, 4))

    def test_true_with_exact_die(self):
        state = _state({4: 1})
        self.assertTrue(can_bear_off(state, "X", 4, 4))

    def test_false_when_die_is_too_small(self):
        state = _state({4: 1})
        self.assertFalse(can_bear_off(state, "X", 4, 3))

    def test_overshoot_allowed_when_no_farther_checker(self):
        state = _state({4: 1})
        self.assertTrue(can_bear_off(state, "X", 4, 6))

    def test_overshoot_blocked_when_a_farther_checker_exists(self):
        # Checker on point 6 (distance 6) is farther than point 4
        # (distance 4), so point 4 cannot be borne off with a die of 6.
        state = _state({4: 1, 6: 1})
        self.assertFalse(can_bear_off(state, "X", 4, 6))
        self.assertTrue(can_bear_off(state, "X", 6, 6))

    def test_overshoot_rule_mirrored_for_o(self):
        # O's home is 19-24; point 21 has distance 4, point 19 has
        # distance 6 (farther).
        state = _state({21: -1, 19: -1})
        self.assertFalse(can_bear_off(state, "O", 21, 6))
        self.assertTrue(can_bear_off(state, "O", 19, 6))

    def test_bear_off_increments_off_and_removes_checker(self):
        state = _state({4: 1})
        new_state = bear_off(state, "X", 4, 4)
        self.assertEqual(new_state["points"][4], 0)
        self.assertEqual(new_state["off"]["X"], 1)

    def test_bear_off_does_not_mutate_original_state(self):
        state = _state({4: 1})
        bear_off(state, "X", 4, 4)
        self.assertEqual(state["points"][4], 1)
        self.assertEqual(state["off"]["X"], 0)

    def test_raises_when_illegal(self):
        state = _state({4: 1, 6: 1})
        with self.assertRaises(ValueError):
            bear_off(state, "X", 4, 6)


class GameOverTest(unittest.TestCase):
    def test_not_over_initially(self):
        self.assertFalse(is_game_over(new_game()))
        self.assertEqual(winner(new_game()), "")

    def test_over_when_a_player_has_borne_off_all_fifteen(self):
        state = _state(off={"X": 15, "O": 3})
        self.assertTrue(is_game_over(state))
        self.assertEqual(winner(state), "X")

    def test_no_winner_when_neither_has_reached_fifteen(self):
        state = _state(off={"X": 10, "O": 12})
        self.assertFalse(is_game_over(state))
        self.assertEqual(winner(state), "")


class DiceToMovesTest(unittest.TestCase):
    def test_double_gives_four_moves(self):
        self.assertEqual(dice_to_moves(3, 3), [3, 3, 3, 3])

    def test_non_double_gives_two_moves_in_order(self):
        self.assertEqual(dice_to_moves(2, 5), [2, 5])
        self.assertEqual(dice_to_moves(5, 2), [5, 2])


class RollDiceTest(unittest.TestCase):
    def test_returns_values_from_injected_rng(self):
        self.assertEqual(roll_dice(_FakeRng([3, 5])), (3, 5))

    def test_real_random_stays_in_range(self):
        for _ in range(50):
            d1, d2 = roll_dice(random)
            self.assertTrue(1 <= d1 <= 6)
            self.assertTrue(1 <= d2 <= 6)


class LegalActionsTest(unittest.TestCase):
    def test_matches_can_move_on_open_board(self):
        state = _state({10: 1})
        self.assertEqual(legal_actions(state, "X", 4), [("move", 10)])

    def test_only_enter_offered_when_checkers_on_bar(self):
        state = _state({10: 1}, bar={"X": 1, "O": 0})
        self.assertEqual(legal_actions(state, "X", 3), [("enter",)])

    def test_empty_when_bar_checkers_and_entry_blocked(self):
        state = _state(
            {19: -2, 20: -2, 21: -2, 22: -2, 23: -2, 24: -2},
            bar={"X": 1, "O": 0},
        )
        self.assertEqual(legal_actions(state, "X", 3), [])

    def test_includes_bear_off_when_eligible(self):
        state = _state({4: 1})
        self.assertEqual(legal_actions(state, "X", 4), [("bear_off", 4)])

    def test_empty_when_no_checkers_for_player(self):
        state = _state({10: -1})
        self.assertEqual(legal_actions(state, "X", 4), [])


if __name__ == "__main__":
    unittest.main()
