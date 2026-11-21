"""End-to-end tests for main.py: run the real script as a subprocess
with piped input, same as a player typing at the terminal, rather than
importing main.py's functions directly. This is the only coverage
main.py gets -- board_test.py only exercises board.py.

Both scenarios below were validated interactively (manual piped-input
runs, output inspected by hand) before being encoded here.
"""

import os
import subprocess
import sys
import unittest
from pathlib import Path

MAIN = Path(__file__).resolve().parent / "main.py"


def _run(input_text, timeout=10, opponent="0", seed="1"):
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


class NemoEndToEndTest(unittest.TestCase):
    def test_hard_nemo_passes_to_win_on_komi(self):
        result = _run("p\n", opponent="3")
        self.assertEqual(result.returncode, 0)
        self.assertIn("Nemo passed", result.stdout)
        self.assertIn("W wins!", result.stdout)

    def test_hard_nemo_answers_a_stone_then_passes_once_ahead(self):
        # After one stone each the empty board borders both colours, so
        # it's neutral and komi wins it for White: Nemo stops there.
        for seed in ("1", "2", "3"):
            result = _run("5\n5\n" + "p\n" * 20, opponent="3", seed=seed)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout.count("Nemo played"), 1)
            self.assertIn("W wins!", result.stdout)


if __name__ == "__main__":
    unittest.main()
