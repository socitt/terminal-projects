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
    def test_horizontal_win(self):
        # X stacks under O in columns 1-3, then wins with column 4 --
        # X's bottom-row pieces land at cols 1,2,3,4 in a row.
        result = _run("1\n1\n2\n2\n3\n3\n4\n")
        self.assertEqual(result.returncode, 0)
        self.assertIn("X wins!", result.stdout)
        self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_full_column_rejected_then_game_continues_to_win(self):
        # Fill column 1 completely (6 alternating drops, no vertical
        # win since marks alternate), then X's 7th attempt at column 1
        # must be rejected without crashing before X goes on to win
        # via columns 2-4.
        result = _run("1\n1\n1\n1\n1\n1\n1\n2\n2\n3\n3\n4\n")
        self.assertEqual(result.returncode, 0)
        self.assertIn("X wins!", result.stdout)
        self.assertNotIn("Traceback", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
