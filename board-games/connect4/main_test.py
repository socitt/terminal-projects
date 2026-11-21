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


class NemoEndToEndTest(unittest.TestCase):
    _CYCLE = "1\n2\n3\n4\n5\n6\n7\n" * 6

    def test_easy_nemo_game_plays_to_an_ending(self):
        result = _run(self._CYCLE, opponent="1")
        self.assertEqual(result.returncode, 0)
        self.assertIn("Nemo played column", result.stdout)
        self.assertRegex(result.stdout, r"(X|O) wins!|Draw!")

    def test_hard_nemo_blocks_a_vertical_four_and_wins(self):
        stack_then_cycle = "1\n1\n1\n1\n" + "2\n3\n4\n5\n6\n7\n" * 6
        for seed in ("1", "2", "3"):
            result = _run(stack_then_cycle, opponent="3", seed=seed)
            self.assertIn("Nemo played column 1", result.stdout)
            self.assertIn("O wins!", result.stdout)


if __name__ == "__main__":
    unittest.main()
