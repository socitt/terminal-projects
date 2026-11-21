import random
import unittest
from types import SimpleNamespace

import nemo
from nemo.search import minimax


def _nim(hard_depth=12):
    """Take 1-3 from a pile; whoever takes the last one wins. A pile that
    is a multiple of 4 is lost for the player to move, so optimal play is
    known exactly. State: (pile, player to move)."""
    def moves(state):
        return [t for t in (1, 2, 3) if t <= state[0]]

    def play(state, take):
        pile, player = state
        return (pile - take, 1 - player)

    def outcome(state):
        pile, player = state
        return (1 - player) if pile == 0 else None  # last taker won

    return SimpleNamespace(
        moves=moves, play=play, outcome=outcome,
        to_move=lambda s: s[1], evaluate=lambda s, p: 0.0,
        HARD_DEPTH=hard_depth,
    )


class EasyTest(unittest.TestCase):
    def test_plays_every_legal_move_eventually_and_only_those(self):
        rng = random.Random(1)
        seen = {minimax.choose_move(_nim(), (10, 0), nemo.EASY, rng)
                for _ in range(60)}
        self.assertEqual(seen, {1, 2, 3})


class MediumTest(unittest.TestCase):
    def test_takes_a_win_in_one(self):
        for pile in (1, 2, 3):
            move = minimax.choose_move(_nim(), (pile, 0), nemo.MEDIUM,
                                       random.Random(pile))
            self.assertEqual(move, pile)

    def test_takes_the_win_over_a_safe_quiet_move(self):
        # Unlike Nim's 1-3, here a quiet move is also safe, so only the
        # win-in-one check (not the threat filter) picks "win".
        adapter = SimpleNamespace(
            moves=lambda s: {"start": ["quiet", "win"], "calm": ["wait"]}[s],
            play=lambda s, m: {"quiet": "calm", "win": "won", "wait": "start"}[m],
            to_move=lambda s: 1 if s == "calm" else 0,
            outcome=lambda s: 0 if s == "won" else None,
            evaluate=lambda s, p: 0.0, HARD_DEPTH=1,
        )
        for seed in range(20):
            self.assertEqual(minimax.choose_move(adapter, "start", nemo.MEDIUM,
                                                 random.Random(seed)), "win")

    def test_never_hands_over_a_win_in_one(self):
        # From 5, taking 2 or 3 leaves the opponent 3 or 2: a win in one.
        for seed in range(30):
            move = minimax.choose_move(_nim(), (5, 0), nemo.MEDIUM,
                                       random.Random(seed))
            self.assertEqual(move, 1)

    def test_falls_back_to_any_move_when_every_move_loses(self):
        # From 4 every move hands over a win; still has to move.
        move = minimax.choose_move(_nim(), (4, 0), nemo.MEDIUM, random.Random(0))
        self.assertIn(move, (1, 2, 3))


class HardTest(unittest.TestCase):
    def test_plays_optimally_from_every_winning_pile(self):
        for pile in range(1, 13):
            if pile % 4 == 0:
                continue
            for seed in range(3):
                move = minimax.choose_move(_nim(), (pile, 0), nemo.HARD,
                                           random.Random(seed))
                self.assertEqual((pile - move) % 4, 0, (pile, move))

    def test_beats_easy_from_a_winning_start(self):
        adapter, rng = _nim(), random.Random(7)
        for _ in range(20):
            state = (11, 0)
            while adapter.outcome(state) is None:
                level = nemo.HARD if state[1] == 0 else nemo.EASY
                state = adapter.play(state, minimax.choose_move(adapter, state,
                                                                level, rng))
            self.assertEqual(adapter.outcome(state), 0)

    def test_prefers_the_sooner_win(self):
        # "now" wins at once; "later" keeps the turn and wins next move.
        # Both are certain wins, so only the depth bonus separates them.
        adapter = SimpleNamespace(
            moves=lambda s: {"start": ["later", "now"], "again": ["win"]}[s],
            play=lambda s, m: {"later": "again", "now": "won", "win": "won"}[m],
            to_move=lambda s: 0,
            outcome=lambda s: 0 if s == "won" else None,
            evaluate=lambda s, p: 0.0,
            HARD_DEPTH=3,
        )
        for seed in range(10):
            self.assertEqual(minimax.choose_move(adapter, "start", nemo.HARD,
                                                 random.Random(seed)), "now")

    def test_depth_one_falls_back_to_the_heuristic(self):
        adapter = _nim(hard_depth=1)
        adapter.evaluate = lambda s, p: -s[0]  # "smaller pile is better"
        move = minimax.choose_move(adapter, (9, 0), nemo.HARD, random.Random(0))
        self.assertEqual(move, 3)


class ExtraTurnTest(unittest.TestCase):
    """A move that keeps the turn must not have its value negated."""

    def test_value_is_not_negated_when_the_mover_keeps_the_turn(self):
        # "bonus" keeps the turn and leads to a won position; "plain" passes
        # the turn into a lost one. Only a correct sign keeps "bonus" best.
        def play(state, move):
            return {"start": {"bonus": "again", "plain": "theirs"},
                    "again": {"finish": "won"}}[state][move]

        adapter = SimpleNamespace(
            moves=lambda s: {"start": ["bonus", "plain"],
                             "again": ["finish"]}[s],
            play=play,
            to_move=lambda s: 1 if s == "theirs" else 0,
            outcome=lambda s: {"won": 0, "theirs": 1}.get(s),
            evaluate=lambda s, p: 0.0,
            HARD_DEPTH=3,
        )
        self.assertEqual(
            minimax.choose_move(adapter, "start", nemo.HARD, random.Random(0)),
            "bonus")


    def test_kept_turn_inside_the_tree_keeps_its_sign(self):
        # "a" hands the opponent a position where their bonus move keeps
        # the turn and then wins; "b" is a draw. Correct play is "b", and
        # only a correct sign two plies down sees that "a" loses.
        nxt = {"a": "A", "b": "drawn", "bonus": "A2", "finish": "won1"}
        adapter = SimpleNamespace(
            moves=lambda s: {"start": ["a", "b"], "A": ["bonus"],
                             "A2": ["finish"]}[s],
            play=lambda s, m: nxt[m],
            to_move=lambda s: 1 if s in ("A", "A2") else 0,
            outcome=lambda s: {"won1": 1, "drawn": "draw"}.get(s),
            evaluate=lambda s, p: 0.0,
            HARD_DEPTH=4,
        )
        self.assertEqual(
            minimax.choose_move(adapter, "start", nemo.HARD, random.Random(0)),
            "b")

class StochasticTest(unittest.TestCase):
    """Dice games: search the mover's own kept turns, stop at a turn
    change and evaluate there instead of guessing the opponent's roll."""

    def _game(self):
        # Two dice for player 0. "safe" then "safe" ends level; "risky"
        # first looks bad but sets up "big", the best finish of the turn.
        nxt = {("start", "safe"): "s1", ("start", "risky"): "r1",
               ("s1", "safe"): "end_ok", ("r1", "big"): "end_great",
               ("r1", "safe"): "end_bad"}
        values = {"s1": 0.1, "r1": -0.5, "end_ok": 0.2, "end_great": 0.9,
                  "end_bad": -0.9}
        calls = []

        def to_move(s):
            return 1 if s.startswith("end") else 0

        def evaluate(s, p):
            calls.append(s)
            return values[s] if p == 0 else -values[s]

        adapter = SimpleNamespace(
            moves=lambda s: {"start": ["safe", "risky"], "s1": ["safe"],
                             "r1": ["safe", "big"]}[s],
            play=lambda s, m: nxt[(s, m)],
            to_move=to_move, outcome=lambda s: None,
            evaluate=evaluate, HARD_DEPTH=3, STOCHASTIC=True,
        )
        return adapter, calls

    def test_hard_searches_the_rest_of_its_own_roll(self):
        adapter, _ = self._game()
        self.assertEqual(
            minimax.choose_move(adapter, "start", nemo.HARD, random.Random(0)),
            "risky")

    def test_search_never_looks_past_the_turn_change(self):
        # The opponent's states have no moves defined: recursing into one
        # would raise KeyError. Every turn-ending state is evaluated.
        adapter, calls = self._game()
        minimax.choose_move(adapter, "start", nemo.HARD, random.Random(0))
        self.assertTrue({"end_ok", "end_great", "end_bad"} <= set(calls))

class GuardTest(unittest.TestCase):
    def test_unknown_level_is_rejected(self):
        with self.assertRaises(ValueError):
            minimax.choose_move(_nim(), (5, 0), 4, random.Random(0))

    def test_no_legal_moves_is_rejected(self):
        with self.assertRaises(ValueError):
            minimax.choose_move(_nim(), (0, 0), nemo.EASY, random.Random(0))


if __name__ == "__main__":
    unittest.main()
