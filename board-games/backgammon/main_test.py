"""End-to-end test for main.py: run the real script as a subprocess
with piped input, same as a player typing at the terminal, rather
than importing main.py's functions directly. This is the only
coverage main.py gets -- board_test.py only exercises board.py.

Unlike tictactoe/connect4/go, backgammon's dice make an exact
scripted outcome impractical, so this doesn't assert who wins or how
-- only that a full real game, played by always picking the first
offered action, runs to completion cleanly. Every action is a real
board.py-validated move (enter/move/bear off), so total pips strictly
decrease each turn: the game is guaranteed to terminate, just not
which player wins or how many turns it takes. 2500 input lines is a
generous margin over any observed run (typically well under 1000
underlying die-plays).
"""

import os
import subprocess
import sys
import unittest
from pathlib import Path

MAIN = Path(__file__).resolve().parent / "main.py"


def _run(input_text, timeout=25, opponent="0", seed="1"):
    """`opponent` answers main.py's opening prompt: "0" for a second
    human (every scenario written before Nemo existed), "1"-"3" for
    Nemo, whose choices TP_NEMO_SEED makes repeatable."""
    return subprocess.run(
        [sys.executable, str(MAIN)],
        input=f"{opponent}\n{input_text}",
        capture_output=True,
        text=True,
        timeout=timeout,
        env={**os.environ, "TP_NEMO_SEED": seed},
    )


class MainEndToEndTest(unittest.TestCase):
    def test_full_game_always_picking_first_option_reaches_a_winner(self):
        result = _run("1\n" * 2500)
        self.assertEqual(result.returncode, 0)
        self.assertTrue(
            "X wins!" in result.stdout or "O wins!" in result.stdout,
            "no winner announced in output",
        )
        self.assertNotIn("Traceback", result.stdout + result.stderr)


class NemoEndToEndTest(unittest.TestCase):
    def test_full_game_against_hard_nemo_reaches_a_winner(self):
        result = _run("1\n" * 2500, opponent="3")
        self.assertEqual(result.returncode, 0)
        self.assertIn("Nemo: ", result.stdout)
        self.assertRegex(result.stdout, r"(X|O) wins!")
        self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_a_seeded_game_repeats_exactly(self):
        # Dice and Nemo share the TP_NEMO_SEED rng, so a whole game --
        # dice included -- is reproducible, which it never was before.
        first = _run("1\n" * 2500, opponent="2", seed="9")
        second = _run("1\n" * 2500, opponent="2", seed="9")
        other = _run("1\n" * 2500, opponent="2", seed="10")
        self.assertEqual(first.stdout, second.stdout)
        self.assertNotEqual(first.stdout, other.stdout)


if __name__ == "__main__":
    unittest.main()
