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

import subprocess
import sys
import unittest
from pathlib import Path

MAIN = Path(__file__).resolve().parent / "main.py"


def _run(input_text, timeout=25):
    return subprocess.run(
        [sys.executable, str(MAIN)],
        input=input_text,
        capture_output=True,
        text=True,
        timeout=timeout,
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


if __name__ == "__main__":
    unittest.main()
