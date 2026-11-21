"""End-to-end tests for main.py: run the real script as a subprocess
with piped input, same as a player typing at the terminal, rather than
importing main.py's functions directly. This is the only coverage
main.py gets -- board_test.py only exercises board.py.

Both scenarios below were validated interactively (manual piped-input
runs against the real script, output inspected by hand) before being
encoded here. Deep rule coverage (en passant, castling, promotion
mechanics) already lives in board_test.py's 55 tests; these two only
exercise the integration wiring: rendering, the file/rank prompt flow,
the illegal-move retry path, the promotion prompt, and a clean
checkmate ending.
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
    def test_illegal_move_then_fools_mate(self):
        # White first tries a2-a5 (illegal: pawns can't jump 3
        # squares), gets rejected, then Fool's Mate plays out:
        # f2-f3 e7-e5 g2-g4 Qd8-h4#.
        keys = "a\n2\na\n5\n\n" "f\n2\nf\n3\ne\n7\ne\n5\ng\n2\ng\n4\nd\n8\nh\n4\n"
        result = _run(keys)
        self.assertEqual(result.returncode, 0)
        self.assertIn("Illegal move: illegal move", result.stdout)
        self.assertIn("Checkmate! Black wins!", result.stdout)
        self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_promotion_then_checkmate(self):
        # A queenside pawn storm (a4, axb5, b6, b7, bxa8=Q) promotes
        # by capturing black's a8 rook, then a standard Scholar's-Mate
        # pattern on the kingside (e4, Bc4, Qh5, Qxf7#) delivers
        # checkmate -- the black king never moves and stays boxed in
        # by its own untouched d7/e7/f7/d8/f8 pieces throughout, so a
        # single undefended check to e8 is immediately mate.
        moves = [
            "a2a4", "b7b5", "a4b5", "h7h6", "b5b6", "h6h5", "b6b7", "h5h4",
            "b7a8q", "h4h3", "e2e4", "h3g2", "f1c4", "a7a6", "d1h5", "a6a5",
            "h5f7",
        ]
        keys = "".join("\n".join(list(m)) + "\n" for m in moves)
        result = _run(keys)
        self.assertEqual(result.returncode, 0)
        self.assertIn("Promote to (q/r/b/n): ", result.stdout)
        self.assertIn("Checkmate! White wins!", result.stdout)
        self.assertNotIn("Traceback", result.stdout + result.stderr)


class NemoEndToEndTest(unittest.TestCase):
    def test_hard_nemo_finds_the_fools_mate(self):
        # 1. f3 ... 2. g4 ... leaves Qh4 mate; hard Nemo takes it.
        moves = "f\n2\nf\n3\n" "g\n2\ng\n4\n" "a\n2\na\n3\n"
        for seed in ("1", "2"):
            result = _run(moves, opponent="3", seed=seed)
            self.assertEqual(result.returncode, 0)
            self.assertIn("Nemo played d8-h4", result.stdout)
            self.assertIn("Checkmate! Black wins!", result.stdout)


if __name__ == "__main__":
    unittest.main()
