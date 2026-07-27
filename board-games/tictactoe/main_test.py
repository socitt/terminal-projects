"""End-to-end tests for main.py: run the real script as a subprocess
with piped input, same as a player typing at the terminal, rather than
importing main.py's functions directly. This is the only coverage
main.py gets -- board_test.py only exercises board.py.
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


if __name__ == "__main__":
    unittest.main()
