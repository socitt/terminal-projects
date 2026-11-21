"""End-to-end tests for main.py: run the real script as a subprocess
with piped input, same as a player typing at the terminal, rather than
importing main.py's functions directly. This is the only coverage
main.py gets -- board_test.py only exercises board.py.
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
    def test_x_wins_top_row(self):
        # X: 1, 2, 3 (top row). O never blocks.
        result = _run("1\n4\n2\n5\n3\n")
        self.assertEqual(result.returncode, 0)
        self.assertIn("X wins!", result.stdout)
        self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_full_board_draw(self):
        # X O X / X O O / O X X -- no line is ever monochrome.
        result = _run("1\n2\n3\n5\n4\n6\n8\n7\n9\n")
        self.assertEqual(result.returncode, 0)
        self.assertIn("Draw!", result.stdout)
        self.assertNotIn("Traceback", result.stdout + result.stderr)


class NemoEndToEndTest(unittest.TestCase):
    # Every cell, repeatedly: occupied ones are rejected and reprompted,
    # so the human always has a legal move to make.
    _EVERY_CELL = "5\n1\n2\n3\n4\n6\n7\n8\n9\n" * 3

    def test_menu_offers_every_nemo_level(self):
        result = _run(self._EVERY_CELL, opponent="1")
        for name in ("easy", "medium", "hard"):
            self.assertIn(f"Nemo ({name})", result.stdout)

    def test_hard_nemo_never_loses(self):
        for seed in ("1", "2", "3"):
            result = _run(self._EVERY_CELL, opponent="3", seed=seed)
            self.assertEqual(result.returncode, 0)
            self.assertIn("Nemo played", result.stdout)
            self.assertNotIn("X wins!", result.stdout)

    def test_nemo_cam_is_shown(self):
        result = _run(self._EVERY_CELL, opponent="2")
        self.assertRegex(result.stdout, r"Nemo is (gloating|thinking|worried|sulking)|Nemo likes this")


if __name__ == "__main__":
    unittest.main()
