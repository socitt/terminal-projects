"""End-to-end tests for main.py: run the real script as a subprocess
with piped input, same as a player typing at the terminal, rather than
importing main.py's functions directly. This is the only coverage
main.py gets -- board_test.py only exercises board.py.

Both scenarios below were validated interactively (manual piped-input
runs, output inspected by hand) before being encoded here.
"""

import subprocess
import sys
import unittest
from pathlib import Path

MAIN = Path(__file__).resolve().parent / "main.py"


def _run(input_text, timeout=10):
    return subprocess.run(
        [sys.executable, str(MAIN)],
        input=input_text,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


class MainEndToEndTest(unittest.TestCase):
    def test_illegal_move_then_pass_pass_scores_correctly(self):
        # Black plays (col5,row5), white plays (col3,row3), black's
        # retry at (col5,row5) is rejected (occupied), then both pass
        # to end the game. Neither stone borders the other, so all
        # remaining territory is neutral (dame): black=1, white=1+5.5
        # komi=6.5.
        result = _run("5\n5\n3\n3\n5\n5\n\np\np\n")
        self.assertEqual(result.returncode, 0)
        self.assertIn("Illegal move: point is occupied", result.stdout)
        self.assertIn("Black: 1  White: 6.5", result.stdout)
        self.assertIn("W wins!", result.stdout)
        self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_corner_capture(self):
        # Black plays two neutral stones, white takes the corner,
        # black surrounds and captures it, then both pass.
        result = _run("9\n9\n1\n1\n2\n1\n8\n9\n1\n2\np\np\n")
        self.assertEqual(result.returncode, 0)
        # Row 1 after capture: (1,1) empty, (1,2) black, rest empty.
        self.assertIn("1 . B . . . . . . .", result.stdout)
        self.assertIn("Black: 4  White: 6.5", result.stdout)
        self.assertIn("W wins!", result.stdout)
        self.assertNotIn("Traceback", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
